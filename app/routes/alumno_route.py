from fastapi import APIRouter

from app.schemas.alumno_schema import (
    AlumnoCreate
)

from app.services.alumno_service import (
    crear_alumno
)

router = APIRouter()



# CREAR ALUMNO

@router.post("/crear")
def crear(alumno: AlumnoCreate):

    return crear_alumno(alumno)