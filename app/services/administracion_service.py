# app/services/administracion_service.py
import asyncio
import time
from decimal import Decimal
from typing import List, Dict, Any
from app.db.queries import execute_procedure
from app.db.connection import DatabaseConnection
from app.schemas.administracion import CuentaCobrarPagarBase
from app.core.exceptions import ServiceError
try:
    from app.core.exceptions import DatabaseError
except ImportError:
    DatabaseError = Exception

import logging

logger = logging.getLogger(__name__)

async def get_cuentas_cobrar_pagar() -> List[CuentaCobrarPagarBase]:
    logger.info("Servicio Administración: Iniciando obtención de cuentas por cobrar y pagar.")

    total_service_start_time = time.time()

    try:
        stored_procedure_name = "dbo.sp_administracion_obtener_cuentas_cobrar_pagar"

        logger.debug(f"Servicio Administración: Llamando SP: {stored_procedure_name}")

        db_call_start_time = time.time()
        raw_data_list: List[Dict[str, Any]] = await asyncio.to_thread(
            execute_procedure,
            stored_procedure_name,
            DatabaseConnection.ADMIN
        )
        db_call_end_time = time.time()
        logger.info(f"Servicio Administración: Llamada a DB (asyncio.to_thread + execute_procedure) tomó: {db_call_end_time - db_call_start_time:.4f} segundos.")
        logger.info(f"Servicio Administración: Datos crudos recibidos del SP: {len(raw_data_list)} filas.")

        if not raw_data_list:
            logger.info("Servicio Administración: No se encontraron datos para el reporte.")
            return []

        python_processing_start_time = time.time()

        cuentas: List[CuentaCobrarPagarBase] = []
        for i, row in enumerate(raw_data_list):
            try:
                moneda = row['moneda'] if row['moneda'] is not None else ""

                cuenta = CuentaCobrarPagarBase(
                    tipo_cuenta=row['tipo_cuenta'],
                    codigo_cliente_proveedor=row['codigo_cliente_proveedor'],
                    cliente_proveedor=row['cliente_proveedor'],
                    cuenta_contable=row['cuenta_contable'],
                    tipo_comprobante=row['tipo_comprobante'],
                    serie_comprobante=row['serie_comprobante'],
                    numero_comprobante=row['numero_comprobante'],
                    fecha_comprobante=row['fecha_comprobante'],
                    tipo_cambio=Decimal(str(row['tipo_cambio'])) if row['tipo_cambio'] else None,
                    moneda=moneda,
                    importe_soles=Decimal(str(row['importe_soles'])) if row['importe_soles'] else None,
                    importe_dolares=Decimal(str(row['importe_dolares'])) if row['importe_dolares'] else None,
                    importe_moneda_funcional=Decimal(str(row['importe_moneda_funcional'])) if row['importe_moneda_funcional'] else None,
                    fecha_vencimiento=row['fecha_vencimiento'],
                    fecha_ultimo_pago=row['fecha_ultimo_pago'],
                    tipo_venta=row['tipo_venta'],
                    usuario=row['usuario'],
                    observacion=row['observacion'],
                    descripcion_comprobante=row['descripcion_comprobante'],
                    servicio=row['servicio'],
                    importe_original=Decimal(str(row['importe_original'])) if row['importe_original'] else None,
                    codigo_responsable=row['codigo_responsable'],
                    responsable=row['responsable'],
                    empresa=row['empresa'],
                    ruta_comprobante_pdf=row['ruta_comprobante_pdf'],
                    semana=row['semana'],
                    semana_ajustada=row['semana_ajustada'],
                    pendiente_cobrar=row['pendiente_cobrar']
                )
                cuentas.append(cuenta)
            except Exception as e:
                logger.error(f"Servicio Administración: Error procesando fila #{i}: {row}. Error: {e}", exc_info=True)

        python_processing_end_time = time.time()
        logger.info(f"Servicio Administración: Procesamiento de datos en Python tomó: {python_processing_end_time - python_processing_start_time:.4f} segundos.")

        total_service_end_time = time.time()
        logger.info(f"Servicio Administración: Tiempo total de ejecución de get_cuentas_cobrar_pagar: {total_service_end_time - total_service_start_time:.4f} segundos.")

        logger.info("Servicio Administración: Cuentas por cobrar y pagar generadas exitosamente.")
        return cuentas

    except DatabaseError as db_err:
        logger.error(f"Servicio Administración: DatabaseError al obtener cuentas: {getattr(db_err, 'detail', str(db_err))}", exc_info=True)
        raise ServiceError(
            status_code=500,
            detail=f"Error de base de datos al obtener cuentas por cobrar y pagar: {getattr(db_err, 'detail', str(db_err))}"
        )
    except ServiceError as se:
        logger.warning(f"Servicio Administración: ServiceError: {se.detail}", exc_info=True)
        raise se
    except Exception as e:
        logger.error(f"Servicio Administración: Error inesperado: {e}", exc_info=True)
        raise ServiceError(
            status_code=500,
            detail=f"Error interno del servidor al obtener cuentas por cobrar y pagar: {str(e)}"
        )