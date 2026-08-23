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
import uuid

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

from app.core.login_tracker import LoginAttemptTracker
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models import CategoriaInsumo, Usuario
from app.seeder import seed_categorias, seed_usuarios

ADMIN_EMAIL = "admin@arpia.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(autouse=True)
def _reset_login_tracker():
    """Reset login attempt tracker before each test for isolation."""
    LoginAttemptTracker.reset()
    yield
    LoginAttemptTracker.reset()


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


def _recrear_bd_test() -> None:
    """Drop and recreate `arpia_test` so the schema is guaranteed clean.

    Drops all connections first, then drops and recreates the database. The
    session fixture then runs ``alembic upgrade head`` on the fresh DB.
    """
    server_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    nombre_bd = TEST_DATABASE_URL.rsplit("/", 1)[1]
    engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :nombre AND pid <> pg_backend_pid()"
                ),
                {"nombre": nombre_bd},
            )
            conn.execute(text(f'DROP DATABASE IF EXISTS "{nombre_bd}"'))
            conn.execute(text(f'CREATE DATABASE "{nombre_bd}"'))
    finally:
        engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _bd_test_lista():
    """(session, autouse) Rebuild the test schema exactly like production and
    apply the base seed (admin + categories) once per test session.

    The test DB is dropped and recreated so the schema is guaranteed clean and
    every migration runs on an empty database — unlike an incremental
    downgrade/upgrade, which can leave orphan rows that violate the new CHECK
    constraints added by later migrations.
    """
    try:
        _crear_bd_test_si_no_existe()

        from alembic.config import Config as AlembicConfig

        from alembic import command as alembic_command

        # Drop + recreate the test DB for a guaranteed-clean schema.
        _recrear_bd_test()

        alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
        cfg = AlembicConfig(str(alembic_ini))
        cfg.set_main_option("script_location", str(alembic_ini.parent / "alembic"))
        alembic_command.upgrade(cfg, "head")

        with SessionLocal() as db:
            seed_usuarios(db, ADMIN_EMAIL, ADMIN_PASSWORD)
            seed_categorias(db)
    except Exception:
        # If test postgres server is offline, yield so pure non-DB unit tests can still run
        yield
        return

    yield


# Idempotent critical endpoints (mirror app.core.idempotency.IDEMPOTENT_ENDPOINTS).
# The client fixture injects a fresh key automatically so functional tests don't
# have to. Use `client_raw` (below) when a test MUST observe the missing-key 400.
IDEMPOTENT_ENDPOINTS = (
    "/api/v1/ventas",
    "/api/v1/devoluciones",
    "/api/v1/compras",
    "/api/v1/finanzas/movimientos",
    "/api/v1/inventario/ajustes",
)
IDEMPOTENT_METHODS = ("POST", "PUT", "PATCH")


class IdempotentTestClient(TestClient):
    """TestClient that injects an Idempotency-Key on critical mutations."""

    def request(self, method: str, url: str, **kwargs):
        if method.upper() in IDEMPOTENT_METHODS and url.startswith(IDEMPOTENT_ENDPOINTS):
            headers = kwargs.get("headers") or {}
            has_key = (
                (isinstance(headers, dict) and "Idempotency-Key" in headers)
                or (hasattr(headers, "get") and headers.get("Idempotency-Key"))
            )
            if not has_key:
                merged = dict(headers)
                merged["Idempotency-Key"] = str(uuid.uuid4())
                kwargs["headers"] = merged
        return super().request(method, url, **kwargs)


@pytest.fixture(scope="session")
def client():
    with IdempotentTestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    """A SQLAlchemy Session bound to the test database (used by service tests)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client_raw():
    """Plain TestClient — no Idempotency-Key injected (for idempotency-missing tests)."""
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
