import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface PainScoreChartProps {
  data: Array<{ name: string; painScore: number; growthRate: number }>;
}

const tooltipStyle = {
  backgroundColor: '#0f172a',
  border: '1px solid rgba(148,163,184,0.35)',
  borderRadius: '12px',
  color: '#e2e8f0'
};

export function PainScoreChart({ data }: PainScoreChartProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Pain score</div>
        <h3 className="mt-2 text-2xl font-semibold text-slate-900">Issue severity ranking</h3>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 100]} />
            <Tooltip formatter={(value: number) => `${value}/100`} contentStyle={tooltipStyle} />
            <Bar dataKey="painScore" radius={[8, 8, 0, 0]} fill="#f87171" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
