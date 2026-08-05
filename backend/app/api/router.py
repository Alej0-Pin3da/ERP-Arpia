from fastapi import APIRouter

from app.api.routes import (
    auth,
    categorias_insumos,
    clientes,
    insumos,
    proveedores,
    usuarios,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(proveedores.router)
api_router.include_router(categorias_insumos.router)
api_router.include_router(insumos.router)
api_router.include_router(clientes.router)
api_router.include_router(usuarios.router)