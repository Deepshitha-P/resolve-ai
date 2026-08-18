import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface SentimentDistributionProps {
  positive: number;
  neutral: number;
  negative: number;
}

const COLORS = ['#86efac', '#94a3b8', '#fca5a5'];

const tooltipStyle = {
  backgroundColor: '#0f172a',
  border: '1px solid rgba(148,163,184,0.35)',
  borderRadius: '12px',
  color: '#e2e8f0'
};

export function SentimentDistribution({ positive, neutral, negative }: SentimentDistributionProps) {
  const data = [
    { name: 'Positive', value: positive },
    { name: 'Neutral', value: neutral },
    { name: 'Negative', value: negative }
  ];

  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Sentiment</div>
        <h3 className="mt-2 text-2xl font-semibold text-slate-900">Customer sentiment distribution</h3>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={60} outerRadius={120} paddingAngle={2} dataKey="value">
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-emerald-700 bg-emerald-50/30 p-3 text-center">
          <div className="text-xs uppercase tracking-[0.2em] text-emerald-300">Positive</div>
          <div className="mt-2 text-2xl font-semibold text-emerald-300">{positive}%</div>
        </div>
        <div className="rounded-2xl border border-slate-300 bg-white/30 p-3 text-center">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Neutral</div>
          <div className="mt-2 text-2xl font-semibold text-slate-600">{neutral}%</div>
        </div>
        <div className="rounded-2xl border border-red-300 bg-red-50/30 p-3 text-center">
          <div className="text-xs uppercase tracking-[0.2em] text-red-300">Negative</div>
          <div className="mt-2 text-2xl font-semibold text-red-300">{negative}%</div>
        </div>
      </div>
    </div>
  );
}
