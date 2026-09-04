"""FastAPI application entry point and app factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router


def create_app() -> FastAPI:
    """Create the API application with only local frontend CORS enabled."""
    app = FastAPI(title="AegisAPI")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(api_v1_router)
    return app


app = create_app()
