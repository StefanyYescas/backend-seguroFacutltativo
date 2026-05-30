from fastapi import Form, HTTPException
from fastapi import BackgroundTasks

from app.db.connection import get_connection
from app.utils.email import enviar_correo

from app.services.pdf_services import (
    extraer_datos_nss,
    extraer_datos_vigencia
)

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from datetime import date, timedelta

import uuid
import os
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

    try:

        id_usuario_bytes = uuid.UUID(
            id_usuario
        ).bytes

    except ValueError:

        return {
            "error": "UUID inválido"
        }

    if constancia.content_type != "application/pdf":

        return {
            "error": "La constancia debe ser PDF"
        }

    if nss.content_type != "application/pdf":

        return {
            "error": "El NSS debe ser PDF"
        }

    conn = get_connection()
    cursor = conn.cursor()

    try:

        id_solicitud = uuid.uuid4().bytes

        nombre_constancia = f"{uuid.uuid4()}.pdf"
        nombre_nss = f"{uuid.uuid4()}.pdf"

        ruta_constancia = os.path.join(
            UPLOAD_CONSTANCIAS,
            nombre_constancia
        )

        ruta_nss = os.path.join(
            UPLOAD_NSS,
            nombre_nss
        )

        with open(
            ruta_constancia,
            "wb"
        ) as buffer:

            buffer.write(
                await constancia.read()
            )

        with open(
            ruta_nss,
            "wb"
        ) as buffer:

            buffer.write(
                await nss.read()
            )

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
# GENERAR PDF PREVIEW
# =========================

async def generar_preview_seguro(

    id_solicitud: str,

    observacion: str

):

    conn = None
    cursor = None

    try:

        id_solicitud_bytes = uuid.UUID(
            id_solicitud
        ).bytes

        conn = get_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        sql_usuario = """
        SELECT 
            s.idUsuario,
            s.rutaNss,
            s.rutaConstancia,

            u.correo,
            u.nomCompleto,
            u.numControl,

            a.carrera,
            a.semestre

        FROM Solicitud s

        INNER JOIN Usuario u
            ON s.idUsuario = u.idUsuario

        INNER JOIN Alumno a
            ON u.idUsuario = a.idUsuario

        WHERE s.idSolicitud = %s
        """

        cursor.execute(
            sql_usuario,
            (id_solicitud_bytes,)
        )

        solicitud = cursor.fetchone()

        if not solicitud:

            return {
                "error": "Solicitud no encontrada"
            }

        datos_nss = extraer_datos_nss(
            solicitud["rutaNss"]
        )

        datos_vigencia = extraer_datos_vigencia(
            solicitud["rutaConstancia"]
        )

        nombre_archivo = f"{uuid.uuid4()}.pdf"

        ruta_archivo = os.path.join(
            UPLOAD_SEGUROS,
            nombre_archivo
        )

        pdf = canvas.Canvas(
            ruta_archivo,
            pagesize=letter
        )

        y = 750

        pdf.setFont(
            "Helvetica-Bold",
            16
        )

        pdf.drawString(
            120,
            y,
            "CONSTANCIA DE SEGURO FACULTATIVO"
        )

        y -= 60

        pdf.setFont(
            "Helvetica",
            12
        )

        pdf.drawString(
            50,
            y,
            f"Nombre: {solicitud['nomCompleto']}"
        )

        y -= 30

        pdf.drawString(
            50,
            y,
            f"Numero de Control: {solicitud['numControl']}"
        )

        y -= 30

        pdf.drawString(
            50,
            y,
            f"Carrera: {solicitud['carrera']}"
        )

        y -= 30

        pdf.drawString(
            50,
            y,
            f"Semestre: {solicitud['semestre']}"
        )

        y -= 30

        pdf.drawString(
            50,
            y,
            f"NSS: {datos_nss['nss']}"
        )

        y -= 30

        pdf.drawString(
            50,
            y,
            f"CURP: {datos_nss['curp']}"
        )

        y -= 30

        pdf.drawString(
            50,
            y,
            f"Clinica: {datos_vigencia['clinica']}"
        )

        y -= 30

        pdf.drawString(
            50,
            y,
            f"Vigencia: {datos_vigencia['vigencia']}"
        )

        y -= 50

        pdf.setFont(
            "Helvetica-Bold",
            12
        )

        pdf.drawString(
            50,
            y,
            "Observacion:"
        )

        y -= 30

        pdf.setFont(
            "Helvetica",
            12
        )

        pdf.drawString(
            50,
            y,
            observacion
        )

        pdf.save()

        return {

            "message": "Preview generado",

            "rutaSeguro": ruta_archivo
        }

    except Exception as e:

        return {
            "error": str(e)
        }

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()



# =========================
# ENTREGAR SEGURO
# =========================

async def entregar_seguro(

    id_solicitud: str,

    observacion: str,

    ruta_seguro: str,

    background_tasks: BackgroundTasks

):

    conn = None
    cursor = None

    try:

        id_solicitud_bytes = uuid.UUID(
            id_solicitud
        ).bytes

        conn = get_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        sql_usuario = """
        SELECT 
            s.idUsuario,
            u.correo
        FROM Solicitud s

        INNER JOIN Usuario u
            ON s.idUsuario = u.idUsuario

        WHERE s.idSolicitud = %s
        """

        cursor.execute(
            sql_usuario,
            (id_solicitud_bytes,)
        )

        solicitud = cursor.fetchone()

        if not solicitud:

            return {
                "error": "Solicitud no encontrada"
            }

        sql = """
        UPDATE Solicitud
        SET estado = %s,
            observacion = %s,
            fechaEntrega = CURDATE(),
            rutaSeguro = %s
        WHERE idSolicitud = %s
        """

        cursor.execute(

            sql,

            (
                "aprobada",
                observacion,
                ruta_seguro,
                id_solicitud_bytes
            )
        )

        conn.commit()

        background_tasks.add_task(

            enviar_correo,

            solicitud["correo"],

            "Seguro aprobado",

            f"""
Tu seguro ha sido aprobado.

Observación:
{observacion}
""",

            ruta_seguro
        )

        return {
            "message": "Seguro enviado correctamente"
        }

    except Exception as e:

        return {
            "error": str(e)
        }

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()



# =========================
# ACTUALIZAR SOLICITUD
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

        sql_correo = """
        SELECT u.correo
        FROM Solicitud s
        INNER JOIN Usuario u
            ON s.idUsuario = u.idUsuario
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

        enviar_correo(

            datos["correo"],

            "Solicitud rechazada",

            f"""
Tu solicitud fue rechazada.

Observación:
{solicitud.observacion}
"""
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
# APROBADAS
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
# RECHAZADAS
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