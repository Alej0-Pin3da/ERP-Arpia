from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

VALID_ROLES = frozenset({"admin", "operador", "consulta"})


def _validate_rol(value: str) -> str:
    if value not in VALID_ROLES:
        raise ValueError(f"rol must be one of {sorted(VALID_ROLES)}")
    return value


class UsuarioBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    email: EmailStr
    rol: str = "consulta"

    @field_validator("rol")
    @classmethod
    def _rol_must_be_valid(cls, value: str) -> str:
        return _validate_rol(value)


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=6, max_length=128)


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    rol: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)

    @field_validator("rol")
    @classmethod
    def _rol_must_be_valid(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_rol(value)


class UsuarioRead(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
