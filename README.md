# Taste Search

A search surface over the House of Sof archive that filters by **taste
attributes** — the role a piece plays in an outfit, the magnitude of its
tension, whether it outlasts a trend — instead of neutral keywords like color
and size.

## Live

- **App:** https://sfdchana.github.io/taste-search/
- **API (interactive docs):** https://taste-search-api-production.up.railway.app/docs
- **Example query:** [`/pieces?role=anchor&survives_trend=true`](https://taste-search-api-production.up.railway.app/pieces?role=anchor&survives_trend=true)

React + TypeScript frontend on GitHub Pages, FastAPI backend on Railway, both
reading a shared Postgres archive.

> Status: in progress. v1 = filter the existing archive by a few schema
> attributes, rendered and live. This README is written as a design doc and
> grows with the project.

## The problem

Resale search is stuck on catalog metadata: brand, color, size, price. That
metadata says nothing about *why* a piece is good. The interesting signal —
what a piece *does*, what it references, whether it has staying power — isn't
captured by any schema in the market. This project models that signal and makes
it queryable.

## Architecture

One Postgres archive is the shared foundation. Each project is a separately
bounded codebase that reads or writes it through a narrow contract:

```
Postgres archive  ──►  taste-search (this repo)   FastAPI + React product
                  ──►  admin tool (separate repo)  back-of-house classify UI
```

This repo is one bounded project: a FastAPI backend (`app/`) and a React
frontend (`frontend/`) that make up the taste-search product. It does **not**
import the admin tool's code and it never writes — it reads the archive through
one query contract. The product surface and the internal tool evolve
independently, on the same shared database.

## Data model (the part that matters)

The queryable taste attributes:

- `role` — `anchor` | `statement` | `connector`: the piece's function in a
  composition, tested by pairing.
- `tension.magnitude` — `low` | `moderate` | `high`: how loud the subverting
  element is. `tension` is a 1:1 table off `items`, not columns on `items` —
  the tension of a piece is its own object (base register + subverter + magnitude).
- `survives_trend` — **derived, not stored.** Computed as
  `COALESCE(items.survives_trend, trends.survives)` by walking
  `item → tension → subverter element → trend`. The judgment about whether a
  *trend* endures lives in one row of the `trends` table; change that row and
  every piece subverted by that element re-derives. A manual per-item override
  wins when set. `null` means genuinely unknown (no trend chain, no override) —
  not `false`.

## API

FastAPI, chosen for: modern-standard Python, type-hint-driven validation that
mirrors the schema-first data model, and auto-generated interactive docs at
`/docs` (an interviewer can query the taste engine themselves).

- `GET /health` → liveness
- `GET /pieces?role=&magnitude=&survives_trend=&era=&vibe=&limit=` → matching pieces

Filters compose dynamically from a **whitelist of columns**; every value is a
bound parameter, so the endpoint is injection-safe by construction. Each piece
also returns its `vibes` (a many-to-many via the `item_vibes` junction), fetched
with a correlated `array_agg` subquery so results don't fan out.

### Design decisions

- **Typed request + response contract** — filter params use `Literal` types that
  mirror the DB's CHECK constraints (`role ∈ {anchor,statement,connector}`,
  `magnitude ∈ {low,moderate,high}`), so invalid input is rejected with a 422
  *before* a query runs, and `/docs` renders them as dropdowns. The response is a
  Pydantic `Piece` model, kept separate from the query — the SQL can change
  without changing the public contract. The contract is enforced at both the API
  and the database layer.
- **Connection pool, not per-request connections** — a small warm pool
  (`min=1,max=5`); this is a read-only surface, not write-heavy.
- **Raw parameterized SQL, no ORM** — the schema is stable and hand-designed;
  an ORM would hide the SQL I want to reason about and optimize, with no benefit
  for a read-only query surface.
- **Typed config, fail-fast** — `DATABASE_URL` is read into a typed settings
  object at boot; missing config crashes at startup, never mid-request. Secrets
  live in a gitignored `.env`, never in the repo.
- **Pool lifecycle tied to app lifecycle** — opened/closed in the FastAPI
  lifespan.

## What I'd change at 10x scale

Today the archive is small enough that a bare `LIMIT` and per-request queries
are fine. What breaks first, and the fix:

- **Pagination.** `LIMIT 500` doesn't scale to a large archive or a scrolling UI.
  Move to keyset (cursor) pagination on `(created_at, id)` — stable under inserts
  and index-friendly, unlike `OFFSET`.
- **Indexes on the filtered columns.** `role`, `era`, and `tension.magnitude`
  want btree indexes; the `vibe` `EXISTS` wants an index on
  `item_vibes(vibe_id, item_id)`. Right now these are sequential scans — invisible
  at this size, not at 100k rows.
- **The derived `survives_trend` is recomputed every query.** At scale I'd
  materialize it — a materialized view (or a maintained column invalidated when a
  `trends` row changes) — so the read path is a lookup, not a 3-table walk. The
  tradeoff is staleness vs. read cost; for a taste signal that changes rarely,
  materialize and refresh on write.
- **Read replica.** A public read-only search surface should hit a replica, not
  the primary the admin tool writes to — isolates product traffic from ingestion.
- **Caching.** Filter combinations are low-cardinality and repeat; a short-TTL
  cache in front of `/pieces` would absorb most of the load.

The through-line: the boundaries are already drawn so each of these is a local
change — the API contract doesn't move when the storage or read path does.

## Frontend

`frontend/` — Vite + React + **TypeScript**. The TS interfaces in `api.ts`
mirror the backend's Pydantic `Piece` model, which mirrors the Postgres schema:
one typed contract from database → API → UI, so a contract change surfaces at
compile time. Components are bounded — `PieceCard` owns how a piece presents,
`App` owns filter state and fetching. The API base URL is config
(`VITE_API_URL`), not hardcoded. CORS is permissive on the API by deliberate
choice (public, read-only).

The UI renders the active filters as a live pseudo-SQL line
(`SELECT * FROM archive WHERE …`) — the interface *is* the query, which is the
whole thesis.

## Run locally

Backend:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# .env with DATABASE_URL=postgresql://...
.venv/bin/uvicorn app.main:app --reload   # http://127.0.0.1:8000/docs
```

Frontend (separate terminal):
```bash
cd frontend
npm install
npm run dev                                # http://localhost:5173
```
