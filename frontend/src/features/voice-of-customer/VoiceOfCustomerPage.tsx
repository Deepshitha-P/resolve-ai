import React, { useEffect, useState } from 'react';
import { Activity, MapPin, Package, Tag } from 'lucide-react';

interface CategoryEntry {
  volume: number;
  csat_proxy: number | null;
}

interface SentimentData {
  positive: number;
  neutral: number;
  negative: number;
  emotion_distribution: Record<string, number>;
  sentiment_by_category: Record<string, CategoryEntry>;
  category_coverage_pct: number;
}
interface CoverageData {
  products: any[];
  known_product_count: number;
  unknown_product_count: number;
  coverage_percent: number;
}
interface RegionData {
  regions: any[];
  known_region_count: number;
  unknown_region_count: number;
  coverage_percent: number;
}

export default function VoiceOfCustomerPage() {
  const [sentiment, setSentiment] = useState<SentimentData | null>(null);
  const [products, setProducts] = useState<CoverageData | null>(null);
  const [regions, setRegions] = useState<RegionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAllCategories, setShowAllCategories] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch('/api/analytics/sentiment').then(r => r.json()),
      fetch('/api/analytics/products').then(r => r.json()),
      fetch('/api/analytics/regions').then(r => r.json())
    ]).then(([s, p, r]) => {
      if (s.error || p.error || r.error) throw new Error();
      setSentiment(s);
      setProducts(p);
      setRegions(r);
      setLoading(false);
    }).catch(console.error);
  }, []);

  if (loading) return <div className="p-8 text-slate-500 font-medium">Loading sentiment analytics...</div>;
  if (!sentiment || !products || !regions) return <div className="p-8 text-red-500 font-medium">Unable to load analytics. Please try again.</div>;

  const totalSentiment = sentiment.positive + sentiment.neutral + sentiment.negative;
  const posPct = totalSentiment > 0 ? ((sentiment.positive / totalSentiment) * 100).toFixed(1) : '0.0';
  const neuPct = totalSentiment > 0 ? ((sentiment.neutral / totalSentiment) * 100).toFixed(1) : '0.0';
  const negPct = totalSentiment > 0 ? ((sentiment.negative / totalSentiment) * 100).toFixed(1) : '0.0';

  // Prepare category rows: known (sorted by volume) then unknown at the bottom
  const catEntries = Object.entries(sentiment.sentiment_by_category ?? {});
  const knownCatRows = catEntries
    .filter(([k]) => k !== 'unknown')
    .sort((a, b) => b[1].volume - a[1].volume);
  const unknownCatRow = catEntries.find(([k]) => k === 'unknown');
  const CAT_INITIAL_LIMIT = 8;
  const visibleCatRows = showAllCategories ? knownCatRows : knownCatRows.slice(0, CAT_INITIAL_LIMIT);
  const hasMoreCategories = knownCatRows.length > CAT_INITIAL_LIMIT;

  return (
    <div className="space-y-6 p-8 pb-20 max-w-7xl mx-auto">
      <div className="border-b border-slate-200 pb-6">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2 tracking-tight">
          <Activity className="h-8 w-8 text-rose-500" /> Sentiment Analysis
        </h1>
        <p className="text-lg text-slate-500 mt-1">Cross-sectional analysis of customer sentiment across categories, products, and regions.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Sentiment Distribution */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-6">Sentiment Distribution</h2>
          <div className="flex flex-col gap-4">
            <div className="w-full h-4 rounded-full overflow-hidden flex">
              <div style={{ width: `${negPct}%` }} className="bg-rose-500 h-full"></div>
              <div style={{ width: `${neuPct}%` }} className="bg-slate-300 h-full"></div>
              <div style={{ width: `${posPct}%` }} className="bg-emerald-500 h-full"></div>
            </div>
            <div className="flex justify-between text-sm font-medium">
              <div className="text-rose-600"><span className="text-2xl font-bold block">{negPct}%</span> Negative ({(sentiment.negative).toLocaleString()})</div>
              <div className="text-slate-500 text-center"><span className="text-2xl font-bold block text-slate-700">{neuPct}%</span> Neutral ({(sentiment.neutral).toLocaleString()})</div>
              <div className="text-emerald-600 text-right"><span className="text-2xl font-bold block">{posPct}%</span> Positive ({(sentiment.positive).toLocaleString()})</div>
            </div>
          </div>
        </div>

        {/* Emotion Distribution */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4">Emotion Distribution</h2>
          <div className="grid grid-cols-2 gap-4">
            {sentiment.emotion_distribution ? Object.entries(sentiment.emotion_distribution).map(([emo, val]: any, i) => (
              <div key={i} className="flex justify-between items-center border-b border-slate-100 pb-2">
                <span className="text-slate-600 font-medium">{emo}</span>
                <span className="font-bold text-slate-900">{val.toLocaleString()}</span>
              </div>
            )) : <div className="text-slate-500 text-sm">No emotion data available.</div>}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Products */}
        <div className="bg-white rounded-2xl p-0 shadow-sm border border-slate-200 overflow-hidden flex flex-col">
          <div className="p-6 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
              <Package className="h-4 w-4" /> Sentiment by Product
            </h2>
            <span className="text-xs font-medium bg-slate-200 text-slate-600 px-2 py-0.5 rounded">Coverage: {products.coverage_percent.toFixed(2)}%</span>
          </div>
          <div className="p-0 overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-semibold">Product</th>
                  <th className="px-6 py-3 font-semibold text-right">Volume</th>
                  <th className="px-6 py-3 font-semibold text-right">CSAT Proxy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {products.products.slice(0, 5).map((p, i) => (
                  <tr key={i} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3 font-medium text-slate-900 capitalize">{p.product_name ? p.product_name.replace('_', ' ') : 'Unknown'}</td>
                    <td className="px-6 py-3 text-right">{p.total_cases ? p.total_cases.toLocaleString() : '0'}</td>
                    <td className="px-6 py-3 text-right font-medium">{p.csat_proxy ? p.csat_proxy.toFixed(1) : '-'}</td>
                  </tr>
                ))}
                <tr className="bg-slate-50 text-slate-500 italic">
                  <td className="px-6 py-3">Unknown / Unmentioned</td>
                  <td className="px-6 py-3 text-right">{products.unknown_product_count.toLocaleString()}</td>
                  <td className="px-6 py-3 text-right">-</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Regions */}
        <div className="bg-white rounded-2xl p-0 shadow-sm border border-slate-200 overflow-hidden flex flex-col">
          <div className="p-6 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
              <MapPin className="h-4 w-4" /> Sentiment by Region
            </h2>
            <span className="text-xs font-medium bg-slate-200 text-slate-600 px-2 py-0.5 rounded">Coverage: {regions.coverage_percent.toFixed(2)}%</span>
          </div>
          <div className="p-0 overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-semibold">Region</th>
                  <th className="px-6 py-3 font-semibold text-right">Volume</th>
                  <th className="px-6 py-3 font-semibold text-right">CSAT Proxy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {regions.regions.slice(0, 5).map((r, i) => (
                  <tr key={i} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3 font-medium text-slate-900 capitalize">{r.region_name ? r.region_name.replace('_', ' ') : 'Unknown'}</td>
                    <td className="px-6 py-3 text-right">{r.total_cases ? r.total_cases.toLocaleString() : '0'}</td>
                    <td className="px-6 py-3 text-right font-medium">{r.csat_proxy ? r.csat_proxy.toFixed(1) : '-'}</td>
                  </tr>
                ))}
                <tr className="bg-slate-50 text-slate-500 italic">
                  <td className="px-6 py-3">Unknown / Unmentioned</td>
                  <td className="px-6 py-3 text-right">{regions.unknown_region_count.toLocaleString()}</td>
                  <td className="px-6 py-3 text-right">-</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Sentiment by Category — full-width card below product/region */}
      <div className="bg-white rounded-2xl p-0 shadow-sm border border-slate-200 overflow-hidden flex flex-col">
        <div className="p-6 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <Tag className="h-4 w-4" /> Sentiment by Category
          </h2>
          <span className="text-xs font-medium bg-slate-200 text-slate-600 px-2 py-0.5 rounded">
            Coverage: {(sentiment.category_coverage_pct ?? 0).toFixed(2)}%
          </span>
        </div>
        <div className="p-0 overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-3 font-semibold">Category</th>
                <th className="px-6 py-3 font-semibold text-right">Volume</th>
                <th className="px-6 py-3 font-semibold text-right">CSAT Proxy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {visibleCatRows.map(([name, entry], i) => (
                <tr key={i} className="hover:bg-slate-50/50">
                  <td className="px-6 py-3 font-bold text-slate-900 capitalize">{name.replace(/_/g, ' ')}</td>
                  <td className="px-6 py-3 text-right">{entry.volume.toLocaleString()}</td>
                  <td className="px-6 py-3 text-right font-medium">
                    {entry.csat_proxy != null ? entry.csat_proxy.toFixed(1) : '-'}
                  </td>
                </tr>
              ))}
              {hasMoreCategories && (
                <tr>
                  <td colSpan={3} className="px-6 py-2 text-center">
                    <button
                      onClick={() => setShowAllCategories(v => !v)}
                      className="text-xs font-semibold text-sky-600 hover:text-sky-800 transition-colors"
                    >
                      {showAllCategories
                        ? '▲ Show less'
                        : `▼ Show ${knownCatRows.length - CAT_INITIAL_LIMIT} more`}
                    </button>
                  </td>
                </tr>
              )}
              {unknownCatRow && (
                <tr className="bg-slate-50 text-slate-500 italic">
                  <td className="px-6 py-3">Unknown / Unclassified</td>
                  <td className="px-6 py-3 text-right">{unknownCatRow[1].volume.toLocaleString()}</td>
                  <td className="px-6 py-3 text-right">-</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
