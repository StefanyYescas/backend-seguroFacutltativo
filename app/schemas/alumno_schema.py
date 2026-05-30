from pydantic import BaseModel



# CREAR ALUMNO

class AlumnoCreate(BaseModel):

    carrera: str
    semestre: int
    idUsuario: str