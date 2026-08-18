interface VocTheme {
  title: string;
  volume: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  excerpt: string;
}

interface VoiceOfCustomerPanelProps {
  themes: VocTheme[];
}

const sentimentStyles = {
  positive: 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20',
  neutral: 'bg-sky-500/10 text-sky-300 border border-sky-500/20',
  negative: 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
};

export function VoiceOfCustomerPanel({ themes }: VoiceOfCustomerPanelProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Voice of customer</div>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">Recurring themes</h3>
        </div>
      </div>

      <div className="space-y-3">
        {themes.map((theme) => (
          <div key={theme.title} className="rounded-2xl border border-slate-300 bg-white/35 p-4">
            <div className="mb-2 flex items-start justify-between gap-3">
              <div>
                <div className="font-medium text-slate-900">{theme.title}</div>
                <div className="mt-2 text-sm text-slate-600">{theme.excerpt}</div>
              </div>
              <span className={`whitespace-nowrap rounded-full px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.14em] ${sentimentStyles[theme.sentiment]}`}>
                {theme.sentiment}
              </span>
            </div>

            <div className="flex items-center justify-between gap-3 text-sm text-slate-400">
              <span>Mentions</span>
              <span className="font-medium text-slate-700">{theme.volume}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
