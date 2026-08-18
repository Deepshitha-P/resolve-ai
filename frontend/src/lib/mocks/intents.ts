export type IntentSentiment = 'positive' | 'neutral' | 'negative';

export interface IntentRecord {
  intent: string;
  volume: number;
  percentage: number;
  trend: number;
  dominantSentiment: IntentSentiment;
  resolutionRate: number;
  company: string;
  segment: string;
  dateRange: '7d' | '30d' | '90d' | 'all';
}

export interface IntentTrendPoint {
  date: string;
  'Technical Support': number;
  Billing: number;
  Complaint: number;
  'Order Status': number;
  Feedback: number;
  'Refund Request': number;
  'Product Quality': number;
  Shipping: number;
  'Account Issue': number;
  'Feature Request': number;
}

export const intentOptions = [
  'All intents',
  'Technical Support',
  'Billing',
  'Complaint',
  'Order Status',
  'Feedback',
  'Refund Request',
  'Product Quality',
  'Shipping',
  'Account Issue',
  'Feature Request'
] as const;

export const intentCompanyOptions = ['All companies', 'Northwind Commerce', 'BluePeak', 'Aster Labs', 'Helio Retail'] as const;
export const intentSegmentOptions = ['All segments', 'Enterprise', 'SMB', 'Consumer', 'New customer'] as const;
export const intentDateOptions = ['7d', '30d', '90d', 'all'] as const;

export const intentRecords: IntentRecord[] = [
  { intent: 'Technical Support', volume: 1480, percentage: 32, trend: 12.2, dominantSentiment: 'negative', resolutionRate: 82, company: 'Northwind Commerce', segment: 'Enterprise', dateRange: '30d' },
  { intent: 'Billing', volume: 1220, percentage: 26, trend: 8.7, dominantSentiment: 'negative', resolutionRate: 68, company: 'BluePeak', segment: 'SMB', dateRange: '30d' },
  { intent: 'Complaint', volume: 980, percentage: 21, trend: 5.1, dominantSentiment: 'negative', resolutionRate: 71, company: 'Aster Labs', segment: 'Consumer', dateRange: '30d' },
  { intent: 'Order Status', volume: 760, percentage: 17, trend: -2.4, dominantSentiment: 'neutral', resolutionRate: 86, company: 'Helio Retail', segment: 'Consumer', dateRange: '30d' },
  { intent: 'Feedback', volume: 640, percentage: 14, trend: 6.8, dominantSentiment: 'positive', resolutionRate: 79, company: 'Northwind Commerce', segment: 'Consumer', dateRange: '30d' },
  { intent: 'Refund Request', volume: 610, percentage: 13, trend: 9.4, dominantSentiment: 'negative', resolutionRate: 63, company: 'BluePeak', segment: 'New customer', dateRange: '30d' },
  { intent: 'Product Quality', volume: 720, percentage: 16, trend: 7.3, dominantSentiment: 'negative', resolutionRate: 74, company: 'Aster Labs', segment: 'SMB', dateRange: '30d' },
  { intent: 'Shipping', volume: 860, percentage: 18, trend: 10.8, dominantSentiment: 'negative', resolutionRate: 75, company: 'Helio Retail', segment: 'Enterprise', dateRange: '30d' },
  { intent: 'Account Issue', volume: 420, percentage: 9, trend: 3.1, dominantSentiment: 'neutral', resolutionRate: 80, company: 'Northwind Commerce', segment: 'Enterprise', dateRange: '30d' },
  { intent: 'Feature Request', volume: 390, percentage: 8, trend: 4.9, dominantSentiment: 'positive', resolutionRate: 88, company: 'BluePeak', segment: 'SMB', dateRange: '30d' },
  { intent: 'Technical Support', volume: 690, percentage: 31, trend: 9.8, dominantSentiment: 'negative', resolutionRate: 81, company: 'Northwind Commerce', segment: 'New customer', dateRange: '7d' },
  { intent: 'Billing', volume: 560, percentage: 24, trend: 11.5, dominantSentiment: 'negative', resolutionRate: 66, company: 'BluePeak', segment: 'SMB', dateRange: '7d' }
];

export const intentTrendData: IntentTrendPoint[] = [
  { date: 'Apr 01', 'Technical Support': 84, Billing: 71, Complaint: 54, 'Order Status': 48, Feedback: 39, 'Refund Request': 35, 'Product Quality': 41, Shipping: 58, 'Account Issue': 24, 'Feature Request': 22 },
  { date: 'Apr 04', 'Technical Support': 88, Billing: 69, Complaint: 57, 'Order Status': 50, Feedback: 42, 'Refund Request': 39, 'Product Quality': 45, Shipping: 62, 'Account Issue': 26, 'Feature Request': 24 },
  { date: 'Apr 08', 'Technical Support': 92, Billing: 75, Complaint: 60, 'Order Status': 54, Feedback: 44, 'Refund Request': 42, 'Product Quality': 47, Shipping: 65, 'Account Issue': 28, 'Feature Request': 29 },
  { date: 'Apr 12', 'Technical Support': 95, Billing: 80, Complaint: 64, 'Order Status': 57, Feedback: 48, 'Refund Request': 46, 'Product Quality': 53, Shipping: 68, 'Account Issue': 29, 'Feature Request': 30 },
  { date: 'Apr 16', 'Technical Support': 97, Billing: 82, Complaint: 66, 'Order Status': 60, Feedback: 50, 'Refund Request': 47, 'Product Quality': 55, Shipping: 74, 'Account Issue': 31, 'Feature Request': 32 },
  { date: 'Apr 20', 'Technical Support': 101, Billing: 78, Complaint: 62, 'Order Status': 58, Feedback: 54, 'Refund Request': 49, 'Product Quality': 57, Shipping: 76, 'Account Issue': 34, 'Feature Request': 36 },
  { date: 'Apr 24', 'Technical Support': 108, Billing: 83, Complaint: 68, 'Order Status': 61, Feedback: 57, 'Refund Request': 53, 'Product Quality': 60, Shipping: 80, 'Account Issue': 38, 'Feature Request': 38 },
  { date: 'Apr 28', 'Technical Support': 112, Billing: 89, Complaint: 71, 'Order Status': 63, Feedback: 58, 'Refund Request': 55, 'Product Quality': 62, Shipping: 84, 'Account Issue': 41, 'Feature Request': 39 },
  { date: 'May 02', 'Technical Support': 116, Billing: 86, Complaint: 69, 'Order Status': 62, Feedback: 61, 'Refund Request': 57, 'Product Quality': 65, Shipping: 83, 'Account Issue': 43, 'Feature Request': 41 },
  { date: 'May 07', 'Technical Support': 120, Billing: 90, Complaint: 73, 'Order Status': 66, Feedback: 63, 'Refund Request': 58, 'Product Quality': 68, Shipping: 85, 'Account Issue': 45, 'Feature Request': 42 },
  { date: 'May 10', 'Technical Support': 124, Billing: 94, Complaint: 75, 'Order Status': 68, Feedback: 66, 'Refund Request': 62, 'Product Quality': 70, Shipping: 87, 'Account Issue': 46, 'Feature Request': 45 },
  { date: 'May 14', 'Technical Support': 129, Billing: 99, Complaint: 79, 'Order Status': 72, Feedback: 68, 'Refund Request': 65, 'Product Quality': 73, Shipping: 90, 'Account Issue': 48, 'Feature Request': 47 }
];
