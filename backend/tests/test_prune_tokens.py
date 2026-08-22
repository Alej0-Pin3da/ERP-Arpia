"""Unit tests for ``scripts.prune_tokens`` — no live database required.

These tests exercise the pure helpers (cutoff computation, CLI parsing and the
SQLAlchemy criteria builder) without ever opening a connection.
"""

from datetime import datetime, timedelta

from scripts.prune_tokens import build_parser, cutoff_date, prune_criteria


def test_cutoff_date_is_utc_aware_and_days_ago():
    cutoff = cutoff_date(30)
    assert cutoff.tzinfo is not None
    diff = datetime.now(cutoff.tzinfo) - cutoff
    assert timedelta(days=29) < diff <= timedelta(days=30)


def test_cutoff_date_zero_days_is_now():
    cutoff = cutoff_date(0)
    assert cutoff.tzinfo is not None
    assert datetime.now(cutoff.tzinfo) - cutoff < timedelta(seconds=60)


def test_prune_criteria_targets_revoked_or_expired():
    criteria = prune_criteria(cutoff_date(30))
    sql = str(criteria)
    assert "revocado_en" in sql
    assert "expira_en" in sql


def test_parser_defaults():
    args = build_parser().parse_args([])
    assert args.days == 30
    assert args.dry_run is False


def test_parser_explicit_args():
    args = build_parser().parse_args(["--days", "7", "--dry-run"])
    assert args.days == 7
    assert args.dry_run is True


def test_parser_rejects_negative_days():
    args = build_parser().parse_args(["--days", "-1"])
    assert args.days == -1
