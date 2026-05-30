from app.db.connection import get_connection
from app.utils.password import hash_password, verify_password
from app.utils.jwt import crear_token
import uuid



# CREAR USUARIO

def crear_usuario(usuario):

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
        "mensaje": "usuario creado"
    }




# LOGIN

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