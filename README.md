# Taste Search

A search surface over the House of Sof archive that filters by **taste
attributes** — the role a piece plays in an outfit, the magnitude of its
tension, whether it outlasts a trend — instead of neutral keywords like color
and size.

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
Postgres archive  ──►  taste-search (this repo)   read-only product API
                  ──►  admin tool (separate repo)  back-of-house classify UI
```

This repo is a standalone FastAPI service. It does **not** import the admin
tool's code and it never writes — it talks to the archive through one query.
The product surface and the internal tool evolve independently.

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
- `GET /pieces?role=&magnitude=&survives_trend=&limit=` → matching pieces

Filters compose dynamically from a **whitelist of columns**; every value is a
bound parameter, so the endpoint is injection-safe by construction.

### Design decisions

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

_(to write: pagination beyond LIMIT, indexes on the filtered columns, caching
the derived `survives_trend`, read replica, moving the taste derivation into a
materialized view.)_

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# .env with DATABASE_URL=postgresql://...
.venv/bin/uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs
```
