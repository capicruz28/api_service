# app/api/v1/endpoints/costura.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from datetime import date
from typing import Annotated, Optional # <--- AÑADIR Optional

# Asegúrate que ReporteEficienciaCosturaResponseSchema se importe desde el lugar correcto
from app.schemas.costura import ReporteEficienciaCosturaResponseSchema, EficienciaCosturaItemSchema # <--- Añadir EficienciaCosturaItemSchema si es necesario para recalcular
from app.services import costura_service
from app.api.deps import get_current_active_user
from app.schemas.usuario import UsuarioReadWithRoles
from app.core.exceptions import ServiceError

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/reporte/eficiencia",
    response_model=ReporteEficienciaCosturaResponseSchema,
    summary="Reporte de Eficiencia del Área de Costura",
    description="Obtiene un reporte detallado de la eficiencia en el área de costura para un rango de fechas."
)
async def get_reporte_eficiencia_costura(
    current_user: Annotated[UsuarioReadWithRoles, Depends(get_current_active_user)],
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    # --- NUEVO PARÁMETRO OPCIONAL ---
    debug_limit: Optional[int] = Query(
        None,
        description="Opcional: Limita el número de registros en 'datos_reporte' para debugging en Swagger. No usar en producción. Los totales generales NO se recalcularán.",
        ge=1 # Opcional: asegurar que el límite sea al menos 1 si se proporciona
    )
):
    log_message_suffix = f"{f' con debug_limit: {debug_limit}' if debug_limit is not None else ''}"
    logger.info(f"Endpoint Costura: GET /reporte/eficiencia de usuario: {current_user.nombre_usuario} para: {fecha_inicio} a {fecha_fin}{log_message_suffix}")

    if fecha_inicio > fecha_fin:
        logger.warning(f"Endpoint Costura: Fechas inválidas - inicio: {fecha_inicio}, fin: {fecha_fin}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de inicio no puede ser posterior a la fecha de fin."
        )

    try:
        # 1. Obtener el reporte completo del servicio
        reporte_completo: ReporteEficienciaCosturaResponseSchema = await costura_service.generar_reporte_eficiencia(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        # 2. Aplicar el debug_limit si se proporcionó
        if debug_limit is not None and reporte_completo.datos_reporte:
            if len(reporte_completo.datos_reporte) > debug_limit:
                logger.info(f"Aplicando debug_limit: {debug_limit}. Devolviendo los primeros {debug_limit} de {len(reporte_completo.datos_reporte)} items.")

                datos_limitados = reporte_completo.datos_reporte[:debug_limit]

                # --- Decisión sobre los totales ---
                # Opción 1 (Actual): No recalcular totales. Los totales reflejan el conjunto completo.
                # La descripción del parámetro debug_limit ya lo advierte.
                # El debug_note también lo aclarará.

                # Opción 2 (Más compleja): Recalcular totales basados en 'datos_limitados'.
                # Esto requeriría una lógica similar a la del servicio aquí en el endpoint.
                # Por ejemplo:
                # sum_total_prendas_limitado = sum(item.cantidad_prendas_producidas for item in datos_limitados)
                # sum_total_min_producidos_limitado = sum(item.minutos_producidos_total for item in datos_limitados)
                # ... y así sucesivamente para los otros totales y la eficiencia promedio.
                # Esto haría la respuesta limitada más autoconsistente pero añade duplicación de lógica.

                # Por ahora, seguimos con la Opción 1 (sin recalcular totales).

                reporte_para_devolver = ReporteEficienciaCosturaResponseSchema(
                    fecha_inicio_reporte=reporte_completo.fecha_inicio_reporte,
                    fecha_fin_reporte=reporte_completo.fecha_fin_reporte,
                    datos_reporte=datos_limitados, # <--- Datos limitados
                    total_prendas_producidas_periodo=reporte_completo.total_prendas_producidas_periodo, # Total del conjunto completo
                    total_minutos_producidos_periodo=reporte_completo.total_minutos_producidos_periodo, # Total del conjunto completo
                    total_minutos_disponibles_periodo=reporte_completo.total_minutos_disponibles_periodo, # Total del conjunto completo
                    eficiencia_promedio_general_periodo=reporte_completo.eficiencia_promedio_general_periodo, # Total del conjunto completo
                    debug_note=f"Resultados limitados a los primeros {debug_limit} registros para debugging. Los totales generales corresponden al conjunto completo de {len(reporte_completo.datos_reporte)} registros."
                )
                logger.info(f"Endpoint Costura: Reporte de eficiencia (limitado) generado exitosamente.")
                return reporte_para_devolver
            else:
                # El límite es mayor o igual al número de items, o no hay items para limitar.
                # Se añade una nota si debug_limit fue especificado pero no resultó en truncamiento.
                if reporte_completo.datos_reporte:
                     reporte_completo.debug_note = f"debug_limit ({debug_limit}) especificado, pero no se truncaron datos (total items: {len(reporte_completo.datos_reporte)})."
                else:
                     reporte_completo.debug_note = f"debug_limit ({debug_limit}) especificado, pero no hay datos en el reporte."


        logger.info(f"Endpoint Costura: Reporte de eficiencia (completo) generado exitosamente.")
        return reporte_completo # Devuelve el reporte completo si no se aplicó el límite

    except ServiceError as se:
        logger.error(f"Endpoint Costura: ServiceError al generar reporte: {se.detail}", exc_info=True)
        raise HTTPException(
            status_code=se.status_code,
            detail=se.detail
        )
    except HTTPException as http_exc:
        logger.warning(f"Endpoint Costura: HTTPException propagada: {http_exc.detail}", exc_info=True)
        raise http_exc
    except Exception as e:
        logger.exception(f"Endpoint Costura: Error inesperado al generar reporte: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno del servidor al procesar la solicitud del reporte de costura."
        )