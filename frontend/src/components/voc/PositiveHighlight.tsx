interface PositiveHighlightProps {
  title: string;
  frequency: number;
  quote: string;
  theme: string;
}

export function PositiveHighlight({ title, frequency, quote, theme }: PositiveHighlightProps) {
  return (
    <div className="rounded-2xl border border-emerald-700/60 bg-emerald-50/30 p-4 backdrop-blur-sm">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div>
          <h4 className="font-semibold text-emerald-200">{title}</h4>
          <div className="mt-1 text-xs uppercase tracking-[0.12em] text-emerald-300/70">{theme}</div>
        </div>
        <span className="inline-flex rounded-lg bg-emerald-900/50 px-2 py-1 text-sm font-medium text-emerald-200">{frequency.toLocaleString()}</span>
      </div>
      <p className="mt-3 italic text-emerald-100/80">"{quote}"</p>
    </div>
  );
}
