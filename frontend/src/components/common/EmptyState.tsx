import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description?: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="flex min-h-44 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/30 p-8 text-center text-slate-400">
      <Inbox className="mb-4 h-8 w-8 text-slate-400" />
      <h4 className="text-lg font-semibold text-slate-700">{title}</h4>
      {description ? <p className="mt-2 max-w-md text-sm text-slate-400">{description}</p> : null}
    </div>
  );
}
