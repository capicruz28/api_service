# app/schemas/costura.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# --- Esquema para un item individual del reporte de eficiencia de costura ---
class EficienciaCosturaItemSchema(BaseModel):
    # Nombres descriptivos que coinciden con los alias del SP modificado
    orden_produccion: str
    codigo_seccion: Optional[str] = None
    codigo_trabajador: str
    nombre_trabajador: Optional[str] = None
    codigo_operacion: str
    nombre_operacion: Optional[str] = None
    cantidad_prendas_producidas: int
    bloque: Optional[str] = None
    linea: Optional[str] = None
    tiempo_estandar_minutos_prenda: float
    importe_destajo_total: Optional[float] = None
    minutos_disponibles_jornada: float
    minutos_producidos_total: float
    nombre_maquina: Optional[str] = None
    codigo_categoria_operacion: Optional[str] = None
    fecha_proceso: date
    codigo_proceso_ticket: Optional[str] = None
    nombre_proceso_ticket: Optional[str] = None
    precio_venta_orden: Optional[float] = None

    # Campo calculado en el backend (si es necesario, o si quieres asegurar el cálculo aquí)
    eficiencia_porcentaje: Optional[float] = None

    class Config:
        from_attributes = True


# --- Esquema para la respuesta completa del reporte de eficiencia de costura ---
class ReporteEficienciaCosturaResponseSchema(BaseModel):
    fecha_inicio_reporte: date
    fecha_fin_reporte: date
    datos_reporte: List[EficienciaCosturaItemSchema]
    total_prendas_producidas_periodo: Optional[int] = None
    total_minutos_producidos_periodo: Optional[float] = None
    total_minutos_disponibles_periodo: Optional[float] = None # Suma de minutos disponibles únicos
    eficiencia_promedio_general_periodo: Optional[float] = None
    debug_note: Optional[str] = Field(None, description="Nota adicional para debugging, por ejemplo, si los datos fueron limitados.")

    class Config:
        from_attributes = True