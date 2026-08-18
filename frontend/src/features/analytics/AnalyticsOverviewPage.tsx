import React, { useEffect, useState } from 'react';
import {
  BarChart3, Clock, AlertTriangle, RefreshCcw, CheckCircle2,
  TrendingUp, TrendingDown, Info, Minus, ShieldCheck, Activity
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';

// ── Types ────────────────────────────────────────────────────────────────────
interface TrendPoint { date: string; complaint_count: number; escalated_count: number; }
interface ExtendedKPIs {
  total_conversations: number;
  date_start: string | null;
  date_end: string | null;
  response_time: {
    average_minutes: number; median_minutes: number;
    p90_minutes: number; p95_minutes: number; coverage_percent: number;
  };
  fcr: {
    fcr_all_conversations: number; fcr_responded_conversations: number;
    numerator: number; denominator: number;
    current_rate: number | null; previous_rate: number | null; change_pct: number | null;
  };
  escalation: {
    rate: number; numerator: number; denominator: number;
    current_rate: number | null; previous_rate: number | null; change_pct: number | null;
  };
  reopen: {
    rate: number; numerator: number; denominator: number;
    current_rate: number | null; previous_rate: number | null; change_pct: number | null;
  };
  csat_proxy: {
    score: number; is_actual_csat: boolean;
    current_score: number | null; previous_score: number | null; change_pct: number | null;
  };
  trend: TrendPoint[];
  note: string;
}

// ── Health status logic ───────────────────────────────────────────────────────
type HealthStatus = 'healthy' | 'attention' | 'critical';
function getHealthStatus(metric: string, value: number): HealthStatus {
  switch (metric) {
    case 'csat':
      return value >= 60 ? 'healthy' : value >= 40 ? 'attention' : 'critical';
    case 'fcr':
      return value >= 0.20 ? 'healthy' : value >= 0.10 ? 'attention' : 'critical';
    case 'reopen':
      return value <= 0.05 ? 'healthy' : value <= 0.10 ? 'attention' : 'critical';
    case 'escalation':
      return value <= 0.05 ? 'healthy' : value <= 0.10 ? 'attention' : 'critical';
    default:
      return 'attention';
  }
}
const STATUS_CONFIG: Record<HealthStatus, { emoji: string; label: string; cls: string }> = {
  healthy:   { emoji: '🟢', label: 'Healthy',         cls: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
  attention: { emoji: '🟡', label: 'Needs Attention', cls: 'text-amber-700   bg-amber-50   border-amber-200'   },
  critical:  { emoji: '🔴', label: 'Critical',        cls: 'text-red-700     bg-red-50     border-red-200'     },
};

// ── Change indicator ─────────────────────────────────────────────────────────
function ChangeIndicator({
  change_pct, lowerIsBetter = false
}: { change_pct: number | null; lowerIsBetter?: boolean }) {
  if (change_pct === null || change_pct === undefined) {
    return <span className="text-xs text-slate-400 flex items-center gap-1"><Minus className="h-3 w-3" /> no comparison</span>;
  }
  const isPositive = change_pct > 0;
  const isBetter   = lowerIsBetter ? !isPositive : isPositive;
  const color = change_pct === 0 ? 'text-slate-400' : isBetter ? 'text-emerald-600' : 'text-red-500';
  const Icon  = change_pct === 0 ? Minus : isPositive ? TrendingUp : TrendingDown;
  return (
    <span className={`text-xs flex items-center gap-1 font-semibold ${color}`}>
      <Icon className="h-3 w-3" />
      {change_pct > 0 ? '+' : ''}{change_pct.toFixed(1)}% vs prev period
    </span>
  );
}

// ── Date formatter ────────────────────────────────────────────────────────────
function fmtDate(d: string) {
  try {
    return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return d; }
}

// ── Tooltip formatter for chart ───────────────────────────────────────────────
function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-lg text-sm">
      <div className="font-bold text-slate-700 mb-2">{fmtDate(label)}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-600">{p.name}:</span>
          <span className="font-semibold text-slate-900">{p.value}</span>
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
export default function AnalyticsOverviewPage() {
  const [data, setData] = useState<ExtendedKPIs | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch('/api/analytics/kpis_extended')
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => { if (d.error) throw new Error(d.error); setData(d); setLoading(false); })
      .catch(() => { setError(true); setLoading(false); });
  }, []);

  if (loading) return <div className="p-8 text-slate-500 font-medium">Loading KPIs...</div>;
  if (error || !data) return <div className="p-8 text-red-500 font-medium">Unable to load KPI analytics. Please try again.</div>;

  const fcrRate      = data.fcr.fcr_all_conversations;
  const escRate      = data.escalation.rate;
  const reopenRate   = data.reopen.rate;
  const csatScore    = data.csat_proxy.score;

  const healthItems = [
    { label: 'Customer Satisfaction', metric: 'csat',      value: csatScore,  display: `${csatScore.toFixed(1)}/100` },
    { label: 'First Contact Resolution', metric: 'fcr',   value: fcrRate,    display: `${(fcrRate*100).toFixed(2)}%` },
    { label: 'Repeat Contact',        metric: 'reopen',   value: reopenRate, display: `${(reopenRate*100).toFixed(2)}%` },
    { label: 'Escalation Risk',       metric: 'escalation', value: escRate,  display: `${(escRate*100).toFixed(2)}%` },
  ];

  const coverageLabel = data.date_start && data.date_end
    ? `${data.total_conversations.toLocaleString()} conversations · ${fmtDate(data.date_start)} – ${fmtDate(data.date_end)}`
    : `Based on ${data.total_conversations.toLocaleString()} conversations in the current analysis period.`;

  return (
    <div className="space-y-8 p-8 pb-20 max-w-7xl mx-auto">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="border-b border-slate-200 pb-6">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2 tracking-tight">
          <BarChart3 className="h-8 w-8 text-sky-500" /> KPI Metrics
        </h1>
        <p className="text-base text-slate-500 mt-1">
          Quantitative performance tracking · <span className="font-medium text-slate-700">{coverageLabel}</span>
        </p>
      </div>

      {/* ── KPI Cards ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        {/* Total Conversations */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Total Conversations</h2>
          <div className="text-4xl font-bold text-slate-900 mt-2">{data.total_conversations.toLocaleString()}</div>
          <p className="text-xs text-slate-400 mt-3">Full analysis period</p>
        </div>

        {/* CSAT Proxy */}
        <div className="bg-gradient-to-br from-violet-500 to-indigo-600 rounded-2xl p-6 shadow-md text-white relative overflow-hidden">
          <TrendingUp className="absolute -right-4 -bottom-4 h-32 w-32 text-white opacity-10" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-white/80 mb-1 flex items-center gap-1 group relative">
            CSAT Proxy <Info className="h-4 w-4" />
            <div className="hidden group-hover:block absolute bottom-full left-0 mb-2 w-64 p-2 bg-slate-900 text-xs rounded text-white z-20 normal-case font-normal">
              Deterministic proxy from sentiment and operational signals. Not a survey-based CSAT.
            </div>
          </h2>
          <div className="text-4xl font-bold mt-2">
            {data.csat_proxy.score.toFixed(2)} <span className="text-xl font-medium text-white/60">/ 100</span>
          </div>
          <div className="mt-3">
            {data.csat_proxy.change_pct !== null ? (
              <span className={`text-xs font-semibold flex items-center gap-1 ${data.csat_proxy.change_pct >= 0 ? 'text-white/90' : 'text-red-200'}`}>
                {data.csat_proxy.change_pct >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {data.csat_proxy.change_pct > 0 ? '+' : ''}{data.csat_proxy.change_pct.toFixed(1)}% vs prev period
              </span>
            ) : <span className="text-xs text-white/50">no comparison available</span>}
          </div>
        </div>

        {/* Response Time */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center justify-between">
            Response Time
            <span className="text-[10px] bg-slate-100 px-2 py-0.5 rounded text-slate-500 normal-case font-medium">
              {data.response_time.coverage_percent}% coverage
            </span>
          </h2>
          <div className="text-4xl font-bold text-slate-900 mt-2">
            {data.response_time.median_minutes.toFixed(1)} <span className="text-xl font-medium text-slate-400">min</span>
          </div>
          <p className="text-xs text-slate-400 mt-1 mb-3">Median · only {data.response_time.coverage_percent}% of conversations have timestamps</p>
          <div className="space-y-1 text-sm border-t border-slate-100 pt-3">
            <div className="flex justify-between"><span className="text-slate-500">Average</span><span className="font-medium text-slate-700">{data.response_time.average_minutes.toFixed(1)}m</span></div>
            <div className="flex justify-between"><span className="text-slate-500">P90</span><span className="font-medium text-slate-700">{data.response_time.p90_minutes.toFixed(1)}m</span></div>
            <div className="flex justify-between"><span className="text-slate-500">P95</span><span className="font-medium text-slate-700">{data.response_time.p95_minutes.toFixed(1)}m</span></div>
          </div>
        </div>

        {/* FCR */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center justify-between">
            FCR Proxy <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </h2>
          <div className="text-4xl font-bold text-slate-900 mt-2">
            {(data.fcr.fcr_all_conversations * 100).toFixed(2)}<span className="text-xl font-medium text-slate-400">%</span>
          </div>
          <div className="mt-2"><ChangeIndicator change_pct={data.fcr.change_pct} /></div>
          <div className="mt-3 space-y-1 text-sm border-t border-slate-100 pt-3">
            <div className="flex justify-between"><span className="text-slate-500">Responded</span><span className="font-medium text-emerald-600">{(data.fcr.fcr_responded_conversations * 100).toFixed(2)}%</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Volume</span><span className="font-medium text-slate-700">{data.fcr.numerator.toLocaleString()} / {data.fcr.denominator.toLocaleString()}</span></div>
          </div>
        </div>

        {/* Escalation */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-red-100 relative">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center justify-between">
            Escalation Rate <AlertTriangle className="h-4 w-4 text-red-500" />
          </h2>
          <div className="text-4xl font-bold text-slate-900 mt-2">
            {(data.escalation.rate * 100).toFixed(2)}<span className="text-xl font-medium text-slate-400">%</span>
          </div>
          <div className="mt-2"><ChangeIndicator change_pct={data.escalation.change_pct} lowerIsBetter /></div>
          <div className="mt-3 space-y-1 text-sm border-t border-slate-100 pt-3">
            <div className="flex justify-between"><span className="text-slate-500">Volume</span><span className="font-medium text-red-600">{data.escalation.numerator.toLocaleString()} / {data.escalation.denominator.toLocaleString()}</span></div>
          </div>
        </div>

        {/* Reopen */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-amber-100">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center justify-between">
            Repeat Contact Rate <RefreshCcw className="h-4 w-4 text-amber-500" />
          </h2>
          <div className="text-4xl font-bold text-slate-900 mt-2">
            {(data.reopen.rate * 100).toFixed(2)}<span className="text-xl font-medium text-slate-400">%</span>
          </div>
          <div className="mt-2"><ChangeIndicator change_pct={data.reopen.change_pct} lowerIsBetter /></div>
          <div className="mt-3 space-y-1 text-sm border-t border-slate-100 pt-3">
            <div className="flex justify-between"><span className="text-slate-500">Volume</span><span className="font-medium text-amber-600">{data.reopen.numerator.toLocaleString()} / {data.reopen.denominator.toLocaleString()}</span></div>
          </div>
        </div>
      </div>

      {/* ── Operational Health ─────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-600 mb-1 flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-indigo-500" /> Operational Health
        </h2>
        <p className="text-xs text-slate-400 mb-5">
          Status thresholds: CSAT ≥60 healthy, FCR ≥20% healthy, Escalation/Repeat ≤5% healthy.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {healthItems.map(item => {
            const status = getHealthStatus(item.metric, item.value);
            const cfg = STATUS_CONFIG[status];
            return (
              <div key={item.label} className={`rounded-xl border px-4 py-3 ${cfg.cls}`}>
                <div className="text-xs font-bold uppercase tracking-wide mb-1">{item.label}</div>
                <div className="text-lg font-bold">{item.display}</div>
                <div className="text-xs mt-1 font-semibold">{cfg.emoji} {cfg.label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Trend Chart ────────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <div className="flex items-start justify-between mb-1">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-600 flex items-center gap-2">
            <Activity className="h-4 w-4 text-indigo-500" /> Complaint &amp; Escalation Trends
          </h2>
        </div>
        <p className="text-xs text-slate-400 mb-5">
          Daily complaint volume from temporal intelligence signals — {data.trend.length} observation days in dataset.
          {' '}Gaps between dates reflect the actual TWCS dataset distribution (not fabricated).
        </p>

        {data.trend.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">No temporal data available for trend chart.</div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data.trend} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="gradComplaints" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}    />
                </linearGradient>
                <linearGradient id="gradEscalated" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}   />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                tickFormatter={d => {
                  try { return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }); }
                  catch { return d; }
                }}
                tickMargin={8}
              />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 16 }} />
              <Area
                type="monotone" dataKey="complaint_count" name="Complaints"
                stroke="#6366f1" strokeWidth={2.5} fill="url(#gradComplaints)" dot={{ r: 4, fill: '#6366f1', stroke: '#fff', strokeWidth: 2 }}
              />
              <Area
                type="monotone" dataKey="escalated_count" name="Escalated"
                stroke="#ef4444" strokeWidth={2} fill="url(#gradEscalated)" dot={{ r: 4, fill: '#ef4444', stroke: '#fff', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ── Data note ──────────────────────────────────────────────────── */}
      <p className="text-xs text-slate-400 text-center">{data.note}</p>
    </div>
  );
}
