export type Search = {
  id: number;
  query: string;
  brand: string | null;
  size: string | null;
  max_price: number | null;
  discount_threshold_percent: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Listing = {
  id: number;
  search_id: number;
  vinted_item_id: string;
  title: string;
  price: number;
  currency: string;
  condition: string | null;
  url: string;
  image_url: string | null;
  first_seen_at: string;
  last_seen_at: string;
};

export type Deal = {
  id: number;
  listing_id: number;
  vinted_price: number;
  benchmark_price: number;
  discount_percent: number;
  match_confidence: number;
  is_notified: boolean;
  created_at: string;
  listing?: Listing;
};

export type JobRun = {
  id: number;
  job_name: string;
  status: string;
  details: string | null;
  started_at: string;
  finished_at: string | null;
};

export type Health = {
  status: string;
  gemini_configured: boolean;
  database: string;
  timestamp: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API error ${response.status} for ${path}`);
  }
  return response.json();
}

export function getHealth() {
  return fetchJson<Health>("/health");
}

export function getSearches() {
  return fetchJson<Search[]>("/searches");
}

export function getDeals() {
  return fetchJson<Deal[]>("/deals");
}

export function getListings() {
  return fetchJson<Listing[]>("/listings");
}

export function getJobs() {
  return fetchJson<JobRun[]>("/jobs");
}
