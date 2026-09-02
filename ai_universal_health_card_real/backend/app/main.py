from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.db.session import Base, engine
from app.db import models  # noqa: F401

from app.api import (
    auth,
    profile,
    reports,
    qr,
    emergency,
    emergency_docs,
    downloads,
    admin,
    doctor,
)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Secure digital health-card platform with "
        "medical report analysis and QR emergency access."
    ),
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.public_base_url.rstrip("/")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# FRONTEND PATH
# =========================================================

frontend = Path(__file__).resolve().parents[2] / "frontend"


# =========================================================
# API ROUTES
# =========================================================

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(reports.router)
app.include_router(qr.router)
app.include_router(emergency.router)
app.include_router(emergency_docs.router)
app.include_router(downloads.router)
app.include_router(admin.router)
app.include_router(doctor.router)


# =========================================================
# HOME PAGE
# =========================================================

@app.get("/")
def home():
    return FileResponse(frontend / "index.html")


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
    }


# =========================================================
# FRONTEND STATIC FILES
# =========================================================
# IMPORTANT:
# This must be AFTER all API routes.
#
# This allows:
# /medical-history.html
# /dashboard.html
# /profile.html
# /login.html
# /register.html
# /hospital.jpg
# etc.
# =========================================================

app.mount(
    "/",
    StaticFiles(
        directory=str(frontend),
        html=True,
    ),
    name="frontend",
)