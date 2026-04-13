# Security Checklist & Testing Plan
> **For Claude Code**: Use this as a checklist during implementation and a reference for writing test cases.

---

## SECURITY CHECKLIST

### File Upload Security

- [ ] **Extension allowlist**: Only `.txt`, `.pdf`, `.docx` accepted — reject everything else with HTTP 400
- [ ] **MIME type validation**: Use `python-magic` to independently verify MIME type, separate from extension
- [ ] **Magic bytes check**: PDF files must start with `%PDF`, DOCX with `PK\x03\x04`
- [ ] **File size hard limit**: Enforce 10 MB server-side — reject with HTTP 413 (do NOT rely on client-side only)
- [ ] **Empty file rejection**: Reject zero-byte files with HTTP 400
- [ ] **UUID filename**: ALL uploaded files renamed to `uuid4().hex + suffix` before any disk operation
- [ ] **Isolated temp directory**: Use `tempfile.gettempdir()` — never user-supplied paths
- [ ] **No file execution**: Uploaded files are NEVER executed, only parsed by Python libraries
- [ ] **Immediate deletion**: Temp files deleted in a `finally` block — even if processing fails
- [ ] **No path traversal**: File path sanitized — no `..`, `/`, or `\` in filename used for storage

### API Security

- [ ] **Rate limiting**: 5 requests per IP per minute via `slowapi`
- [ ] **CORS configured**: Only your GitHub Pages URL in `allow_origins` (not `"*"`)
- [ ] **HTTPS only**: TLS enforced by HF Spaces hosting
- [ ] **No eval/exec**: No user input passed to `eval()`, `exec()`, `subprocess`, or `os.system()`
- [ ] **Timeout on requests**: 120-second server timeout to prevent resource exhaustion
- [ ] **Error messages safe**: Server errors never expose stack traces, file paths, or internal details

### Data Privacy

- [ ] **No text logging**: Extracted document text NEVER written to logs or files
- [ ] **No persistent storage**: No uploaded file content stored after the request completes
- [ ] **No analytics on content**: No calls to external services with document content
- [ ] **Privacy notice displayed**: Frontend footer states files are processed in memory and deleted
- [ ] **Voice model not exposed**: No API endpoint that returns or exposes model weights

### Content Security (Frontend)

- [ ] **Text sanitized before display**: Use `textContent` not `innerHTML` for any user-derived text displayed in browser
- [ ] **No inline scripts**: No `<script>` tags with user content
- [ ] **Blob URL cleanup**: `URL.revokeObjectURL()` called when audio is no longer needed
- [ ] **No localStorage with sensitive data**: No document content or audio stored in browser storage

### Legal Compliance

- [ ] **AI disclosure**: Visible text on every page where audio plays: "Audio generated using AI voice synthesis"
- [ ] **Privacy statement**: Footer with data handling explanation
- [ ] **Terms of use**: Statement that users are responsible for their uploaded content
- [ ] **No facilitation of impersonation**: No user-selectable voice targets in MVP

---

## TESTING PLAN

### Test Suite Structure

```
tests/
├── test_parser.py        # Unit: DocumentParser (TXT, PDF, DOCX)
├── test_security.py      # Unit: file validation middleware
├── test_api.py           # Integration: API endpoints (TTS mocked)
├── test_tts_engine.py    # Unit: chunk_text, concatenate_wav_bytes (model mocked)
└── fixtures/
    ├── sample.txt         # Valid TXT with Unicode content
    ├── sample.pdf         # Valid PDF with text
    ├── sample.docx        # Valid DOCX with paragraphs
    ├── empty.txt          # Zero-byte file
    ├── scanned.pdf        # PDF with no extractable text (image-only)
    ├── large.txt          # 11 MB file (for size limit testing)
    └── malware.exe.txt    # Executable bytes with .txt extension
```

### COMPLETE FILE: `backend/tests/test_tts_engine.py`

```python
"""Unit tests for TTSEngine helper methods (no actual model loading)."""
import pytest
import io
import wave
from unittest.mock import patch, MagicMock
from services.tts_engine import TTSEngine


engine = TTSEngine()


