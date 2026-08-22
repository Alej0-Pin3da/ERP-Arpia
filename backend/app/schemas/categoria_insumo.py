from pydantic import BaseModel, ConfigDict, Field


class CategoriaInsumoBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)


class CategoriaInsumoCreate(CategoriaInsumoBase):
    pass


class CategoriaInsumoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)


class CategoriaInsumoRead(CategoriaInsumoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
