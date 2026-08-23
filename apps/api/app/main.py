import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.db.database import initialise_database


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Foundation API for a synthetic-data payment risk intelligence demo. "
        "No Razorpay private systems or data are used."
    ),
)


# ---------------------------------------------------------
# CORS CONFIGURATION
# ---------------------------------------------------------

# Explicitly allow production Vercel frontend, Render backend, and local dev
ALLOWED_ORIGINS = [
    "https://razorpay-ai-risk-manager.vercel.app",
    "https://razorpay-ai-risk-manager-web.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Pattern for Vercel preview branch deployments
DEFAULT_ORIGIN_REGEX = r"^https://(razorpay-ai-risk-manager\.vercel\.app|razorpay-ai-risk-manager-git-[A-Za-z0-9_-]+\.vercel\.app)$"

# Read from Render env or fall back to default regex
env_regex = os.getenv("ALLOW_ORIGIN_REGEX", "").strip()
origin_regex = env_regex if env_regex else DEFAULT_ORIGIN_REGEX

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="api",
        version=settings.app_version,
    )


# ---------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------

app.include_router(api_router)


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------

@app.on_event("startup")
def startup() -> None:
    initialise_database()