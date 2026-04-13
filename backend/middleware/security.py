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
