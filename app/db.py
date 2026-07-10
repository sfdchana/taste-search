"""Database access.

Decision: a connection *pool*, not a new connection per request. Opening a
Postgres connection is expensive; a pool keeps a small set warm and hands them
out. min/max are deliberately small — this is a read-only search surface, not a
write-heavy service.

Decision: raw parameterized SQL via psycopg, no ORM. The schema is stable and
I designed it; an ORM would add a translation layer with no benefit for a
read-only query surface, and it would hide the exact SQL I want to be able to
reason about and optimize. Every query is parameterized, so it is injection-safe.
"""
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

from .config import settings

# open=False: the pool is opened in the FastAPI lifespan (see main.py) and closed
# on shutdown, so connection lifecycle is tied to the app's lifecycle.
pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=5,
    open=False,
    kwargs={"row_factory": dict_row},  # rows come back as dicts, ready to serialize
)
