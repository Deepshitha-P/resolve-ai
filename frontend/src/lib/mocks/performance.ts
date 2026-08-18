export type PerformanceTone = 'success' | 'warning' | 'primary';

export interface PerformanceKpi {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  tone: PerformanceTone;
}

export interface ResponseTrendPoint {
  date: string;
  responseTime: number;
  resolutionRate: number;
  satisfaction: number;
}

export interface PerformanceByIntent {
  intent: string;
  avgResponseTime: number;
  resolutionRate: number;
  satisfaction: number;
  escalationRate: number;
  repeatContactRate: number;
  attention: boolean;
}

export interface CompanyPerformanceMetric {
  company: string;
  avgResponseTime: number;
  resolutionRate: number;
  satisfaction: number;
  escalationRate: number;
  repeatContactRate: number;
}

export const performanceKpis: PerformanceKpi[] = [
  { label: 'Average response time', value: '4.7 min', change: '-0.8 min vs last week', trend: 'down', tone: 'success' },
  { label: 'Resolution rate', value: '83.2%', change: '+2.6% vs last week', trend: 'up', tone: 'success' },
  { label: 'Customer satisfaction', value: '84.6/100', change: '+1.7 pts', trend: 'up', tone: 'primary' },
  { label: 'Escalation rate', value: '11.9%', change: '+0.6 pts', trend: 'down', tone: 'warning' }
];

export const responseTrendData: ResponseTrendPoint[] = [
  { date: 'Apr 01', responseTime: 6.4, resolutionRate: 76, satisfaction: 80 },
  { date: 'Apr 04', responseTime: 6.1, resolutionRate: 77, satisfaction: 81 },
  { date: 'Apr 08', responseTime: 5.8, resolutionRate: 79, satisfaction: 82 },
  { date: 'Apr 12', responseTime: 5.6, resolutionRate: 80, satisfaction: 83 },
  { date: 'Apr 16', responseTime: 5.4, resolutionRate: 81, satisfaction: 83 },
  { date: 'Apr 20', responseTime: 5.1, resolutionRate: 82, satisfaction: 84 },
  { date: 'Apr 24', responseTime: 4.9, resolutionRate: 83, satisfaction: 85 },
  { date: 'Apr 28', responseTime: 4.7, resolutionRate: 84, satisfaction: 86 },
  { date: 'May 02', responseTime: 4.8, resolutionRate: 84, satisfaction: 85 },
  { date: 'May 06', responseTime: 4.6, resolutionRate: 85, satisfaction: 86 },
  { date: 'May 10', responseTime: 4.4, resolutionRate: 86, satisfaction: 87 },
  { date: 'May 14', responseTime: 4.2, resolutionRate: 88, satisfaction: 88 }
];

export const performanceByIntent: PerformanceByIntent[] = [
  { intent: 'Billing', avgResponseTime: 8.6, resolutionRate: 64, satisfaction: 71, escalationRate: 18, repeatContactRate: 24, attention: true },
  { intent: 'Technical Support', avgResponseTime: 7.4, resolutionRate: 79, satisfaction: 76, escalationRate: 15, repeatContactRate: 18, attention: true },
  { intent: 'Complaint', avgResponseTime: 6.9, resolutionRate: 71, satisfaction: 73, escalationRate: 16, repeatContactRate: 21, attention: true },
  { intent: 'Shipping', avgResponseTime: 6.2, resolutionRate: 76, satisfaction: 78, escalationRate: 12, repeatContactRate: 17, attention: false },
  { intent: 'Refund Request', avgResponseTime: 7.1, resolutionRate: 68, satisfaction: 69, escalationRate: 17, repeatContactRate: 22, attention: true },
  { intent: 'Product Quality', avgResponseTime: 5.9, resolutionRate: 74, satisfaction: 77, escalationRate: 11, repeatContactRate: 15, attention: false }
];

export const companyPerformanceMetrics: CompanyPerformanceMetric[] = [
  { company: 'Northwind Commerce', avgResponseTime: 4.0, resolutionRate: 88, satisfaction: 88, escalationRate: 9, repeatContactRate: 12 },
  { company: 'BluePeak', avgResponseTime: 5.4, resolutionRate: 81, satisfaction: 82, escalationRate: 12, repeatContactRate: 16 },
  { company: 'Aster Labs', avgResponseTime: 5.8, resolutionRate: 78, satisfaction: 80, escalationRate: 14, repeatContactRate: 19 },
  { company: 'Helio Retail', avgResponseTime: 4.8, resolutionRate: 84, satisfaction: 84, escalationRate: 11, repeatContactRate: 15 }
];
