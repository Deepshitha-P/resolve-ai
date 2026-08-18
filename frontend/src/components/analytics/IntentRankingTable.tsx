interface IntentRow {
  intent: string;
  volume: number;
  percentage: number;
  trend: number;
  dominantSentiment: 'positive' | 'neutral' | 'negative';
  resolutionRate: number;
}

interface IntentRankingTableProps {
  rows: IntentRow[];
}

const sentimentBadge = {
  positive: 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20',
  neutral: 'bg-sky-500/10 text-sky-300 border border-sky-500/20',
  negative: 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
};

export function IntentRankingTable({ rows }: IntentRankingTableProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Ranked intent mix</div>
        <h3 className="mt-2 text-2xl font-semibold text-slate-900">Intent performance</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-300 text-slate-400">
              <th className="py-3 pr-4 font-medium">Intent</th>
              <th className="py-3 pr-4 font-medium">Volume</th>
              <th className="py-3 pr-4 font-medium">%</th>
              <th className="py-3 pr-4 font-medium">Trend</th>
              <th className="py-3 pr-4 font-medium">Sentiment</th>
              <th className="py-3 pr-4 font-medium">Resolution</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.intent} className="border-b border-slate-200/80 text-slate-700 last:border-0">
                <td className="py-3 pr-4 font-medium text-slate-900">{row.intent}</td>
                <td className="py-3 pr-4">{row.volume.toLocaleString()}</td>
                <td className="py-3 pr-4">{row.percentage}%</td>
                <td className={`py-3 pr-4 ${row.trend >= 0 ? 'text-emerald-300' : 'text-amber-300'}`}>
                  {row.trend >= 0 ? '+' : ''}{row.trend}%
                </td>
                <td className="py-3 pr-4">
                  <span className={`inline-flex rounded-full px-2.5 py-1 text-[10px] uppercase tracking-[0.12em] ${sentimentBadge[row.dominantSentiment]}`}>
                    {row.dominantSentiment}
                  </span>
                </td>
                <td className="py-3 pr-4">{row.resolutionRate}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
