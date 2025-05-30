# app/api/v1/endpoints/administracion.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Annotated, Optional
from app.schemas.administracion import CuentaCobrarPagarResponse, CuentaCobrarPagarBase
from app.services import administracion_service
from app.api.deps import get_current_active_user
from app.schemas.usuario import UsuarioReadWithRoles
from app.core.exceptions import ServiceError

from fastapi.responses import FileResponse
import urllib.parse
from pathlib import Path
import os

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/pdf")
async def servir_pdf(
    current_user: Annotated[UsuarioReadWithRoles, Depends(get_current_active_user)],
    ruta: str = Query(..., description="Ruta del PDF codificada en URL")
):
    """
    Servir archivos PDF de manera segura desde rutas de red.
    Parámetros:
    - ruta: Ruta del archivo codificada (ej: %2Fperufashions1%2Fdoc.pdf)
    - current_user: Usuario autenticado (manejado automáticamente por Depends)
    """
    try:
        # Decodificar y normalizar ruta
        # Asegúrate de que la ruta que llega del frontend esté codificada en URL
        ruta_decodificada = urllib.parse.unquote(ruta)

        # Normalizar barras invertidas a barras normales
        ruta_normalizada_str = ruta_decodificada.replace('\\', '/')

        # Opcional pero recomendado: Validar que la ruta esté dentro de un directorio permitido
        # Esto es crucial por seguridad. Define una o más carpetas raíz permitidas.
        # Ejemplo:
        # DIRECTORIOS_PERMITIDOS = ["//servidor/carpeta_pdfs", "//otro_servidor/archivos"]
        # if not any(ruta_normalizada_str.startswith(dir_permitido.replace('\\', '/')) for dir_permitido in DIRECTORIOS_PERMITIDOS):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Acceso denegado a la ruta especificada."
        #     )

        ruta_normalizada = Path(ruta_normalizada_str)

        # Validar existencia
        if not ruta_normalizada.exists():
            logger.warning(f"Archivo no encontrado al intentar servir PDF: {ruta_normalizada}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archivo no encontrado: {ruta_normalizada}"
            )

        # Servir archivo
        logger.info(f"Sirviendo archivo PDF desde: {ruta_normalizada}")
        return FileResponse(
            ruta_normalizada,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline"} # 'inline' para mostrar en el navegador, 'attachment' para descargar
        )

    except HTTPException:
        # Si ya es una HTTPException, la relanzamos
        raise
    except Exception as e:
        logger.error(f"Error inesperado al servir PDF desde {ruta}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al procesar el PDF"
        )

@router.get(
    "/cuentas-cobrar-pagar",
    response_model=CuentaCobrarPagarResponse,
    summary="Reporte de Cuentas por Cobrar y Pagar",
    description="Obtiene un reporte detallado de las cuentas por cobrar y pagar consolidadas de PF y FKS."
)
async def obtener_cuentas_cobrar_pagar(
    current_user: Annotated[UsuarioReadWithRoles, Depends(get_current_active_user)],
    debug_limit: Optional[int] = Query(
        None,
        description="Opcional: Limita el número de registros para debugging en Swagger. No usar en producción.",
        ge=1
    )
):
    log_message_suffix = f"{f' con debug_limit: {debug_limit}' if debug_limit is not None else ''}"
    logger.info(f"Endpoint Administración: GET /cuentas-cobrar-pagar de usuario: {current_user.nombre_usuario}{log_message_suffix}")

    try:
        # Obtener datos completos del servicio
        cuentas_completas = await administracion_service.get_cuentas_cobrar_pagar()

        # Aplicar debug_limit si se proporcionó
        if debug_limit is not None and cuentas_completas:
            if len(cuentas_completas) > debug_limit:
                logger.info(f"Aplicando debug_limit: {debug_limit}. Devolviendo los primeros {debug_limit} de {len(cuentas_completas)} items.")

                cuentas_limitadas = cuentas_completas[:debug_limit]

                response = CuentaCobrarPagarResponse(
                    status=True,
                    message="Cuentas por cobrar y pagar obtenidas correctamente (versión limitada para debug)",
                    data=cuentas_limitadas,
                    debug_note=f"Resultados limitados a los primeros {debug_limit} registros para debugging. Total de registros disponibles: {len(cuentas_completas)}"
                )

                logger.info(f"Endpoint Administración: Reporte de cuentas (limitado) generado exitosamente.")
                return response
            else:
                # El límite es mayor o igual al número de items
                debug_note = f"debug_limit ({debug_limit}) especificado, pero no se truncaron datos (total items: {len(cuentas_completas)})."
        else:
            debug_note = None

        # Devolver respuesta completa
        response = CuentaCobrarPagarResponse(
            status=True,
            message="Cuentas por cobrar y pagar obtenidas correctamente",
            data=cuentas_completas,
            debug_note=debug_note
        )

        logger.info(f"Endpoint Administración: Reporte de cuentas (completo) generado exitosamente.")
        return response

    except ServiceError as se:
        logger.error(f"Endpoint Administración: ServiceError al obtener cuentas: {se.detail}", exc_info=True)
        raise HTTPException(
            status_code=se.status_code,
            detail=se.detail
        )
    except HTTPException as http_exc:
        logger.warning(f"Endpoint Administración: HTTPException propagada: {http_exc.detail}", exc_info=True)
        raise http_exc
    except Exception as e:
        logger.exception(f"Endpoint Administración: Error inesperado al obtener cuentas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno del servidor al procesar la solicitud de cuentas por cobrar y pagar."
        )