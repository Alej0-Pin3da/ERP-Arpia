"""Seed script for the base data. Run with `python -m app.seeder`."""

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import CategoriaInsumo, Usuario

ADMIN_EMAIL = "admin@arpia.com"
ADMIN_PASSWORD = "Admin123!"

BASE_CATEGORIES = ["Telas", "Herrajes", "Empaques", "Químicos"]


def seed_usuarios(db) -> None:
    existing = db.scalar(select(Usuario).where(Usuario.email == ADMIN_EMAIL))
    if existing is None:
        db.add(
            Usuario(
                nombre="Administrador",
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
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
    with SessionLocal() as db:
        seed_usuarios(db)
        seed_categorias(db)
    print("Seeder completed successfully.")


if __name__ == "__main__":
    run()