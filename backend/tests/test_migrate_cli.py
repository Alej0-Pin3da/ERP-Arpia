"""Tests for migrate.cli - argparse contract (PR#1 slice)."""

import sys
from pathlib import Path

import pytest

from migrate import cli


def test_dry_run_es_default():
    parser = cli.construir_parser()
    args = parser.parse_args([])
    assert args.modo == "dry-run"


def test_commit_flag():
    parser = cli.construir_parser()
    args = parser.parse_args(["--commit"])
    assert args.modo == "commit"


def test_fase_simple():
    parser = cli.construir_parser()
    args = parser.parse_args(["--fase", "2"])
    assert args.fase == "2"
    assert args.todas is False


def test_fase_f0_aceptado():
    assert cli._normalizar_fase("0") == "F0"
    assert cli._normalizar_fase("F7") == "F7"


def test_all_flag_setea_todas():
    parser = cli.construir_parser()
    args = parser.parse_args(["--all"])
    assert args.todas is True


def test_fase_y_all_son_mutuamente_excluyentes():
    parser = cli.construir_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--fase", "1", "--all"])


def test_fases_a_correr():
    fases = cli._fases_a_correr(type("A", (), {"todas": False, "fase": "0"})())
    assert fases == ["F0"]

    fases_all = cli._fases_a_correr(type("A", (), {"todas": True, "fase": None})())
    assert fases_all[0] == "F0"
    assert fases_all[-1] == "F7"


def test_fase_inexistente_es_clara():
    from migrate import get_fase

    with pytest.raises(KeyError, match="F9"):
        get_fase("F9")