class TestChunkText:
    def test_short_text_stays_one_chunk(self):
        chunks = engine._chunk_text("Hello world.", max_chars=250)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world."

    def test_long_text_split_on_sentences(self):
        text = "First sentence. Second sentence. Third sentence."
        chunks = engine._chunk_text(text, max_chars=25)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 35  # Some tolerance for long words

    def test_empty_text_returns_empty(self):
        chunks = engine._chunk_text("", max_chars=250)
        assert chunks == []

    def test_whitespace_only_returns_empty(self):
        chunks = engine._chunk_text("   \n\t  ", max_chars=250)
        assert chunks == []

    def test_oversized_single_sentence_split_by_length(self):
        long_sentence = "A" * 500
        chunks = engine._chunk_text(long_sentence, max_chars=250)
        assert len(chunks) == 2
        for chunk in chunks:
            assert len(chunk) <= 250

    def test_normalizes_excess_whitespace(self):
        text = "Hello    world.   How are   you?"
        chunks = engine._chunk_text(text, max_chars=250)
        assert len(chunks) == 1
        assert "  " not in chunks[0]

    def test_preserves_all_content(self):
        text = "First sentence. Second sentence."
        chunks = engine._chunk_text(text, max_chars=20)
        rejoined = " ".join(chunks)
        # All words should still be present
        assert "First" in rejoined
        assert "Second" in rejoined


class TestConcatenateWavBytes:
    def make_wav(self, num_frames=100, frame_rate=22050):
        """Create minimal WAV bytes."""
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(frame_rate)
            w.writeframes(b'\x00\x00' * num_frames)
        return buf.getvalue()

    def test_concatenate_two_segments(self):
        seg1 = self.make_wav(100)
        seg2 = self.make_wav(100)
        result = engine._concatenate_wav_bytes([seg1, seg2])

        buf = io.BytesIO(result)
        with wave.open(buf, 'rb') as w:
            assert w.getnframes() == 200

    def test_single_segment_unchanged(self):
        seg = self.make_wav(150)
        result = engine._concatenate_wav_bytes([seg])

        buf = io.BytesIO(result)
        with wave.open(buf, 'rb') as w:
            assert w.getnframes() == 150

    def test_valid_wav_header(self):
        result = engine._concatenate_wav_bytes([self.make_wav(50)])
        assert result[:4] == b'RIFF'
        assert result[8:12] == b'WAVE'
```

### COMPLETE FILE: `tests/fixtures/create_fixtures.py`

```python
"""
Script to create test fixture files.
Run once: python tests/fixtures/create_fixtures.py
"""
import os

fixtures_dir = os.path.join(os.path.dirname(__file__))

# sample.txt
with open(os.path.join(fixtures_dir, 'sample.txt'), 'w', encoding='utf-8') as f:
    f.write("This is a sample text file for testing.\n\n")
    f.write("It contains multiple paragraphs.\n\n")
    f.write("Unicode test: café, résumé, naïve, über, 日本語\n\n")
    f.write("The quick brown fox jumps over the lazy dog.\n")

# sample.pdf
try:
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Sample PDF content for testing.")
    page.insert_text((50, 80), "Page 1 of the test document.")
    doc.save(os.path.join(fixtures_dir, 'sample.pdf'))
    doc.close()
    print("Created sample.pdf")
except ImportError:
    print("Skipping sample.pdf (PyMuPDF not available)")

# sample.docx
try:
    from docx import Document
    doc = Document()
    doc.add_paragraph("Sample DOCX content for testing.")
    doc.add_paragraph("Second paragraph with more content.")
    doc.save(os.path.join(fixtures_dir, 'sample.docx'))
    print("Created sample.docx")
except ImportError:
    print("Skipping sample.docx (python-docx not available)")

# empty.txt
with open(os.path.join(fixtures_dir, 'empty.txt'), 'wb') as f:
    pass  # Zero bytes

print("Fixtures created in:", fixtures_dir)
```

---

## MANUAL QA PROTOCOL

Run this before every release.

### Frontend Tests (Browser)

```
Browser: Chrome (latest), Firefox (latest), Safari (latest), Edge (latest)
Mobile:  iOS Safari 16+, Android Chrome (latest)

