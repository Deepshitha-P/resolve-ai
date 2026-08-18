interface PerformanceRow {
  intent: string;
  avgResponseTime: number;
  resolutionRate: number;
  satisfaction: number;
  escalationRate: number;
  repeatContactRate: number;
  attention: boolean;
}

interface PerformanceTableProps {
  rows: PerformanceRow[];
}

export function PerformanceTable({ rows }: PerformanceTableProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Summary</div>
        <h3 className="mt-2 text-2xl font-semibold text-slate-900">Performance by intent</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-300 text-slate-400">
              <th className="py-3 pr-4 font-medium">Intent</th>
              <th className="py-3 pr-4 font-medium">Avg response</th>
              <th className="py-3 pr-4 font-medium">Resolution</th>
              <th className="py-3 pr-4 font-medium">Satisfaction</th>
              <th className="py-3 pr-4 font-medium">Escalation</th>
              <th className="py-3 pr-4 font-medium">Repeat</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.intent} className="border-b border-slate-200/80 text-slate-700 last:border-0">
                <td className="py-3 pr-4 font-medium text-slate-900">
                  <div className="flex items-center gap-2">
                    <span>{row.intent}</span>
                    {row.attention ? <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] text-amber-300">Attention</span> : null}
                  </div>
                </td>
                <td className="py-3 pr-4">{row.avgResponseTime} min</td>
                <td className="py-3 pr-4">{row.resolutionRate}%</td>
                <td className="py-3 pr-4">{row.satisfaction}/100</td>
                <td className="py-3 pr-4">{row.escalationRate}%</td>
                <td className="py-3 pr-4">{row.repeatContactRate}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
