"""Taste Search API.

The product surface: filter the House of Sof archive by *taste attributes*
(role, tension magnitude, survives-trend, era, vibe) instead of neutral keywords.

Decision: this is a standalone service that reads the shared archive through a
narrow contract. It does not import the admin tool's code and it never writes.
"""
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Query

from .db import pool
from .models import PiecesResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()


app = FastAPI(title="Taste Search", version="0.2.0", lifespan=lifespan)


# survives_trend is COALESCE(manual override, derived-from-trend) — computed, not
# stored. Each piece's vibes come from the item_vibes junction as an array.
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
        COALESCE(i.survives_trend, tr.survives)  AS survives_trend,
        (
            SELECT COALESCE(array_agg(v.name ORDER BY v.name), ARRAY[]::text[])
            FROM item_vibes iv
            JOIN vibes v ON v.id = iv.vibe_id
            WHERE iv.item_id = i.id
        )                                        AS vibes
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


@app.get("/pieces", response_model=PiecesResponse)
def get_pieces(
    # Literal types mirror the DB CHECK constraints — invalid values are rejected
    # with a 422 before a query ever runs, and /docs renders them as dropdowns.
    role: Literal["anchor", "statement", "connector"] | None = Query(default=None),
    magnitude: Literal["low", "moderate", "high"] | None = Query(default=None),
    survives_trend: bool | None = Query(default=None, description="does it outlast the trend"),
    era: str | None = Query(default=None, description="e.g. 90s, 00s, current"),
    vibe: str | None = Query(default=None, description="a single vibe the piece carries"),
    limit: int = Query(default=100, ge=1, le=500),
):
    """Return archive pieces matching the given taste attributes.

    Filters compose from a whitelist of columns; every value is a bound
    parameter, so the endpoint is injection-safe by construction.
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
    if era is not None:
        clauses.append("i.era = %(era)s")
        params["era"] = era
    if vibe is not None:
        # many-to-many: the piece must carry this vibe (EXISTS avoids row fan-out)
        clauses.append(
            "EXISTS (SELECT 1 FROM item_vibes iv JOIN vibes v ON v.id = iv.vibe_id"
            " WHERE iv.item_id = i.id AND v.name = %(vibe)s)"
        )
        params["vibe"] = vibe

    sql = PIECES_SQL.format(where=" AND ".join(clauses))

    with pool.connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return {"count": len(rows), "pieces": rows}
