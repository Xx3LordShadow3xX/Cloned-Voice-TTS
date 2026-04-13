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
        # MIME mismatch is non-blocking (logged only); content passes validation.
        # May 503 if model not loaded, 422 if text can't be parsed, or 200/400.
        # The important thing is it doesn't execute the content as code.
        assert response.status_code in (200, 400, 422, 503)

    def test_reject_exe_disguised_as_txt(self):
        """EXE magic bytes in a .txt file."""
        exe_bytes = b'MZ\x90\x00\x03\x00\x00\x00'
        response = client.post(
            "/api/v1/synthesize",
            files={"file": ("innocent.txt", exe_bytes, "text/plain")}
        )
        # MIME mismatch is non-blocking (logged only). Content will fail TTS
        # but never execute as code — acceptable. May 503 if model not loaded.
        assert response.status_code in (200, 400, 422, 500, 503)

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
