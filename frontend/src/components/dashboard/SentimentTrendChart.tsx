import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

interface SentimentTrendPoint {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
}

interface SentimentTrendChartProps {
  data: SentimentTrendPoint[];
}

const tooltipStyles = {
  backgroundColor: '#0f172a',
  border: '1px solid rgba(148,163,184,0.35)',
  borderRadius: '12px',
  color: '#e2e8f0'
};

export function SentimentTrendChart({ data }: SentimentTrendChartProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Sentiment trend</div>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">Customer sentiment by day</h3>
        </div>
        <div className="rounded-xl border border-slate-300 bg-white/40 px-3 py-2 text-sm text-slate-600">Last 14 days</div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="positiveFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#34d399" stopOpacity={0.5} />
                <stop offset="95%" stopColor="#34d399" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="neutralFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#60a5fa" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="negativeFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f87171" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#f87171" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 100]} />
            <Tooltip contentStyle={tooltipStyles} />
            <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: '12px' }} />
            <Area type="monotone" dataKey="positive" stroke="#34d399" fill="url(#positiveFill)" strokeWidth={2} name="Positive" />
            <Area type="monotone" dataKey="neutral" stroke="#60a5fa" fill="url(#neutralFill)" strokeWidth={2} name="Neutral" />
            <Line type="monotone" dataKey="negative" stroke="#f87171" strokeWidth={2} name="Negative" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
