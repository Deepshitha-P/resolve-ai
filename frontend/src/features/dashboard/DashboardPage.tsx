import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, AlertTriangle, TrendingUp, Users, ChevronRight,
  ExternalLink, RefreshCw, AlertCircle, Activity, Calendar,
  Database, Clock, ArrowUpRight, Search
} from 'lucide-react';

// ── Types matching /api/executive-summary-v2 ────────────────────────────────
interface OperationalSignal {
  label: string;
  value: number;
  unit: string;
  note: string;
  direction: string;
}
interface KeyFinding {
  category: string;
  raw_category: string;
  growth_pct: number;
  recent_volume: number;
  prior_volume: number;
  emerging_score: number;
  signal: string;
}
interface TopIssue {
  rank: number;
  category: string;
  raw_category: string;
  total_cases: number;
  escalation_rate: number;
  reopen_rate: number;
  fcr_rate: number;
  avg_sentiment: number;
  csat_proxy: number;
  is_spike: boolean;
  spike_growth_pct: number | null;
}
interface CustomerImpact {
  negative_sentiment_pct: number;
  escalation_pct: number;
  repeat_contact_pct: number;
  highest_escalation_category: string | null;
  highest_escalation_rate: number | null;
  highest_repeat_category: string | null;
  highest_repeat_rate: number | null;
  lowest_csat_category: string | null;
  lowest_csat_score: number | null;
}
interface TrendPoint { date: string; complaint_count: number; }
interface RecommendedAction {
  priority: string;
  action: string;
  reason: string;
  rag_query: string;
  evidence_ref: string;
}
interface ExecSummaryV2 {
  total_conversations: number;
  date_start: string | null;
  date_end: string | null;
  last_analyzed: string | null;
  observation_days: number;
  operational_signals: OperationalSignal[];
  key_findings: KeyFinding[];
  top_priority_issues: TopIssue[];
  customer_impact: CustomerImpact;
  trend_overview: TrendPoint[];
  recommended_actions: RecommendedAction[];
  data_note: string;
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function fmtDate(iso: string | null) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return iso; }
}
function fmtDateTime(iso: string | null) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit', hour12: false, timeZoneName: 'short'
    });
  } catch { return iso; }
}

// ── Signal icon/colour based on direction ───────────────────────────────────
function signalColour(sig: OperationalSignal): string {
  if (sig.direction === 'higher is better') {
    return sig.value < 10 ? 'text-red-600' : sig.value < 20 ? 'text-amber-600' : 'text-emerald-600';
  }
  if (sig.direction === 'lower is better') {
    return sig.value > 15 ? 'text-red-600' : sig.value > 8 ? 'text-amber-600' : 'text-emerald-600';
  }
  // CSAT: lower is worse
  return sig.value < 40 ? 'text-red-600' : sig.value < 60 ? 'text-amber-600' : 'text-emerald-600';
}

