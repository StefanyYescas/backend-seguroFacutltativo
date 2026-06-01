from fastapi import APIRouter

from app.schemas.usuario_schema import (
    UsuarioCreate,
    UsuarioLogin,
    Paso1Request,
    Paso2Request,
    Paso3Request,
    ReenviarRequest
)

from app.services.usuario_service import (
    crear_usuario,
    login_usuario,
    login_paso1,
    login_paso2,
    login_paso3,
    login_reenviar
)



router = APIRouter()



# CREAR USUARIO

@router.post("/crear")
def crear(usuario: UsuarioCreate):

    return crear_usuario(usuario)



# LOGIN (DIRECTO — SIN 3 PASOS)

@router.post("/login")
def login(usuario: UsuarioLogin):



    return login_usuario(usuario)



# =========================
# 3 PASOS
# =========================

# PASO 1 — CREDENCIALES

@router.post("/paso1")
def paso1(usuario: Paso1Request):

    return login_paso1(usuario)



# PASO 2 — CÓDIGO OTP

@router.post("/paso2")
def paso2(datos: Paso2Request):

    return login_paso2(datos)



# PASO 3 — CONFIRMAR

@router.post("/paso3")
def paso3(datos: Paso3Request):

    return login_paso3(datos)



# REENVIAR CÓDIGO OTP

@router.post("/reenviar")
def reenviar(datos: ReenviarRequest):

    return login_reenviar(datos)
