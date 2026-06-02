from app.db.connection import get_connection
from app.utils.password import hash_password, verify_password
from app.utils.jwt import crear_token, crear_token_temporal, verificar_token
from app.utils.otp import generar_codigo
from app.utils.email import enviar_correo
from datetime import datetime, timedelta
import uuid
import mysql.connector

DOMINIO_CORREO = "@veracruz.tecnm.mx"

def validar_dominio_correo(correo):

    if not correo.lower().endswith(
        DOMINIO_CORREO
    ):

        return {
            "error": f"correo debe ser institucional {DOMINIO_CORREO}"
        }

    return None



# CREAR USUARIO

def crear_usuario(usuario):

    err = validar_dominio_correo(
        usuario.correo
    )

    if err:

        return err

    conn = get_connection()
    cursor = conn.cursor()

    # UUID AUTOMÁTICA
    id_usuario = uuid.uuid4().bytes

    # HASH PASSWORD
    password_hash = hash_password(
        usuario.contrasena
    )

    sql = """
    INSERT INTO Usuario
    (
        idUsuario,
        nomCompleto,
        numControl,
        correo,
        contrasena,
        rol
    )
    VALUES (%s,%s,%s,%s,%s,%s)
    """

    values = (
        id_usuario,
        usuario.nomCompleto,
        usuario.numControl,
        usuario.correo,
        password_hash,
        usuario.rol
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "mensaje": "usuario creado",
        "idUsuario": str(
            uuid.UUID(bytes=id_usuario)
        )
    }




# LOGIN (DIRECTO — SIN 3 PASOS)

def login_usuario(usuario):

    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    sql = """
    SELECT * FROM Usuario
    WHERE numControl = %s
    """

    cursor.execute(
        sql,
        (usuario.numControl,)
    )

    user = cursor.fetchone()

    cursor.close()

    conn.close()

    # USUARIO NO EXISTE

    if not user:

        return {
            "error": "usuario no encontrado"
        }

    # VALIDAR PASSWORD

    password_valida = verify_password(
        usuario.contrasena,
        user["contrasena"]
    )

    # PASSWORD INCORRECTA

    if not password_valida:

        return {
            "error": "contraseña incorrecta"
        }


    # CREAR TOKEN


    token = crear_token({

        "idUsuario": str(
            uuid.UUID(
                bytes=user["idUsuario"]
            )
        ),

        "rol": user["rol"]
    })


    # LOGIN CORRECTO


    return {

        "mensaje": "login correcto",

        "token": token,

        "idUsuario": str(
            uuid.UUID(
                bytes=user["idUsuario"]
            )
        ),

        "usuario": user["nomCompleto"],

        "rol": user["rol"],

        "numControl": user["numControl"]

    }




# =========================
# PASO 1 — CREDENCIALES
# =========================

def login_paso1(data):

    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        # BUSCAR USUARIO

        sql = """
        SELECT * FROM Usuario
        WHERE numControl = %s
        """

        cursor.execute(
            sql,
            (data.numControl,)
        )

        user = cursor.fetchone()

        if not user:

            return {
                "error": "usuario no encontrado"
            }

        # VALIDAR PASSWORD

        password_valida = verify_password(
            data.contrasena,
            user["contrasena"]
        )

        if not password_valida:

            return {
                "error": "contraseña incorrecta"
            }


        # VALIDAR ROL SEGÚN TAB

        if user["rol"] != data.rol:

            return {
                "error": f"acceso no autorizado para el rol {data.rol}"
            }

        # VALIDAR DOMINIO INSTITUCIONAL

        err = validar_dominio_correo(
            user["correo"]
        )

        if err:

            return err


        # VERIFICAR LÍMITE DE INTENTOS (máx 5 cada 10 min)


        sql_contar = """
        SELECT COUNT(*) AS total
        FROM LoginIntent
        WHERE idUsuario = %s
        AND expira > NOW()
        """

        cursor.execute(
            sql_contar,
            (user["idUsuario"],)
        )

        count_row = cursor.fetchone()

        if count_row["total"] >= 5:

            return {
                "error": "demasiados intentos, espera 10 minutos"
            }


        # GENERAR CÓDIGO OTP


        codigo = generar_codigo()

        id_intent = str(uuid.uuid4())

        expira = datetime.utcnow() + timedelta(
            minutes=10
        )


        # GUARDAR EN LoginIntent


        sql_intent = """
        INSERT INTO LoginIntent
        (
            id,
            idUsuario,
            codigo,
            expira,
            paso
        )
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            sql_intent,
            (
                id_intent,
                user["idUsuario"],
                codigo,
                expira,
                1
            )
        )

        conn.commit()


        # ENVIAR CORREO


        enviar_correo(
            user["correo"],
            "Código de verificación — Seguro Facultativo",
            f"""
