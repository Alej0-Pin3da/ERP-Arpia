"""Pytest fixtures — isolated test database.

The test suite runs against a DEDICATED database (`arpia_test`) so it never
touches the development/production data. `DATABASE_URL` is set BEFORE the app
modules are imported (pydantic-settings gives real env vars priority over the
`.env` file), so every `SessionLocal`/`engine` in the process points at the
test database. The schema is rebuilt from alembic (same shape as production)
and the base seed (admin + categories) runs once per session.
"""

import os
from pathlib import Path

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://arpia:arpia_secret@localhost:5433/arpia_test",
)

# Must be set before importing any app module.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
# Disable slowapi rate limiting in tests (conftest #1: many logins from the
# same TestClient IP would otherwise hit 429). Must precede app imports.
os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models import CategoriaInsumo, Usuario
from app.seeder import seed_categorias, seed_usuarios

ADMIN_EMAIL = "admin@arpia.com"
ADMIN_PASSWORD = "Admin123!"


def _crear_bd_test_si_no_existe() -> None:
    """Create `arpia_test` on the same server (idempotent)."""
    server_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
    nombre_bd = TEST_DATABASE_URL.rsplit("/", 1)[1]
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :nombre"),
                {"nombre": nombre_bd},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{nombre_bd}"'))
    finally:
        engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _bd_test_lista():
    """(session, autouse) Rebuild the test schema exactly like production and
    apply the base seed (admin + categories) once per test session."""
    try:
        _crear_bd_test_si_no_existe()

        from alembic.config import Config as AlembicConfig

        from alembic import command as alembic_command

        alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
        cfg = AlembicConfig(str(alembic_ini))
        alembic_command.downgrade(cfg, "base")
        alembic_command.upgrade(cfg, "head")

        with SessionLocal() as db:
            seed_usuarios(db)
            seed_categorias(db)
    except Exception:
        # If test postgres server is offline, yield so pure non-DB unit tests can still run
        yield
        return

    yield


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def _operador_user():
    db = SessionLocal()
    try:
        existing = db.query(Usuario).filter(Usuario.email == "operador@arpia.com").first()
        if existing:
            user = existing
        else:
            user = Usuario(
                nombre="Operador",
                email="operador@arpia.com",
                password_hash=hash_password("Operador123!"),
                rol="operador",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        yield user
    finally:
        db.close()


@pytest.fixture(scope="module")
def _consulta_user():
    db = SessionLocal()
    try:
        existing = db.query(Usuario).filter(Usuario.email == "consulta@arpia.com").first()
        if existing:
            user = existing
        else:
            user = Usuario(
                nombre="Consulta",
                email="consulta@arpia.com",
                password_hash=hash_password("Consulta123!"),
                rol="consulta",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        yield user
    finally:
        db.close()


@pytest.fixture(scope="module")
def categoria_fixture():
    db = SessionLocal()
    try:
        existing = db.query(CategoriaInsumo).filter(CategoriaInsumo.nombre == "Telas").first()
        if existing:
            categoria = existing
        else:
            categoria = CategoriaInsumo(nombre="Telas")
            db.add(categoria)
            db.commit()
            db.refresh(categoria)
        yield {"id": categoria.id, "nombre": categoria.nombre}
    finally:
        db.close()


@pytest.fixture
def admin_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@pytest.fixture
def operador_token(client, _operador_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "operador@arpia.com", "password": "Operador123!"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@pytest.fixture
def consulta_token(client, _consulta_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "consulta@arpia.com", "password": "Consulta123!"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]
