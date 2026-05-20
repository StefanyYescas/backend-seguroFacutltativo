from app.db.connection import get_connection

import uuid


# =========================
# CREAR ADMIN
# =========================
def crear_admin(admin):

    conn = get_connection()
    cursor = conn.cursor()

    id_admin = uuid.uuid4().bytes

    sql = """
    INSERT INTO Admin
    (
        idAdmin,
        idUsuario
    )
    VALUES (%s,%s)
    """

    values = (
        id_admin,
        uuid.UUID(admin.idUsuario).bytes
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "mensaje": "admin creado"
    }