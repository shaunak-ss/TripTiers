from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers.collab import router as collab_router
from app.routers.health import router as health_router
from app.routers.me import router as me_router
from app.routers.trips import router as trips_router
from app.utils.errors import AppError
from app.utils.logger import configure_logging, get_logger

log = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="TripTiers API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": "validation_error", "message": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error", error=str(exc))
        detail = f"{type(exc).__name__}: {exc}" if settings.environment != "production" else "An unexpected error occurred."
        return JSONResponse(status_code=500, content={"error": "internal_error", "message": detail})

    app.include_router(health_router)
    app.include_router(me_router)
    app.include_router(trips_router)
    app.include_router(collab_router)
    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=settings.environment == "development")
