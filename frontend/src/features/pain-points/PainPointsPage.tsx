import React, { useEffect, useState, useMemo } from 'react';
import { AlertTriangle, Search, CalendarDays, Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { fetchWeeklySpikeData, CategoryData, WeeklyPoint } from './spikesService';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

// ── Derive year/month options from real data ────────────────────────────────
function getYearMonthOptions(data: CategoryData[]) {
  const set = new Set<string>();
  data.forEach(cat => cat.points.forEach(p => {
    const d = new Date(p.date);
    set.add(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
  }));
  return Array.from(set).sort();
}

export default function PainPointsPage() {
  const [data, setData] = useState<CategoryData[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedPoint, setSelectedPoint] = useState<WeeklyPoint | null>(null);

  // Date filter state — start/end as YYYY-MM-DD strings (empty = no filter)
  const [filterFrom, setFilterFrom] = useState('');
  const [filterTo, setFilterTo] = useState('');
  // Quick "no data for range" message
  const [noDataMsg, setNoDataMsg] = useState('');

  const navigate = useNavigate();

  // All unique observation dates across the whole dataset (sorted)
  const allObservationDates = useMemo(() => {
    if (!data) return [];
    const s = new Set<string>();
    data.forEach(c => c.points.forEach(p => s.add(p.date)));
    return Array.from(s).sort();
  }, [data]);

  // Global min/max (earliest + latest real observation)
  const dataDateRange = useMemo(() => {
    if (allObservationDates.length === 0) return { min: '', max: '' };
    return { min: allObservationDates[0], max: allObservationDates[allObservationDates.length - 1] };
  }, [allObservationDates]);

  // Dates available for the currently selected category
  const categoryDates = useMemo(() => {
    if (!data) return [];
    const cat = data.find(c => c.category === selectedCategory);
    return cat ? cat.points.map(p => p.date).sort() : [];
  }, [data, selectedCategory]);

  useEffect(() => {
    fetchWeeklySpikeData()
      .then(d => {
        setData(d);
        if (d.length > 0) {
          setSelectedCategory(d[0].category);
          setSelectedPoint(d[0].points[d[0].points.length - 1]);
        }
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, []);

  // Apply date filter to the current category's points
  // String comparison works correctly for YYYY-MM-DD (lexicographic == chronological)
  const chartData = useMemo(() => {
    if (!data) return [];
    const cat = data.find(c => c.category === selectedCategory);
    if (!cat) return [];

    let pts = cat.points;
    if (filterFrom) pts = pts.filter(p => p.date >= filterFrom);
    if (filterTo)   pts = pts.filter(p => p.date <= filterTo);

    return pts;
  }, [data, selectedCategory, filterFrom, filterTo]);

  // Compute the empty-state message separately (avoids setState-in-useMemo anti-pattern)
  const emptyStateMsg = useMemo(() => {
    if (!data || chartData.length > 0 || (!filterFrom && !filterTo)) return null;
    const catMin = categoryDates[0] || '';
    const catMax = categoryDates[categoryDates.length - 1] || '';
    return {
      selectedRange: `${filterFrom || '(start)'} → ${filterTo || '(end)'}`,
      categoryRange: catMin && catMax ? `${catMin} → ${catMax}` : null,
      categoryDates,
    };
  }, [data, chartData.length, filterFrom, filterTo, categoryDates]);

  const handleCategoryClick = (categoryName: string) => {
    setSelectedCategory(categoryName);
    const catData = data?.find(c => c.category === categoryName);
    if (catData && catData.points.length > 0) {
      const filtered = catData.points.filter(p => {
        if (filterFrom && p.date < filterFrom) return false;
        if (filterTo   && p.date > filterTo)   return false;
        return true;
      });
      setSelectedPoint(filtered.length > 0 ? filtered[filtered.length - 1] : null);
    }
  };

  const handlePointClick = (pointData: any) => {
    if (pointData?.activePayload?.length > 0) {
      setSelectedPoint(pointData.activePayload[0].payload);
    }
  };

  const handleInvestigate = () => {
    if (!selectedCategory || !selectedPoint) return;
    const formattedDate = new Date(selectedPoint.date).toLocaleDateString(undefined, {
      month: 'short', day: 'numeric', year: 'numeric'
    });
    navigate('/rag', {
      state: {
        query: `Investigate the spike in ${selectedCategory} complaints around ${formattedDate}.`
      }
    });
  };

  const handleClearFilter = () => {
    setFilterFrom('');
    setFilterTo('');
    setNoDataMsg('');
  };

  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!cx || !cy) return null;
    const isSpike = payload.is_spike;
    const isSelected = selectedPoint?.date === payload.date;
    return (
      <g transform={`translate(${cx},${cy})`} onClick={() => setSelectedPoint(payload)} style={{ cursor: 'pointer' }}>
        {isSpike && (
          <circle r={10} fill="none" stroke="#f59e0b" strokeWidth={2.5} className="animate-pulse" />
        )}
        <circle
          r={isSelected ? 7 : (isSpike ? 6 : 4)}
          fill={isSelected ? '#f59e0b' : '#4f46e5'}
          stroke="#ffffff"
          strokeWidth={2}
        />
      </g>
    );
  };

  if (loading) return <div className="p-8 text-slate-500 font-medium">Loading spike detection...</div>;
  if (error || !data) return <div className="p-8 text-red-500 font-medium">Unable to load analytics. Please try again.</div>;

  const currentCatMeta = data.find(c => c.category === selectedCategory);

  return (
    <div className="space-y-6 p-8 pb-20 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-end gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2 tracking-tight">
            <AlertTriangle className="h-8 w-8 text-amber-500" /> Spike Detection
          </h1>
          <p className="text-lg text-slate-500 mt-1">
            Complaint volume by category — click any point to investigate
          </p>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1 flex-wrap">
            <Info className="h-3 w-3 shrink-0" />
            Source data: TWCS historical dataset ·{' '}
            <span className="font-medium text-slate-500">{allObservationDates.length} sparse observation days</span>
            {' '}(earliest: {dataDateRange.min}, latest: {dataDateRange.max})
          </p>
        </div>

        {/* Date Range Filter */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 flex flex-wrap items-end gap-3">
          <div className="flex items-center gap-1 text-xs text-slate-500 font-semibold mb-1 w-full">
            <CalendarDays className="h-3.5 w-3.5" /> Filter by date range
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-slate-400 font-medium uppercase">From</label>
            <input
              type="date"
              value={filterFrom}
              min={dataDateRange.min}
              max={filterTo || dataDateRange.max}
              onChange={e => { setFilterFrom(e.target.value); }}
              className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-slate-400 font-medium uppercase">To</label>
            <input
              type="date"
              value={filterTo}
              min={filterFrom || dataDateRange.min}
              max={dataDateRange.max}
              onChange={e => { setFilterTo(e.target.value); }}
              className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          {(filterFrom || filterTo) && (
            <button
              onClick={handleClearFilter}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold px-2 py-1.5 rounded-lg hover:bg-indigo-50"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Empty-state: shown when filter yields no results for this category */}
      {emptyStateMsg && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-800">
          <div className="flex items-start gap-2 mb-2">
            <Info className="h-4 w-4 mt-0.5 shrink-0" />
            <span>
              <strong>No observations in this category for {emptyStateMsg.selectedRange}.</strong>
            </span>
          </div>
          {emptyStateMsg.categoryRange && (
            <p className="text-xs text-amber-700 mb-1">
              This category has data from <strong>{emptyStateMsg.categoryRange}</strong>.
            </p>
          )}
          {emptyStateMsg.categoryDates.length > 0 && (
            <details className="text-xs text-amber-700">
              <summary className="cursor-pointer font-medium hover:underline">
                View all {emptyStateMsg.categoryDates.length} actual observation dates
              </summary>
              <div className="mt-1 flex flex-wrap gap-1">
                {emptyStateMsg.categoryDates.map(d => (
                  <button
                    key={d}
                    onClick={() => { setFilterFrom(d); setFilterTo(d); }}
                    className="bg-amber-100 hover:bg-amber-200 text-amber-900 px-1.5 py-0.5 rounded font-mono"
                  >
                    {d}
                  </button>
                ))}
              </div>
            </details>
          )}
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-6">
        {/* Categories Sidebar */}
        <div className="w-full md:w-64 shrink-0 flex flex-col gap-1.5">
          {data.map(cat => (
            <button
              key={cat.category}
              onClick={() => handleCategoryClick(cat.category)}
              className={`text-left px-4 py-3 rounded-lg font-medium transition-colors text-sm ${
                selectedCategory === cat.category
                  ? 'bg-blue-50 text-blue-700 border border-blue-200'
                  : 'text-slate-600 hover:bg-slate-100 border border-transparent'
              }`}
            >
              <span>{cat.display_name || cat.category}</span>
              {cat.has_spike && <span className="ml-1.5 text-[10px] font-bold text-amber-500">⚠ spike</span>}
              <div className="text-[10px] text-slate-400 mt-0.5">{cat.total_complaints} total</div>
            </button>
          ))}
        </div>

        {/* Chart + Detail */}
        <div className="flex-1 flex flex-col gap-4">
          <div className="bg-[#0a0a0f] rounded-2xl p-6 border border-slate-800 shadow-xl overflow-hidden">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-white text-xl font-bold">
                {currentCatMeta?.display_name || selectedCategory} — Complaint Volume
              </h3>
              {(filterFrom || filterTo) && (
                <span className="text-xs text-indigo-300 bg-indigo-900/50 px-2 py-1 rounded-lg">
                  Filtered: {filterFrom || dataDateRange.min} → {filterTo || dataDateRange.max}
                </span>
              )}
            </div>

            {chartData.length === 0 ? (
              <div className="h-[300px] flex flex-col items-center justify-center text-slate-500 text-sm gap-2">
                <span>No observations in the selected range for this category.</span>
                {categoryDates.length > 0 && (
                  <span className="text-slate-600 text-xs">
                    This category has {categoryDates.length} observation{categoryDates.length > 1 ? 's' : ''}:{' '}
                    {categoryDates[0]}{categoryDates.length > 1 ? ` → ${categoryDates[categoryDates.length - 1]}` : ''}
                  </span>
                )}
              </div>
            ) : (
              <div className="w-full h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={chartData}
                    margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    onClick={handlePointClick}
                  >
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#4f46e5" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e1e28" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#64748b"
                      tick={{ fill: '#94a3b8', fontSize: 11 }}
                      tickFormatter={val => {
                        const d = new Date(val);
                        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: '2-digit' });
                      }}
                      tickMargin={10}
                    />
                    <YAxis
                      stroke="#64748b"
                      tick={{ fill: '#94a3b8', fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e1e28', border: 'none', borderRadius: '8px', color: '#fff' }}
                      itemStyle={{ color: '#818cf8' }}
                      labelFormatter={label =>
                        new Date(label).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
                      }
                    />
                    <Area
                      type="monotone"
                      dataKey="complaint_count"
                      name="Complaints"
                      stroke="#4f46e5"
                      strokeWidth={3}
                      fillOpacity={1}
                      fill="url(#colorCount)"
                      activeDot={<CustomDot />}
                      dot={<CustomDot />}
                      isAnimationActive={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Detail Panel */}
          {selectedPoint && (
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
              <div>
                <div className="text-slate-500 font-medium mb-1">
                  <span className="text-slate-900 font-bold">{currentCatMeta?.display_name || selectedCategory}</span>{' '}
                  — {new Date(selectedPoint.date).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                  {selectedPoint.is_spike && (
                    <span className="ml-2 text-xs font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">⚠ Spike detected</span>
                  )}
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-slate-900">{selectedPoint.complaint_count}</span>
                  <span className="text-slate-500 font-medium">complaints on this date</span>
                </div>
              </div>
              <button
                onClick={handleInvestigate}
                className={`px-6 py-3 rounded-xl font-bold transition-all shadow-sm flex items-center gap-2 ${
                  selectedPoint.is_spike
                    ? 'bg-rose-600 hover:bg-rose-700 text-white'
                    : 'bg-slate-900 hover:bg-slate-800 text-white'
                }`}
              >
                <Search className="h-4 w-4" />
                Investigate with AI ↗
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
