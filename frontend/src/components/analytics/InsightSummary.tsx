interface InsightSummaryProps {
  title: string;
  summary: string;
  tone?: 'positive' | 'warning' | 'danger';
}

const toneStyles = {
  positive: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200',
  warning: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
  danger: 'border-rose-500/30 bg-rose-500/10 text-rose-200'
};

export function InsightSummary({ title, summary, tone = 'warning' }: InsightSummaryProps) {
  return (
    <div className={`rounded-2xl border p-4 ${toneStyles[tone]}`}>
      <div className="text-xs uppercase tracking-[0.18em] opacity-80">Insight summary</div>
      <div className="mt-2 text-lg font-semibold">{title}</div>
      <p className="mt-2 text-sm leading-6 opacity-90">{summary}</p>
    </div>
  );
}
