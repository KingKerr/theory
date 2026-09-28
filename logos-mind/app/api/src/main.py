from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core_api.core.config import get_settings
from core_api.routes.health import router as health_router
from core_api.routes.sessions import router as sessions_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix, tags=["health"])
app.include_router(sessions_router, prefix=settings.api_prefix, tags=["sessions"])