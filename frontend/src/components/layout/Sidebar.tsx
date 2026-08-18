import { LayoutDashboard, MessageSquareText, AlertTriangle, BarChart3, Database, FileText, Sparkles, Bot, BrainCircuit, Activity, ShieldCheck } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const navItems = [
  { label: 'Executive Summary', path: '/dashboard', icon: LayoutDashboard },
  { label: 'KPI Metrics', path: '/kpis', icon: BarChart3 },
  { label: 'Spike Detection', path: '/spikes', icon: AlertTriangle },
  { label: 'Sentiment Analysis', path: '/sentiment', icon: Activity },
  { label: 'RAG / AI Insights', path: '/rag', icon: Bot }
];

export function Sidebar() {
  return (
    <aside className="flex h-full min-h-screen w-full flex-col border-r border-slate-300/60 bg-white/80 backdrop-blur-xl">
      <div className="flex items-center gap-3 border-b border-slate-300/60 p-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-violet-500 shadow-glow">
          <BrainCircuit className="h-5 w-5 text-slate-900" />
        </div>
        <div>
          <div className="font-display text-xl font-bold tracking-tight text-slate-900">Resolve AI</div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Insights</div>
        </div>
      </div>

      <nav className="flex-1 space-y-2 p-4">
        {navItems.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-sky-500/20 to-violet-500/20 text-slate-900 ring-1 ring-sky-400/30'
                  : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-900'
              }`
            }
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-300/60 p-4">
        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300">
          <ShieldCheck className="h-3.5 w-3.5" />
          Pipeline active
        </div>
      </div>
    </aside>
  );
}
