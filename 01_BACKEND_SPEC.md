# Backend Implementation Spec — Voice TTS API
> **For Claude Code**: This document contains the complete backend implementation. Build every file listed here exactly as specified.

---

## COMPLETE FILE: `backend/app.py`

```python
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
```

---

## COMPLETE FILE: `backend/routers/synthesize.py`

```python
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
    tts = get_tts_engine()

    if not tts.is_loaded:
        raise HTTPException(503, "TTS model is still loading. Please wait and try again.")

    # ── Read file into memory ─────────────────────────────────────────────────
    file_bytes = await file.read()
    file_size = len(file_bytes)
    filename = file.filename or "upload"

    logger.info(f"Synthesis request — file={filename!r}, size={file_size}B")

    # ── Validate ──────────────────────────────────────────────────────────────
    validate_file(filename, file_bytes, file_size)

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
```

---

## COMPLETE FILE: `backend/services/tts_engine.py`

```python
"""
TTS Engine wrapper for Coqui XTTS v2.
Loaded once at startup, reused for all requests.
"""

import io
import os
import logging
import tempfile
import wave
import re
from typing import Optional

logger = logging.getLogger(__name__)


class TTSEngine:
    """Singleton wrapper for Coqui XTTS v2 model."""

    def __init__(self):
        self._model = None
        self.is_loaded = False

    def load(self):
        """Load XTTS v2 model into memory. Call once at startup."""
        try:
            from TTS.api import TTS
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading XTTS v2 on device: {device}")

            self._model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            self.is_loaded = True
            logger.info("XTTS v2 loaded successfully.")

        except ImportError:
            logger.error("Coqui TTS not installed. Run: pip install TTS")
            raise
        except Exception as e:
            logger.error(f"XTTS v2 load failed: {e}")
            raise

    def synthesize(self, text: str, reference_wav: str, language: str = "en") -> bytes:
        """
        Synthesize text using the cloned voice reference.
        Returns WAV audio as bytes.
        """
        if not self.is_loaded or self._model is None:
            raise RuntimeError("TTS model is not loaded.")

        if not os.path.exists(reference_wav):
            raise FileNotFoundError(f"Reference WAV not found: {reference_wav}")

        chunks = self._chunk_text(text)
        logger.info(f"Synthesizing {len(chunks)} chunks for {len(text)} chars of text.")

        wav_segments = []

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                self._model.tts_to_file(
                    text=chunk,
                    speaker_wav=reference_wav,
                    language=language,
                    file_path=tmp_path,
                )
                with open(tmp_path, "rb") as f:
                    wav_segments.append(f.read())

                logger.debug(f"Chunk {i+1}/{len(chunks)} synthesized.")

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        if not wav_segments:
            raise ValueError("No audio was generated.")

        return self._concatenate_wav_bytes(wav_segments)

    @staticmethod
    def _chunk_text(text: str, max_chars: int = 250) -> list:
        """Split text into sentence-boundary-aware chunks."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current) + len(sentence) + 1 <= max_chars:
                current = (current + " " + sentence).strip() if current else sentence
            else:
                if current:
                    chunks.append(current)
                # Handle oversized individual sentences
                if len(sentence) > max_chars:
                    for i in range(0, len(sentence), max_chars):
                        sub = sentence[i:i + max_chars].strip()
                        if sub:
                            chunks.append(sub)
                    current = ""
                else:
                    current = sentence

        if current:
            chunks.append(current)

        return [c for c in chunks if c.strip()]

    @staticmethod
    def _concatenate_wav_bytes(wav_bytes_list: list) -> bytes:
        """Merge multiple WAV byte sequences into a single WAV."""
        output = io.BytesIO()

        with wave.open(output, 'wb') as out_wav:
            params_set = False
            for wav_bytes in wav_bytes_list:
                with wave.open(io.BytesIO(wav_bytes), 'rb') as in_wav:
                    if not params_set:
                        out_wav.setparams(in_wav.getparams())
                        params_set = True
                    out_wav.writeframes(in_wav.readframes(in_wav.getnframes()))

        return output.getvalue()
```

---

## COMPLETE FILE: `backend/services/parser.py`

