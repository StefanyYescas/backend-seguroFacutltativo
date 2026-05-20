from pydantic import BaseModel
from typing import Optional


# =========================
# ACTUALIZAR SOLICITUD
# =========================
class SolicitudUpdate(BaseModel):

    estado: str

    observacion: Optional[str] = None

    fechaEntrega: Optional[str] = None