import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models import CategoriaInsumo, Usuario

ADMIN_EMAIL = "admin@arpia.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def _operador_user():
    db = SessionLocal()
    try:
        existing = (
            db.query(Usuario).filter(Usuario.email == "operador@arpia.com").first()
        )
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
def categoria_fixture():
    db = SessionLocal()
    try:
        existing = (
            db.query(CategoriaInsumo)
            .filter(CategoriaInsumo.nombre == "Telas")
            .first()
        )
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