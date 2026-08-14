"""Execution context for a migration phase.

Provides:
- ``FaseOptions``: shared CLI options for the whole run.
- ``MigrationContext``: per-phase shared state (options, report).
- ``session_scope``: a single-transaction context per phase (EXM-4). In
  ``--commit`` the session commits once at the end of the phase and rolls back
  entirely on any error. In ``--dry-run`` nothing touches the database:
  loaders and normalizers run, but no writes are emitted.
- ``savepoint``: nested savepoint used by per-row loops (e.g. historical WAC
  purchases). The enclosing ``session_scope`` still owns the final commit; a
  failed row rolls back only its own savepoint so the phase can report and
  continue.

Business phases (catalog, purchases, ...) receive a ``MigrationContext``.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from pathlib import Path

from migrate.report import Report

EMPTY_SOURCE = Path("")


@dataclass
class FaseOptions:
    """Shared options for the whole run (from the CLI)."""

    source: Path = EMPTY_SOURCE
    modo: str = "dry-run"  # "dry-run" | "commit"
    fuerza: bool = False
    canal_venta: str | None = None


@dataclass
class MigrationContext:
    """Per-phase execution context. ``db`` is a sessionmaker-less handle used
    by later slices; here it stays ``None`` in dry-run and is provided by the
    phase runner in commit mode."""

    options: FaseOptions
    fase_id: str
    report: Report = field(default_factory=Report)
    session: object | None = None

    @classmethod
    def para_fase(cls, options: FaseOptions, fase_id: str) -> MigrationContext:
        return cls(
            options=options,
            fase_id=fase_id,
            report=Report(fase=fase_id, modo=options.modo),
        )

    def con_session(self, session: object) -> MigrationContext:
        """Return a copy bound to the given SQLAlchemy session (commit mode)."""
        return replace(self, session=session)


@contextmanager
def session_scope(ctx: MigrationContext, db):
    """Single-transaction boundary per phase (EXM-4).

    - commit mode: commit once at exit; rollback entirely on exception.
    - dry-run mode: never persist; no session is opened by phase code.
    """
    if ctx.options.modo == "dry-run":
        yield None
        return
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


@contextmanager
def savepoint(session):
    """Nested savepoint used by per-row loops (e.g. historical WAC purchases).

    The enclosing ``session_scope`` still owns the final commit; a failed row
    rolls back only its own savepoint so the phase can report and continue.
    """
    nested = session.begin_nested()
    try:
        yield nested
    except Exception:
        nested.rollback()
        raise
