from fastapi import Form, File, UploadFile
from app.db.connection import get_connection
from datetime import date, timedelta
from app.utils.email import enviar_correo
from fastapi import BackgroundTasks

import uuid
import os
import shutil
import mysql.connector


# =========================
# CARPETAS
# =========================
UPLOAD_CONSTANCIAS = "app/uploads/constancias"
UPLOAD_NSS = "app/uploads/nss"
UPLOAD_SEGUROS = "app/uploads/seguros"

os.makedirs(
    UPLOAD_SEGUROS,
    exist_ok=True
)

os.makedirs(
    UPLOAD_CONSTANCIAS,
    exist_ok=True
)

os.makedirs(
    UPLOAD_NSS,
    exist_ok=True
)


# =========================
# CREAR SOLICITUD
# =========================
async def crear_solicitud(
    id_usuario,
    constancia,
    nss
):

    # =========================
    # VALIDAR UUID
    # =========================
    try:

        id_usuario_bytes = uuid.UUID(
            id_usuario
        ).bytes

    except ValueError:

        return {
            "error": "UUID inválido"
        }

    # =========================
    # VALIDAR PDF
    # =========================
    if constancia.content_type != "application/pdf":

        return {
            "error": "La constancia debe ser PDF"
        }

    if nss.content_type != "application/pdf":

        return {
            "error": "El NSS debe ser PDF"
        }

    # =========================
    # CONEXIÓN
    # =========================
    conn = get_connection()
    cursor = conn.cursor()

    try:

        # =========================
        # UUID SOLICITUD
        # =========================
        id_solicitud = uuid.uuid4().bytes

        # =========================
        # NOMBRES ÚNICOS
        # =========================
        nombre_constancia = f"{uuid.uuid4()}.pdf"

        nombre_nss = f"{uuid.uuid4()}.pdf"

        # =========================
        # RUTAS
        # =========================
        ruta_constancia = os.path.join(
            UPLOAD_CONSTANCIAS,
            nombre_constancia
        )

        ruta_nss = os.path.join(
            UPLOAD_NSS,
            nombre_nss
        )

        # =========================
        # GUARDAR CONSTANCIA
        # =========================
        with open(
            ruta_constancia,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                constancia.file,
                buffer
            )

        # =========================
        # GUARDAR NSS
        # =========================
        with open(
            ruta_nss,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                nss.file,
                buffer
            )

        # =========================
        # INSERT SQL
        # =========================
        sql = """
        INSERT INTO Solicitud
        (
            idSolicitud,
            rutaConstancia,
            rutaNss,
            idUsuario
        )
        VALUES (%s, %s, %s, %s)
        """

        values = (
            id_solicitud,
            ruta_constancia,
            ruta_nss,
            id_usuario_bytes
        )

        cursor.execute(
            sql,
            values
        )

        conn.commit()

        return {
            "message": "Solicitud creada correctamente"
        }

    except mysql.connector.Error as e:

        # =========================
        # BORRAR PDFs SI FALLA MYSQL
        # =========================
        if os.path.exists(ruta_constancia):

            os.remove(ruta_constancia)

        if os.path.exists(ruta_nss):

            os.remove(ruta_nss)

        return {
            "error": str(e)
        }

    finally:

        cursor.close()
        conn.close()



   # =========================
# OBTENER TODAS
# =========================

