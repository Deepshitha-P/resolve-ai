import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface BenchmarkChartProps {
  data: Array<{ company: string; resolutionRate: number; satisfaction: number; responseTime: number; escalationRate: number }>;
}

const tooltipStyle = {
  backgroundColor: '#0f172a',
  border: '1px solid rgba(148,163,184,0.35)',
  borderRadius: '12px',
  color: '#e2e8f0'
};

export function BenchmarkChart({ data }: BenchmarkChartProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Benchmarking</div>
        <h3 className="mt-2 text-2xl font-semibold text-slate-900">Resolution across companies</h3>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis dataKey="company" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 100]} />
            <Tooltip formatter={(value: number) => `${value}%`} contentStyle={tooltipStyle} />
            <Bar dataKey="resolutionRate" radius={[8, 8, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={entry.company} fill={index === 0 ? '#34d399' : index === 1 ? '#60a5fa' : index === 2 ? '#fbbf24' : '#f87171'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
