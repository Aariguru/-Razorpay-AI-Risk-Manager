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

import os

# CORS configuration: prefer explicit production origin list when provided.
if os.getenv("APP_ENV", "").lower() == "production":
    # Allow explicit override via ALLOW_ORIGIN_REGEX in the environment. If not set,
    # default to the known Vercel production host and allow Vercel preview domains.
    allow_origin_regex = os.getenv("ALLOW_ORIGIN_REGEX")
    if not allow_origin_regex:
        allow_origin_regex = r"^https://(razorpay-ai-risk-manager\.vercel\.app|razorpay-ai-risk-manager-git-[A-Za-z0-9_-]+\.vercel\.app)$"
else:
    allow_origin_regex = r"https?://(localhost|127\.0\.0\.1|\[::1\])(?::\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=allow_origin_regex,

    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

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


app.include_router(api_router)


@app.on_event("startup")
def startup() -> None:
    initialise_database()