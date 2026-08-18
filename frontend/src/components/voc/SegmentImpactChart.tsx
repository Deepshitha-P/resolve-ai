import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from 'recharts';

interface SegmentImpactChartProps {
  data: Array<{
    segment: string;
    serviceSpeed: number;
    productReliability: number;
    pricing: number;
    supportQuality: number;
    deliveryExperience: number;
  }>;
}

const tooltipStyle = {
  backgroundColor: '#0f172a',
  border: '1px solid rgba(148,163,184,0.35)',
  borderRadius: '12px',
  color: '#e2e8f0'
};

export function SegmentImpactChart({ data }: SegmentImpactChartProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Impact by segment</div>
        <h3 className="mt-2 text-2xl font-semibold text-slate-900">Customer satisfaction by segment & theme</h3>
      </div>

      <div className="h-80 overflow-x-auto">
        <ResponsiveContainer width="100%" height="100%" minWidth={500}>
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis dataKey="segment" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 100]} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend />
            <Bar dataKey="serviceSpeed" fill="#86efac" name="Service Speed" />
            <Bar dataKey="productReliability" fill="#fbbf24" name="Product Reliability" />
            <Bar dataKey="pricing" fill="#60a5fa" name="Pricing" />
            <Bar dataKey="supportQuality" fill="#a78bfa" name="Support Quality" />
            <Bar dataKey="deliveryExperience" fill="#f472b6" name="Delivery Experience" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
