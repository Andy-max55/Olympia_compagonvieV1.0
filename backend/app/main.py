from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.endpoints.chat import router as chat_router
from app.api.endpoints.users import router as users_router
from app.core.config import settings
from app.core.database import Base, engine
from app.models.user import User  # noqa: F401 — enregistre le modèle sur Base.metadata

# Création des tables au démarrage, une fois la configuration chargée.
Base.metadata.create_all(bind=engine)

# Initialisation de l'application FastAPI à partir de la configuration centralisée.
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG_MODE else None,
    redoc_url=None,
)

# Configuration stricte de la sécurité CORS (Empêche les accès non autorisés au backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])

# Montage en dernier : les routes /api/* restent prioritaires.
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