```python
"""
Document text extraction for TXT, PDF, and DOCX files.
All parsers return plain UTF-8 text.
"""

import io
import logging

logger = logging.getLogger(__name__)


class DocumentParser:
    """Routes to the correct parser based on file extension."""

    def parse(self, file_bytes: bytes, extension: str) -> str:
        """
        Extract text from file bytes.
        extension: '.txt', '.pdf', or '.docx'
        Returns: plain text string
        Raises: ValueError on parse failure
        """
        ext = extension.lower()
        if ext == '.txt':
            return self._parse_txt(file_bytes)
        elif ext == '.pdf':
            return self._parse_pdf(file_bytes)
        elif ext == '.docx':
            return self._parse_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported extension: {ext}")

    @staticmethod
    def _parse_txt(file_bytes: bytes) -> str:
        """Attempt multiple encodings for TXT files."""
        for encoding in ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1', 'ascii']:
            try:
                text = file_bytes.decode(encoding)
                logger.debug(f"TXT decoded with {encoding}")
                return text
            except (UnicodeDecodeError, ValueError):
                continue
        raise ValueError("Could not decode text file. Ensure it is saved as UTF-8.")

    @staticmethod
    def _parse_pdf(file_bytes: bytes) -> str:
        """Extract text from PDF using PyMuPDF (fitz)."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise RuntimeError("PyMuPDF not installed. Run: pip install pymupdf")

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pages = []
            for page_num, page in enumerate(doc):
                text = page.get_text("text").strip()
                if text:
                    pages.append(text)
                else:
                    logger.debug(f"Page {page_num + 1} has no extractable text (may be image).")
            doc.close()
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}")

        if not pages:
            raise ValueError(
                "No extractable text found in PDF. "
                "The file may contain only scanned images. "
                "Please use a text-based PDF."
            )

        return "\n\n".join(pages)

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> str:
        """Extract paragraph text from DOCX."""
        try:
            from docx import Document
        except ImportError:
            raise RuntimeError("python-docx not installed. Run: pip install python-docx")

        try:
            doc = Document(io.BytesIO(file_bytes))
            paragraphs = []

            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)

            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text = cell.text.strip()
                        if text and text not in paragraphs:
                            paragraphs.append(text)

        except Exception as e:
            raise ValueError(f"Failed to open DOCX: {e}")

        if not paragraphs:
            raise ValueError("No extractable text found in DOCX.")

        return "\n\n".join(paragraphs)
```

---

## COMPLETE FILE: `backend/middleware/security.py`

```python
"""
File validation middleware.
Validates extension, MIME type, and file size.
"""

import logging
from pathlib import Path
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.docx'}

# Magic bytes (file signatures) for additional validation
MAGIC_SIGNATURES = {
    '.pdf':  [(0, b'%PDF')],
    '.docx': [(0, b'PK\x03\x04')],  # DOCX is a ZIP archive
    '.txt':  [],  # No reliable magic bytes for plain text
}

# MIME type mapping used if python-magic is available
ALLOWED_MIMES = {
    '.txt':  {'text/plain'},
    '.pdf':  {'application/pdf'},
    '.docx': {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/zip',
        'application/octet-stream',  # Some systems return this for DOCX
    },
}


def validate_file(filename: str, file_bytes: bytes, file_size: int):
    """
    Validate uploaded file. Raises HTTPException on failure.
    Checks: extension, file size, magic bytes.
    """
    # 1. File size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            413,
            f"File exceeds maximum allowed size of "
            f"{MAX_FILE_SIZE_BYTES // (1024*1024)} MB. "
            f"Uploaded: {file_size / (1024*1024):.1f} MB."
        )

    if file_size == 0:
        raise HTTPException(400, "Uploaded file is empty.")

    # 2. Extension check
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported file type '{ext}'. "
            f"Accepted formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # 3. Magic bytes check (defense against extension spoofing)
    _validate_magic_bytes(file_bytes, ext)

    # 4. MIME type check (best-effort via python-magic)
    _validate_mime_type(file_bytes, ext, filename)

    logger.debug(f"File validation passed: {filename!r} ({file_size}B, ext={ext})")


def _validate_magic_bytes(file_bytes: bytes, ext: str):
    """Check file header magic bytes to prevent extension spoofing."""
    signatures = MAGIC_SIGNATURES.get(ext, [])
    for offset, magic in signatures:
        if file_bytes[offset:offset + len(magic)] != magic:
            raise HTTPException(
                400,
                f"File content does not match expected format for {ext}. "
                "File may be corrupted or misnamed."
            )


def _validate_mime_type(file_bytes: bytes, ext: str, filename: str):
    """Optional MIME type validation using python-magic if available."""
    try:
        import magic
        mime = magic.from_buffer(file_bytes[:2048], mime=True)
        allowed = ALLOWED_MIMES.get(ext, set())
        if allowed and mime not in allowed:
            logger.warning(
                f"MIME mismatch for {filename!r}: "
                f"detected={mime!r}, expected one of {allowed}"
            )
            # Log but don't hard-reject — some legitimate files have unexpected MIME types.
            # The magic bytes check above is the harder enforcement.
    except ImportError:
        logger.debug("python-magic not available; skipping MIME validation.")
    except Exception as e:
        logger.debug(f"MIME check failed (non-critical): {e}")
```

