from jose import jwt
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