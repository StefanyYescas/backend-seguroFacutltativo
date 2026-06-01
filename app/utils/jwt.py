from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = "seguro_facultativo"

ALGORITHM = "HS256"

def crear_token(data: dict):

    datos = data.copy()

    expire = datetime.utcnow() + timedelta(hours=5)

    datos.update({
        "exp": expire
    })

    token = jwt.encode(
        datos,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token



# TOKEN TEMPORAL PARA AUTENTICACIÓN DE 3 PASOS

def crear_token_temporal(
    data: dict,
    exp_minutos: int = 10
):

    datos = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=exp_minutos
    )

    datos.update({
        "exp": expire,
        "temporal": True
    })

    token = jwt.encode(
        datos,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token



# VERIFICAR Y DECODIFICAR TOKEN

def verificar_token(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:

        return None