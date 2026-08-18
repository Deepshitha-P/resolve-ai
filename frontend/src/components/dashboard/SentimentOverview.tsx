import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts';

interface SentimentSlice {
  name: 'Positive' | 'Neutral' | 'Negative';
  value: number;
  color: string;
}

interface SentimentOverviewProps {
  slices: SentimentSlice[];
  total: number;
}

export function SentimentOverview({ slices, total }: SentimentOverviewProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Sentiment overview</div>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">Customer mood</h3>
        </div>
        <div className="rounded-xl border border-slate-300 bg-white/40 px-3 py-2 text-sm text-slate-600">
          {total.toLocaleString()} interactions
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[220px_1fr] lg:items-center">
        <div className="mx-auto h-52 w-52">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={slices} dataKey="value" nameKey="name" innerRadius={54} outerRadius={82} paddingAngle={3}>
                {slices.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-4">
          {slices.map((slice) => (
            <div key={slice.name} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-300 bg-white/35 px-3 py-2">
              <div className="flex items-center gap-3">
                <span className="h-3 w-3 rounded-full" style={{ background: slice.color }} />
                <span className="text-sm text-slate-600">{slice.name}</span>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-slate-900">{slice.value}%</div>
                <div className="text-xs text-slate-400">share</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
