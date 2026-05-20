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
    