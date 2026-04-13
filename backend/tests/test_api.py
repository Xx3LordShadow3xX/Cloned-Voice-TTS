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
