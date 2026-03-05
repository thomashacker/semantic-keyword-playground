const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface BM25Result {
  title: string;
  description: string;
  score: number;
  properties: Record<string, unknown>;
}

export interface SemanticResult {
  title: string;
  description: string;
  distance: number | null;
  certainty: number | null;
  properties: Record<string, unknown>;
}

export interface SearchTiming {
  bm25_ms: number;
  semantic_ms: number;
}

export interface DualSearchResponse {
  query: string;
  collection: string;
  bm25: BM25Result[];
  semantic: SemanticResult[];
  timing: SearchTiming;
  query_terms: string[];
}

export interface VectorPoint {
  title: string;
  vector_2d: [number, number];
  certainty: number | null;
  distance: number | null;
  country: string | null;
}

export interface DatasetInfo {
  name: string;
  description: string;
  record_count: number;
  fields: string[];
  seeded: boolean;
}

export async function searchDual(
  query: string,
  collection: string,
  limit = 5
): Promise<DualSearchResponse> {
  const res = await fetch(`${BASE_URL}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, collection, limit }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Search failed: ${res.status}`);
  }
  return res.json();
}

export async function getSuggestions(dataset: string, limit = 5): Promise<string[]> {
  const res = await fetch(`${BASE_URL}/datasets/${dataset}/suggestions?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch suggestions");
  return res.json();
}

export async function getDatasets(): Promise<DatasetInfo[]> {
  const res = await fetch(`${BASE_URL}/datasets`);
  if (!res.ok) throw new Error("Failed to fetch datasets");
  return res.json();
}

export async function getSearchVectors(query: string, collection: string, limit = 5): Promise<VectorPoint[]> {
  const res = await fetch(
    `${BASE_URL}/search/vectors?query=${encodeURIComponent(query)}&collection=${encodeURIComponent(collection)}&limit=${limit}`
  );
  if (!res.ok) throw new Error("Failed to fetch vectors");
  return res.json();
}

export interface HybridResult {
  title: string;
  description: string;
  score: number | null;
  certainty: number | null;
  distance: number | null;
  properties: Record<string, unknown>;
}

export interface HybridSearchResponse {
  query: string;
  collection: string;
  results: HybridResult[];
  alpha: number;
  hybrid_ms: number;
}

export async function searchHybrid(
  query: string,
  collection: string,
  alpha: number,
  limit = 10
): Promise<HybridSearchResponse> {
  const res = await fetch(`${BASE_URL}/search/hybrid`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, collection, alpha, limit }),
  });
  if (!res.ok) throw new Error("Hybrid search failed");
  return res.json();
}

export async function seedDataset(name: string, force = false): Promise<void> {
  const res = await fetch(`${BASE_URL}/datasets/${name}/seed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ force }),
  });
  if (!res.ok) throw new Error(`Failed to seed ${name}`);
}
