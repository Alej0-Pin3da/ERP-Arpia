from typing import Any


class DomainError(Exception):
    """Base domain exception for ERP-Arpia application logic."""

    def __init__(self, message: str, status_code: int = 400, details: Any | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class InsufficientStockError(DomainError):
    """Raised when an operation requires more stock than currently available."""

    def __init__(self, insumo_nombre: str):
        super().__init__(
            message=f"Stock insuficiente para insumo '{insumo_nombre}'",
            status_code=409,
        )
        self.insumo_nombre = insumo_nombre


class BomCycleDetectedError(DomainError):
    """Raised when a circular reference is detected during BOM material explosion."""

    def __init__(self, path: list[int]):
        cadena = " -> ".join(str(p) for p in path)
        super().__init__(
            message=f"Cycle detected in BOM explosion: {cadena}",
            status_code=409,
        )
        self.path = path


class EntityNotFoundError(DomainError):
    """Raised when a requested domain entity does not exist."""

    def __init__(self, entity_name: str, entity_id: Any | None = None):
        msg = (
            f"{entity_name} no encontrado"
            if entity_id is None
            else f"{entity_name} {entity_id!r} no encontrado"
        )
        super().__init__(
            message=msg,
            status_code=404,
        )
        self.entity_name = entity_name
        self.entity_id = entity_id


class DomainValidationError(DomainError):
    """Raised when business input validation fails at domain level."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message=message, status_code=status_code)
