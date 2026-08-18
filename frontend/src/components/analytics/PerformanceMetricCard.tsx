import { Clock3, Gauge, MessageSquareText, TrendingUp } from 'lucide-react';

interface PerformanceMetricCardProps {
  label: string;
  value: string;
  delta: string;
  tone?: 'success' | 'warning' | 'primary';
  attention?: boolean;
}

const toneStyles = {
  success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200',
  warning: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
  primary: 'border-sky-500/30 bg-sky-500/10 text-sky-200'
};

const iconMap = {
  response: Clock3,
  resolution: TrendingUp,
  satisfaction: MessageSquareText,
  escalation: Gauge
};

export function PerformanceMetricCard({ label, value, delta, tone = 'primary', attention = false }: PerformanceMetricCardProps) {
  const Icon = iconMap[label.toLowerCase().includes('response') ? 'response' : label.toLowerCase().includes('resolution') ? 'resolution' : label.toLowerCase().includes('satisfaction') ? 'satisfaction' : 'escalation'];

  return (
    <div className={`rounded-2xl border p-4 ${toneStyles[tone]} ${attention ? 'ring-1 ring-amber-500/30' : ''}`}>
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm opacity-80">{label}</div>
        <Icon className="h-4 w-4" />
      </div>
      <div className="mt-5 text-3xl font-bold tracking-tight text-slate-900">{value}</div>
      <div className="mt-2 text-sm opacity-80">{delta}</div>
    </div>
  );
}
