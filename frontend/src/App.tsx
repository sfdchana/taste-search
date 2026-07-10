import { useEffect, useState } from "react";
import { fetchPieces, toQuery, type Filters, type Piece } from "./api";
import { PieceCard } from "./PieceCard";
import "./App.css";

const ROLES = ["anchor", "statement", "connector"];
const MAGNITUDES = ["low", "moderate", "high"];
const ERAS = ["50s", "60s", "70s", "80s", "90s", "00s", "10s", "current"];

export default function App() {
  const [filters, setFilters] = useState<Filters>({});
  const [pieces, setPieces] = useState<Piece[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // refetch whenever a filter changes
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchPieces(filters)
      .then((data) => {
        if (cancelled) return;
        setPieces(data.pieces);
        setCount(data.count);
      })
      .catch((e) => !cancelled && setError(String(e)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [filters]);

  const set = (key: keyof Filters, value: string) =>
    setFilters((f) => ({ ...f, [key]: value }));

  const qs = toQuery(filters);
  const where = qs
    ? qs.replace(/&/g, " AND ").replace(/=/g, " = ")
    : "status = approved";

  return (
    <div className="app">
      <header className="head">
        <h1>Taste Search</h1>
        <p className="tagline">
          filter the archive by what a piece <em>does</em>, not what it's called.
        </p>
        <code className="query">SELECT * FROM archive WHERE {where}</code>
      </header>

      <div className="filters">
        <label>
          role
          <select value={filters.role ?? ""} onChange={(e) => set("role", e.target.value)}>
            <option value="">any</option>
            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </label>
        <label>
          magnitude
          <select value={filters.magnitude ?? ""} onChange={(e) => set("magnitude", e.target.value)}>
            <option value="">any</option>
            {MAGNITUDES.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </label>
        <label>
          era
          <select value={filters.era ?? ""} onChange={(e) => set("era", e.target.value)}>
            <option value="">any</option>
            {ERAS.map((x) => <option key={x} value={x}>{x}</option>)}
          </select>
        </label>
        <label>
          survives trend
          <select value={filters.survives_trend ?? ""} onChange={(e) => set("survives_trend", e.target.value)}>
            <option value="">any</option>
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </label>
        <label>
          vibe
          <input
            type="text"
            placeholder="e.g. edgy"
            value={filters.vibe ?? ""}
            onChange={(e) => set("vibe", e.target.value)}
          />
        </label>
      </div>

      <div className="count">
        {loading ? "querying…" : error ? error : `${count} piece${count === 1 ? "" : "s"}`}
      </div>

      <div className="grid">
        {pieces.map((p) => <PieceCard key={p.id} piece={p} />)}
      </div>
    </div>
  );
}
