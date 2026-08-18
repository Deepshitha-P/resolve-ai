import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface IntentTrendChartProps {
  data: Array<{ date: string; 'Technical Support': number; Billing: number; Complaint: number; 'Order Status': number; Feedback: number; 'Refund Request': number; 'Product Quality': number; Shipping: number; 'Account Issue': number; 'Feature Request': number }>;
}

const tooltipStyle = {
  backgroundColor: '#0f172a',
  border: '1px solid rgba(148,163,184,0.35)',
  borderRadius: '12px',
  color: '#e2e8f0'
};

export function IntentTrendChart({ data }: IntentTrendChartProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Trend</div>
        <h3 className="mt-2 text-2xl font-semibold text-slate-900">Intent volume over time</h3>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={tooltipStyle} />
            <Line type="monotone" dataKey="Technical Support" stroke="#38bdf8" strokeWidth={2.5} dot={false} />
            <Line type="monotone" dataKey="Billing" stroke="#a78bfa" strokeWidth={2.5} dot={false} />
            <Line type="monotone" dataKey="Complaint" stroke="#f87171" strokeWidth={2.5} dot={false} />
            <Line type="monotone" dataKey="Shipping" stroke="#34d399" strokeWidth={2.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
