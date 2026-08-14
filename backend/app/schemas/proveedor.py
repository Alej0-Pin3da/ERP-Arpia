from pydantic import BaseModel, ConfigDict, Field


class ProveedorBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    ubicacion: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=500)
    contacto: str | None = Field(default=None, max_length=255)


class ProveedorCreate(ProveedorBase):
    pass


class ProveedorUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    ubicacion: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=500)
    contacto: str | None = Field(default=None, max_length=255)


class ProveedorRead(ProveedorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
