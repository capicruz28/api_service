# app/services/costura_service.py
import asyncio
import time
import json # --- NUEVO ---
from datetime import date
from typing import List, Dict, Any
from app.db.queries import execute_procedure_params
from app.schemas.costura import (
    EficienciaCosturaItemSchema,
    ReporteEficienciaCosturaResponseSchema
)
from app.core.exceptions import ServiceError
try:
    from app.core.exceptions import DatabaseError
except ImportError:
    DatabaseError = Exception

import logging

logger = logging.getLogger(__name__)

async def generar_reporte_eficiencia(
    fecha_inicio: date,
    fecha_fin: date
) -> ReporteEficienciaCosturaResponseSchema:
    logger.info(f"Servicio Costura: Iniciando reporte de eficiencia para: {fecha_inicio} a {fecha_fin}")

    total_service_start_time = time.time()

    try:
        stored_procedure_name = "dbo.sp_costura_eficiencia_web"
        sp_params = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        }

        logger.debug(f"Servicio Costura: Llamando SP: {stored_procedure_name} con params: {sp_params}")

        db_call_start_time = time.time()
        raw_data_list: List[Dict[str, Any]] = await asyncio.to_thread(
            execute_procedure_params,
            stored_procedure_name,
            sp_params
        )
        db_call_end_time = time.time()
        logger.info(f"Servicio Costura: Llamada a DB (asyncio.to_thread + execute_procedure_params) tomó: {db_call_end_time - db_call_start_time:.4f} segundos.")
        logger.info(f"Servicio Costura: Datos crudos recibidos del SP: {len(raw_data_list)} filas.")

        if not raw_data_list:
            logger.info("Servicio Costura: No se encontraron datos para el reporte.")
            return ReporteEficienciaCosturaResponseSchema(
                fecha_inicio_reporte=fecha_inicio,
                fecha_fin_reporte=fecha_fin,
                datos_reporte=[],
                total_prendas_producidas_periodo=0,
                total_minutos_producidos_periodo=0.0,
                total_minutos_disponibles_periodo=0.0,
                eficiencia_promedio_general_periodo=0.0
            )

        python_processing_start_time = time.time()

        items_procesados: List[EficienciaCosturaItemSchema] = []
        sum_total_prendas = 0
        sum_total_min_producidos = 0.0
        min_disponibles_unicos_tracker = {}
        sum_total_min_disponibles_unicos = 0.0

        for i, row_dict in enumerate(raw_data_list):
            try:
                item_data = EficienciaCosturaItemSchema.parse_obj(row_dict)

                if item_data.minutos_disponibles_jornada is not None and item_data.minutos_disponibles_jornada > 0:
                    item_data.eficiencia_porcentaje = round(
                        (item_data.minutos_producidos_total / item_data.minutos_disponibles_jornada) * 100, 2
                    )
                else:
                    item_data.eficiencia_porcentaje = 0.0
                items_procesados.append(item_data)
                sum_total_prendas += item_data.cantidad_prendas_producidas
                sum_total_min_producidos += item_data.minutos_producidos_total
                tracker_key = (item_data.codigo_trabajador, item_data.fecha_proceso)
                if tracker_key not in min_disponibles_unicos_tracker:
                    minutos_jornada_actual = item_data.minutos_disponibles_jornada or 0.0
                    min_disponibles_unicos_tracker[tracker_key] = minutos_jornada_actual
                    sum_total_min_disponibles_unicos += minutos_jornada_actual
            except Exception as e:
                logger.error(f"Servicio Costura: Error procesando fila #{i}: {row_dict}. Error: {e}", exc_info=True)

        eficiencia_general_promedio = 0.0
        if sum_total_min_disponibles_unicos > 0:
            eficiencia_general_promedio = round(
                (sum_total_min_producidos / sum_total_min_disponibles_unicos) * 100, 2
            )

        python_processing_end_time = time.time()
        logger.info(f"Servicio Costura: Procesamiento de datos en Python (bucle y Pydantic) tomó: {python_processing_end_time - python_processing_start_time:.4f} segundos.")

        response_object_creation_start_time = time.time()
        response = ReporteEficienciaCosturaResponseSchema(
            fecha_inicio_reporte=fecha_inicio,
            fecha_fin_reporte=fecha_fin,
            datos_reporte=items_procesados,
            total_prendas_producidas_periodo=sum_total_prendas,
            total_minutos_producidos_periodo=round(sum_total_min_producidos, 2),
            total_minutos_disponibles_periodo=round(sum_total_min_disponibles_unicos, 2),
            eficiencia_promedio_general_periodo=eficiencia_general_promedio
        )
        response_object_creation_end_time = time.time()
        logger.info(f"Servicio Costura: Creación del objeto de respuesta Pydantic tomó: {response_object_creation_end_time - response_object_creation_start_time:.4f} segundos.")

        # --- NUEVO: Medir serialización a JSON y tamaño ---
        json_serialization_start_time = time.time()
        json_output = "{}" # Fallback
        json_size_bytes = 0
        try:
            # Para Pydantic v2 (recomendado con FastAPI moderno):
            if hasattr(response, 'model_dump_json'):
                json_output = response.model_dump_json()
            # Para Pydantic v1 (si estás en una versión más antigua):
            elif hasattr(response, 'json'):
                json_output = response.json() # type: ignore
            else:
                logger.warning("Servicio Costura: El objeto de respuesta no tiene 'model_dump_json()' ni 'json()'. No se puede serializar para medir.")
                # Como fallback, intentamos con el módulo json estándar, aunque no es lo que FastAPI usaría directamente con Pydantic.
                # Esto es solo para tener una idea del tamaño si los métodos de Pydantic no están.
                # Necesitarías convertir el objeto Pydantic a dict primero si usas json.dumps directamente.
                # Por ahora, lo dejamos simple. La idea es que uno de los métodos de Pydantic debería existir.
                pass # json_output sigue siendo "{}"

            if json_output != "{}": # Solo calcular tamaño si la serialización tuvo éxito
                json_size_bytes = len(json_output.encode('utf-8'))
                logger.info(f"Servicio Costura: Tamaño estimado del JSON de respuesta: {json_size_bytes / (1024*1024):.2f} MB ({json_size_bytes} bytes)")
            else:
                logger.info("Servicio Costura: No se pudo serializar la respuesta para medir el tamaño del JSON.")

        except Exception as e:
            logger.error(f"Servicio Costura: Error al intentar serializar a JSON para medir: {e}", exc_info=True)

        json_serialization_end_time = time.time()
        logger.info(f"Servicio Costura: Serialización del objeto de respuesta a JSON (dentro del servicio) tomó: {json_serialization_end_time - json_serialization_start_time:.4f} segundos.")
        # --- FIN NUEVO ---

        total_service_end_time = time.time() # --- MODIFICADO: Mover esta línea después de la medición JSON ---
        logger.info(f"Servicio Costura: Tiempo total de ejecución de generar_reporte_eficiencia (incluyendo medición JSON): {total_service_end_time - total_service_start_time:.4f} segundos.")

        logger.info("Servicio Costura: Reporte de eficiencia generado exitosamente.")
        return response

    except DatabaseError as db_err:
        logger.error(f"Servicio Costura: DatabaseError al generar reporte: {getattr(db_err, 'detail', str(db_err))}", exc_info=True)
        raise ServiceError(
            status_code=500,
            detail=f"Error de base de datos al generar el reporte de costura: {getattr(db_err, 'detail', str(db_err))}"
        )
    except ServiceError as se:
        logger.warning(f"Servicio Costura: ServiceError: {se.detail}", exc_info=True)
        raise se
    except Exception as e:
        logger.error(f"Servicio Costura: Error inesperado al generar reporte: {e}", exc_info=True)
        raise ServiceError(
            status_code=500,
            detail=f"Error interno del servidor al generar el reporte de costura: {str(e)}"
        )