Tu código de verificación es:

    {codigo}

Este código expira en 10 minutos.

Si no solicitaste este código, ignora este mensaje.
"""
        )


        # CREAR TOKEN TEMPORAL


        temp_token = crear_token_temporal({
            "idIntent": id_intent
        })


        return {

            "tempToken": temp_token,

            "correo": user["correo"]
        }

    except mysql.connector.Error as e:

        return {
            "error": str(e)
        }

    finally:

        cursor.close()
        conn.close()




# =========================
# PASO 2 — CÓDIGO OTP
# =========================

def login_paso2(data):

    # VERIFICAR TOKEN TEMPORAL

    payload = verificar_token(
        data.tempToken
    )

    if not payload:

        return {
            "error": "sesión inválida o expirada"
        }

    if not payload.get("temporal"):

        return {
            "error": "token inválido"
        }

    id_intent = payload.get("idIntent")

    if not id_intent:

        return {
            "error": "token inválido"
        }

    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        # BUSCAR INTENT

        sql = """
        SELECT * FROM LoginIntent
        WHERE id = %s AND paso = 1
        """

        cursor.execute(sql, (id_intent,))

        intent = cursor.fetchone()

        if not intent:

            return {
                "error": "código no encontrado o sesión expirada"
            }

        # VERIFICAR EXPIRACIÓN

        if intent["expira"] < datetime.utcnow():

            return {
                "error": "código expirado"
            }

        # VERIFICAR LÍMITE DE OTP

        if intent["intentos"] >= 3:

            sql_delete = """
            DELETE FROM LoginIntent
            WHERE id = %s
            """

            cursor.execute(
                sql_delete,
                (id_intent,)
            )

            conn.commit()

            return {
                "error": "demasiados códigos incorrectos, inicia sesión de nuevo"
            }

        # INCREMENTAR INTENTOS

        sql_intentos = """
        UPDATE LoginIntent
        SET intentos = intentos + 1
        WHERE id = %s
        """

        cursor.execute(
            sql_intentos,
            (id_intent,)
        )

        conn.commit()

        # VERIFICAR CÓDIGO

        if intent["codigo"] != data.codigo:

            return {
                "error": "código incorrecto"
            }

        # OBTENER DATOS DEL USUARIO

        sql_user = """
        SELECT * FROM Usuario
        WHERE idUsuario = %s
        """

        cursor.execute(
            sql_user,
            (intent["idUsuario"],)
        )

        user = cursor.fetchone()

        if not user:

            return {
                "error": "usuario no encontrado"
            }

        # ACTUALIZAR INTENT A PASO 2, REINICIAR INTENTOS

        sql_update = """
        UPDATE LoginIntent
        SET paso = 2,
            intentos = 0
        WHERE id = %s
        """

        cursor.execute(
            sql_update,
            (id_intent,)
        )

        conn.commit()

        # CREAR NUEVO TOKEN TEMPORAL

        temp_token = crear_token_temporal({
            "idIntent": id_intent,
            "idUsuario": str(
                uuid.UUID(
                    bytes=user["idUsuario"]
                )
            ),
            "rol": user["rol"]
        })

        return {

            "tempToken": temp_token,

            "usuario": user["nomCompleto"],

            "numControl": user["numControl"],

            "rol": user["rol"]
        }

    except mysql.connector.Error as e:

        return {
            "error": str(e)
        }

    finally:

        cursor.close()
        conn.close()




# =========================
# PASO 3 — CONFIRMAR
# =========================

def login_paso3(data):

    # VERIFICAR TOKEN TEMPORAL

    payload = verificar_token(
        data.tempToken
    )

    if not payload:

        return {
            "error": "sesión inválida o expirada"
        }

    if not payload.get("temporal"):

        return {
            "error": "token inválido"
        }

    id_intent = payload.get("idIntent")

    id_usuario_str = payload.get("idUsuario")

    rol_token = payload.get("rol")

    if not id_intent or not id_usuario_str or not rol_token:

        return {
            "error": "token inválido"
        }

    # VERIFICAR QUE EL ROL COINCIDA

    if rol_token != data.rol:

        return {
            "error": "rol inválido"
        }

    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        # CONFIRMAR QUE EL INTENT EXISTE Y ESTÁ EN PASO 2

        sql = """
        SELECT * FROM LoginIntent
        WHERE id = %s AND paso = 2
        """

        cursor.execute(sql, (id_intent,))

        intent = cursor.fetchone()

        if not intent:

            return {
                "error": "sesión no encontrada"
            }

        # OBTENER USUARIO

        id_usuario_bytes = uuid.UUID(
            id_usuario_str
        ).bytes

        sql_user = """
        SELECT * FROM Usuario
        WHERE idUsuario = %s
        """

        cursor.execute(
            sql_user,
            (id_usuario_bytes,)
        )

        user = cursor.fetchone()

        if not user:

            return {
                "error": "usuario no encontrado"
            }

        # CREAR TOKEN FINAL

        token_final = crear_token({
            "idUsuario": id_usuario_str,
            "rol": user["rol"]
        })

        # ELIMINAR INTENT

        sql_delete = """
        DELETE FROM LoginIntent
        WHERE id = %s
        """

        cursor.execute(
            sql_delete,
            (id_intent,)
        )

        conn.commit()

        return {

            "mensaje": "login correcto",

            "token": token_final,

            "idUsuario": id_usuario_str,

            "usuario": user["nomCompleto"],

            "rol": user["rol"],

            "numControl": user["numControl"]
        }

    except mysql.connector.Error as e:

        return {
            "error": str(e)
        }

    finally:

        cursor.close()
        conn.close()




# =========================
# REENVIAR CÓDIGO OTP
# =========================

def login_reenviar(data):

    payload = verificar_token(
        data.tempToken
    )

    if not payload:

        return {
            "error": "sesión inválida o expirada"
        }

    if not payload.get("temporal"):

        return {
            "error": "token inválido"
        }

    id_intent = payload.get("idIntent")

    if not id_intent:

        return {
            "error": "token inválido"
        }

    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        sql = """
        SELECT li.*, u.correo
        FROM LoginIntent li
        INNER JOIN Usuario u
            ON li.idUsuario = u.idUsuario
        WHERE li.id = %s AND li.paso = 1
        """

        cursor.execute(sql, (id_intent,))

        intent = cursor.fetchone()

        if not intent:

            return {
                "error": "sesión no encontrada"
            }

        if intent["expira"] < datetime.utcnow():

            return {
                "error": "sesión expirada"
            }

        # GENERAR NUEVO CÓDIGO

        codigo = generar_codigo()

        sql_update = """
        UPDATE LoginIntent
        SET codigo = %s,
            intentos = 0,
            expira = %s
        WHERE id = %s
        """

        nueva_expira = datetime.utcnow() + timedelta(
            minutes=10
        )

        cursor.execute(
            sql_update,
            (
                codigo,
                nueva_expira,
                id_intent
            )
        )

        conn.commit()

        # REENVIAR CORREO

        enviar_correo(
            intent["correo"],
            "Nuevo código de verificación — Seguro Facultativo",
            f"""
Tu nuevo código de verificación es:

    {codigo}

Este código expira en 10 minutos.

Si no solicitaste este código, ignora este mensaje.
"""
        )

        return {
            "mensaje": "código reenviado"
        }

    except mysql.connector.Error as e:

        return {
            "error": str(e)
        }

    finally:

        cursor.close()
        conn.close()