"""Taste Search API.

The product surface: filter the House of Sof archive by *taste attributes*
(role, tension magnitude, survives-trend) instead of neutral keywords.

Decision: this is a standalone service that reads the shared archive through a
narrow contract (this one endpoint). It does not import the admin tool's code
and it never writes. Clean boundary — the product and the back-of-house tool
evolve independently.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query

from .db import pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    # open the pool when the app boots, close it on shutdown
    pool.open()
    yield
    pool.close()


app = FastAPI(title="Taste Search", version="0.1.0", lifespan=lifespan)


# The taste query. survives_trend is COALESCE(manual override, derived-from-trend),
# i.e. the same derivation the archive uses — computed, not stored.
PIECES_SQL = """
    SELECT
        i.id,
        i.name,
        i.brand,
        i.image_url,
        i.role,
        i.provokes,
        i.era,
        i.gender_coding,
        t.base                                   AS tension_base,
        t.magnitude                              AS tension_magnitude,
        el.name                                  AS subverter,
        tr.name                                  AS trend,
        COALESCE(i.survives_trend, tr.survives)  AS survives_trend
    FROM items i
    LEFT JOIN tension  t  ON t.item_id = i.id
    LEFT JOIN elements el ON t.subverter_element_id = el.id
    LEFT JOIN trends   tr ON el.trend_id = tr.id
    WHERE {where}
    ORDER BY i.created_at DESC
    LIMIT %(limit)s
"""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/pieces")
def get_pieces(
    role: str | None = Query(default=None, description="anchor | statement | connector"),
    magnitude: str | None = Query(default=None, description="low | moderate | high"),
    survives_trend: bool | None = Query(default=None, description="does it outlast the trend"),
    limit: int = Query(default=100, ge=1, le=500),
):
    """Return archive pieces matching the given taste attributes.

    Filters are composed dynamically but every value is a bound parameter —
    the WHERE clause is built from a whitelist of columns, never string-joined
    user input, so this is injection-safe.
    """
    clauses = ["i.status = 'approved'"]
    params: dict = {"limit": limit}

    if role is not None:
        clauses.append("i.role = %(role)s")
        params["role"] = role
    if magnitude is not None:
        clauses.append("t.magnitude = %(magnitude)s")
        params["magnitude"] = magnitude
    if survives_trend is not None:
        clauses.append("COALESCE(i.survives_trend, tr.survives) = %(survives_trend)s")
        params["survives_trend"] = survives_trend

    sql = PIECES_SQL.format(where=" AND ".join(clauses))

    with pool.connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return {"count": len(rows), "pieces": rows}
