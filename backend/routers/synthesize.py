"""
POST /api/v1/synthesize
Receives uploaded document, extracts text, returns synthesized audio.
"""

import os
import time
import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.parser import DocumentParser
from services.tts_engine import TTSEngine
from middleware.security import validate_file

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Access the singleton from app.py
def get_tts_engine() -> TTSEngine:
    # Import here to avoid circular import
    from app import tts_engine
    return tts_engine

RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "5")

@router.post("/synthesize")
@limiter.limit(f"{RATE_LIMIT}/minute")
async def synthesize(request: Request, file: UploadFile = File(...)):
    """
    Accept a document file (.txt, .pdf, .docx), synthesize speech, return WAV audio.
    """
    start_time = time.time()

    # ── Read file into memory ─────────────────────────────────────────────────
    file_bytes = await file.read()
    file_size = len(file_bytes)
    filename = file.filename or "upload"

    logger.info(f"Synthesis request — file={filename!r}, size={file_size}B")

    # ── Validate first (returns proper error codes even during model warm-up) ──
    validate_file(filename, file_bytes, file_size)

    # ── Check model is loaded ────────────────────────────────────────────────
    tts = get_tts_engine()
    if not tts.is_loaded:
        raise HTTPException(503, "TTS model is still loading. Please wait and try again.")

    # ── Parse document ────────────────────────────────────────────────────────
    ext = Path(filename).suffix.lower()
    try:
        parser = DocumentParser()
        text = parser.parse(file_bytes, ext)
    except ValueError as e:
        raise HTTPException(422, str(e))

    if not text or not text.strip():
        raise HTTPException(422, "Document appears to be empty or contains no extractable text.")

    logger.info(f"Extracted {len(text)} characters from {ext} document.")

    # ── Synthesize ────────────────────────────────────────────────────────────
    reference_wav = os.getenv("REFERENCE_WAV_PATH", "./voice_data/reference.wav")
    language = os.getenv("TTS_LANGUAGE", "en")

    try:
        audio_bytes = tts.synthesize(text, reference_wav, language)
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}", exc_info=True)
        raise HTTPException(500, "TTS synthesis failed. Please try again.")

    elapsed = time.time() - start_time
    logger.info(f"Synthesis complete — {len(audio_bytes)} bytes audio, {elapsed:.2f}s elapsed.")

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": 'attachment; filename="narration.wav"',
            "X-Processing-Time": f"{elapsed:.2f}s",
        }
    )
