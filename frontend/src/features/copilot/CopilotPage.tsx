import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  Bot, Send, ShieldCheck, AlertCircle, Database, Search, 
  History, Trash2, Clock, MessageSquare, Sparkles, ChevronRight, Zap
} from 'lucide-react';
import { fetchChatHistory, clearChatHistory } from '../../lib/api';

interface RagResponse {
  query: string;
  query_type: string;
  target_layers: string[];
  answer: {
    executive_summary: string;
    key_findings: string[];
    root_causes: string[];
    recommendations: string[];
    priority: string;
  };
  evidence: {
    source_layer: string;
    document_id: string;
    excerpt: string;
    retrieval_score: number;
    confidence: number;
  }[];
  grounded: boolean;
}

interface ConversationItem {
  id: string;
  timestamp: string;
  query: string;
  response: RagResponse;
}

const SUGGESTED_QUERIES = [
  "Why is broadband down in London?",
  "What is our refund policy for service delays?",
  "Show me top customer complaint clusters",
  "How were node outage issues resolved previously?"
];

/**
 * Strip embedded ROOT CAUSE / RECOMMENDED ACTIONS sections from the
 * executive_summary string so they only appear in their own structured panels.
 */
function extractSummaryOnly(text: string): string {
  if (!text) return text;
  // Remove anything from ROOT CAUSE / RECOMMENDED ACTIONS headers onwards
  const cutPatterns = [
    /\n?\s*ROOT CAUSE[S]?\s*:/i,
    /\n?\s*RECOMMENDED ACTIONS?\s*:/i,
    /\n?\s*RECOMMENDATIONS?\s*:/i,
    /\n?\s*KEY FINDING[S]?\s*:/i,
  ];
  let result = text;
  for (const pattern of cutPatterns) {
    const match = result.search(pattern);
    if (match !== -1) {
      result = result.substring(0, match);
    }
  }
  return result.trim();
}

