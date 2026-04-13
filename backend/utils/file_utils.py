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
