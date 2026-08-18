export type SentimentTone = 'Positive' | 'Neutral' | 'Negative';

export interface SentimentTrendPoint {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
  score: number;
}

export interface SentimentSegmentBreakdown {
  segment: string;
  positive: number;
  neutral: number;
  negative: number;
  score: number;
}

export interface SentimentCompanyBreakdown {
  company: string;
  positive: number;
  neutral: number;
  negative: number;
  score: number;
}

export const sentimentDateOptions = ['7d', '30d', '90d', 'all'] as const;
export const sentimentSegmentOptions = ['All segments', 'Enterprise', 'SMB', 'Consumer', 'New customer'] as const;
export const sentimentCompanyOptions = ['All companies', 'Northwind Commerce', 'BluePeak', 'Aster Labs', 'Helio Retail'] as const;

export const overallSentiment = {
  positive: 52,
  neutral: 28,
  negative: 20,
  averageScore: 74.8
};

export const sentimentTrendData: SentimentTrendPoint[] = [
  { date: 'Apr 01', positive: 56, neutral: 28, negative: 16, score: 74.8 },
  { date: 'Apr 04', positive: 53, neutral: 30, negative: 17, score: 73.4 },
  { date: 'Apr 08', positive: 51, neutral: 31, negative: 18, score: 72.1 },
  { date: 'Apr 12', positive: 49, neutral: 29, negative: 22, score: 70.2 },
  { date: 'Apr 16', positive: 48, neutral: 30, negative: 22, score: 69.8 },
  { date: 'Apr 20', positive: 50, neutral: 29, negative: 21, score: 71.6 },
  { date: 'Apr 24', positive: 54, neutral: 27, negative: 19, score: 73.9 },
  { date: 'Apr 28', positive: 57, neutral: 24, negative: 19, score: 75.1 },
  { date: 'May 02', positive: 55, neutral: 26, negative: 19, score: 74.4 },
  { date: 'May 06', positive: 58, neutral: 25, negative: 17, score: 76.3 },
  { date: 'May 10', positive: 60, neutral: 22, negative: 18, score: 77.9 },
  { date: 'May 14', positive: 62, neutral: 21, negative: 17, score: 79.1 }
];

export const sentimentBySegment: SentimentSegmentBreakdown[] = [
  { segment: 'Enterprise', positive: 46, neutral: 31, negative: 23, score: 69.7 },
  { segment: 'SMB', positive: 54, neutral: 28, negative: 18, score: 75.4 },
  { segment: 'Consumer', positive: 59, neutral: 24, negative: 17, score: 79.8 },
  { segment: 'New customer', positive: 38, neutral: 33, negative: 29, score: 62.1 }
];

export const sentimentByCompany: SentimentCompanyBreakdown[] = [
  { company: 'Northwind Commerce', positive: 58, neutral: 27, negative: 15, score: 79.6 },
  { company: 'BluePeak', positive: 49, neutral: 31, negative: 20, score: 71.8 },
  { company: 'Aster Labs', positive: 45, neutral: 33, negative: 22, score: 68.2 },
  { company: 'Helio Retail', positive: 53, neutral: 28, negative: 19, score: 74.7 }
];
