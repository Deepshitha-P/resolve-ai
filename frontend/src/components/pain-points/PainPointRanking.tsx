interface PainPointRankingProps {
  items: Array<{
    name: string;
    painScore: number;
    mentionCount: number;
    percentage: number;
    growthRate: number;
    severity: 'critical' | 'high' | 'medium';
  }>;
}

const severityColors = {
  critical: '#f87171',
  high: '#fbbf24',
  medium: '#60a5fa'
};

export function PainPointRanking({ items }: PainPointRankingProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Ranking</div>
        <h3 className="mt-2 text-2xl font-semibold text-slate-900">Pain score leaderboard</h3>
      </div>

      <div className="space-y-4">
        {items.map((item, index) => (
          <div key={item.name} className="rounded-2xl border border-slate-300 bg-white/35 p-4">
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-slate-100 text-sm font-medium text-slate-800">#{index + 1}</span>
                <span className="font-medium text-slate-900">{item.name}</span>
              </div>
              <span className="text-lg font-semibold text-slate-900">{item.painScore}</span>
            </div>

            <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-[0.12em] text-slate-400">
              <span>Mentions</span>
              <span>{item.mentionCount.toLocaleString()}</span>
            </div>

            <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full" style={{ width: `${Math.min(item.painScore, 100)}%`, background: severityColors[item.severity] }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
