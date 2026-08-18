import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

interface SentimentDistributionProps {
  positive: number;
  neutral: number;
  negative: number;
}

const pieData = [
  { name: 'Positive', value: 52, color: '#34d399' },
  { name: 'Neutral', value: 28, color: '#60a5fa' },
  { name: 'Negative', value: 20, color: '#f87171' }
];

const tooltipStyle = {
  backgroundColor: '#0f172a',
  border: '1px solid rgba(148,163,184,0.35)',
  borderRadius: '12px',
  color: '#e2e8f0'
};

export function SentimentDistribution({ positive, neutral, negative }: SentimentDistributionProps) {
  const chartData = [
    { name: 'Positive', value: positive, color: '#34d399' },
    { name: 'Neutral', value: neutral, color: '#60a5fa' },
    { name: 'Negative', value: negative, color: '#f87171' }
  ];

  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Distribution</div>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">Overall sentiment</h3>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-[220px_1fr] md:items-center">
        <div className="mx-auto h-56 w-56">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={52} outerRadius={82} paddingAngle={4}>
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `${value}%`} contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-3">
          {chartData.map((slice) => (
            <div key={slice.name} className="flex items-center justify-between rounded-2xl border border-slate-300 bg-white/35 px-3 py-2">
              <div className="flex items-center gap-3">
                <span className="h-3 w-3 rounded-full" style={{ background: slice.color }} />
                <span className="text-sm text-slate-600">{slice.name}</span>
              </div>
              <span className="text-base font-semibold text-slate-900">{slice.value}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
