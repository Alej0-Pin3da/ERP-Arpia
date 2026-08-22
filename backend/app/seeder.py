"""Seed script for the base data. Run with `python -m app.seeder`."""

import os

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import CategoriaInsumo, Usuario

DEFAULT_ADMIN_EMAIL = "admin@arpia.com"

BASE_CATEGORIES = ["Telas", "Herrajes", "Empaques", "Químicos"]


def seed_usuarios(
    db,
    admin_email: str = DEFAULT_ADMIN_EMAIL,
    admin_password: str | None = None,
) -> None:
    existing = db.scalar(select(Usuario).where(Usuario.email == admin_email))
    if existing is None:
        if not admin_password:
            raise RuntimeError(
                "Admin password is required when the seed administrator does not exist."
            )
        db.add(
            Usuario(
                nombre="Administrador",
                email=admin_email,
                password_hash=hash_password(admin_password),
                rol="admin",
            )
        )
        db.commit()


def seed_categorias(db) -> None:
    existing_names = set(db.scalars(select(CategoriaInsumo.nombre)).all())
    for name in BASE_CATEGORIES:
        if name not in existing_names:
            db.add(CategoriaInsumo(nombre=name))
    db.commit()


def run() -> None:
    admin_email = os.getenv("ARPIA_ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL)
    admin_password = os.getenv("ARPIA_ADMIN_PASSWORD")
    with SessionLocal() as db:
        seed_usuarios(db, admin_email, admin_password)
        seed_categorias(db)
    print("Seeder completed successfully.")


if __name__ == "__main__":
    run()
