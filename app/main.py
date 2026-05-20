from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routes.usuario_route import router as usuario_router
from app.routes.solicitud_route import router as solicitud_router
from app.routes.admin_route import router as admin_router
from app.routes.alumno_route import router as alumno_router

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/app/uploads",
    StaticFiles(directory="app/uploads"),
    name="uploads"
)


app.include_router(
    usuario_router,
    prefix="/usuario"
)


app.include_router(
    solicitud_router,
    prefix="/solicitud"
)

app.include_router(
    admin_router,
    prefix="/admin"
)

app.include_router(
    alumno_router,
    prefix="/alumno"
)

@app.get("/")
def home():
    return {
        "ok": True
    }

