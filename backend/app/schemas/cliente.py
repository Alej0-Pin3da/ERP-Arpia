from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClienteBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    documento_identidad: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=50)


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    documento_identidad: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=50)


class ClienteRead(ClienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
