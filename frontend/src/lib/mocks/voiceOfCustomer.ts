export type VocSentiment = 'positive' | 'neutral' | 'negative';

export interface VocTheme {
  id: string;
  name: string;
  frequency: number;
  percentage: number;
  sentiment: VocSentiment;
  trend: number;
  affectedSegment: string;
  impact: string;
  recommendedAction: string;
  priority: 'critical' | 'high' | 'medium';
  confidence: number;
}

export interface VocQuote {
  quote: string;
  sentiment: VocSentiment;
  theme: string;
  segment: string;
  source: string;
  date: string;
}

export interface PositiveHighlight {
  title: string;
  frequency: number;
  quote: string;
  theme: string;
}

export interface SegmentImpact {
  segment: string;
  serviceSpeed: number;
  productReliability: number;
  pricing: number;
  supportQuality: number;
  deliveryExperience: number;
}

export interface PainPointSummaryItem {
  frustration: string;
  affectedSegments: string[];
  sentiment: VocSentiment;
  frequency: number;
  businessImpact: string;
}

export const vocThemes: VocTheme[] = [
  { id: 'service-speed', name: 'Service Speed', frequency: 2280, percentage: 26, sentiment: 'negative', trend: 12.5, affectedSegment: 'Enterprise', impact: 'High urgency and repeat contacts', recommendedAction: 'Streamline triage and reduce SLA breaches', priority: 'critical', confidence: 91 },
  { id: 'product-reliability', name: 'Product Reliability', frequency: 1920, percentage: 21, sentiment: 'negative', trend: 9.6, affectedSegment: 'Consumer', impact: 'Frequent quality and defect complaints', recommendedAction: 'Improve issue detection and warranty flow', priority: 'high', confidence: 88 },
  { id: 'pricing', name: 'Pricing', frequency: 1710, percentage: 18, sentiment: 'negative', trend: 7.4, affectedSegment: 'SMB', impact: 'Confusion around discounts and charges', recommendedAction: 'Clarify invoice messaging and cost transparency', priority: 'high', confidence: 86 },
  { id: 'support-quality', name: 'Support Quality', frequency: 1470, percentage: 16, sentiment: 'positive', trend: 5.8, affectedSegment: 'Consumer', impact: 'Positive reinforcement when support is helpful', recommendedAction: 'Scale best-practice agent playbooks', priority: 'medium', confidence: 79 },
  { id: 'delivery-experience', name: 'Delivery Experience', frequency: 1290, percentage: 14, sentiment: 'negative', trend: 6.9, affectedSegment: 'Consumer', impact: 'Late shipments and poor status visibility', recommendedAction: 'Heighten proactive tracking and exception alerts', priority: 'high', confidence: 84 },
  { id: 'account-experience', name: 'Account Experience', frequency: 980, percentage: 11, sentiment: 'neutral', trend: 4.1, affectedSegment: 'New customer', impact: 'Login friction and onboarding confusion', recommendedAction: 'Simplify identity recovery and setup steps', priority: 'medium', confidence: 75 }
];

export const emotionalWords = [
  { word: 'frustrated', weight: 96 },
  { word: 'helpful', weight: 84 },
  { word: 'delayed', weight: 90 },
  { word: 'satisfied', weight: 78 },
  { word: 'confusing', weight: 87 },
  { word: 'reliable', weight: 72 },
  { word: 'disappointed', weight: 91 },
  { word: 'excellent', weight: 70 }
];

export const overallSentiment = {
  positive: 51,
  neutral: 28,
  negative: 21,
  score: 74.5,
  change: 4.2,
  trend: 'up'
};

export const vocQuotes: VocQuote[] = [
  { quote: 'Support was quick to answer and genuinely helpful when I explained the issue.', sentiment: 'positive', theme: 'Support Quality', segment: 'Consumer', source: 'X', date: 'May 13' },
  { quote: 'The platform is reliable most of the time, but outages during payment steps are a major pain point.', sentiment: 'neutral', theme: 'Product Reliability', segment: 'Enterprise', source: 'Email', date: 'May 11' },
  { quote: 'I was frustrated by the delayed shipment update and had no idea where my order was.', sentiment: 'negative', theme: 'Delivery Experience', segment: 'Consumer', source: 'Review', date: 'May 10' },
  { quote: 'Billing charges were confusing and made the purchase feel deceptive.', sentiment: 'negative', theme: 'Pricing', segment: 'SMB', source: 'Chat', date: 'May 08' },
  { quote: 'The account recovery steps were confusing and I still had to contact support.', sentiment: 'negative', theme: 'Account Experience', segment: 'New customer', source: 'Email', date: 'May 06' },
  { quote: 'The support team was patient and solved my issue in a single conversation.', sentiment: 'positive', theme: 'Support Quality', segment: 'Consumer', source: 'Call', date: 'May 02' }
];

export const positiveHighlights: PositiveHighlight[] = [
  { title: 'Helpful support interactions', frequency: 1280, quote: 'The support team was patient and solved my issue in a single conversation.', theme: 'Support Quality' },
  { title: 'Reliable product moments', frequency: 940, quote: 'The product works smoothly when everything is stable and the experience feels dependable.', theme: 'Product Reliability' },
  { title: 'Strong handoff experience', frequency: 870, quote: 'I loved how quickly the issue was escalated and explained to me.', theme: 'Service Speed' }
];

export const painPointSummary: PainPointSummaryItem[] = [
  { frustration: 'Delayed responses and lack of proactive communication', affectedSegments: ['Enterprise', 'Consumer'], sentiment: 'negative', frequency: 2140, businessImpact: 'High repeated-contact pressure and delayed recovery' },
  { frustration: 'Billing confusion and unclear charges', affectedSegments: ['SMB', 'Consumer'], sentiment: 'negative', frequency: 1830, businessImpact: 'Trust erosion and revenue leakage' },
  { frustration: 'Late deliveries and weak status updates', affectedSegments: ['Consumer', 'SMB'], sentiment: 'negative', frequency: 1690, businessImpact: 'Increased refunds and lower post-purchase loyalty' }
];

export const segmentImpact: SegmentImpact[] = [
  { segment: 'Enterprise', serviceSpeed: 82, productReliability: 76, pricing: 48, supportQuality: 68, deliveryExperience: 56 },
  { segment: 'SMB', serviceSpeed: 70, productReliability: 62, pricing: 81, supportQuality: 64, deliveryExperience: 54 },
  { segment: 'Consumer', serviceSpeed: 73, productReliability: 79, pricing: 58, supportQuality: 76, deliveryExperience: 88 },
  { segment: 'New customer', serviceSpeed: 65, productReliability: 60, pricing: 72, supportQuality: 69, deliveryExperience: 57 }
];

export interface VocRecommendation {
  theme: string;
  action: string;
  priority: 'critical' | 'high' | 'medium';
  impact: string;
  confidence: number;
}

export const vocRecommendations: VocRecommendation[] = [
  { theme: 'Service Speed', action: 'Improve triage and SLA tracking for high-risk conversations', priority: 'critical', impact: 'Better first response time and fewer escalations', confidence: 92 },
  { theme: 'Pricing', action: 'Clarify invoices and add up-front cost warnings', priority: 'high', impact: 'Reduce pricing-related confusion and repeat contacts', confidence: 88 },
  { theme: 'Delivery Experience', action: 'Add proactive shipment exception messaging', priority: 'high', impact: 'Lower post-purchase friction and dissatisfaction', confidence: 85 }
];
