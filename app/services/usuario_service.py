from typing import Dict
from app.db.queries import execute_query, execute_insert
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