// ════════════════════════════════════════════════════════════════════════════
export default function DashboardPage() {
  const [data, setData] = useState<ExecSummaryV2 | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch('/api/executive-summary-v2');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      if (d.error) throw new Error(d.error);
      setData(d);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const investigateWithAI = (query: string) =>
    navigate('/rag', { state: { query } });

  if (loading) return (
    <div className="p-8 flex flex-col items-center gap-3 text-slate-500">
      <div className="h-6 w-6 border-2 border-indigo-400 border-t-indigo-700 rounded-full animate-spin" />
      <span className="font-medium">Loading executive overview...</span>
    </div>
  );

  if (error || !data) return (
    <div className="p-8 flex flex-col items-center gap-4">
      <div className="flex items-center gap-2 text-red-500 font-medium">
        <AlertCircle className="h-5 w-5" />
        <span>{error || 'Unable to load executive summary.'}</span>
      </div>
      <button onClick={load} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700">
        <RefreshCw className="h-4 w-4" /> Retry
      </button>
    </div>
  );

  const topIssue = data.top_priority_issues[0];

  return (
    <div className="space-y-6 p-8 pb-24 max-w-7xl mx-auto">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="border-b border-slate-200 pb-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Sparkles className="h-7 w-7 text-violet-500" />
              Executive Overview
            </h1>
            <p className="text-base text-slate-500 mt-1">
              Customer support intelligence — operational health, emerging risks, and priority issues
            </p>
          </div>
          <div className="text-right space-y-0.5">
            <div className="flex items-center gap-1.5 justify-end text-sm text-slate-600">
              <Database className="h-3.5 w-3.5 text-slate-400" />
              <span className="font-semibold">{data.total_conversations.toLocaleString()} conversations</span>
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1 justify-end">
              <Calendar className="h-3 w-3" />
              Source data: {fmtDate(data.date_start)} – {fmtDate(data.date_end)}
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1 justify-end">
              <Clock className="h-3 w-3" />
              Last analyzed: {fmtDateTime(data.last_analyzed)}
            </div>
          </div>
        </div>
      </div>

      {/* ── Operational Signals ──────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <Activity className="h-4 w-4 text-indigo-500" />
            Operational Signals
          </h2>
          <span className="text-xs text-slate-400 italic">Based on available signals — no invented health score</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mt-4">
          {data.operational_signals.map(sig => (
            <div key={sig.label} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <div className="text-xs text-slate-500 font-medium mb-1">{sig.label}</div>
              <div className={`text-2xl font-bold ${signalColour(sig)}`}>
                {sig.value}<span className="text-sm font-normal text-slate-400 ml-0.5">{sig.unit}</span>
              </div>
              <div className="text-[10px] text-slate-400 mt-1 leading-tight">{sig.note}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* ── Key Findings ──────────────────────────────────────────────── */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-amber-500" />
            Key Findings
            <span className="text-[10px] normal-case font-normal text-slate-400 ml-1">— from backend emerging_issue_score ranking</span>
          </h2>
          {data.key_findings.length === 0 ? (
            <p className="text-sm text-slate-400">No emerging issues detected in current dataset.</p>
          ) : (
            <div className="space-y-4">
              {data.key_findings.map((f, i) => (
                <div key={i} className="flex gap-4 items-start">
                  <div className="text-lg font-bold text-slate-200 shrink-0 w-7 text-right">{String(i + 1).padStart(2, '0')}</div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-slate-900 flex items-center gap-2 flex-wrap">
                      {f.category}
                      {f.growth_pct >= 300 && (
                        <span className="text-[10px] font-bold bg-red-100 text-red-700 px-1.5 py-0.5 rounded uppercase">Spike</span>
                      )}
                    </div>
                    <div className="text-sm text-slate-500 mt-0.5">{f.signal}</div>
                  </div>
                  <button
                    onClick={() => investigateWithAI(`What is causing the spike in ${f.category} complaints?`)}
                    className="text-indigo-600 hover:text-indigo-800 shrink-0"
                    title="Investigate with AI"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Top Priority Issues ───────────────────────────────────────── */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              Top Priority Issues
              <span className="text-[10px] normal-case font-normal text-slate-400 ml-1">— backend category ordering</span>
            </h2>
            <button
              onClick={() => navigate('/spikes')}
              className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 font-medium"
            >
              View all <ArrowUpRight className="h-3 w-3" />
            </button>
          </div>
          <div className="space-y-3">
            {data.top_priority_issues.map(issue => (
              <div key={issue.rank} className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/30 transition-colors group">
                <div className="text-xs font-bold text-slate-300 w-5 shrink-0 pt-0.5">#{issue.rank}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-slate-900 text-sm">{issue.category}</span>
                    {issue.is_spike && (
                      <span className="text-[10px] font-bold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded uppercase">
                        +{issue.spike_growth_pct?.toFixed(0)}% spike
                      </span>
                    )}
                  </div>
                  <div className="flex gap-3 text-xs text-slate-500 mt-1 flex-wrap">
                    <span>Vol: <span className="font-medium text-slate-700">{issue.total_cases}</span></span>
                    <span>Esc: <span className={`font-medium ${issue.escalation_rate > 15 ? 'text-red-600' : 'text-slate-700'}`}>{issue.escalation_rate}%</span></span>
                    <span>FCR: <span className="font-medium text-slate-700">{issue.fcr_rate}%</span></span>
                    <span>CSAT: <span className={`font-medium ${issue.csat_proxy < 45 ? 'text-amber-600' : 'text-slate-700'}`}>{issue.csat_proxy}/100</span></span>
                  </div>
                </div>
                <button
                  onClick={() => investigateWithAI(`Investigate the top complaints in the ${issue.category} category and recommend resolutions.`)}
                  className="text-slate-300 group-hover:text-indigo-600 transition-colors shrink-0"
                  title="Investigate"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Customer Impact + Trend ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Customer Impact */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 flex items-center gap-2">
            <Users className="h-4 w-4 text-rose-500" />
            Customer Impact
          </h2>
          <div className="space-y-3 text-sm">
            {data.customer_impact.highest_escalation_category && (
              <div className="flex gap-3 items-start">
                <span className="mt-0.5 h-2 w-2 rounded-full bg-red-500 shrink-0" />
                <span className="text-slate-700">
                  <span className="font-semibold">{data.customer_impact.highest_escalation_category}</span> has the highest escalation rate at{' '}
                  <span className="font-semibold text-red-600">{data.customer_impact.highest_escalation_rate}%</span> of conversations escalated.
                </span>
              </div>
            )}
            {data.customer_impact.highest_repeat_category && (
              <div className="flex gap-3 items-start">
                <span className="mt-0.5 h-2 w-2 rounded-full bg-amber-500 shrink-0" />
                <span className="text-slate-700">
                  Repeat-contact signals are concentrated in{' '}
                  <span className="font-semibold">{data.customer_impact.highest_repeat_category}</span>{' '}
                  (<span className="font-semibold text-amber-600">{data.customer_impact.highest_repeat_rate}%</span> repeat contact rate).
                </span>
              </div>
            )}
            {data.customer_impact.lowest_csat_category && (
              <div className="flex gap-3 items-start">
                <span className="mt-0.5 h-2 w-2 rounded-full bg-violet-500 shrink-0" />
                <span className="text-slate-700">
                  Lowest CSAT proxy is in{' '}
                  <span className="font-semibold">{data.customer_impact.lowest_csat_category}</span>{' '}
                  (<span className="font-semibold text-violet-600">{data.customer_impact.lowest_csat_score}/100</span>).
                </span>
              </div>
            )}
            <div className="flex gap-3 items-start">
              <span className="mt-0.5 h-2 w-2 rounded-full bg-slate-400 shrink-0" />
              <span className="text-slate-700">
                <span className="font-semibold text-slate-900">{data.customer_impact.negative_sentiment_pct}%</span> of conversations have negative sentiment overall.
              </span>
            </div>
            <div className="pt-2 border-t border-slate-100">
              <button
                onClick={() => navigate('/sentiment')}
                className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 font-medium"
              >
                View Sentiment Analysis <ArrowUpRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>

        {/* Trend Overview */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
              <Activity className="h-4 w-4 text-sky-500" />
              Trend Overview
            </h2>
            <button
              onClick={() => navigate('/kpis')}
              className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 font-medium"
            >
              View detailed trends <ArrowUpRight className="h-3 w-3" />
            </button>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            {data.observation_days} observation days in source dataset (2011–2017 historical TWCS data).
            Gaps between dates reflect actual dataset distribution — not fabricated.
          </p>
          <div className="space-y-2">
            {data.trend_overview.map((pt, i) => {
              const maxCount = Math.max(...data.trend_overview.map(p => p.complaint_count));
              const barWidth = maxCount > 0 ? (pt.complaint_count / maxCount) * 100 : 0;
              return (
                <div key={i} className="flex items-center gap-3 text-xs">
                  <span className="text-slate-400 w-24 shrink-0 text-right">{fmtDate(pt.date)}</span>
                  <div className="flex-1 bg-slate-100 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-indigo-400"
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                  <span className="text-slate-600 font-medium w-8 text-right">{pt.complaint_count}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Recommended Actions ──────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-violet-500" />
          Recommended Actions
          <span className="text-[10px] normal-case font-normal text-slate-400 ml-1">— derived from emerging_issues backend ranking</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.recommended_actions.map((action, i) => (
            <div key={i} className="border border-slate-200 rounded-xl p-4 hover:border-indigo-200 hover:shadow-sm transition-all">
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${action.priority === 'HIGH'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-amber-100 text-amber-700'
                  }`}>
                  {action.priority} Priority
                </span>
              </div>
              <div className="font-semibold text-slate-900 text-sm mb-1">{action.action}</div>
              <div className="text-xs text-slate-500 mb-3">{action.reason}</div>
              <div className="text-[10px] font-mono text-slate-400 bg-slate-50 px-2 py-1 rounded mb-3">
                {action.evidence_ref}
              </div>
              <button
                onClick={() => investigateWithAI(action.rag_query)}
                className="w-full flex items-center justify-center gap-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg px-3 py-2 transition-colors"
              >
                <Search className="h-3 w-3" /> Investigate with AI →
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ── Data note ────────────────────────────────────────────────────── */}
      <p className="text-xs text-slate-400 text-center pb-2">{data.data_note}</p>
    </div>
  );
}
