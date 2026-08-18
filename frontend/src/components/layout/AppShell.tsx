import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

interface AppShellProps {
  children?: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pageTitle = 'Executive Overview';
  const pageSubtitle = 'Real-time AI operational analytics';

  return (
    <div className="flex min-h-screen bg-white text-slate-800">
      <div className="hidden w-72 shrink-0 md:block">
        <Sidebar />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={pageTitle} subtitle={pageSubtitle} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
