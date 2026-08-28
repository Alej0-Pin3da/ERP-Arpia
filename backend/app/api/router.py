from fastapi import APIRouter

from app.api.routes import (
    analiticos,
    audit,
    auth,
    bom,
    categorias_insumos,
    clientes,
    compras_insumos,
    costos,
    devoluciones,
    finanzas,
    insumos,
    maestros,
    omisiones,
    produccion,
    productos,
    tipos_productos,
    usuarios,
    ventas,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(categorias_insumos.router)
api_router.include_router(insumos.router)
api_router.include_router(compras_insumos.router)
api_router.include_router(clientes.router)
api_router.include_router(productos.router)
api_router.include_router(bom.router)
api_router.include_router(costos.router)
api_router.include_router(tipos_productos.router)
api_router.include_router(usuarios.router)
api_router.include_router(ventas.router)
api_router.include_router(devoluciones.router)
api_router.include_router(finanzas.router)
api_router.include_router(analiticos.router)
api_router.include_router(omisiones.router)
api_router.include_router(maestros.router)
api_router.include_router(produccion.router_prendas)
api_router.include_router(produccion.router_pedidos)
api_router.include_router(audit.router)


@api_router.get("/__mode", tags=["mode"])
def get_mode():
    return {
        "mode": "real",
        "db_connected": True,
        "version": "V4",
    }
