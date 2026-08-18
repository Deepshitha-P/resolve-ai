interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = 'LoadingΓÇª' }: LoadingStateProps) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-300/60 bg-slate-50/50 p-4 text-sm text-slate-600">
      <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-sky-400" />
      <span>{label}</span>
    </div>
  );
}
