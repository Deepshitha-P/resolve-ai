interface SuggestedActionProps {
  title: string;
  impact: string;
  priority: 'critical' | 'high' | 'medium';
}

const priorityColors = {
  critical: '#f87171',
  high: '#fbbf24',
  medium: '#60a5fa'
};

const priorityBg = {
  critical: 'bg-red-50',
  high: 'bg-amber-50',
  medium: 'bg-blue-50'
};

export function SuggestedAction({ title, impact, priority }: SuggestedActionProps) {
  return (
    <div className={`rounded-2xl border border-slate-300 ${priorityBg[priority]} bg-opacity-30 p-4 backdrop-blur-sm`}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <h4 className="font-medium text-slate-900">{title}</h4>
        <span className="inline-flex rounded px-2 py-1 text-xs font-medium uppercase tracking-[0.12em]" style={{ color: priorityColors[priority], background: `${priorityColors[priority]}15` }}>
          {priority}
        </span>
      </div>
      <p className="text-sm text-slate-600">{impact}</p>
    </div>
  );
}
