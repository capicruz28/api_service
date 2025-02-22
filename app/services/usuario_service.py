from typing import Dict
from app.db.queries import execute_query, execute_insert, execute_update
from app.core.exceptions import ServiceError, ValidationError
from app.core.security import get_password_hash
import logging

logger = logging.getLogger(__name__)

class UsuarioService:
    @staticmethod
    async def verificar_usuario_existente(nombre_usuario: str, correo: str) -> bool:
        """
        Verifica si ya existe un usuario con el mismo nombre de usuario o correo
        """
        try:
            query = """
            SELECT nombre_usuario, correo
            FROM usuario
            WHERE nombre_usuario = ? OR correo = ?
            """
            resultados = execute_query(query, (nombre_usuario, correo))

            if resultados:
                for resultado in resultados:
                    if resultado['nombre_usuario'] == nombre_usuario:
                        raise ValidationError(
                            status_code=400,
                            detail="El nombre de usuario ya está en uso"
                        )
                    if resultado['correo'] == correo:
                        raise ValidationError(
                            status_code=400,
                            detail="El correo electrónico ya está registrado"
                        )
            return False
        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error verificando usuario existente: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error en la verificación: {str(e)}")

    @staticmethod
    async def crear_usuario(usuario_data: Dict) -> Dict:
        try:
            # Verificar si el usuario o correo ya existen
            await UsuarioService.verificar_usuario_existente(
                usuario_data['nombre_usuario'],
                usuario_data['correo']
            )

            # Hash de la contraseña
            hashed_password = get_password_hash(usuario_data['contrasena'])

            # Insertar nuevo usuario
            insert_query = """
            INSERT INTO usuario (
                nombre_usuario,
                correo,
                contrasena,
                nombre,
                apellido,
                es_activo,
                correo_confirmado
            )
            OUTPUT
                INSERTED.usuario_id,
                INSERTED.nombre_usuario,
                INSERTED.correo,
                INSERTED.nombre,
                INSERTED.apellido,
                INSERTED.es_activo,
                INSERTED.fecha_creacion
            VALUES (?, ?, ?, ?, ?, 1, 0)
            """

            params = (
                usuario_data['nombre_usuario'],
                usuario_data['correo'],
                hashed_password,
                usuario_data.get('nombre'),
                usuario_data.get('apellido')
            )

            result = execute_insert(insert_query, params)

            if not result:
                raise ServiceError(status_code=500, detail="Error creando usuario")

            return result

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error creando usuario: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error creando usuario: {str(e)}")

    @staticmethod
    async def actualizar_usuario(usuario_id: int, usuario_data: Dict) -> Dict:
        try:
            # Verificar si el usuario existe
            check_query = """
            SELECT usuario_id, nombre_usuario, correo
            FROM usuario
            WHERE usuario_id = ? AND es_eliminado = 0
            """
            usuario_existente = execute_query(check_query, (usuario_id,))

            if not usuario_existente:
                raise ValidationError(
                    status_code=404,
                    detail="Usuario no encontrado"
                )

            # Verificar duplicados si se está actualizando nombre_usuario o correo
            if 'nombre_usuario' in usuario_data or 'correo' in usuario_data:
                verify_query = """
                SELECT usuario_id
                FROM usuario
                WHERE (nombre_usuario = ? OR correo = ?)
                AND usuario_id != ? AND es_eliminado = 0
                """
                params = (
                    usuario_data.get('nombre_usuario', ''),
                    usuario_data.get('correo', ''),
                    usuario_id
                )
                duplicados = execute_query(verify_query, params)

                if duplicados:
                    raise ValidationError(
                        status_code=400,
                        detail="El nombre de usuario o correo ya está en uso"
                    )

            # Construir la consulta de actualización
            update_parts = []
            params = []

            # Mapeo de campos permitidos para actualizar
            allowed_fields = {
                'nombre_usuario': 'nombre_usuario',
                'correo': 'correo',
                'nombre': 'nombre',
                'apellido': 'apellido',
                'es_activo': 'es_activo'
            }

            # Construir la consulta dinámicamente
            for field, db_field in allowed_fields.items():
                if field in usuario_data and usuario_data[field] is not None:
                    update_parts.append(f"{db_field} = ?")
                    params.append(usuario_data[field])

            if not update_parts:
                raise ValidationError(
                    status_code=400,
                    detail="No hay campos válidos para actualizar"
                )

            # Agregar fecha de actualización
            update_parts.append("fecha_actualizacion = GETDATE()")

            # Agregar el ID del usuario a los parámetros
            params.append(usuario_id)

            # Construir y ejecutar la consulta de actualización
            update_query = f"""
            UPDATE usuario
            SET {', '.join(update_parts)}
            OUTPUT
                INSERTED.usuario_id,
                INSERTED.nombre_usuario,
                INSERTED.correo,
                INSERTED.nombre,
                INSERTED.apellido,
                INSERTED.es_activo,
                INSERTED.fecha_creacion
            WHERE usuario_id = ? AND es_eliminado = 0
            """

            # Usar la nueva función execute_update
            result = execute_update(update_query, tuple(params))

            if not result:
                raise ServiceError(
                    status_code=500,
                    detail="Error al actualizar el usuario"
                )

            return result

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error actualizando usuario: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail=f"Error actualizando usuario: {str(e)}"
            )

    @staticmethod
    async def eliminar_usuario(usuario_id: int) -> Dict:
        """
        Realiza un borrado lógico del usuario
        """
        try:
            # Verificar si el usuario existe y no está eliminado
            check_query = """
            SELECT usuario_id
            FROM usuario
            WHERE usuario_id = ? AND es_eliminado = 0
            """
            usuario_existente = execute_query(check_query, (usuario_id,))

            if not usuario_existente:
                raise ValidationError(
                    status_code=404,
                    detail="Usuario no encontrado o ya está eliminado"
                )

            # Realizar el borrado lógico
            update_query = """
            UPDATE usuario
            SET es_eliminado = 1,
                es_activo = 0,
                fecha_actualizacion = GETDATE()
            OUTPUT
                INSERTED.usuario_id,
                INSERTED.nombre_usuario,
                INSERTED.correo,
                INSERTED.nombre,
                INSERTED.apellido,
                INSERTED.es_activo,
                INSERTED.es_eliminado,
                INSERTED.fecha_actualizacion
            WHERE usuario_id = ? AND es_eliminado = 0
            """

            result = execute_update(update_query, (usuario_id,))

            if not result:
                raise ServiceError(
                    status_code=500,
                    detail="Error al eliminar el usuario"
                )

            return {
                "message": "Usuario eliminado exitosamente",
                "usuario": result
            }

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error eliminando usuario: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail=f"Error eliminando usuario: {str(e)}"
            )