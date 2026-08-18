import type { ReactNode } from 'react';

interface AnalyticsHeaderProps {
  title: string;
  subtitle: string;
  actions?: ReactNode;
}

export function AnalyticsHeader({ title, subtitle, actions }: AnalyticsHeaderProps) {
  return (
    <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h2>
        <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}
