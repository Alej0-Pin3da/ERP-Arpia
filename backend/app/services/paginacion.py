"""Shared pagination helper (design D1/D2).

``paginar`` runs the count over the FILTERED statement (limit/offset ignored)
and returns the sliced rows — the single code path every list endpoint uses so
`total` is always the count of the full filtered set (API-1).

``aplicar_orden`` applies a WHITELISTED ORDER BY for server-side column
sorting: the frontend never feeds raw SQL — sort keys are mapped through a
per-endpoint dict of SQLAlchemy columns, and unknown keys (or no key) keep
the route's default ordering unchanged.
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


def aplicar_orden(stmt, sort_by, order, sortable):
    """Replace the statement's ORDER BY with a whitelisted column.

    ``sort_by`` None / unknown key -> the statement is returned untouched, so
    the route's default ordering (applied before this call) is preserved.
    Known key -> ``ORDER BY <column> ASC|DESC``, REPLACING whatever the route
    set (Select.order_by APPENDS in SQLAlchemy 2.0, so the default is cleared
    first with ``order_by(None)``). ``sortable`` maps a frontend sort key to a
    SQLAlchemy column/expression; joined columns are resolved by the route's
    existing joins (helpers never add joins, avoiding ambiguity).
    """
    if sort_by is None:
        return stmt
    column = sortable.get(sort_by)
    if column is None:
        return stmt
    direction = column.asc() if order == "asc" else column.desc()
    return stmt.order_by(None).order_by(direction)
