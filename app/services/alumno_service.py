from app.db.connection import get_connection

import uuid



# CREAR ALUMNO

def crear_alumno(alumno):

    conn = get_connection()
    cursor = conn.cursor()

    # UUID
    id_alumno = uuid.uuid4().bytes

    sql = """
    INSERT INTO Alumno
    (
        idAlumno,
        carrera,
        semestre,
        idUsuario
    )
    VALUES (%s,%s,%s,%s)
    """

    values = (
        id_alumno,
        alumno.carrera,
        alumno.semestre,
        uuid.UUID(alumno.idUsuario).bytes
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "mensaje": "alumno creado"
    }