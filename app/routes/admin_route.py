from fastapi import APIRouter

from app.schemas.admin_schema import (
    AdminCreate
)

from app.services.admin_service import (
    crear_admin
)

router = APIRouter()


# =========================
# CREAR ADMIN
# =========================
@router.post("/crear")
def crear(admin: AdminCreate):

    return crear_admin(admin)