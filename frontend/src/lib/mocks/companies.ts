export interface CompanyBenchmarkRow {
  company: string;
  resolutionRate: number;
  customerSatisfaction: number;
  averageResponseTime: number;
  escalationRate: number;
  negativeSentiment: number;
  repeatContact: number;
}

export const companyBenchmarkRows: CompanyBenchmarkRow[] = [
  { company: 'Northwind Commerce', resolutionRate: 88, customerSatisfaction: 88, averageResponseTime: 4.1, escalationRate: 9, negativeSentiment: 15, repeatContact: 12 },
  { company: 'Helio Retail', resolutionRate: 84, customerSatisfaction: 84, averageResponseTime: 4.8, escalationRate: 11, negativeSentiment: 19, repeatContact: 15 },
  { company: 'BluePeak', resolutionRate: 81, customerSatisfaction: 82, averageResponseTime: 5.4, escalationRate: 12, negativeSentiment: 20, repeatContact: 16 },
  { company: 'Aster Labs', resolutionRate: 78, customerSatisfaction: 80, averageResponseTime: 5.8, escalationRate: 14, negativeSentiment: 22, repeatContact: 19 }
];

export const benchmarkComparison = [
  { company: 'Northwind Commerce', resolutionRate: 88, satisfaction: 88, responseTime: 4.1, escalationRate: 9 },
  { company: 'Helio Retail', resolutionRate: 84, satisfaction: 84, responseTime: 4.8, escalationRate: 11 },
  { company: 'BluePeak', resolutionRate: 81, satisfaction: 82, responseTime: 5.4, escalationRate: 12 },
  { company: 'Aster Labs', resolutionRate: 78, satisfaction: 80, responseTime: 5.8, escalationRate: 14 }
];

export const companyOptions = ['All companies', 'Northwind Commerce', 'Helio Retail', 'BluePeak', 'Aster Labs'] as const;
