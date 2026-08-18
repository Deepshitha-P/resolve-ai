import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';

interface AnalyticsKPIProps {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  tone?: 'success' | 'warning' | 'primary';
}

const toneStyles = {
  success: 'text-emerald-300 bg-emerald-500/10',
  warning: 'text-amber-300 bg-amber-500/10',
  primary: 'text-sky-300 bg-sky-500/10'
};

export function AnalyticsKPI({ label, value, change, trend, tone = 'primary' }: AnalyticsKPIProps) {
  const Icon = trend === 'up' ? ArrowUpRight : trend === 'down' ? ArrowDownRight : Minus;

  return (
    <div className="rounded-2xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <span className="text-sm text-slate-400">{label}</span>
        <span className={`rounded-md p-2 ${toneStyles[tone]}`}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <div className="text-3xl font-bold tracking-tight text-slate-900">{value}</div>
      <div className={`mt-3 inline-flex items-center gap-2 text-sm ${toneStyles[tone].split(' ')[0]}`}>
        <Icon className="h-4 w-4" />
        <span>{change}</span>
      </div>
    </div>
  );
}
