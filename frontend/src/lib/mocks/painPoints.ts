export type PainPointSeverity = 'critical' | 'high' | 'medium';
export type PainPointSentiment = 'positive' | 'neutral' | 'negative';

export interface PainPointQuote {
  quote: string;
  sentiment: PainPointSentiment;
  channel: string;
  segment: string;
  source: string;
}

export interface PainPointSuggestion {
  title: string;
  impact: string;
  priority: 'critical' | 'high' | 'medium';
}

export interface PainPointItem {
  id: string;
  name: string;
  category: string;
  painScore: number;
  mentionCount: number;
  percentage: number;
  growthRate: number;
  dominantSentiment: PainPointSentiment;
  severity: PainPointSeverity;
  priority: 'critical' | 'high' | 'medium';
  company: string;
  segment: string;
  resolutionRate: number;
  affectedInteractions: number;
  averageResponseTime: number;
  quotes: PainPointQuote[];
  suggestions: PainPointSuggestion[];
}

export interface RootCauseIssue {
  issue: string;
  frequency: number;
  percentage: number;
  sentiment: PainPointSentiment;
  resolutionRate: number;
  averageResponseTime: number;
  growth: number;
  businessImpact: string;
}

export const painPointCategories = ['All categories', 'Service Speed', 'Billing', 'Delivery', 'Product Quality', 'Account Access', 'Refunds', 'Technical'] as const;
export const painPointSeverities = ['All severities', 'critical', 'high', 'medium'] as const;
export const painPointSentiments = ['All sentiments', 'negative', 'neutral', 'positive'] as const;
export const painPointCompanies = ['All companies', 'Northwind Commerce', 'BluePeak', 'Aster Labs', 'Helio Retail'] as const;
export const painPointSegments = ['All segments', 'Enterprise', 'SMB', 'Consumer', 'New customer'] as const;
export const painPointDateOptions = ['7d', '30d', '90d', 'all'] as const;

