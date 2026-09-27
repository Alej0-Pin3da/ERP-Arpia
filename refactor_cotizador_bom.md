IMPLEMENTACIÓN DE LISTA DINÁMICA DE MATERIALES (BOM) EN COTIZADOR ARPIA ERP
Documento de especificación técnica de arquitectura, modelo de datos y diseño de interfaz para la refactorización del módulo de cotizaciones.
1. Contexto y Objetivos
El módulo actual de cotizaciones depende de estructuras fijas para los insumos de confección (limitado a campos estáticos como tela y forro). Esta arquitectura no refleja la complejidad real del proceso textil, el cual requiere flexibilidad para incluir $N$ cantidad de insumos por prenda (telas, forros, avíos, cierres, botones, marquillas, etc.), replicando el comportamiento dinámico del modelo original alojado en Google Sheets.
Objetivos Clave
Flexibilidad Operativa: Permitir una estructura dinámica de materiales por cotización sin restricciones de tipo o cantidad.
Inmutabilidad Histórica: Garantizar que los cambios en el catálogo maestro de insumos no alteren las cotizaciones emitidas previamente.
Precisión Financiera: Eliminar imprecisiones por coma flotante mediante el uso estricto del tipo de dato Decimal en el cálculo de costos y márgenes.


2. Paso 1: Backend - Migración de Base de Datos (SQLAlchemy & Alembic)
Se requiere modificar el modelo de datos Cotizacion para reemplazar las columnas fijas por una columna de tipo documento JSON estructurado.
Cambios en SQLAlchemy
Agregar la columna insumos_detalle utilizando el tipo JSONB de PostgreSQL:from sqlalchemy import Column

from sqlalchemy.dialects.postgresql import JSONB

class Cotizacion(Base):

    __tablename__ = "cotizaciones"

    

    # ... otros campos ...

    insumos_detalle = Column(JSONB, nullable=True, server_default='[]')
Script de Migración Alembic
La migración debe eliminar las columnas estáticas en desuso y agregar el nuevo campo de almacenamiento dinámico:def upgrade():

    # Agregar nueva columna JSONB

    op.add_column('cotizaciones', sa.Column('insumos_detalle', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True))

    

    # Drop de columnas estáticas en desuso

    op.drop_column('cotizaciones', 'metros_tela')

    op.drop_column('cotizaciones', 'precio_metro_tela')

    op.drop_column('cotizaciones', 'metros_forro')

    op.drop_column('cotizaciones', 'precio_metro_forro')

def downgrade():

    # Reversión de esquema

    op.add_column('cotizaciones', sa.Column('precio_metro_forro', sa.NUMERIC(), autoincrement=False, nullable=True))

    op.add_column('cotizaciones', sa.Column('metros_forro', sa.NUMERIC(), autoincrement=False, nullable=True))

    op.add_column('cotizaciones', sa.Column('precio_metro_tela', sa.NUMERIC(), autoincrement=False, nullable=True))

    op.add_column('cotizaciones', sa.Column('metros_tela', sa.NUMERIC(), autoincrement=False, nullable=True))

    op.drop_column('cotizaciones', 'insumos_detalle')


3. Paso 2: Backend - Esqueletos de Validación (Pydantic Schemas)
Definición de modelos de validación con parseo automático a Decimal para evitar imprecisiones financieras.from decimal import Decimal

from pydantic import BaseModel, Field

class InsumoCotizacion(BaseModel):

    nombre: str = Field(..., description="Nombre del insumo o material")

    cantidad: Decimal = Field(..., gt=0, description="Cantidad requerida por prenda")

    precio_unitario: Decimal = Field(..., ge=0, description="Costo unitario del insumo")

    unidad_medida: str = Field(..., description="Unidad de medida (ej: metros, unidades, yardas)")

    desperdicio_pct: Decimal = Field(default=Decimal('0.00'), ge=0, description="Porcentaje de desperdicio aplicado")

    class Config:

        json_encoders = {

            Decimal: lambda v: str(v)

        }

class CotizacionCreate(BaseModel):

    # ... otros campos de la cotización ...

    insumos: list[InsumoCotizacion] = Field(default_factory=list, description="Lista dinámica de insumos")


