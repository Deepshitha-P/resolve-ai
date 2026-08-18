import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';

interface KPIStatCardProps {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  tone: 'success' | 'warning' | 'primary';
}

const toneStyles = {
  success: 'text-emerald-400',
  warning: 'text-amber-400',
  primary: 'text-sky-400'
};

export function KPIStatCard({ label, value, change, trend, tone }: KPIStatCardProps) {
  const TrendIcon = trend === 'up' ? ArrowUpRight : trend === 'down' ? ArrowDownRight : Minus;

  return (
    <div className="rounded-2xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between text-sm text-slate-400">
        <span>{label}</span>
        <span className={`rounded-md bg-slate-100 p-2 ${toneStyles[tone]}`}>
          <TrendIcon size={14} />
        </span>
      </div>
      <div className="text-3xl font-bold tracking-tight text-slate-900">{value}</div>
      <div className={`mt-3 inline-flex items-center gap-2 text-sm ${toneStyles[tone]}`}>
        <TrendIcon size={14} />
        <span>{change}</span>
      </div>
    </div>
  );
}
