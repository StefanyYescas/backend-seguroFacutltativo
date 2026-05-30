from fastapi import APIRouter

from app.schemas.usuario_schema import (
    UsuarioCreate,
    UsuarioLogin
)

from app.services.usuario_service import (
    crear_usuario,
    login_usuario
)



router = APIRouter()



# CREAR USUARIO

@router.post("/crear")
def crear(usuario: UsuarioCreate):

    return crear_usuario(usuario)



# LOGIN

@router.post("/login")
def login(usuario: UsuarioLogin):



    return login_usuario(usuario)
