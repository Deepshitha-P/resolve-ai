import { Bell, Menu, Search, Sparkles } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface TopBarProps {
  title: string;
  subtitle?: string;
}

interface SpikeAlert {
  category: string;
  growth_pct: number;
  recent_volume: number;
}

export function TopBar({ title, subtitle }: TopBarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [notifOpen, setNotifOpen] = useState(false);
  const [spikes, setSpikes] = useState<SpikeAlert[]>([]);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 768) setMobileMenuOpen(false);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Load real spike/notification data from backend
  useEffect(() => {
    fetch('/api/executive-summary-v2')
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d?.key_findings) {
          setSpikes(d.key_findings.map((f: any) => ({
            category: f.category,
            growth_pct: f.growth_pct,
            recent_volume: f.recent_volume,
          })));
        }
      })
      .catch(() => {});
  }, []);

  // Close notifications on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSearch = () => {
    const q = searchQuery.trim();
    if (q) {
      navigate('/rag', { state: { query: q } });
      setSearchQuery('');
      setSearchOpen(false);
    }
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
    if (e.key === 'Escape') { setSearchOpen(false); setSearchQuery(''); }
  };

  return (
    <header className="border-b border-slate-300/60 bg-white/70 px-4 py-3 backdrop-blur-xl md:px-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 md:hidden">
          <button
            type="button"
            aria-label="Toggle menu"
            className="rounded-xl border border-slate-300 bg-slate-50 p-2 text-slate-700"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
          >
            <Menu className="h-4 w-4" />
          </button>
        </div>

        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
          {subtitle ? <p className="text-sm text-slate-400">{subtitle}</p> : null}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          {/* Search Insights — functional */}
          {searchOpen ? (
            <div className="flex items-center gap-2 rounded-xl border border-indigo-300 bg-white px-3 py-2 text-sm shadow-sm">
              <Search className="h-4 w-4 text-indigo-500" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                placeholder="Ask AI about any issue..."
                className="outline-none bg-transparent text-slate-700 placeholder:text-slate-400 w-48"
                autoFocus
              />
              <button
                onClick={handleSearch}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
              >
                Go
              </button>
            </div>
          ) : (
            <button
              onClick={() => { setSearchOpen(true); setTimeout(() => searchInputRef.current?.focus(), 50); }}
              className="flex items-center gap-2 rounded-xl border border-slate-300 bg-slate-50/70 px-3 py-2 text-sm text-slate-600 hover:border-indigo-300 hover:bg-indigo-50/50 transition-colors"
            >
              <Search className="h-4 w-4 text-slate-400" />
              <span>Search insights</span>
            </button>
          )}

          {/* Notifications — real spikes from backend */}
          <div className="relative" ref={notifRef}>
            <button
              type="button"
              onClick={() => setNotifOpen(prev => !prev)}
              className="rounded-xl border border-slate-300 bg-slate-50/70 p-2.5 text-slate-600 relative hover:border-amber-300 transition-colors"
            >
              <Bell className="h-4 w-4" />
              {spikes.length > 0 && (
                <span className="absolute -top-1 -right-1 h-4 w-4 flex items-center justify-center rounded-full bg-red-500 text-[9px] text-white font-bold">
                  {spikes.length}
                </span>
              )}
            </button>
            {notifOpen && (
              <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-xl shadow-lg z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-100 bg-slate-50">
                  <div className="text-xs font-bold uppercase text-slate-500">Active Alerts</div>
                  <div className="text-[10px] text-slate-400">From emerging_issues backend analysis</div>
                </div>
                {spikes.length === 0 ? (
                  <div className="px-4 py-6 text-sm text-slate-400 text-center">No active alerts.</div>
                ) : (
                  <div className="max-h-64 overflow-y-auto divide-y divide-slate-100">
                    {spikes.map((spike, i) => (
                      <button
                        key={i}
                        className="w-full text-left px-4 py-3 hover:bg-indigo-50 transition-colors"
                        onClick={() => {
                          setNotifOpen(false);
                          navigate('/rag', {
                            state: { query: `What is causing the spike in ${spike.category} complaints?` }
                          });
                        }}
                      >
                        <div className="text-sm font-medium text-slate-800">{spike.category}</div>
                        <div className="text-xs text-slate-500">
                          +{spike.growth_pct.toFixed(0)}% growth · {spike.recent_volume} complaints
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Settings REMOVED — no real functionality exists */}

          {/* AI Agent — navigates to RAG with default priority query */}
          <button
            onClick={() => navigate('/rag', {
              state: { query: 'Analyze the highest-priority operational issues in the current dataset.' }
            })}
            className="flex items-center gap-2 rounded-xl border border-slate-300 bg-gradient-to-r from-sky-500/15 to-violet-500/15 px-3 py-2 text-sm text-violet-700 hover:from-sky-500/25 hover:to-violet-500/25 transition-colors cursor-pointer font-medium"
          >
            <Sparkles className="h-4 w-4" />
            <span>AI Agent</span>
          </button>
        </div>
      </div>

      {mobileMenuOpen ? (
        <div className="mt-4 rounded-xl border border-slate-300 bg-slate-50/80 p-3 md:hidden space-y-2">
          <div className="flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-600">
            <Search className="h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              placeholder="Search insights..."
              className="outline-none bg-transparent text-slate-700 placeholder:text-slate-400 flex-1"
            />
          </div>
        </div>
      ) : null}
    </header>
  );
}
