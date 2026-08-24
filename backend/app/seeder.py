"""Seed script for the base data. Run with `python -m app.seeder`."""

import os

from sqlalchemy import select, text

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import CategoriaInsumo, Usuario

DEFAULT_ADMIN_EMAIL = "admin@arpia.com"

BASE_CATEGORIES = ["Telas", "Herrajes", "Empaques", "Químicos"]

# Mirrors Alembic 0010_ventas_canal_pago — keep in sync
CANALES_VENTA = [
    ("web", "Web"),
    ("whatsapp", "WhatsApp"),
    ("instagram", "Instagram"),
    ("feria", "Feria"),
    ("showroom_pereira", "Showroom Pereira"),
]
METODOS_PAGO = [
    ("efectivo", "Efectivo"),
    ("transferencia", "Transferencia"),
    ("tarjeta", "Tarjeta"),
    ("contraentrega", "Contraentrega"),
]


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


def seed_canales_venta(db) -> None:
    """Idempotent seed for maestros_canales_venta — mirrors 0010 Alembic."""
    for codigo, nombre in CANALES_VENTA:
        try:
            db.execute(
                text(
                    "INSERT INTO maestros_canales_venta (codigo, nombre) VALUES (:codigo, :nombre) ON CONFLICT (codigo) DO NOTHING"
                ),
                {"codigo": codigo, "nombre": nombre},
            )
        except Exception:
            # Table may not exist on very old DB — ensure it exists then retry
            db.rollback()
            db.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS maestros_canales_venta (id SERIAL PRIMARY KEY, codigo VARCHAR(50) UNIQUE NOT NULL, nombre VARCHAR(100) NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
                )
            )
            db.execute(
                text(
                    "INSERT INTO maestros_canales_venta (codigo, nombre) VALUES (:codigo, :nombre) ON CONFLICT (codigo) DO NOTHING"
                ),
                {"codigo": codigo, "nombre": nombre},
            )
    db.commit()


def seed_metodos_pago(db) -> None:
    """Idempotent seed for maestros_metodos_pago — mirrors 0010 Alembic."""
    for codigo, nombre in METODOS_PAGO:
        try:
            db.execute(
                text(
                    "INSERT INTO maestros_metodos_pago (codigo, nombre) VALUES (:codigo, :nombre) ON CONFLICT (codigo) DO NOTHING"
                ),
                {"codigo": codigo, "nombre": nombre},
            )
        except Exception:
            db.rollback()
            db.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS maestros_metodos_pago (id SERIAL PRIMARY KEY, codigo VARCHAR(50) UNIQUE NOT NULL, nombre VARCHAR(100) NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
                )
            )
            db.execute(
                text(
                    "INSERT INTO maestros_metodos_pago (codigo, nombre) VALUES (:codigo, :nombre) ON CONFLICT (codigo) DO NOTHING"
                ),
                {"codigo": codigo, "nombre": nombre},
            )
    db.commit()


def run() -> None:
    admin_email = os.getenv("ARPIA_ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL)
    admin_password = os.getenv("ARPIA_ADMIN_PASSWORD")
    with SessionLocal() as db:
        seed_usuarios(db, admin_email, admin_password)
        seed_categorias(db)
        seed_canales_venta(db)
        seed_metodos_pago(db)
    print("Seeder completed successfully.")


if __name__ == "__main__":
    run()
