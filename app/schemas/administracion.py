# app/schemas/administracion.py
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

class CuentaCobrarPagarBase(BaseModel):
    tipo_cuenta: str
    codigo_cliente_proveedor: str
    cliente_proveedor: str
    cuenta_contable: str
    tipo_comprobante: str
    serie_comprobante: str
    numero_comprobante: str
    fecha_comprobante: Optional[datetime]
    tipo_cambio: Optional[Decimal]
    moneda: Optional[str] = Field(default="")
    importe_soles: Optional[Decimal]
    importe_dolares: Optional[Decimal]
    importe_moneda_funcional: Optional[Decimal]
    fecha_vencimiento: Optional[datetime]
    fecha_ultimo_pago: Optional[datetime]
    tipo_venta: Optional[str]
    usuario: Optional[str]
    observacion: Optional[str]
    descripcion_comprobante: Optional[str]
    servicio: Optional[str]
    importe_original: Optional[Decimal]
    codigo_responsable: Optional[str]
    responsable: Optional[str]
    empresa: str
    ruta_comprobante_pdf: Optional[str]
    semana: Optional[str]
    semana_ajustada: Optional[str]
    pendiente_cobrar: Optional[Decimal]

class CuentaCobrarPagarResponse(BaseModel):
    status: bool = True
    message: str = "Proceso ejecutado correctamente"
    data: List[CuentaCobrarPagarBase]
    debug_note: Optional[str] = None

    class Config:
        from_attributes = True