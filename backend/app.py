"""
Voice-Cloned TTS Web Application — FastAPI Backend
Entry point. Wires together all components.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routers.synthesize import router as synthesize_router
from services.tts_engine import TTSEngine

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── TTS Engine singleton ──────────────────────────────────────────────────────
tts_engine = TTSEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load TTS model at startup, clean up on shutdown."""
    logger.info("Starting up — loading TTS model...")
    try:
        tts_engine.load()
        logger.info("TTS model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load TTS model: {e}")
        # Don't crash — health endpoint will report model_loaded: false
    yield
    logger.info("Shutting down.")

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Voice TTS API",
    version="1.0.0",
    description="Document-to-speech using cloned voice synthesis.",
    lifespan=lifespan,
    docs_url="/docs",      # Disable in production if desired
    redoc_url="/redoc",
)

# ── Rate limit error handler ──────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
allowed_origins_raw = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000"
)
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(synthesize_router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok" if tts_engine.is_loaded else "loading",
        "model_loaded": tts_engine.is_loaded,
        "version": "1.0.0"
    }

# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."}
    )
