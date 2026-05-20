from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Form
from fastapi import HTTPException

from app.services.solicitud_service import (
    crear_solicitud,
    actualizar_solicitud,
    entregar_seguro,
    obtener_solicitudes,
    obtener_historial,
    obtener_rechazadas,
    obtener_aprobadas
)

from app.schemas.solicitud_schema import (
    SolicitudUpdate
)

router = APIRouter()


# =========================
# CREAR SOLICITUD
# =========================
@router.post("/")
async def crear(

    idUsuario: str = Form(...),

    constancia: UploadFile = File(...),

    nss: UploadFile = File(...)
):

    if constancia.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Constancia debe ser PDF"
        )

    if nss.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="NSS debe ser PDF"
        )

    return await crear_solicitud(
        idUsuario,
        constancia,
        nss
    )


# =========================
# ACTUALIZAR
# =========================
@router.put("/{idSolicitud}")
def actualizar(
    idSolicitud: str,
    solicitud: SolicitudUpdate
):

    return actualizar_solicitud(
        idSolicitud,
        solicitud
    )


# =========================
# APROBADAS
# =========================
@router.get("/aprobadas")
def aprobadas():
    return obtener_aprobadas()


# =========================
# RECHAZADAS
# =========================
@router.get("/rechazadas")
def rechazadas():
    return obtener_rechazadas()


# =========================
# TODAS
# =========================
@router.get("/")
def obtener():
    return obtener_solicitudes()


# =========================
# HISTORIAL
# =========================
@router.get("/historial")
def historial():
    return obtener_historial()


# =========================
# ENTREGAR SEGURO
# =========================
from fastapi import BackgroundTasks

@router.put("/entregar/{idSolicitud}")
async def entregar(

    idSolicitud: str,

    background_tasks: BackgroundTasks,

    observacion: str = Form(...),

    archivo: UploadFile = File(...)
):

    return await entregar_seguro(

        idSolicitud,

        observacion,

        archivo,

        background_tasks
    )