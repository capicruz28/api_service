from app.db.connection import get_db_connection

# METODOS PARA EJECUTAR CONSULTAS SQL
def execute_query(query: str, params: tuple = ()):
    conn = get_db_connection()  # 1. Obtiene una conexión a la base de datos
    cursor = conn.cursor()  # 2. Crea un cursor para ejecutar la consulta
    try:
        cursor.execute(query, params) # 3. Ejecuta la consulta con parámetros
        rows = cursor.fetchall() # 4. Obtiene todas las filas del resultado

         # 5. Convierte las filas en una lista de diccionarios
        result = [
            {column[0]: value for column, value in zip(cursor.description, row)}
            for row in rows
        ]
        return result # 6. Retorna la lista de diccionarios
    except Exception as e:
        raise Exception(f"Error ejecutando la consulta: {e}") # 7. Manejo de errores
    finally:
        cursor.close() # 8. Cierra el cursor
        conn.close() # 9. Cierra la conexión

# METODOS PARA EJECUTAR PROCEDIMIENTOS ALMACENADOS
def execute_procedure(procedure_name: str):
    conn = get_db_connection() # 1. Obtiene la conexión a la base de datos
    cursor = conn.cursor() # 2. Crea un cursor para ejecutar la consulta
    try:            
        query = f"EXEC {procedure_name}" # 3. Construye la consulta SQL para ejecutar el procedimiento almacenado
        
        print(f"Ejecutando consulta: {query}") # 4. Muestra la consulta en consola
        
        cursor.execute(query) # 5. Ejecuta el procedimiento almacenado
        
        # 6. Manejo de múltiples conjuntos de resultados
        results = []
        while True:
            if cursor.description:  # Si hay datos en el resultado
                rows = cursor.fetchall() # 7. Obtiene todas las filas
                results.extend(
                    [{column[0]: value for column, value in zip(cursor.description, row)} for row in rows]
                )
            if not cursor.nextset():  # 8. Pasa al siguiente conjunto de resultados
                break
        
        # 9. Si no hay resultados, devuelve un mensaje
        if not results:
            print("Procedimiento ejecutado correctamente, sin resultados.")
            return {"message": "Procedimiento ejecutado correctamente, sin resultados"}
        
        print(f"Resultados obtenidos: {results}") # 10. Muestra los resultados en consola
        return results # 11. Retorna los datos en formato de lista de diccionarios
    
    except Exception as e:
        print(f"Error al ejecutar el procedimiento almacenado: {str(e)}") # 12. Muestra el error en consola
        raise Exception(f"Error ejecutando el procedimiento almacenado: {str(e)}") # 13. Lanza una excepción con el error

    finally:
        cursor.close() # 14. Cierra el cursor
        conn.close() # 15. Cierra la conexión a la base de datos

# METODOS PARA EJECUTAR PROCEDIMIENTOS ALMACENADOS CON PARÁMETROS
def execute_procedure_params(procedure_name: str, params: dict):
    conn = get_db_connection() # 1. Obtiene la conexión a la base de datos
    cursor = conn.cursor() # 2. Crea un cursor para ejecutar la consulta
    try:
        # 3. Construye la cadena de parámetros nombrados
        param_str = ", ".join([f"@{key} = ?" for key in params.keys()])
        query = f"EXEC {procedure_name} {param_str}"
        
        print(f"Ejecutando consulta: {query} con parámetros: {params}") # 4. Muestra la consulta y parámetros en consola
        
        cursor.execute(query, tuple(params.values())) # 5. Ejecuta el procedimiento con los valores de los parámetros

        # 6. Manejo de múltiples conjuntos de resultados
        results = []
        while True:
            if cursor.description:  # Si hay resultados
                rows = cursor.fetchall() # 7. Obtiene todas las filas
                results.extend(
                    [{column[0]: value for column, value in zip(cursor.description, row)} for row in rows]
                )
            if not cursor.nextset():  # 8. Pasa al siguiente conjunto de resultados
                break
        
        # 9. Si no hay resultados, devuelve un mensaje
        if not results:
            print("Procedimiento ejecutado correctamente, sin resultados.")
            return {"message": "Procedimiento ejecutado correctamente, sin resultados"}
        
        print(f"Resultados obtenidos: {results}")  # 10. Muestra los resultados en consola
        return results # 11. Retorna los datos en formato de lista de diccionarios
    
    except Exception as e:
        print(f"Error al ejecutar el procedimiento almacenado: {str(e)}") # 12. Muestra el error en consola
        raise Exception(f"Error ejecutando el procedimiento almacenado: {str(e)}") # 13. Lanza una excepción con el error

    finally:
        cursor.close() # 14. Cierra el cursor
        conn.close() # 15. Cierra la conexión a la base de datos