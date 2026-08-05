from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    email: EmailStr
    rol: str = "consulta"


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=6, max_length=128)


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    rol: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UsuarioRead(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
