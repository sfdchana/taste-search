"""Response schemas.

Decision: the API declares the exact shape it returns, separate from the query
that produces it. The DB query and the public contract are different concerns —
the query can change (add a join, rename an alias) without changing what
consumers see, as long as it still satisfies this model. FastAPI also uses these
models to generate the /docs contract, so the schema documents itself.
"""
from uuid import UUID

from pydantic import BaseModel


class Piece(BaseModel):
    id: UUID
    name: str
    brand: str | None = None
    image_url: str | None = None

    # taste attributes
    role: str | None = None
    provokes: str | None = None
    era: str | None = None
    gender_coding: str | None = None

    # tension object (flattened for the API surface)
    tension_base: str | None = None
    tension_magnitude: str | None = None
    subverter: str | None = None
    trend: str | None = None

    survives_trend: bool | None = None  # None = unknown, not False
    vibes: list[str] = []


class PiecesResponse(BaseModel):
    count: int
    pieces: list[Piece]
