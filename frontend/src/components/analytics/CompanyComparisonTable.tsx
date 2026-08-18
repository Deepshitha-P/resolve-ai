interface CompanyComparisonRow {
  company: string;
  resolutionRate: number;
  customerSatisfaction: number;
  averageResponseTime: number;
  escalationRate: number;
  negativeSentiment: number;
  repeatContact: number;
}

interface CompanyComparisonTableProps {
  rows: CompanyComparisonRow[];
}

export function CompanyComparisonTable({ rows }: CompanyComparisonTableProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Ranking</div>
        <h3 className="mt-2 text-2xl font-semibold text-slate-900">Company benchmark leaderboard</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-300 text-slate-400">
              <th className="py-3 pr-4 font-medium">Company</th>
              <th className="py-3 pr-4 font-medium">Resolution</th>
              <th className="py-3 pr-4 font-medium">CSAT</th>
              <th className="py-3 pr-4 font-medium">Resp. time</th>
              <th className="py-3 pr-4 font-medium">Escalation</th>
              <th className="py-3 pr-4 font-medium">Neg. sentiment</th>
              <th className="py-3 pr-4 font-medium">Repeat</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.company} className="border-b border-slate-200/80 text-slate-700 last:border-0">
                <td className="py-3 pr-4 font-medium text-slate-900">{row.company}</td>
                <td className="py-3 pr-4">{row.resolutionRate}%</td>
                <td className="py-3 pr-4">{row.customerSatisfaction}/100</td>
                <td className="py-3 pr-4">{row.averageResponseTime} min</td>
                <td className="py-3 pr-4">{row.escalationRate}%</td>
                <td className="py-3 pr-4">{row.negativeSentiment}%</td>
                <td className="py-3 pr-4">{row.repeatContact}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