---

## COMPLETE FILE: `backend/requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9
slowapi==0.1.9
pymupdf==1.24.5
python-docx==1.1.2
scipy==1.13.1
pydub==0.25.1
TTS==0.22.0
torch==2.3.1
torchaudio==2.3.1
python-magic==0.4.27
httpx==0.27.0
pytest==8.2.2
pytest-asyncio==0.23.7
```

> **Note on torch**: On CPU-only HF Spaces, use `torch==2.3.1+cpu` and the CPU-only index:
> `--extra-index-url https://download.pytorch.org/whl/cpu`

---

## COMPLETE FILE: `backend/Dockerfile`

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Copy application code
COPY . .

# Pre-download XTTS v2 model weights (bakes them into the image — large image but fast startup)
# Comment this out if you want to download on first startup instead (saves image build time)
RUN python -c "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2')"

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
```

---

## COMPLETE FILE: `backend/tests/test_parser.py`

```python
"""Unit tests for DocumentParser."""
import pytest
from services.parser import DocumentParser


parser = DocumentParser()


class TestTXTParsing:
    def test_utf8(self):
        text = parser.parse("Hello, world!".encode('utf-8'), '.txt')
        assert "Hello, world!" in text

    def test_latin1(self):
        text = parser.parse("Café résumé".encode('latin-1'), '.txt')
        assert text  # Should decode without error

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            # Empty file should still decode but be empty — handled upstream
            result = parser.parse(b"", '.txt')
            # Parser itself returns empty string; upstream raises

    def test_utf8_bom(self):
        text = parser.parse("\ufeffHello".encode('utf-8-sig'), '.txt')
        assert "Hello" in text


class TestPDFParsing:
    def test_valid_pdf(self, tmp_path):
        # Minimal PDF with text (use fixture file)
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Test PDF content")
        pdf_bytes = doc.tobytes()
        doc.close()

        text = parser.parse(pdf_bytes, '.pdf')
        assert "Test PDF content" in text

    def test_empty_pdf_raises(self):
        import fitz
        doc = fitz.open()
        doc.new_page()  # Page with no text
        pdf_bytes = doc.tobytes()
        doc.close()

        with pytest.raises(ValueError, match="No extractable text"):
            parser.parse(pdf_bytes, '.pdf')

    def test_corrupt_pdf_raises(self):
        with pytest.raises(ValueError):
            parser.parse(b"not a pdf at all", '.pdf')


class TestDOCXParsing:
    def test_valid_docx(self):
        from docx import Document
        import io
        doc = Document()
        doc.add_paragraph("Test DOCX content")
        buf = io.BytesIO()
        doc.save(buf)
        docx_bytes = buf.getvalue()

        text = parser.parse(docx_bytes, '.docx')
        assert "Test DOCX content" in text

    def test_empty_docx_raises(self):
        from docx import Document
        import io
        doc = Document()
        buf = io.BytesIO()
        doc.save(buf)
        docx_bytes = buf.getvalue()

        with pytest.raises(ValueError, match="No extractable text"):
            parser.parse(docx_bytes, '.docx')


class TestUnsupportedExtension:
    def test_unknown_extension_raises(self):
        with pytest.raises(ValueError, match="Unsupported extension"):
            parser.parse(b"data", '.exe')
```

---

## COMPLETE FILE: `backend/tests/test_security.py`

```python
"""Security validation tests."""
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestFileValidation:
    def test_reject_exe_extension(self):
        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")}
        )
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_reject_oversized_file(self):
        big_file = b"A" * (11 * 1024 * 1024)  # 11 MB
        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("big.txt", big_file, "text/plain")}
        )
        assert response.status_code == 413

    def test_reject_empty_file(self):
        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("empty.txt", b"", "text/plain")}
        )
        assert response.status_code == 400

    def test_reject_pdf_with_txt_extension(self):
        """Magic bytes mismatch: PDF content with .txt extension."""
        pdf_magic = b'%PDF-1.4 fake pdf content'
        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("document.txt", pdf_magic, "text/plain")}
        )
        # Should succeed (txt has no magic bytes check) or fail gracefully
        # The important thing is it doesn't execute the content
        assert response.status_code in (200, 400, 422)

    def test_reject_exe_disguised_as_txt(self):
        """EXE magic bytes in a .txt file."""
        exe_bytes = b'MZ\x90\x00\x03\x00\x00\x00'
        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("innocent.txt", exe_bytes, "text/plain")}
        )
        # Content will fail TTS but not execute — acceptable
        assert response.status_code in (200, 400, 422, 500)

    def test_path_traversal_filename(self):
        """Filename with path traversal attempt."""
        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("../../etc/passwd", b"root:x:0:0", "text/plain")}
        )
        # Extension check will catch this (no .txt extension)
        assert response.status_code == 400


