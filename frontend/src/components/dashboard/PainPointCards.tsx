interface PainPointItem {
  id: string;
  label: string;
  description: string;
  severity: 'critical' | 'high' | 'medium';
  share: number;
  rank: number;
}

interface PainPointCardsProps {
  items: PainPointItem[];
}

const severityStyles = {
  critical: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  high: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  medium: 'bg-sky-500/15 text-sky-300 border-sky-500/30'
};

export function PainPointCards({ items }: PainPointCardsProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Priority pain points</div>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">Top friction areas</h3>
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="rounded-2xl border border-slate-300 bg-white/35 p-4">
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-slate-100 text-sm font-semibold text-slate-800">
                  #{item.rank}
                </span>
                <div>
                  <div className="font-medium text-slate-900">{item.label}</div>
                </div>
              </div>
              <span className={`rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.14em] ${severityStyles[item.severity]}`}>
                {item.severity}
              </span>
            </div>

            <p className="mb-3 text-sm leading-6 text-slate-600">{item.description}</p>

            <div className="flex items-center justify-between gap-3 text-sm text-slate-400">
              <span>Share of complaints</span>
              <span className="font-medium text-slate-700">{item.share}%</span>
            </div>
            <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-gradient-to-r from-rose-500 via-amber-400 to-yellow-300"
                style={{ width: `${Math.min(item.share, 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
