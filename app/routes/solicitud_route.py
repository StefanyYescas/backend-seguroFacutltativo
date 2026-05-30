from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import BackgroundTasks

from app.services.solicitud_service import (

    crear_solicitud,

    actualizar_solicitud,

    entregar_seguro,

    generar_preview_seguro,

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
# PREVIEW PDF
# =========================

@router.post("/preview/{idSolicitud}")
async def preview_pdf(

    idSolicitud: str,

    observacion: str = Form(...)

):

    return await generar_preview_seguro(

        idSolicitud,

        observacion
    )



# =========================
# ENTREGAR SEGURO
# =========================

@router.put("/entregar/{idSolicitud}")
async def entregar(

    idSolicitud: str,

    observacion: str = Form(...),

    rutaSeguro: str = Form(...),

    background_tasks: BackgroundTasks = None

):

    return await entregar_seguro(

        idSolicitud,

        observacion,

        rutaSeguro,

        background_tasks
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