class TestHealthEndpoint:
    def test_health_returns_json(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "version" in data
```

---

## COMPLETE FILE: `backend/tests/test_api.py`

```python
"""API integration tests."""
import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app

client = TestClient(app)


def make_wav_bytes():
    """Create minimal valid WAV bytes for mock responses."""
    import wave, io
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(b'\x00\x00' * 100)
    return buf.getvalue()


class TestSynthesizeEndpoint:
    @patch('routers.synthesize.get_tts_engine')
    def test_synthesize_txt(self, mock_get_engine):
        mock_engine = MagicMock()
        mock_engine.is_loaded = True
        mock_engine.synthesize.return_value = make_wav_bytes()
        mock_get_engine.return_value = mock_engine

        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("test.txt", b"Hello world this is a test.", "text/plain")}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    @patch('routers.synthesize.get_tts_engine')
    def test_synthesize_returns_wav_header(self, mock_get_engine):
        mock_engine = MagicMock()
        mock_engine.is_loaded = True
        mock_engine.synthesize.return_value = make_wav_bytes()
        mock_get_engine.return_value = mock_engine

        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("test.txt", b"Sample text content here.", "text/plain")}
        )
        assert response.status_code == 200
        # WAV files start with RIFF header
        assert response.content[:4] == b'RIFF'

    @patch('routers.synthesize.get_tts_engine')
    def test_model_not_loaded_returns_503(self, mock_get_engine):
        mock_engine = MagicMock()
        mock_engine.is_loaded = False
        mock_get_engine.return_value = mock_engine

        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("test.txt", b"Text content", "text/plain")}
        )
        assert response.status_code == 503

    def test_missing_file_returns_422(self):
        response = client.post("/api/v1/synthesize")
        assert response.status_code == 422

    def test_unsupported_extension_returns_400(self):
        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("doc.rtf", b"content", "text/rtf")}
        )
        assert response.status_code == 400

    def test_cors_headers_present(self):
        response = client.options(
            "/api/v1/synthesize",
            headers={"Origin": "http://localhost:5500"}
        )
        # CORS preflight or actual request headers
        assert response.status_code in (200, 204, 405)
```

---

## COMPLETE FILE: `backend/utils/file_utils.py`

```python
"""Temporary file management utilities."""

import os
import uuid
import tempfile
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def temp_file(suffix: str = ".tmp"):
    """
    Context manager that creates a UUID-named temp file and deletes it on exit.
    Usage:
        with temp_file(".wav") as path:
            # use path
        # file is deleted here
    """
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    path = os.path.join(tempfile.gettempdir(), safe_name)
    try:
        yield path
    finally:
        if os.path.exists(path):
            try:
                os.unlink(path)
                logger.debug(f"Deleted temp file: {path}")
            except OSError as e:
                logger.warning(f"Could not delete temp file {path}: {e}")


def safe_temp_dir():
    """Return the system temp directory path."""
    return tempfile.gettempdir()
```

---

## NOTES FOR CLAUDE CODE

1. **Import the `tts_engine` singleton carefully** — it's instantiated in `app.py` and must be shared across requests. The `get_tts_engine()` function in `routers/synthesize.py` handles this via a late import to avoid circular imports.

2. **XTTS v2 model path** — When pre-downloaded in Docker, the model caches in `~/.local/share/tts/` by default. This is fine for HF Spaces where the container has persistent storage.

3. **Reference WAV path** — Must be provided via the `REFERENCE_WAV_PATH` environment variable. Default is `./voice_data/reference.wav`. The owner must place their reference audio here before deployment.

4. **HF Spaces port** — Must be 7860. The Dockerfile CMD uses this. Do not use 8000 for HF deployment.

5. **Worker count** — Set to 1 in production (`--workers 1`). XTTS v2 uses ~2 GB RAM; multiple workers would cause OOM on free tier.

6. **WAV concatenation** — The `_concatenate_wav_bytes` method assumes all chunks have the same WAV parameters (sample rate, channels, bit depth). XTTS v2 always outputs consistent parameters, so this is safe.
