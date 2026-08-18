// ============================================================
// Resolve-AI API Client
// Connects the React frontend to the FastAPI backend (server.py)
// All endpoints served at http://localhost:8000
// ============================================================

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request<T>(path: string, options?: RequestInit): Promise<{ ok: boolean; data: T | null; error?: string }> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) {
      const err = await res.text();
      return { ok: false, data: null, error: err };
    }
    const data = await res.json();
    return { ok: true, data };
  } catch (e: any) {
    return { ok: false, data: null, error: e?.message ?? "Network error" };
  }
}

export const api = {
  /**
   * GET /api/dashboard
   * Returns the full metrics_summary.json:
   * total_conversations, response_rate, avg_first_response_hours,
   * fcr_rate, escalation_rate, reopen_rate, csat_proxy_score,
   * negative_sentiment_rate, avg_sentiment, high_severity_rate,
   * active_spikes, ai_confidence, category_breakdown, emerging_issues, etc.
   */
  getDashboardKpis: async () => request<Record<string, any>>("/api/dashboard"),

  /**
   * GET /api/dashboard  (same endpoint — full analytics snapshot)
   * Used by analytics summary panels.
   */
  getAnalyticsSummary: async () => request<Record<string, any>>("/api/dashboard"),

  /**
   * GET /api/pain-points
   * Returns { clusters: [...], total: N }
   * Each cluster: { label, size, pain_score, keywords, top_issues, avg_sentiment }
   */
  getPainPoints: async () => request<{ clusters: any[]; total: number }>("/api/pain-points"),

  /**
   * GET /api/pain-points  (top clusters ranked by pain_score = recommendations)
   */
  getRecommendations: async () => request<{ clusters: any[]; total: number }>("/api/pain-points"),

  /**
   * GET /api/dashboard  (voice of customer uses category_breakdown + emerging_issues)
   */
  getVoiceOfCustomer: async () => request<Record<string, any>>("/api/dashboard"),

  /**
   * POST /api/chat
   * Body: { query: string }
   * Returns: { response: string }  — grounded LLM insight from stage 17
   */
  analyzeConversation: async (query: string) =>
    request<{ response: string }>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),

  /**
   * POST /api/chat  (same endpoint — used from chat UI)
   * Body: { query: string }
   * Returns: { response: string }
   */
  sendChat: async (query: string) =>
    request<{ response: string }>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),

  /**
   * GET /api/reports/date-range?start=YYYY-MM-DD&end=YYYY-MM-DD
   * Returns a dynamically computed warehouse report:
   * { date_range, total_volume, response_rate, escalation_rate, avg_csat, avg_sentiment, top_intents }
   */
  getDateRangeReport: async (start: string, end: string) =>
    request<Record<string, any>>(`/api/reports/date-range?start=${start}&end=${end}`),

  /**
   * GET /api/chat/history
   * Returns: { conversations: [...], total: N }
   */
  getChatHistory: async (limit: number = 50) =>
    request<{ conversations: any[]; total: number }>(`/api/chat/history?limit=${limit}`),


  /**
   * DELETE /api/chat/history
   */
  clearChatHistory: async () =>
    request<{ status: string }>("/api/chat/history", { method: "DELETE" }),
};

export type ApiClient = typeof api;
