import type { ReactNode } from 'react';

interface FilterBarProps {
  children: ReactNode;
}

export function FilterBar({ children }: FilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-300/60 bg-slate-50/50 p-3">
      {children}
    </div>
  );
}
