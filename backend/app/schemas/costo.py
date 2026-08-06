from decimal import Decimal

from pydantic import BaseModel


class CostoLineaRead(BaseModel):
    tipo: str  # "insumo" | "producto" | "operativos_fijos"
    id: int
    nombre: str
    cantidad: Decimal
    costo_unitario: Decimal
    costo_total: Decimal


class CostoProduccionRead(BaseModel):
    total: Decimal
    lineas: list[CostoLineaRead]
