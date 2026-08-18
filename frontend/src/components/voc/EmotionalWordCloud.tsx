interface EmotionalWordCloudProps {
  words: Array<{ word: string; weight: number }>;
}

export function EmotionalWordCloud({ words }: EmotionalWordCloudProps) {
  // Normalize both mock (word/weight) and live API (text/value/sentiment) formats
  const normalizedWords = words.map((w: any) => ({
    word: w.word || w.text,
    weight: typeof w.weight === 'number' ? w.weight : w.value,
    sentiment: w.sentiment
  })).filter(w => w.word && typeof w.weight === 'number');

  if (normalizedWords.length === 0) return null;

  const maxWeight = Math.max(...normalizedWords.map((w) => w.weight));
  const minWeight = Math.min(...normalizedWords.map((w) => w.weight));
  const range = maxWeight - minWeight || 1;

  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Keywords</div>
        <h3 className="mt-2 text-2xl font-semibold text-slate-900">Emotional keywords</h3>
      </div>

      <div className="flex flex-wrap gap-3">
        {normalizedWords.map((item, idx) => {
          const normalized = (item.weight - minWeight) / range;
          const size = 0.75 + normalized * 1.25; // Range from 0.75rem to 2rem
          const opacity = 0.6 + normalized * 0.4; // Range from 0.6 to 1.0

          let isPositive = false;
          if (item.sentiment === 'positive') {
            isPositive = true;
          } else if (!item.sentiment) {
            // Fallback for mock data without sentiment
            isPositive = ['helpful', 'satisfied', 'reliable', 'excellent'].includes(item.word.toLowerCase());
          }
          
          const color = isPositive ? '#059669' : '#dc2626';

          return (
            <div
              key={idx}
              style={{
                fontSize: `${size}rem`,
                color,
                opacity,
                fontWeight: 600,
                cursor: 'default',
                transition: 'all 0.3s ease'
              }}
              className="hover:scale-110 hover:opacity-100"
            >
              {item.word}
            </div>
          );
        })}
      </div>

      <div className="mt-5 rounded-2xl border border-slate-300 bg-white/35 p-4">
        <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Scale</div>
        <div className="mt-3 flex items-center justify-between">
          <span className="text-sm text-slate-600">Low frequency</span>
          <div className="flex gap-2">
            {[0, 0.25, 0.5, 0.75, 1].map((norm) => (
              <div
                key={norm}
                style={{
                  fontSize: `${0.75 + norm * 1.25}rem`,
                  color: '#64748b',
                  opacity: 0.6 + norm * 0.4
                }}
              >
                ★
              </div>
            ))}
          </div>
          <span className="text-sm text-slate-600">High frequency</span>
        </div>
      </div>
    </div>
  );
}
