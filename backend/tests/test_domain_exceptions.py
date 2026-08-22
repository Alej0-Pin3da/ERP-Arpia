from fastapi.testclient import TestClient

from app.core.exceptions import (
    BomCycleDetectedError,
    DomainValidationError,
    EntityNotFoundError,
    InsufficientStockError,
)
from app.main import app

client = TestClient(app)


def test_domain_exception_hierarchy():
    err = InsufficientStockError("Tela Algodón")
    assert err.status_code == 409
    assert err.insumo_nombre == "Tela Algodón"
    assert "Stock insuficiente" in str(err)

    cycle_err = BomCycleDetectedError([1, 2, 1])
    assert cycle_err.status_code == 409
    assert "Cycle detected" in cycle_err.message

    nf_err = EntityNotFoundError("Producto", 999)
    assert nf_err.status_code == 404
    assert "Producto 999 no encontrado" in nf_err.message

    val_err = DomainValidationError("Dato inválido", status_code=400)
    assert val_err.status_code == 400
    assert val_err.message == "Dato inválido"


def test_domain_exception_handler():
    @app.get("/test-domain-error")
    def trigger_domain_error():
        raise InsufficientStockError("Hilo Negro")

    res = client.get("/test-domain-error")
    assert res.status_code == 409
    assert res.json() == {"detail": "Stock insuficiente para insumo 'Hilo Negro'"}


def test_unhandled_exception_handler():
    @app.get("/test-500-error")
    def trigger_500():
        raise RuntimeError("DB crash internal error detail")

    client_no_raise = TestClient(app, raise_server_exceptions=False)
    res = client_no_raise.get("/test-500-error")
    assert res.status_code == 500
    assert "detail" in res.json()
