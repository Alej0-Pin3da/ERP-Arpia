from datetime import datetime

from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ClienteBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    documento_identidad: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=50)
    ciudad: str | None = Field(default=None, max_length=80)
    direccion: str | None = Field(default=None, max_length=200)
    tipo: str | None = Field(default=None, max_length=30)
    talla_habitual: str | None = Field(default=None, max_length=10)
    talla_superior: str | None = Field(default=None, max_length=10)
    talla_inferior: str | None = Field(default=None, max_length=10)
    categoria_preferida: str | None = Field(default=None, max_length=50)
    tipo_producto_frecuente: str | None = Field(default=None, max_length=50)
    notas: str | None = None
    medidas: dict[str, Any] | None = None

    @field_validator("medidas")
    @classmethod
    def validate_medidas(cls, v: Any) -> Any:
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError("medidas must be a JSON object (dict)")
        return v


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    documento_identidad: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=50)
    ciudad: str | None = Field(default=None, max_length=80)
    direccion: str | None = Field(default=None, max_length=200)
    tipo: str | None = Field(default=None, max_length=30)
    talla_habitual: str | None = Field(default=None, max_length=10)
    talla_superior: str | None = Field(default=None, max_length=10)
    talla_inferior: str | None = Field(default=None, max_length=10)
    categoria_preferida: str | None = Field(default=None, max_length=50)
    tipo_producto_frecuente: str | None = Field(default=None, max_length=50)
    notas: str | None = None
    medidas: dict[str, Any] | None = None

    @field_validator("medidas")
    @classmethod
    def validate_medidas(cls, v: Any) -> Any:
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError("medidas must be a JSON object (dict)")
        return v


class ClienteRead(ClienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
