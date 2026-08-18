/**
 * spikesService.ts
 * Fetches real category spike data from /api/analytics/spikes-by-category.
 * All dates come from the actual TWCS dataset (2011-2017 historical data).
 * NO mock or fabricated data.
 */

export type WeeklyPoint = {
  date: string;          // actual date from dataset, e.g. "2017-10-31"
  complaint_count: number;
  is_spike: boolean;
};

export type CategoryData = {
  category: string;       // raw category key, e.g. "technical_support"
  display_name: string;   // human readable, e.g. "Technical Support"
  total_complaints: number;
  has_spike: boolean;
  points: WeeklyPoint[];
};

export type SpikeResponse = {
  categories: CategoryData[];
  date_start: string | null;
  date_end: string | null;
  observation_days: number;
  date_note: string;
  data_source: string;
};

export async function fetchWeeklySpikeData(): Promise<CategoryData[]> {
  const res = await fetch('/api/analytics/spikes-by-category');
  if (!res.ok) {
    throw new Error(`spikes-by-category failed: HTTP ${res.status}`);
  }
  const data: SpikeResponse = await res.json();
  return data.categories;
}

export async function fetchSpikeMetadata(): Promise<Omit<SpikeResponse, 'categories'>> {
  const res = await fetch('/api/analytics/spikes-by-category');
  if (!res.ok) {
    throw new Error(`spikes-by-category failed: HTTP ${res.status}`);
  }
  const data: SpikeResponse = await res.json();
  const { categories: _cats, ...meta } = data;
  return meta;
}
