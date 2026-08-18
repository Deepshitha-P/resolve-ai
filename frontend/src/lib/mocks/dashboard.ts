import type { CategoryBreakdownItem, DashboardKpi, PainPointItem, RecommendationItem, VoiceOfCustomerTheme } from '../../types/api';

export const dashboardKpis: DashboardKpi[] = [
  {
    label: 'FCR Rate',
    value: '89.4%',
    change: '+2.4% vs last week',
    trend: 'up',
    tone: 'success'
  },
  {
    label: 'Escalation Rate',
    value: '12.1%',
    change: '-1.1% vs last week',
    trend: 'down',
    tone: 'warning'
  },
  {
    label: 'CSAT Proxy',
    value: '84.6/100',
    change: 'Stable',
    trend: 'neutral',
    tone: 'primary'
  }
];

export const sentimentOverview: Array<{
  name: 'Positive' | 'Neutral' | 'Negative';
  value: number;
  color: string;
}> = [
  { name: 'Positive', value: 42, color: '#34d399' },
  { name: 'Neutral', value: 31, color: '#60a5fa' },
  { name: 'Negative', value: 27, color: '#f87171' }
];

export const sentimentTrendData = [
  { date: 'May 1', positive: 48, neutral: 30, negative: 22 },
  { date: 'May 2', positive: 52, neutral: 25, negative: 23 },
  { date: 'May 3', positive: 46, neutral: 33, negative: 21 },
  { date: 'May 4', positive: 54, neutral: 27, negative: 19 },
  { date: 'May 5', positive: 58, neutral: 24, negative: 18 },
  { date: 'May 6', positive: 55, neutral: 28, negative: 17 },
  { date: 'May 7', positive: 50, neutral: 30, negative: 20 },
  { date: 'May 8', positive: 49, neutral: 32, negative: 19 },
  { date: 'May 9', positive: 53, neutral: 29, negative: 18 },
  { date: 'May 10', positive: 57, neutral: 25, negative: 18 },
  { date: 'May 11', positive: 60, neutral: 22, negative: 18 },
  { date: 'May 12', positive: 59, neutral: 24, negative: 17 },
  { date: 'May 13', positive: 56, neutral: 26, negative: 18 },
  { date: 'May 14', positive: 62, neutral: 21, negative: 17 }
];

export const intentRanking: Array<{
  name: string;
  value: number;
  percentage: number;
  trend: 'up' | 'down' | 'neutral';
  sentiment: 'positive' | 'neutral' | 'negative';
}> = [
  { name: 'Issue resolution', value: 1840, percentage: 34, trend: 'up', sentiment: 'positive' },
  { name: 'Billing clarity', value: 1430, percentage: 26, trend: 'neutral', sentiment: 'neutral' },
  { name: 'Delivery updates', value: 1180, percentage: 21, trend: 'down', sentiment: 'negative' },
  { name: 'App performance', value: 970, percentage: 19, trend: 'up', sentiment: 'positive' }
];

export const executiveInsights = [
  {
    title: 'Support quality is improving',
    detail: 'First-contact resolution is trending upward as agents resolve more complex billing concerns before escalation.',
    priority: 'high'
  },
  {
    title: 'Billing friction still spikes at checkout',
    detail: 'A persistent 21% share of complaint volume is tied to price confusion and unexpected charges.',
    priority: 'critical'
  },
  {
    title: 'Shipping communications remain noisy',
    detail: 'Customer sentiment recovers when proactive order updates are sent within 24 hours of dispatch.',
    priority: 'medium'
  }
];

export const dataSourceStatus = [
  { name: 'CRM ticket feed', status: 'Healthy', freshness: '4 min ago', records: '1.28M', confidence: 96 },
  { name: 'App telemetry', status: 'Monitoring', freshness: '9 min ago', records: '620K', confidence: 93 },
  { name: 'Support transcripts', status: 'Healthy', freshness: '2 min ago', records: '340K', confidence: 97 },
  { name: 'Shipping events', status: 'Watchlist', freshness: '18 min ago', records: '190K', confidence: 88 }
];

export const categoryBreakdown: CategoryBreakdownItem[] = [
  { name: 'Network reliability', value: 318, percentage: 42 },
  { name: 'Billing confusion', value: 214, percentage: 31 },
  { name: 'App stability', value: 161, percentage: 24 },
  { name: 'Shipping updates', value: 138, percentage: 18 },
  { name: 'Refund delays', value: 95, percentage: 12 }
];

export const painPoints: PainPointItem[] = [
  {
    id: 'pp-1',
    rank: 1,
    name: 'Network outages in metro regions',
    category: 'technical_support',
    painScore: 92,
    volume: 4210,
    escalationRate: 0.18,
    summary: 'Persistent service instability and missed connectivity windows are driving the highest customer dissatisfaction.',
    sentiment: {
      positive: 8,
      neutral: 24,
      negative: 68
    }
  },
  {
    id: 'pp-2',
    rank: 2,
    name: 'Unexpected billing charges',
    category: 'billing',
    painScore: 81,
    volume: 3240,
    escalationRate: 0.14,
    summary: 'Billing confusion and unclear fee changes are increasing complaint volume and trust issues.',
    sentiment: {
      positive: 10,
      neutral: 27,
      negative: 63
    }
  },
  {
    id: 'pp-3',
    rank: 3,
    name: 'App crashes during checkout',
    category: 'product_quality',
    painScore: 74,
    volume: 2470,
    escalationRate: 0.12,
    summary: 'Checkout instability is blocking purchases and pushing customers toward competitor channels.',
    sentiment: {
      positive: 9,
      neutral: 30,
      negative: 61
    }
  }
];

export const recommendations: RecommendationItem[] = [
  {
    id: 'rec-1',
    title: 'Improve mobile app stability',
    category: 'product',
    priority: 'critical',
    impact: 'High',
    confidence: 94,
    description: 'Checkout and login crashes are the single biggest source of friction for new and returning customers.',
    timeline: '2ΓÇô4 weeks'
  },
  {
    id: 'rec-2',
    title: 'Clarify billing statement language',
    category: 'operations',
    priority: 'high',
    impact: 'High',
    confidence: 88,
    description: 'Simplify fee definitions and warn customers earlier to reduce avoidable disputes and repeat contacts.',
    timeline: '1ΓÇô2 weeks'
  },
  {
    id: 'rec-3',
    title: 'Reduce response latency in network incidents',
    category: 'support',
    priority: 'medium',
    impact: 'Medium',
    confidence: 81,
    description: 'Priority routing should tighten for network-related complaints where severe impact compounds quickly.',
    timeline: '3ΓÇô6 weeks'
  }
];

export const voiceOfCustomerThemes: VoiceOfCustomerTheme[] = [
  {
    id: 'voc-1',
    theme: 'Product quality concerns',
    sentiment: 'negative',
    frequency: 4210,
    percentage: 26,
    quotes: ['Item arrived damaged', 'The product quality has really gone downhill']
  },
  {
    id: 'voc-2',
    theme: 'Slow support response',
    sentiment: 'negative',
    frequency: 3450,
    percentage: 21,
    quotes: ['Took too long to get help', 'I had to contact support multiple times']
  },
  {
    id: 'voc-3',
    theme: 'Helpful and friendly support',
    sentiment: 'positive',
    frequency: 1450,
    percentage: 12,
    quotes: ['Support was patient and helpful', 'The team resolved my issue quickly']
  }
];
