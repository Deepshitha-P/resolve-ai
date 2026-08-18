import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface IntentItem {
  name: string;
  value: number;
  percentage: number;
  trend: 'up' | 'down' | 'neutral';
  sentiment: 'positive' | 'neutral' | 'negative';
}

interface IntentRankingProps {
  items: IntentItem[];
}

const sentimentStyles = {
  positive: 'text-emerald-300',
  neutral: 'text-sky-300',
  negative: 'text-rose-300'
};

export function IntentRanking({ items }: IntentRankingProps) {
  return (
    <div className="rounded-3xl border border-slate-300/60 bg-slate-50/70 p-5 shadow-panel backdrop-blur-sm">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <div className="text-sm uppercase tracking-[0.18em] text-slate-400">Top customer intents</div>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">Intent overview</h3>
        </div>
      </div>

      <div className="space-y-4">
        {items.map((item, index) => {
          const TrendIcon = item.trend === 'up' ? ArrowUpRight : item.trend === 'down' ? ArrowDownRight : Minus;

          return (
            <div key={item.name} className="rounded-2xl border border-slate-300 bg-white/35 p-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-slate-100 text-xs font-medium text-slate-700">
                    {index + 1}
                  </span>
                  <div>
                    <div className="font-medium text-slate-900">{item.name}</div>
                  </div>
                </div>
                <div className={`flex items-center gap-1 text-sm ${sentimentStyles[item.sentiment]}`}>
                  <TrendIcon className="h-4 w-4" />
                  <span>{item.trend === 'up' ? 'Rising' : item.trend === 'down' ? 'Cooling' : 'Stable'}</span>
                </div>
              </div>

              <div className="mb-2 flex items-center justify-between text-sm text-slate-600">
                <span>{item.value.toLocaleString()} interactions</span>
                <span>{item.percentage}%</span>
              </div>

              <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-gradient-to-r from-sky-500 via-blue-500 to-violet-500" style={{ width: `${Math.max(item.percentage, 8)}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
