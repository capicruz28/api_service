# app/services/area_service.py

from typing import List, Optional, Dict, Any
import math
import logging
from app.schemas.area import AreaSimpleList

# Ajusta las rutas de importación según tu estructura
from app.db.queries import (
    execute_query, execute_insert, execute_update,
    # Importa las NUEVAS queries (asegúrate que COUNT_AREAS_QUERY tenga alias 'total_count')
    GET_AREAS_PAGINATED_QUERY, COUNT_AREAS_QUERY, GET_AREA_BY_ID_QUERY,
    CHECK_AREA_EXISTS_BY_NAME_QUERY, CREATE_AREA_QUERY,
    UPDATE_AREA_BASE_QUERY_TEMPLATE, TOGGLE_AREA_STATUS_QUERY,GET_ACTIVE_AREAS_SIMPLE_LIST_QUERY
)
# Importa los schemas necesarios
from app.schemas.area import AreaCreate, AreaUpdate, AreaRead, PaginatedAreaResponse
from app.core.exceptions import ServiceError # Usa tu excepción personalizada

logger = logging.getLogger(__name__)

# Asumimos que DatabaseError puede o no estar definida
try:
    # Intenta importar tu excepción de DB específica si existe
    from app.core.exceptions import DatabaseError
except ImportError:
    # Si no, usa la excepción genérica como fallback para el catch
    DatabaseError = Exception

