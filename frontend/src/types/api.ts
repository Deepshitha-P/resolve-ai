export type ApiStatus = 'idle' | 'loading' | 'success' | 'error';

export interface DashboardKpi {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  tone: 'success' | 'warning' | 'primary';
}

export interface CategoryBreakdownItem {
  name: string;
  value: number;
  percentage: number;
}

export interface PainPointItem {
  id: string;
  rank: number;
  name: string;
  category: string;
  painScore: number;
  volume: number;
  escalationRate: number;
  summary: string;
  sentiment: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

export interface RecommendationItem {
  id: string;
  title: string;
  category: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  impact: string;
  confidence: number;
  description: string;
  timeline: string;
}

export interface VoiceOfCustomerTheme {
  id: string;
  theme: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  frequency: number;
  percentage: number;
  quotes: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}
