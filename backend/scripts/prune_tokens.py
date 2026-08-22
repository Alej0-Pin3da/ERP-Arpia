"""Prune revoked/expired refresh tokens from the ``RefreshTokens`` table.

A standalone maintenance script meant to be scheduled (e.g. cron) so the table
does not grow unboundedly with every login/refresh cycle. It removes tokens
that are revoked OR expired and older than ``--days`` days.

Usage:
    python scripts/prune_tokens.py [--days N] [--dry-run]

Examples:
    # Delete every revoked/expired token older than 30 days.
    python scripts/prune_tokens.py --days 30

    # Show how many rows would be removed, without deleting anything.
    python scripts/prune_tokens.py --days 30 --dry-run

Scheduling (cron, daily at 03:00):
    0 3 * * * cd /path/to/backend && .venv/bin/python scripts/prune_tokens.py --days 30

Exit codes:
    0  — success
    1  — database connection or execution failure
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import and_, delete, func, or_, select

from app.db.session import SessionLocal
from app.models.refresh_token import RefreshToken


def cutoff_date(days: int) -> datetime:
    """Return the UTC timestamp ``days`` days ago used as the prune boundary."""
    return datetime.now(UTC) - timedelta(days=days)


def prune_criteria(cutoff: datetime):
    """SQLAlchemy WHERE clause matching rows eligible for pruning.

    A row is eligible when it was revoked more than ``days`` days ago, or when
    it expired more than ``days`` days ago without ever being revoked.
    """
    return or_(
        and_(
            RefreshToken.revocado_en.is_not(None),
            RefreshToken.revocado_en < cutoff,
        ),
        and_(
            RefreshToken.revocado_en.is_(None),
            RefreshToken.expira_en < cutoff,
        ),
    )


def count_eligible(db, cutoff: datetime) -> int:
    """Count rows matching ``prune_criteria`` without deleting them."""
    stmt = select(func.count()).select_from(RefreshToken).where(prune_criteria(cutoff))
    return db.execute(stmt).scalar_one()


def delete_eligible(db, cutoff: datetime) -> int:
    """Bulk-delete rows matching ``prune_criteria`` and commit; return count."""
    stmt = delete(RefreshToken).where(prune_criteria(cutoff))
    result = db.execute(stmt)
    db.commit()
    return result.rowcount or 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prune revoked/expired refresh tokens older than --days days."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Age cutoff in days (default: 30).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only count candidates; do not delete anything.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.days < 0:
        print(f"error: --days must be >= 0, got {args.days}", file=sys.stderr)
        return 1

    cutoff = cutoff_date(args.days)
    started = time.perf_counter()
    try:
        with SessionLocal() as db:
            if args.dry_run:
                count = count_eligible(db, cutoff)
                print(
                    f"[dry-run] Would delete {count} refresh token(s) older than {args.days} days."
                )
            else:
                deleted = delete_eligible(db, cutoff)
                print(f"Deleted {deleted} refresh token(s) older than {args.days} days.")
    except Exception as exc:
        print(f"error: could not reach the database: {exc}", file=sys.stderr)
        return 1

    elapsed = time.perf_counter() - started
    print(f"Done in {elapsed:.2f}s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
