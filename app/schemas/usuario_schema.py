from pydantic import BaseModel, EmailStr



class UsuarioCreate(BaseModel):
    nomCompleto: str
    numControl: str
    correo: EmailStr
    contrasena: str
    rol: str



class UsuarioLogin(BaseModel):
    numControl: str
    contrasena: str



# =========================
# 3 PASOS
# =========================

class Paso1Request(BaseModel):
    numControl: str
    contrasena: str
    rol: str



class Paso2Request(BaseModel):
    tempToken: str
    codigo: str



class Paso3Request(BaseModel):
    tempToken: str
    rol: str



class ReenviarRequest(BaseModel):
    tempToken: str