export default function CopilotPage() {
  const location = useLocation();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RagResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<ConversationItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [engineReady, setEngineReady] = useState<boolean | null>(null);
  const [engineProgress, setEngineProgress] = useState('Checking...');

  // Load chat history from backend on mount
  useEffect(() => {
    loadHistory();
    checkEngineStatus();
  }, []);

  // Poll engine status until ready
  const checkEngineStatus = async () => {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) { setEngineReady(false); return; }
      const data = await res.json();
      setEngineReady(data.pipeline_ready);
      setEngineProgress(data.progress || 'Loading...');
      if (!data.pipeline_ready) {
        setTimeout(checkEngineStatus, 5000); // poll every 5s until ready
      }
    } catch {
      setEngineReady(false);
      setTimeout(checkEngineStatus, 8000);
    }
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const data = await fetchChatHistory(50);
      if (data && data.conversations) {
        setHistory(data.conversations);
      }
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (location.state && location.state.query) {
      setQuery(location.state.query);
      handleAnalyze(location.state.query);
    }
  }, [location]);

  const handleAnalyze = async (q: string = query) => {
    const trimmed = q.trim();
    if (!trimmed) return;
    
    // Check if we already have this in history to show immediately
    const existing = history.find(h => h.query.toLowerCase() === trimmed.toLowerCase());
    if (existing && existing.response) {
      setResult(existing.response);
      setSelectedId(existing.id);
      setQuery(trimmed);
      return;
    }

    setLoading(true);
    setError(null);
    setSelectedId(null);

    try {
      const res = await fetch('/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed })
      });
      if (res.status === 503) {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || 'RAG engine is still loading. Please wait a moment and try again.');
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: RagResponse = await res.json();
      setResult(data);
      
      // Update local history cache
      const newEntry: ConversationItem = {
        id: 'temp-' + Date.now(),
        timestamp: new Date().toISOString(),
        query: trimmed,
        response: data
      };
      setHistory(prev => [newEntry, ...prev.filter(p => p.query.toLowerCase() !== trimmed.toLowerCase())]);
      setSelectedId(newEntry.id);
    } catch (e: any) {
      setError(e?.message ?? 'Unable to process query. Please make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectHistory = (item: ConversationItem) => {
    setSelectedId(item.id);
    setQuery(item.query);
    setResult(item.response);
    setError(null);
  };

  const handleClearHistory = async () => {
    if (!confirm("Are you sure you want to clear conversation history?")) return;
    try {
      await clearChatHistory();
      setHistory([]);
      setSelectedId(null);
    } catch (err) {
      console.error('Failed to clear history:', err);
    }
  };

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div className="p-6 md:p-8 pb-20 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2.5 tracking-tight">
            <div className="bg-indigo-600 p-2 rounded-xl text-white shadow-md shadow-indigo-200">
              <Bot className="h-6 w-6" />
            </div>
            Ask RootIQ
          </h1>
          <p className="text-slate-500 mt-1 text-base">
            Analytics-aware operational copilot for systemic customer issues &amp; policy insights.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <Zap className="h-3.5 w-3.5" /> Fast Retrieval Layer Cached
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
            <History className="h-3.5 w-3.5" /> Persistent Memory Active
          </span>
        </div>
      </div>

      {/* Main Grid: Sidebar (History) + Main Chat */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Sidebar: Conversation History */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2 text-sm font-bold text-slate-800">
                <History className="h-4 w-4 text-indigo-600" />
                <span>Conversation Memory</span>
                <span className="bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded-full font-medium">
                  {history.length}
                </span>
              </div>
              {history.length > 0 && (
                <button 
                  onClick={handleClearHistory}
                  title="Clear conversation history"
                  className="text-slate-400 hover:text-red-600 p-1 rounded-lg hover:bg-red-50 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* Conversation List */}
            <div className="space-y-1.5 max-h-[460px] overflow-y-auto pr-1">
              {historyLoading && (
                <div className="text-center py-6 text-sm text-slate-400">Loading history...</div>
              )}
              {!historyLoading && history.length === 0 && (
                <div className="text-center py-8 text-slate-400 space-y-2">
                  <MessageSquare className="h-8 w-8 mx-auto text-slate-300" />
                  <p className="text-xs">No previous conversations yet.</p>
                  <p className="text-[11px] text-slate-400">Ask a question to see cached investigations.</p>
                </div>
              )}
              {history.map((item) => {
                const isSelected = selectedId === item.id || (result && result.query === item.query);
                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelectHistory(item)}
                    className={`w-full text-left p-3 rounded-xl transition-all border text-sm flex flex-col gap-1 group ${
                      isSelected
                        ? 'bg-indigo-50 border-indigo-200 text-indigo-950 font-medium shadow-xs'
                        : 'bg-white border-transparent hover:border-slate-200 hover:bg-slate-50/80 text-slate-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="line-clamp-2 leading-snug">{item.query}</span>
                      <ChevronRight className={`h-4 w-4 shrink-0 transition-transform ${isSelected ? 'text-indigo-600 translate-x-0.5' : 'text-slate-300 group-hover:text-slate-400'}`} />
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-slate-400 font-normal">
                      <Clock className="h-3 w-3" />
                      <span>{formatTime(item.timestamp)}</span>
                      {item.response?.query_type && (
                        <span className="bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded font-mono text-[10px]">
                          {item.response.query_type}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Quick Prompts */}
          <div className="bg-slate-50 rounded-2xl border border-slate-200/80 p-4 space-y-2.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-600 uppercase tracking-wider">
              <Sparkles className="h-3.5 w-3.5 text-amber-500" /> Suggested Investigations
            </div>
            <div className="space-y-1.5">
              {SUGGESTED_QUERIES.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setQuery(sq);
                    handleAnalyze(sq);
                  }}
                  className="w-full text-left text-xs bg-white hover:bg-indigo-50/60 p-2.5 rounded-lg border border-slate-200/60 text-slate-700 hover:text-indigo-900 transition-colors line-clamp-1"
                >
                  "{sq}"
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Area: Search Input & Investigation Details */}
        <div className="lg:col-span-8 space-y-6">
          {/* Query Bar */}
          <div className="bg-white rounded-2xl p-2 shadow-sm border border-slate-200 flex items-center focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 transition-all">
            <Search className="h-5 w-5 text-slate-400 ml-4 mr-2 shrink-0" />
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
              placeholder='Ask a question (e.g. "Why are delivery complaints increasing?")'
              className="flex-1 py-3.5 bg-transparent outline-none text-slate-800 text-base placeholder:text-slate-400"
            />
            <button 
              onClick={() => handleAnalyze()}
              disabled={loading || !query.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl font-semibold transition-colors flex items-center gap-2 mr-1 shadow-sm shrink-0"
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <span>Analyze</span>
                  <Send className="h-4 w-4" />
                </>
              )}
            </button>
          </div>

          {engineReady === false && (
            <div className="bg-indigo-50 border border-indigo-200 text-indigo-700 p-4 rounded-2xl flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-3">
                <div className="h-5 w-5 border-2 border-indigo-400 border-t-indigo-700 rounded-full animate-spin shrink-0" />
                <span className="font-medium text-sm">RAG Engine is warming up: {engineProgress}</span>
              </div>
              <span className="text-xs text-indigo-500 hidden sm:block">Please wait...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-5 rounded-2xl flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!result && !loading && !error && (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4">
              <div className="w-14 h-14 bg-indigo-50 rounded-2xl flex items-center justify-center mx-auto text-indigo-600 shadow-inner">
                <Bot className="h-7 w-7" />
              </div>
              <div className="max-w-md mx-auto space-y-1">
                <h3 className="text-lg font-bold text-slate-800">Ready to Investigate</h3>
                <p className="text-sm text-slate-500">
                  Type a query above or click a conversation from your memory history to explore root causes and policy evidence.
                </p>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-300">
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Answer Main Column */}
                <div className="md:col-span-2 space-y-6">
                  {!result.grounded ? (
                    <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
                      <h3 className="text-amber-800 font-bold flex items-center gap-2 text-lg mb-2">
                        <AlertCircle /> Insufficient Evidence
                      </h3>
                      <p className="text-amber-700 text-sm">
                        RootIQ could not find sufficient supporting evidence in the available knowledge base. No unsupported answer was generated.
                      </p>
                    </div>
                  ) : (
                    <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200 space-y-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="text-xs uppercase font-bold tracking-wider text-slate-400">Query Investigation</span>
                          <h2 className="text-xl font-bold text-slate-900 mt-0.5">"{result.query}"</h2>
                        </div>
                        <span className="bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-xs font-bold tracking-wide flex items-center gap-1 shrink-0">
                          <ShieldCheck className="h-3.5 w-3.5" /> GROUNDED
                        </span>
                      </div>

                      <div className="space-y-5">
                        <div>
                          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                            Executive Summary
                          </h3>
                          <p className="text-slate-800 leading-relaxed text-[15px]">
                            {extractSummaryOnly(result.answer?.executive_summary)}
                          </p>
                        </div>

                        {result.answer?.root_causes && result.answer.root_causes.length > 0 && (
                          <div className="pt-4 border-t border-slate-100">
                            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                              Root Causes / Drivers
                            </h3>
                            <ul className="list-disc pl-5 space-y-1 text-slate-700 text-sm">
                              {result.answer.root_causes.map((c, i) => (
                                <li key={i}>{c}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div className="pt-4 border-t border-slate-100 bg-indigo-50/50 -mx-7 px-7 py-5 -mb-7 rounded-b-2xl">
                          <div className="flex items-center gap-2 mb-3">
                            <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                              Recommended Actions
                            </h3>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                              (() => {
                                const p = (result.answer?.priority || 'MEDIUM').toUpperCase();
                                if (p === 'CRITICAL') return 'bg-red-200 text-red-800 ring-1 ring-red-400';
                                if (p === 'HIGH')     return 'bg-rose-100 text-rose-700';
                                if (p === 'LOW')      return 'bg-slate-100 text-slate-500';
                                return 'bg-amber-100 text-amber-700'; // MEDIUM default
                              })()
                            }`}>
                              {result.answer?.priority || 'MEDIUM'} PRIORITY
                            </span>
                          </div>
                          <ul className="space-y-2.5 text-sm">
                            {result.answer?.recommendations?.map((r, i) => (
                              <li key={i} className="flex gap-3 text-slate-800">
                                <span className="bg-indigo-200 text-indigo-800 w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-xs font-bold">
                                  {i + 1}
                                </span>
                                <span className="pt-0.5">{r}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Right Side: Routing & Evidence */}
                <div className="space-y-6">
                  {/* Routing Card */}
                  <div className="bg-slate-900 rounded-2xl p-5 shadow-sm text-slate-300 space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                      <Database className="h-4 w-4 text-sky-400" /> Pipeline Routing
                    </h3>
                    <div>
                      <div className="text-[10px] uppercase text-slate-500 mb-0.5">Query Intent Type</div>
                      <div className="font-mono text-xs text-sky-300 bg-slate-800/80 px-2 py-1 rounded">
                        {result.query_type}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase text-slate-500 mb-1.5">Target Layers</div>
                      <div className="flex flex-wrap gap-1.5">
                        {result.target_layers?.map(layer => (
                          <span key={layer} className="bg-slate-800 text-[11px] px-2 py-0.5 rounded text-slate-300 font-mono">
                            ✓ {layer}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Evidence Cards */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 px-1">
                      Retrieved Evidence ({result.evidence?.length || 0})
                    </h3>
                    <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
                      {result.evidence?.map((ev, i) => (
                        <div key={i} className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-xs text-xs space-y-1.5">
                          <div className="flex justify-between items-start">
                            <span className="font-mono bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[10px]">
                              {ev.source_layer}
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono">
                              Score: {ev.retrieval_score ? ev.retrieval_score.toFixed(2) : '1.00'}
                            </span>
                          </div>
                          <div className="font-mono text-indigo-600 truncate text-[11px]" title={ev.document_id}>
                            {ev.document_id}
                          </div>
                          <p className="text-slate-600 italic leading-relaxed line-clamp-3">
                            "{ev.excerpt}"
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
