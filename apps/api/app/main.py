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

app.add_middleware(
    CORSMiddleware,
    # During local development allow all origins so the Vite dev server (on variable ports)
    # can access the API without CORS issues. In production this should be locked down.
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="api", version=settings.app_version)


app.include_router(api_router)


@app.on_event("startup")
def startup() -> None:
    initialise_database()


# Development-time fallback CORS handling: ensure the API emits CORS headers
# for arbitrary localhost origins and responds to preflight OPTIONS requests.
# This is intentionally conservative for local dev only — in production rely on
# a stricter CORSMiddleware configuration or a reverse proxy.
from starlette.responses import Response as StarletteResponse

@app.middleware("http")
async def _dev_cors_middleware(request, call_next):
    origin = request.headers.get("origin")
    if request.method == "OPTIONS":
        # Return a short-circuit preflight response
        if origin:
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS,PUT,DELETE",
                "Access-Control-Allow-Headers": request.headers.get(
                    "access-control-request-headers", "*"
                ),
            }
        else:
            headers = {}
        return StarletteResponse(status_code=204, headers=headers)

    response = await call_next(request)
    if origin:
        response.headers.setdefault("Access-Control-Allow-Origin", origin)
        response.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        response.headers.setdefault("Access-Control-Allow-Headers", "*")
    return response