Test matrix:
┌─────────────────────────────────┬───────┬─────────┬────────┬──────┐
│ Test                            │ Chrome│ Firefox │ Safari │ Edge │
├─────────────────────────────────┼───────┼─────────┼────────┼──────┤
│ Page loads without errors       │       │         │        │      │
│ Backend status shows correctly  │       │         │        │      │
│ TXT upload → audio plays        │       │         │        │      │
│ PDF upload → audio plays        │       │         │        │      │
│ DOCX upload → audio plays       │       │         │        │      │
│ .exe rejected with error msg    │       │         │        │      │
│ 12MB file rejected with msg     │       │         │        │      │
│ Download button works           │       │         │        │      │
│ Speed control works             │       │         │        │      │
│ Upload another → resets state   │       │         │        │      │
│ AI disclosure visible           │       │         │        │      │
│ Privacy notice visible          │       │         │        │      │
│ Keyboard navigation works       │       │         │        │      │
└─────────────────────────────────┴───────┴─────────┴────────┴──────┘
```

### Voice Quality Assessment (MOS Test)

For each test sentence:
1. Generate audio using `test_zero_shot.py`
2. Have 3–5 listeners (or yourself multiple times) rate each on 1–5:
   - **5**: Indistinguishable from real voice
   - **4**: Natural, clearly the target voice
   - **3**: Recognizable voice, some artifacts
   - **2**: Some similarity, notable artifacts
   - **1**: Poor similarity or unintelligible
3. Target: Average MOS ≥ 3.5 for MVP release

```
Sentence                                          Rater1  Rater2  Rater3  Avg
─────────────────────────────────────────────────────────────────────────────
Hello, this is a test of the voice cloning.       ____    ____    ____    ___
The quick brown fox jumps over the lazy dog.      ____    ____    ____    ___
Welcome to the document reader.                   ____    ____    ____    ___
A longer sentence to test extended synthesis...   ____    ____    ____    ___
Is the voice quality acceptable?                  ____    ____    ____    ___
─────────────────────────────────────────────────────────────────────────────
Overall MOS Target: ≥ 3.5
```

### Performance Benchmarks

Measure and document these before launch:

```python
# backend/tests/test_performance.py
import time, requests

BASE_URL = "http://localhost:8000"

def benchmark_synthesis(text_length_chars: int):
    """Measure synthesis time for a given text length."""
    text = "The quick brown fox jumps over the lazy dog. " * (text_length_chars // 45 + 1)
    text = text[:text_length_chars]
    
    with open('/tmp/bench.txt', 'w') as f:
        f.write(text)
    
    start = time.time()
    with open('/tmp/bench.txt', 'rb') as f:
        response = requests.post(f"{BASE_URL}/api/v1/synthesize",
                                  files={"file": ("bench.txt", f, "text/plain")})
    elapsed = time.time() - start
    
    return {
        "text_chars": text_length_chars,
        "elapsed_seconds": round(elapsed, 2),
        "chars_per_second": round(text_length_chars / elapsed, 1),
        "status": response.status_code,
    }

if __name__ == '__main__':
    for length in [100, 300, 500, 1000, 2000]:
        result = benchmark_synthesis(length)
        print(f"  {length:5d} chars → {result['elapsed_seconds']:6.1f}s "
              f"({result['chars_per_second']} chars/sec)")
```

Expected benchmark results (CPU inference, Hugging Face Spaces):

| Text Length | Expected Time | User Experience |
|---|---|---|
| 100 chars (~15 words) | 20–60 sec | Acceptable |
| 300 chars (~1 paragraph) | 60–120 sec | Acceptable with progress bar |
| 500 chars (~1/2 page) | 2–4 min | Inform user explicitly |
| 1000 chars (~1 page) | 4–8 min | Warn user, consider chunk limit |
| 2000 chars (~2 pages) | 8–15 min | Consider max text limit |

**Recommendation**: Enforce a maximum of 2000 characters (~2 pages) for the MVP to prevent timeout issues and improve user experience. Display character count and limit on the frontend.

---

## ERROR HANDLING MATRIX

Every error scenario must produce a user-friendly message. No raw stack traces to the user.

| Scenario | HTTP Status | User-Facing Message |
|---|---|---|
| Unsupported file type | 400 | "Unsupported file type '.xyz'. Please use TXT, PDF, or DOCX." |
| File too large | 413 | "File is X MB. Maximum allowed size is 10 MB." |
| Empty file | 400 | "Uploaded file is empty." |
| Scanned PDF | 422 | "No extractable text found. This PDF may contain only scanned images." |
| Empty document | 422 | "Document appears to be empty or contains no readable text." |
| TTS failure | 500 | "Audio generation failed. Please try again." |
| Model loading | 503 | "Server is warming up. Please wait a moment and try again." |
| Rate limit | 429 | "Too many requests. Please wait a minute and try again." |
| Network error | N/A (client) | "Could not reach the server. Check your connection." |
| Timeout | N/A (client) | "Request timed out. The server may be busy." |
