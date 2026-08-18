type BadgeTone = 'success' | 'warning' | 'danger' | 'neutral' | 'primary';

interface BadgeProps {
  label: string;
  tone?: BadgeTone;
}

const toneStyles: Record<BadgeTone, string> = {
  success: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
  warning: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
  danger: 'bg-rose-500/15 text-rose-300 border border-rose-500/30',
  neutral: 'bg-slate-200/60 text-slate-700 border border-slate-600',
  primary: 'bg-sky-500/15 text-sky-300 border border-sky-500/30'
};

export function Badge({ label, tone = 'neutral' }: BadgeProps) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${toneStyles[tone]}`}>{label}</span>;
}
