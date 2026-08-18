interface CustomerQuoteProps {
  quote: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  channel: string;
  source: string;
  segment?: string;
}

const sentimentColors = {
  positive: '#059669',
  neutral: '#475569',
  negative: '#dc2626'
};

const sentimentBgColors = {
  positive: 'bg-emerald-50',
  neutral: 'bg-slate-100',
  negative: 'bg-red-50'
};

export function CustomerQuote({ quote, sentiment, channel, source, segment }: CustomerQuoteProps) {
  return (
    <div className={`rounded-2xl border border-slate-300 ${sentimentBgColors[sentiment]} bg-opacity-40 p-4 backdrop-blur-sm`}>
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="text-sm italic text-slate-700">"{quote}"</div>
      </div>

      <div className="flex flex-wrap gap-2">
        <span className="inline-block rounded-full border border-slate-600 bg-white/40 px-2 py-1 text-xs uppercase tracking-[0.12em]" style={{ color: sentimentColors[sentiment] }}>
          {sentiment}
        </span>
        <span className="inline-block rounded-full border border-slate-600 bg-white/40 px-2 py-1 text-xs text-slate-600">{channel}</span>
        <span className="inline-block rounded-full border border-slate-600 bg-white/40 px-2 py-1 text-xs text-slate-400">{source}</span>
        {segment && <span className="inline-block rounded-full border border-slate-600 bg-white/40 px-2 py-1 text-xs text-slate-400">{segment}</span>}
      </div>
    </div>
  );
}
