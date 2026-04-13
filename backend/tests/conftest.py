"""
pytest configuration for backend tests.
Sets environment variables before any app imports so rate limits are relaxed.
"""
import os

# Relax rate limit for tests (default 5/min would cause 429 during test suite)
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "1000")
os.environ.setdefault("REFERENCE_WAV_PATH", "./voice_data/reference.wav")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5500")
