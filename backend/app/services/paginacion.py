"""Shared pagination helper (design D1/D2).

``paginar`` runs the count over the FILTERED statement (limit/offset ignored)
and returns the sliced rows — the single code path every list endpoint uses so
`total` is always the count of the full filtered set (API-1).
"""

from sqlalchemy import func, select


def paginar(db, stmt, limit: int, offset: int):
    """Return ``(rows, total)`` for a filtered statement.

    - ``total`` = count of the complete filtered set (ignores limit/offset).
    - ``rows`` = the statement sliced with ``limit``/``offset``.
    """
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return rows, total