def obtener_solicitudes():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT
        BIN_TO_UUID(idSolicitud) AS idSolicitud,
        BIN_TO_UUID(idUsuario) AS idUsuario,
        fechaSolicitud,
        fechaEntrega,
        estado,
        observacion,
        rutaNss,
        rutaConstancia,
        rutaSeguro,
        nomCompleto,
        numControl,
        correo,
        carrera,
        semestre
    FROM vista_solicitudes_admin
    WHERE estado = 'pendiente'
    """

    cursor.execute(sql)

    solicitudes = cursor.fetchall()

    cursor.close()
    conn.close()

    return solicitudes

# =========================
# ENTREGAR SEGURO (APROBACIÓN)
# =========================

async def entregar_seguro(
    id_solicitud: str,
    observacion: str,
    archivo: UploadFile,
    background_tasks: BackgroundTasks  # 👈 AGREGAR ESTE PARÁMETRO
):

    ruta_archivo = None

    try:
        id_solicitud_bytes = uuid.UUID(id_solicitud).bytes

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        sql_usuario = """
            SELECT 
                s.idUsuario,
                u.correo
            FROM Solicitud s
            INNER JOIN Usuario u
                ON s.idUsuario = u.idUsuario
            WHERE s.idSolicitud = %s
        """

        cursor.execute(sql_usuario, (id_solicitud_bytes,))
        solicitud = cursor.fetchone()

        if not solicitud:
            return {"error": "Solicitud no encontrada"}

        correo = solicitud["correo"]
        id_usuario = solicitud["idUsuario"]

        sql_validar = """
        SELECT fechaEntrega
        FROM Solicitud
        WHERE idUsuario = %s
        AND estado = 'aprobada'
        ORDER BY fechaEntrega DESC
        LIMIT 1
        """

        cursor.execute(sql_validar, (id_usuario,))
        ultima_aprobada = cursor.fetchone()

        if ultima_aprobada and ultima_aprobada["fechaEntrega"]:
            fecha_entrega = ultima_aprobada["fechaEntrega"]
            fecha_limite = fecha_entrega + timedelta(days=180)

            if date.today() < fecha_limite:
                return {"error": "El alumno ya tiene un seguro vigente"}

        nombre_archivo = f"{uuid.uuid4()}.pdf"
        ruta_archivo = os.path.join(UPLOAD_SEGUROS, nombre_archivo)

        with open(ruta_archivo, "wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)

        sql = """
        UPDATE Solicitud
        SET estado = %s,
            observacion = %s,
            fechaEntrega = CURDATE(),
            rutaSeguro = %s
        WHERE idSolicitud = %s
        """

        cursor.execute(sql, (
            "aprobada",
            observacion,
            ruta_archivo,
            id_solicitud_bytes
        ))

        conn.commit()
        
        print("🔥 VOY A PROGRAMAR EL ENVÍO DE CORREO")
        
        # 👇 ENVIAR CORREO EN SEGUNDO PLANO (NO esperar a que termine)
        background_tasks.add_task(
            enviar_correo,
            correo,
            "Seguro aprobado",
            f"Tu seguro ha sido aprobado.\nObservación: {observacion}",
            ruta_archivo
        )
        
        print("✅ CORREO PROGRAMADO - La respuesta se enviará al frontend inmediatamente")

        return {"message": "Seguro entregado"}

    finally:
        cursor.close()
        conn.close()

# =========================
# ACTUALIZAR SOLICITUD (RECHAZO)
# =========================
def actualizar_solicitud(id_solicitud, solicitud):

    try:

        id_solicitud_bytes = uuid.UUID(
            id_solicitud
        ).bytes

    except ValueError:

        return {
            "error": "UUID inválido"
        }

    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        # =========================
        # OBTENER CORREO
        # =========================
        sql_correo = """
        SELECT u.correo
        FROM Solicitud s
        INNER JOIN Usuario u ON s.idUsuario = u.idUsuario
        WHERE s.idSolicitud = %s
        """

        cursor.execute(
            sql_correo,
            (id_solicitud_bytes,)
        )

        datos = cursor.fetchone()

        if not datos:

            return {
                "error": "Solicitud no encontrada"
            }

        # =========================
        # UPDATE
        # =========================
        sql = """
        UPDATE Solicitud
        SET estado = %s,
            observacion = %s,
            fechaEntrega = %s
        WHERE idSolicitud = %s
        """

        values = (

            solicitud.estado,

            solicitud.observacion,

            solicitud.fechaEntrega,

            id_solicitud_bytes
        )

        cursor.execute(
            sql,
            values
        )

        conn.commit()

        print("✅ SOLICITUD ACTUALIZADA")

        # =========================
        # CORREO
        # =========================
        try:

            print("🔥 VOY A ENVIAR CORREO RECHAZO")

            print(
                "📨 DESTINATARIO:",
                datos["correo"]
            )

            print(
                "📝 OBSERVACIÓN:",
                solicitud.observacion
            )

            enviado = enviar_correo(

                datos["correo"],

                "Solicitud rechazada",

                f"""
Tu solicitud fue rechazada.

Observación:
{solicitud.observacion}
"""
            )

            print(
                "✅ RESULTADO ENVÍO:",
                enviado
            )

        except Exception as e:

            print(
                "❌ Error enviando correo:",
                str(e)
            )

        return {
            "message": "Solicitud actualizada"
        }

    except mysql.connector.Error as e:

        return {
            "error": str(e)
        }

    finally:

        cursor.close()

        conn.close()


# =========================
# OBTENER APROBADAS
# =========================

def obtener_aprobadas():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT
        BIN_TO_UUID(idSolicitud) AS idSolicitud,
        BIN_TO_UUID(idUsuario) AS idUsuario,
        fechaSolicitud,
        fechaEntrega,
        estado,
        observacion,
        rutaNss,
        rutaConstancia,
        rutaSeguro,
        nomCompleto,
        numControl,
        correo,
        carrera,
        semestre
    FROM vista_solicitudes_admin
    WHERE estado = 'aprobada'
    """

    cursor.execute(sql)

    solicitudes = cursor.fetchall()

    cursor.close()
    conn.close()

    return solicitudes


# =========================
# OBTENER APROBADAS
# =========================

def obtener_rechazadas():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT
        BIN_TO_UUID(idSolicitud) AS idSolicitud,
        BIN_TO_UUID(idUsuario) AS idUsuario,
        fechaSolicitud,
        fechaEntrega,
        estado,
        observacion,
        rutaNss,
        rutaConstancia,
        rutaSeguro,
        nomCompleto,
        numControl,
        correo,
        carrera,
        semestre
    FROM vista_solicitudes_admin
    WHERE estado = 'rechazada'
    """

    cursor.execute(sql)
    solicitudes = cursor.fetchall()

    cursor.close()
    conn.close()

    return solicitudes



# =========================
# HISTORIAL
# =========================
# =========================
# HISTORIAL
# =========================
def obtener_historial():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT
        BIN_TO_UUID(idSolicitud) AS idSolicitud,
        BIN_TO_UUID(idUsuario) AS idUsuario,
        fechaSolicitud,
        fechaEntrega,
        estado,
        observacion,
        rutaNss,
        rutaConstancia,
        rutaSeguro,
        nomCompleto,
        numControl,
        correo,
        carrera,
        semestre
    FROM vista_solicitudes_admin
    WHERE estado IN (
        'aprobada',
        'rechazada'
    )
    ORDER BY fechaSolicitud DESC
    """

    cursor.execute(sql)

    solicitudes = cursor.fetchall()

    cursor.close()
    conn.close()

    return solicitudes