export const painPoints: PainPointItem[] = [
  {
    id: 'delayed-response',
    name: 'Delayed Response',
    category: 'Service Speed',
    painScore: 92,
    mentionCount: 2140,
    percentage: 18,
    growthRate: 14.8,
    dominantSentiment: 'negative',
    severity: 'critical',
    priority: 'critical',
    company: 'Northwind Commerce',
    segment: 'Enterprise',
    resolutionRate: 63,
    affectedInteractions: 1840,
    averageResponseTime: 9.4,
    quotes: [
      { quote: 'It took three days to get an update on my issue and I still had no clear answer.', sentiment: 'negative', channel: 'X', segment: 'Enterprise', source: 'Customer tweet' },
      { quote: 'Support replies were slow and repetitive, which made the problem feel bigger than it was.', sentiment: 'negative', channel: 'Email', segment: 'Enterprise', source: 'Support follow-up' }
    ],
    suggestions: [
      { title: 'Auto-prioritize high-risk tickets', impact: 'Reduce backlog by 18%', priority: 'critical' },
      { title: 'Add proactive status updates', impact: 'Cut repeated contacts', priority: 'high' }
    ]
  },
  {
    id: 'billing-disputes',
    name: 'Billing Disputes',
    category: 'Billing',
    painScore: 89,
    mentionCount: 1830,
    percentage: 15,
    growthRate: 11.2,
    dominantSentiment: 'negative',
    severity: 'critical',
    priority: 'critical',
    company: 'BluePeak',
    segment: 'SMB',
    resolutionRate: 58,
    affectedInteractions: 1560,
    averageResponseTime: 7.8,
    quotes: [
      { quote: 'I was charged twice and the statement details were nearly impossible to understand.', sentiment: 'negative', channel: 'Chat', segment: 'SMB', source: 'Web chat' },
      { quote: 'The invoice language was confusing and I had to call twice before anyone explained it.', sentiment: 'negative', channel: 'Call', segment: 'SMB', source: 'Voice support' }
    ],
    suggestions: [
      { title: 'Simplify invoice explanations', impact: 'Lower dispute volume by 24%', priority: 'critical' },
      { title: 'Offer pre-charge alerts', impact: 'Reduce surprise billing complaints', priority: 'high' }
    ]
  },
  {
    id: 'delivery-issues',
    name: 'Delivery Issues',
    category: 'Delivery',
    painScore: 84,
    mentionCount: 1690,
    percentage: 14,
    growthRate: 9.7,
    dominantSentiment: 'negative',
    severity: 'high',
    priority: 'high',
    company: 'Helio Retail',
    segment: 'Consumer',
    resolutionRate: 72,
    affectedInteractions: 1420,
    averageResponseTime: 6.9,
    quotes: [
      { quote: 'My delivery was marked late with no status change for three days.', sentiment: 'negative', channel: 'Review', segment: 'Consumer', source: 'App review' },
      { quote: 'I still do not know where my order is, even after contacting support.', sentiment: 'negative', channel: 'Email', segment: 'Consumer', source: 'Customer email' }
    ],
    suggestions: [
      { title: 'Add shipment exception alerts', impact: 'Improve transparency', priority: 'high' },
      { title: 'Prioritize late package recovery', impact: 'Reduce repeat contacts', priority: 'medium' }
    ]
  },
  {
    id: 'product-quality',
    name: 'Product Quality',
    category: 'Product Quality',
    painScore: 80,
    mentionCount: 1520,
    percentage: 13,
    growthRate: 8.3,
    dominantSentiment: 'negative',
    severity: 'high',
    priority: 'high',
    company: 'Aster Labs',
    segment: 'Consumer',
    resolutionRate: 70,
    affectedInteractions: 1260,
    averageResponseTime: 6.1,
    quotes: [
      { quote: 'The hardware arrived damaged and there was no simple replacement path.', sentiment: 'negative', channel: 'Social', segment: 'Consumer', source: 'Instagram DM' },
      { quote: 'The product quality has fallen off and the return process feels cumbersome.', sentiment: 'negative', channel: 'Review', segment: 'Consumer', source: 'Trustpilot' }
    ],
    suggestions: [
      { title: 'Strengthen quality inspection gates', impact: 'Reduce returning defects', priority: 'high' },
      { title: 'Simplify replacement workflow', impact: 'Improve customer confidence', priority: 'medium' }
    ]
  },
  {
    id: 'account-access',
    name: 'Account Access',
    category: 'Account Access',
    painScore: 77,
    mentionCount: 1210,
    percentage: 10,
    growthRate: 7.6,
    dominantSentiment: 'negative',
    severity: 'medium',
    priority: 'medium',
    company: 'Northwind Commerce',
    segment: 'New customer',
    resolutionRate: 74,
    affectedInteractions: 980,
    averageResponseTime: 5.3,
    quotes: [
      { quote: 'I could not log in after reset and no one could explain why.', sentiment: 'negative', channel: 'Live chat', segment: 'New customer', source: 'Web chat' },
      { quote: 'The account recovery workflow felt broken and confusing.', sentiment: 'negative', channel: 'Email', segment: 'New customer', source: 'Support email' }
    ],
    suggestions: [
      { title: 'Improve account recovery self-service', impact: 'Reduce login dependency', priority: 'medium' },
      { title: 'Offer clearer recovery status messaging', impact: 'Lower support volume', priority: 'medium' }
    ]
  },
  {
    id: 'refund-delays',
    name: 'Refund Delays',
    category: 'Refunds',
    painScore: 75,
    mentionCount: 1100,
    percentage: 9,
    growthRate: 6.9,
    dominantSentiment: 'negative',
    severity: 'medium',
    priority: 'medium',
    company: 'BluePeak',
    segment: 'Consumer',
    resolutionRate: 67,
    affectedInteractions: 905,
    averageResponseTime: 6.8,
    quotes: [
      { quote: 'The refund was approved but the money still has not returned to my account.', sentiment: 'negative', channel: 'Review', segment: 'Consumer', source: 'Google review' },
      { quote: 'I am still waiting for the refund confirmation after four weeks.', sentiment: 'negative', channel: 'Email', segment: 'Consumer', source: 'Customer email' }
    ],
    suggestions: [
      { title: 'Automate refund status alerts', impact: 'Reduce follow-ups', priority: 'medium' },
      { title: 'Improve internal approval workflow', impact: 'Shorten time-to-settlement', priority: 'high' }
    ]
  },
  {
    id: 'technical-failures',
    name: 'Technical Failures',
    category: 'Technical',
    painScore: 88,
    mentionCount: 1440,
    percentage: 12,
    growthRate: 13.1,
    dominantSentiment: 'negative',
    severity: 'critical',
    priority: 'critical',
    company: 'Aster Labs',
    segment: 'Enterprise',
    resolutionRate: 65,
    affectedInteractions: 1165,
    averageResponseTime: 8.1,
    quotes: [
      { quote: 'The platform keeps failing during key workflows and nothing explains the outage.', sentiment: 'negative', channel: 'Forum', segment: 'Enterprise', source: 'Community forum' },
      { quote: 'We are losing productivity because the system is unstable during customer operations.', sentiment: 'negative', channel: 'Call', segment: 'Enterprise', source: 'Account manager' }
    ],
    suggestions: [
      { title: 'Tighten platform health alerts', impact: 'Reduce outage exposure', priority: 'critical' },
      { title: 'Prioritize reliability fixes in critical workflows', impact: 'Improve trust and retention', priority: 'critical' }
    ]
  }
];

export const rootCauseIssues: RootCauseIssue[] = [
  { issue: 'Delayed Response', frequency: 2140, percentage: 18, sentiment: 'negative', resolutionRate: 63, averageResponseTime: 9.4, growth: 14.8, businessImpact: 'High churn risk and repeated escalations' },
  { issue: 'Billing Disputes', frequency: 1830, percentage: 15, sentiment: 'negative', resolutionRate: 58, averageResponseTime: 7.8, growth: 11.2, businessImpact: 'Revenue leakage and trust erosion' },
  { issue: 'Technical Failures', frequency: 1440, percentage: 12, sentiment: 'negative', resolutionRate: 65, averageResponseTime: 8.1, growth: 13.1, businessImpact: 'Operational interruption and SLA risk' },
  { issue: 'Delivery Issues', frequency: 1690, percentage: 14, sentiment: 'negative', resolutionRate: 72, averageResponseTime: 6.9, growth: 9.7, businessImpact: 'Strong warranty and service recovery burden' },
  { issue: 'Product Quality', frequency: 1520, percentage: 13, sentiment: 'negative', resolutionRate: 70, averageResponseTime: 6.1, growth: 8.3, businessImpact: 'Returns, refunds, and brand damage' }
];
