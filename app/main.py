"""FastAPI Main Application Entry Point."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.logging import logger
from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("==================================================")
    logger.info("  YouTube Social & Contact Intelligence System   ")
    logger.info("==================================================")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"YouTube API Key configured: {settings.has_youtube_api_key}")
    logger.info(f"Gemini API Key configured:  {settings.has_gemini_api_key}")
    logger.info(f"Server binding: http://{settings.HOST}:{settings.PORT}")
    yield
    logger.info("Application shutting down...")


app = FastAPI(
    title="YouTube Social & Contact Intelligence System",
    description="Evidence-based social media and contact extraction engine powered by LangGraph, LangChain, Google Gemini, and YouTube Data API.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)

# Mount frontend static directory
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(str(frontend_dir / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development")
    )
