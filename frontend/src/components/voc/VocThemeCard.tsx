interface VocThemeCardProps {
  name: string;
  frequency: number;
  percentage: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  trend: number;
  affectedSegment: string;
  priority: 'critical' | 'high' | 'medium';
  confidence: number;
}

const sentimentColors = {
  positive: '#059669',
  neutral: '#475569',
  negative: '#dc2626'
};

const sentimentBgColors = {
  positive: 'bg-emerald-50',
  neutral: 'bg-slate-100',
  negative: 'bg-red-50'
};

const priorityColors = {
  critical: '#dc2626',
  high: '#d97706',
  medium: '#2563eb'
};

const priorityBg = {
  critical: 'bg-red-50',
  high: 'bg-amber-50',
  medium: 'bg-blue-50'
};

export function VocThemeCard({
  name,
  frequency,
  percentage,
  sentiment,
  trend,
  affectedSegment,
  priority,
  confidence
}: VocThemeCardProps) {
  return (
    <div className={`rounded-3xl border border-slate-300/60 ${sentimentBgColors[sentiment]} bg-opacity-20 p-5 shadow-panel backdrop-blur-sm`}>
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.2em]" style={{ color: sentimentColors[sentiment] }}>
            {sentiment}
          </div>
          <h3 className="mt-2 text-xl font-semibold text-slate-900">{name}</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="inline-flex rounded-lg px-2.5 py-1 text-sm font-medium" style={{ color: priorityColors[priority], background: `${priorityColors[priority]}20` }}>
            {priority}
          </span>
          <span className="inline-flex rounded-lg border border-slate-300 bg-white/40 px-2.5 py-1 text-sm text-slate-600">{confidence}% confident</span>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-300 bg-white/35 p-3">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Frequency</div>
          <div className="mt-2 text-xl font-semibold text-slate-900">{frequency.toLocaleString()}</div>
        </div>
        <div className="rounded-2xl border border-slate-300 bg-white/35 p-3">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Share</div>
          <div className="mt-2 text-xl font-semibold text-slate-900">{percentage}%</div>
        </div>
        <div className="rounded-2xl border border-slate-300 bg-white/35 p-3">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Trend</div>
          <div className="mt-2 text-xl font-semibold text-emerald-600">+{trend}%</div>
        </div>
        <div className="rounded-2xl border border-slate-300 bg-white/35 p-3">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Affected</div>
          <div className="mt-2 text-sm font-semibold text-slate-900">{affectedSegment}</div>
        </div>
      </div>
    </div>
  );
}