class AreaService:

    @staticmethod
    async def _verificar_nombre_existente(nombre: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica si ya existe un área con el mismo nombre (insensible a mayúsculas), opcionalmente excluyendo un ID."""
        # Usa la query CHECK_AREA_EXISTS_BY_NAME_QUERY (con alias 'count')
        id_a_excluir = excluir_id if excluir_id is not None else -1
        params = (nombre.lower(), id_a_excluir)
        try:
            # Llama a execute_query SIN fetch_one.
            resultado_lista = execute_query(CHECK_AREA_EXISTS_BY_NAME_QUERY, params)
            if resultado_lista:
                # Accede al primer (y único) diccionario y luego al valor 'count'
                return resultado_lista[0].get('count', 0) > 0
            else:
                logger.warning("La consulta CHECK_AREA_EXISTS_BY_NAME_QUERY no devolvió resultados.")
                return False
        except KeyError:
             logger.error("Error al acceder a la clave 'count' en el resultado de CHECK_AREA_EXISTS_BY_NAME_QUERY. ¿Se definió el alias en la query?", exc_info=True)
             raise ServiceError(status_code=500, detail="Error interno al verificar nombre de área (formato respuesta DB).")
        except Exception as e:
            logger.error(f"Error al verificar nombre existente '{nombre}': {e}", exc_info=True)
            raise ServiceError(status_code=500, detail="Error interno al verificar nombre de área.")

    @staticmethod
    async def crear_area(area_data: AreaCreate) -> AreaRead:
        """Crea una nueva área en la tabla 'area_menu'."""
        logger.info(f"Intentando crear área: {area_data.nombre}")
        try:
            if await AreaService._verificar_nombre_existente(area_data.nombre):
                raise ServiceError(status_code=409, detail=f"Ya existe un área con el nombre '{area_data.nombre}'.")

            params = (
                area_data.nombre,
                area_data.descripcion,
                area_data.icono,
                area_data.es_activo
            )
            # Asume que execute_insert devuelve un diccionario del registro creado
            resultado_insert = execute_insert(CREATE_AREA_QUERY, params)
            if not resultado_insert:
                 raise ServiceError(status_code=500, detail="La inserción del área no devolvió el registro creado.")

            created_area = AreaRead(**resultado_insert)
            logger.info(f"Área '{created_area.nombre}' creada con ID: {created_area.area_id}")
            return created_area

        except DatabaseError as db_err:
            logger.error(f"Error de DB al crear área: {db_err}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error DB al crear área: {getattr(db_err, 'detail', str(db_err))}")
        except ServiceError as se:
             logger.warning(f"Conflicto al crear área: {se.detail}")
             raise se
        except Exception as e:
            logger.exception(f"Error inesperado al crear área: {e}")
            raise ServiceError(status_code=500, detail=f"Error interno al crear área: {str(e)}")

    @staticmethod
    async def obtener_area_por_id(area_id: int) -> Optional[AreaRead]:
        """Obtiene un área específica por su ID desde 'area_menu'."""
        logger.debug(f"Buscando área con ID: {area_id}")
        try:
            # Llama a execute_query SIN fetch_one.
            # Asume que devuelve una lista de diccionarios.
            resultado_lista = execute_query(GET_AREA_BY_ID_QUERY, (area_id,))
            # Si la lista no está vacía, toma el primer diccionario
            if resultado_lista:
                return AreaRead(**resultado_lista[0])
            else:
                logger.debug(f"Área con ID {area_id} no encontrada.")
                return None
        except Exception as e:
            logger.error(f"Error obteniendo área por ID {area_id}: {str(e)}", exc_info=True)
            # Considera lanzar ServiceError aquí también si la consulta falla
            # raise ServiceError(status_code=500, detail=f"Error interno al obtener área ID {area_id}.")
            return None # O mantener return None para que el endpoint maneje 404

    @staticmethod
    async def obtener_areas_paginadas(
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None
    ) -> PaginatedAreaResponse:
        """Obtiene una lista paginada y filtrada de áreas desde 'area_menu'."""
        logger.info(f"Obteniendo áreas paginadas: skip={skip}, limit={limit}, search='{search}'")
        search_param = f"%{search}%" if search else None
        where_params = (search, search_param, search_param)
        total_count = 0
        areas_lista: List[AreaRead] = []

        try:
            # 1. Obtener el conteo total filtrado
            # Llama a execute_query SIN fetch_one.
            # Asume que devuelve una lista con un diccionario: [{'total_count': N}]
            count_result_list = execute_query(COUNT_AREAS_QUERY, where_params)
            if count_result_list:
                # Accede al primer diccionario y obtiene 'total_count'
                total_count = count_result_list[0].get('total_count', 0)
            else:
                 logger.warning("La consulta COUNT_AREAS_QUERY no devolvió resultados.")
                 total_count = 0 # Asegura que sea 0 si no hay resultado

            # 2. Obtener los datos paginados si hay resultados y el límite es > 0
            if total_count > 0 and limit > 0:
                pagination_params = where_params + (skip, limit)
                # execute_query sin fetch_one devuelve una lista de diccionarios
                rows = execute_query(GET_AREAS_PAGINATED_QUERY, pagination_params)
                if rows:
                    for row_dict in rows:
                        try:
                            areas_lista.append(AreaRead(**row_dict))
                        except Exception as map_err:
                            logger.error(f"Error al mapear fila de área a AreaRead: {map_err}. Fila: {row_dict}", exc_info=True)

            # 3. Calcular detalles de paginación
            total_pages = math.ceil(total_count / limit) if limit > 0 else 0
            current_page = (skip // limit) + 1 if limit > 0 else 1

            return PaginatedAreaResponse(
                areas=areas_lista,
                total_areas=total_count,
                pagina_actual=current_page,
                total_paginas=total_pages
            )
        except KeyError:
             # Error si el alias 'total_count' no está presente
             logger.error("Error al acceder a la clave 'total_count' en el resultado de COUNT_AREAS_QUERY. ¿Se definió el alias en la query?", exc_info=True)
             raise ServiceError(status_code=500, detail="Error interno al obtener conteo de áreas (formato respuesta DB).")
        except DatabaseError as db_err:
            logger.error(f"Error de DB al obtener áreas paginadas: {db_err}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error DB al obtener áreas: {getattr(db_err, 'detail', str(db_err))}")
        except Exception as e:
            logger.exception(f"Error inesperado al obtener áreas paginadas: {e}")
            raise ServiceError(status_code=500, detail="Error interno al obtener áreas.")

    @staticmethod
    async def actualizar_area(area_id: int, area_data: AreaUpdate) -> AreaRead:
        """Actualiza un área existente en 'area_menu'."""
        logger.info(f"Intentando actualizar área ID: {area_id}")

        update_payload = area_data.model_dump(exclude_unset=True)
        if not update_payload:
             raise ServiceError(status_code=400, detail="No se proporcionaron datos para actualizar el área.")

        # Verificar que el área exista primero (usa el método corregido)
        area_existente = await AreaService.obtener_area_por_id(area_id)
        if not area_existente:
            raise ServiceError(status_code=404, detail=f"Área con ID {area_id} no encontrada para actualizar.")

        try:
            if 'nombre' in update_payload and update_payload['nombre'].lower() != area_existente.nombre.lower():
                if await AreaService._verificar_nombre_existente(update_payload['nombre'], excluir_id=area_id):
                    raise ServiceError(status_code=409, detail=f"Ya existe otra área con el nombre '{update_payload['nombre']}'.")

            fields_to_update = []
            params_list = []
            for key, value in update_payload.items():
                fields_to_update.append(f"{key} = ?")
                params_list.append(value)

            if not fields_to_update:
                 raise ServiceError(status_code=400, detail="No hay campos válidos para actualizar.")

            params_list.append(area_id)
            update_query = UPDATE_AREA_BASE_QUERY_TEMPLATE.format(fields=", ".join(fields_to_update))

            # --- Punto Crítico: Salida de execute_update ---
            # Asume que execute_update devuelve un diccionario del registro actualizado
            # Si devuelve otra cosa (ej. None o número de filas), esta parte fallará.
            resultado_update = execute_update(update_query, tuple(params_list))
            if not resultado_update:
                 # Si execute_update NO devuelve el diccionario, necesitas obtenerlo después
                 logger.warning(f"execute_update no devolvió el registro actualizado para ID {area_id}. Intentando obtenerlo de nuevo.")
                 updated_area = await AreaService.obtener_area_por_id(area_id)
                 if not updated_area:
                     # Esto sería muy raro si la actualización fue exitosa pero no se puede leer después
                     raise ServiceError(status_code=500, detail="Error crítico: Área actualizada pero no se pudo recuperar.")
                 logger.info(f"Área ID: {area_id} actualizada (verificada post-actualización).")
                 return updated_area
            else:
                # Si execute_update SÍ devuelve el diccionario
                updated_area = AreaRead(**resultado_update)
                logger.info(f"Área ID: {area_id} actualizada exitosamente (devuelta por execute_update).")
                return updated_area
            # --- Fin Punto Crítico ---

        except DatabaseError as db_err:
            logger.error(f"Error de DB al actualizar área {area_id}: {db_err}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error DB al actualizar área: {getattr(db_err, 'detail', str(db_err))}")
        except ServiceError as se:
             logger.warning(f"Error de servicio al actualizar área {area_id}: {se.detail}")
             raise se
        except Exception as e:
            logger.exception(f"Error inesperado al actualizar área {area_id}: {e}")
            raise ServiceError(status_code=500, detail=f"Error interno al actualizar área: {str(e)}")

    @staticmethod
    async def cambiar_estado_area(area_id: int, activar: bool) -> AreaRead:
        """Activa o desactiva un área (borrado lógico) usando TOGGLE_AREA_STATUS_QUERY."""
        accion = "reactivar" if activar else "desactivar"
        logger.info(f"Intentando {accion} área ID: {area_id}")

        try:
            area_existente = await AreaService.obtener_area_por_id(area_id)
            if not area_existente:
                 raise ServiceError(status_code=404, detail=f"Área con ID {area_id} no encontrada para {accion}.")
            if area_existente.es_activo == activar:
                 estado_str = "activa" if activar else "inactiva"
                 raise ServiceError(status_code=400, detail=f"Área con ID {area_id} ya está {estado_str}.")

            # --- Punto Crítico: Salida de execute_update ---
            # Asume que execute_update devuelve un diccionario del registro actualizado
            resultado_toggle = execute_update(TOGGLE_AREA_STATUS_QUERY, (activar, area_id))
            if not resultado_toggle:
                # Si execute_update NO devuelve el diccionario
                logger.warning(f"execute_update no devolvió el registro actualizado al {accion} ID {area_id}. Intentando obtenerlo de nuevo.")
                toggled_area = await AreaService.obtener_area_por_id(area_id)
                if not toggled_area or toggled_area.es_activo != activar:
                     # Si no se encuentra o el estado no cambió como se esperaba
                     raise ServiceError(status_code=500, detail=f"Error crítico: Área {accion}da pero no se pudo verificar el estado.")
                logger.info(f"Área ID: {area_id} {accion}da (verificada post-actualización).")
                return toggled_area
            else:
                # Si execute_update SÍ devuelve el diccionario
                toggled_area = AreaRead(**resultado_toggle)
                logger.info(f"Área ID: {area_id} {accion}da exitosamente (devuelta por execute_update).")
                return toggled_area
            # --- Fin Punto Crítico ---

        except DatabaseError as db_err:
            logger.error(f"Error de DB al {accion} área {area_id}: {db_err}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error DB al {accion}: {getattr(db_err, 'detail', str(db_err))}")
        except ServiceError as se:
             logger.warning(f"No se pudo {accion} área {area_id}: {se.detail}")
             raise se
        except Exception as e:
            logger.exception(f"Error inesperado al {accion} área {area_id}: {e}")
            raise ServiceError(status_code=500, detail=f"Error interno al {accion} área: {str(e)}")

    @staticmethod
    async def obtener_lista_simple_areas_activas() -> List[AreaSimpleList]:
        """Obtiene una lista simplificada (ID, Nombre) de todas las áreas activas."""
        logger.info("Obteniendo lista simple de áreas activas desde el servicio.")
        try:
            # Llama a execute_query SIN fetch_one, espera lista de dicts
            rows = execute_query(GET_ACTIVE_AREAS_SIMPLE_LIST_QUERY)
            if not rows:
                logger.info("No se encontraron áreas activas para la lista simple.")
                return []

            # Mapea los resultados al schema Pydantic
            # Usa un list comprehension con manejo de errores básico
            areas_list = []
            for row in rows:
                try:
                    areas_list.append(AreaSimpleList(**row))
                except Exception as map_err:
                    logger.error(f"Error al mapear fila de área simple: {map_err}. Fila: {row}", exc_info=True)
                    # Decide si continuar o fallar todo
                    # continue # Opción: Saltar fila con error
                    raise ServiceError(status_code=500, detail="Error al procesar datos de áreas.") # Opción: Fallar

            return areas_list
        except DatabaseError as db_err:
             logger.error(f"Error de DB al obtener lista simple de áreas: {db_err}", exc_info=True)
             raise ServiceError(status_code=500, detail=f"Error DB al obtener lista de áreas: {getattr(db_err, 'detail', str(db_err))}")
        except Exception as e:
            logger.error(f"Error inesperado al obtener lista simple de áreas activas: {e}", exc_info=True)
            raise ServiceError(status_code=500, detail="Error interno al obtener la lista de áreas.")