4. Paso 3: Backend - Lógica de Cálculo (cotizaciones.py)
Actualización de la función interna _calcular para iterar dinámicamente sobre la lista de insumos.from decimal import Decimal, ROUND_HALF_UP

def _calcular(payload: CotizacionCreate) -> dict:

    subtotal_materiales = Decimal('0.00')

    

    for insumo in payload.insumos:

        # Cálculo del desperdicio: cantidad * (1 + % desperdicio / 100)

        factor_desperdicio = Decimal('1.00') + (insumo.desperdicio_pct / Decimal('100.00'))

        cantidad_efectiva = insumo.cantidad * factor_desperdicio

        

        # Subtotal por insumo

        costo_insumo = cantidad_efectiva * insumo.precio_unitario

        subtotal_materiales += costo_insumo

    # Redondeo financiero estándar

    subtotal_materiales = subtotal_materiales.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    

    # Procesamiento posterior de hilos, mano de obra y márgenes...

    return {

        "subtotal_materiales": subtotal_materiales,

        "insumos_procesados": [i.dict() for i in payload.insumos]

    }


5. Paso 4: Frontend - Componente Vue 3 (CotizadorView.vue)
Sustitución de variables reactivas estáticas por un estado reactivo basado en arreglos y hooks computados.
Lógica de JavaScript (<script setup>)
import { ref, computed } from 'vue'

interface InsumoCotizacion {

  nombre: string

  cantidad: number

  precio_unitario: number

  unidad_medida: string

  desperdicio_pct: number

}

const insumos = ref<InsumoCotizacion[]>([])

const agregarInsumo = () => {

  insumos.value.push({

    nombre: '',

    cantidad: 0,

    precio_unitario: 0,

    unidad_medida: 'metros',

    desperdicio_pct: 0

  })

}

const eliminarInsumo = (index: number) => {

  insumos.value.splice(index, 1)

}

const subtotalTelas = computed(() => {

  return insumos.value.reduce((acc, item) => {

    const cantidadConDesperdicio = item.cantidad * (1 + (item.desperdicio_pct / 100))

    return acc + (cantidadConDesperdicio * item.precio_unitario)

  }, 0)

})
Interfaz de Usuario (<template>)
<div class="bom-container">

  <h3>Lista de Materiales (BOM)</h3>

  

  <div v-for="(insumo, idx) in insumos" :key="idx" class="insumo-row">

    <input type="text" v-model="insumo.nombre" placeholder="Nombre del insumo" />

    <input type="number" step="0.01" v-model.number="insumo.cantidad" placeholder="Cantidad" />

    <select v-model="insumo.unidad_medida">

      <option value="metros">Metros</option>

      <option value="unidades">Unidades</option>

      <option value="yardas">Yardas</option>

      <option value="kilos">Kilos</option>

    </select>

    <input type="number" step="0.01" v-model.number="insumo.precio_unitario" placeholder="Precio U." />

    <input type="number" step="0.1" v-model.number="insumo.desperdicio_pct" placeholder="% Desp." />

    <button type="button" @click="eliminarInsumo(idx)">Eliminar</button>

  </div>

  <button type="button" @click="agregarInsumo">Añadir Insumo</button>

  

  <div class="summary">

    <strong>Subtotal Materiales:</strong> {{ subtotalTelas.toFixed(2) }}

  </div>

</div>


6. Mejoras Detectadas y Decisiones de Arquitectura
Área
Riesgo / Limitación Previa
Solución Implementada
Backend
Pérdida de precisión centesimal por el uso de float de Python.
Conversión forzada a Decimal desde la capa de validación Pydantic y operaciones matemáticas de precisión fija.
Frontend
Pérdida de granularidad al importar recetas de base de datos (cargarBaseBom).
Poblamiento dinámico del arreglo insumos respetando la estructura completa del BOM en lugar de condensar valores.
Base de Datos
Inconsistencia en cotizaciones históricas si un insumo del catálogo principal cambia de precio o se elimina.
El campo JSONB actúa como una captura de estado (snapshot) inmutable en el tiempo del costo y tipo de material usado en esa cotización específica.


