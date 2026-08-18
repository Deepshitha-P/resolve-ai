import { Badge } from '../common/Badge';

interface PainPointCardProps {
  name: string;
  category: string;
  painScore: number;
  mentionCount: number;
  percentage: number;
  growthRate: number;
  dominantSentiment: 'positive' | 'neutral' | 'negative';
  severity: 'critical' | 'high' | 'medium';
  priority: 'critical' | 'high' | 'medium';
  company: string;
  segment: string;
  resolutionRate: number;
}

const sentimentTone = {
  positive: 'success' as const,
  neutral: 'primary' as const,
  negative: 'danger' as const
};

const severityTone = {
  critical: 'danger' as const,
  high: 'warning' as const,
  medium: 'neutral' as const
};

export function PainPointCard({
  name,
  category,
  painScore,
  mentionCount,
  percentage,
  growthRate,
  dominantSentiment,
  severity,
  priority,
  company,
  segment,
  resolutionRate
}: PainPointCardProps) {
  const priorityTone = {
    critical: 'danger' as const,
    high: 'warning' as const,
    medium: 'neutral' as const
  };

  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{category}</div>
          <h3 className="mt-2 text-xl font-semibold text-slate-900">{name}</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge label={`${painScore}/100`} tone={severityTone[severity]} />
          <Badge label={priority} tone={priorityTone[priority]} />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-300 bg-white/35 p-3">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Mentions</div>
          <div className="mt-2 text-xl font-semibold text-slate-900">{mentionCount.toLocaleString()}</div>
        </div>
        <div className="rounded-2xl border border-slate-300 bg-white/35 p-3">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Share</div>
          <div className="mt-2 text-xl font-semibold text-slate-900">{percentage}%</div>
        </div>
        <div className="rounded-2xl border border-slate-300 bg-white/35 p-3">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Growth</div>
          <div className="mt-2 text-xl font-semibold text-emerald-300">+{growthRate}%</div>
        </div>
        <div className="rounded-2xl border border-slate-300 bg-white/35 p-3">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Resolution</div>
          <div className="mt-2 text-xl font-semibold text-slate-900">{resolutionRate}%</div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2 text-sm text-slate-600">
        <span className="rounded-full border border-slate-300 bg-white/40 px-2.5 py-1">{company}</span>
        <span className="rounded-full border border-slate-300 bg-white/40 px-2.5 py-1">{segment}</span>
        <Badge label={dominantSentiment} tone={sentimentTone[dominantSentiment]} />
      </div>
    </div>
  );
}
