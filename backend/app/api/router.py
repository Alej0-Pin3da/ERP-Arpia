from fastapi import APIRouter

from app.api.routes import (
    auth,
    categorias_insumos,
    clientes,
    compras_insumos,
    insumos,
    productos,
    proveedores,
    tipos_productos,
    usuarios,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(proveedores.router)
api_router.include_router(categorias_insumos.router)
api_router.include_router(insumos.router)
api_router.include_router(compras_insumos.router)
api_router.include_router(clientes.router)
api_router.include_router(productos.router)
api_router.include_router(tipos_productos.router)
api_router.include_router(usuarios.router)