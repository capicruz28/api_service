from app.db.connection import get_db_connection

def execute_query(query: str, params: tuple = ()):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = [
            {column[0]: value for column, value in zip(cursor.description, row)}
            for row in rows
        ]
        return result
    except Exception as e:
        raise Exception(f"Error ejecutando la consulta: {e}")
    finally:
        cursor.close()
        conn.close()

def execute_procedure(procedure_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Crear consulta con parámetros nombrados        
        query = f"EXEC {procedure_name}"
        
        print(f"Ejecutando consulta: {query}")

        # Ejecutar la consulta
        cursor.execute(query)

        # Manejar múltiples conjuntos de resultados
        results = []
        while True:
            if cursor.description:  # Si hay resultados
                rows = cursor.fetchall()
                results.extend(
                    [{column[0]: value for column, value in zip(cursor.description, row)} for row in rows]
                )
            if not cursor.nextset():  # Siguiente conjunto
                break
        
        if not results:
            print("Procedimiento ejecutado correctamente, sin resultados.")
            return {"message": "Procedimiento ejecutado correctamente, sin resultados"}
        
        print(f"Resultados obtenidos: {results}")
        return results
    
    except Exception as e:
        print(f"Error al ejecutar el procedimiento almacenado: {str(e)}")
        raise Exception(f"Error ejecutando el procedimiento almacenado: {str(e)}")

    finally:
        cursor.close()
        conn.close()

def execute_procedure_params(procedure_name: str, params: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Crear consulta con parámetros nombrados
        param_str = ", ".join([f"@{key} = ?" for key in params.keys()])
        query = f"EXEC {procedure_name} {param_str}"
        
        print(f"Ejecutando consulta: {query} con parámetros: {params}")

        # Ejecutar la consulta
        cursor.execute(query, tuple(params.values()))

        # Manejar múltiples conjuntos de resultados
        results = []
        while True:
            if cursor.description:  # Si hay resultados
                rows = cursor.fetchall()
                results.extend(
                    [{column[0]: value for column, value in zip(cursor.description, row)} for row in rows]
                )
            if not cursor.nextset():  # Siguiente conjunto
                break
        
        if not results:
            print("Procedimiento ejecutado correctamente, sin resultados.")
            return {"message": "Procedimiento ejecutado correctamente, sin resultados"}
        
        print(f"Resultados obtenidos: {results}")
        return results
    
    except Exception as e:
        print(f"Error al ejecutar el procedimiento almacenado: {str(e)}")
        raise Exception(f"Error ejecutando el procedimiento almacenado: {str(e)}")

    finally:
        cursor.close()
        conn.close()