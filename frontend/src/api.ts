// Typed API client. These interfaces mirror the backend's Pydantic `Piece`
// model, which mirrors the Postgres schema — one typed contract end to end.
// If the API contract changes, TypeScript surfaces it here at compile time.

export interface Piece {
  id: string;
  name: string;
  brand: string | null;
  image_url: string | null;
  role: string | null;
  provokes: string | null;
  era: string | null;
  gender_coding: string | null;
  tension_base: string | null;
  tension_magnitude: string | null;
  subverter: string | null;
  trend: string | null;
  survives_trend: boolean | null;
  vibes: string[];
}

export interface PiecesResponse {
  count: number;
  pieces: Piece[];
}

export interface Filters {
  role?: string;
  magnitude?: string;
  era?: string;
  vibe?: string;
  survives_trend?: string; // "" | "true" | "false"
}

// Base URL is config, not hardcoded — localhost in dev, the deployed API in prod.
const API = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export function toQuery(f: Filters): string {
  const p = new URLSearchParams();
  if (f.role) p.set("role", f.role);
  if (f.magnitude) p.set("magnitude", f.magnitude);
  if (f.era) p.set("era", f.era);
  if (f.vibe) p.set("vibe", f.vibe);
  if (f.survives_trend) p.set("survives_trend", f.survives_trend);
  return p.toString();
}

export async function fetchPieces(f: Filters): Promise<PiecesResponse> {
  const res = await fetch(`${API}/pieces?${toQuery(f)}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
