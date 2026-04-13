# Voice-Cloned TTS Web Application — Master Context Document
> **For Claude Code**: This is the authoritative context document. Read this first before any other file.
> Every architectural decision is documented here. Do not deviate from these decisions without explicit instruction.

---

## 1. PROJECT IDENTITY

| Field | Value |
|---|---|
| Project Name | Voice-Cloned TTS Web Application |
| Version | 1.0 (MVP) |
| Budget | $0 — Zero cost. Every dependency must be free. |
| Primary Language | Python 3.10+ (backend), Vanilla JS ES6+ (frontend) |
| Frontend Host | GitHub Pages (static) |
| Backend Host | Hugging Face Spaces (primary) |
| TTS Engine | Coqui XTTS v2 |
| Document Source | Professional Design Review v1.0, March 12, 2026 |

**What this project does in one sentence**: A user uploads a TXT, PDF, or DOCX file to a web interface; the backend extracts the text and synthesizes audio using the site owner's cloned voice; the audio is played back in the browser and optionally downloaded.

---

## 2. HARD CONSTRAINTS — NON-NEGOTIABLE

These constraints are architectural laws. No implementation decision may violate them.

1. **Zero monetary cost** — GitHub Pages (free), Hugging Face Spaces (free CPU/ZeroGPU), Coqui TTS (open source). No paid APIs.
2. **No persistent storage of user data** — Uploaded files and generated audio MUST be deleted within the same request cycle or after a max 15-minute TTL. No database. No user accounts.
3. **Stateless backend per request** — The API is stateless. No sessions. The only persistent state on the server is the loaded TTS model weights in memory.
4. **Privacy-first** — Extracted text content must NEVER be logged to disk or external services.
5. **File upload limits** — Hard 10 MB limit enforced server-side. Only `.txt`, `.pdf`, `.docx` accepted. MIME type validated independently of extension.
6. **HTTPS only** — All API communication over TLS. Hugging Face Spaces and Render both provide this free.
7. **Single-owner voice** — The cloned voice belongs to the website owner only. No user voice cloning capability in MVP.

---

## 3. TECHNOLOGY STACK — COMPLETE REFERENCE

### 3.1 Frontend Stack

| Component | Technology | Reason for choice |
|---|---|---|
| Markup | HTML5 semantic | Native file input, native audio element |
| Styling | CSS3 + Tailwind CSS via CDN | Zero build step, utility-first, responsive |
| Interactivity | Vanilla JavaScript ES6+ | No framework overhead for MVP |
| File Upload | HTML5 Drag-and-Drop API | Native browser, no library needed |
| Audio Playback | HTML5 `<audio>` + Web Audio API | Native controls + optional waveform |
| HTTP Client | Fetch API | Built-in, promise-based, handles binary |
| Hosting | GitHub Pages | Free, CDN-backed, custom domain support |

**Do NOT use**: React, Vue, npm build pipeline, webpack, or any bundler for the MVP. CDN-only if additional libraries are needed. Keep the frontend deployable as raw HTML/CSS/JS files pushed to a `gh-pages` branch.

### 3.2 Backend Stack

| Component | Technology | Package |
|---|---|---|
| Language | Python 3.10+ | — |
| Framework | FastAPI | `fastapi`, `uvicorn[standard]` |
| ASGI Server | Uvicorn | `uvicorn[standard]` |
| PDF Parsing | PyMuPDF | `pymupdf` (import as `fitz`) |
| DOCX Parsing | python-docx | `python-docx` |
| TTS Engine | Coqui TTS XTTS v2 | `TTS` |
| Audio Encoding | scipy | `scipy` |
| CORS | FastAPI middleware | `fastapi.middleware.cors` |
| Rate Limiting | slowapi | `slowapi` |
| File Validation | python-magic | `python-magic` |
| MIME Detection | python-magic-bin (Windows) or libmagic | platform-dependent |
| Audio Post-process | pydub | `pydub` (optional, MP3 conversion) |

### 3.3 Voice Engine

| Attribute | Value |
|---|---|
| Model | Coqui XTTS v2 |
| Mode | Zero-shot cloning (prototype) → Fine-tuned (production) |
| Minimum reference audio | 6–15 seconds (zero-shot) |
| Recommended training data | 15–30 minutes at 44.1 kHz WAV mono |
| Languages | 17 languages supported |
| GPU | Recommended but not required (CPU is ~0.3x real-time) |
| Model size | ~1.8 GB in memory |
| License | Mozilla Public License 2.0 |

### 3.4 Hosting Architecture

```
┌────────────────────────────────────┐      ┌──────────────────────────────────────┐
│         GITHUB PAGES               │      │       HUGGING FACE SPACES            │
│   (Static Frontend Host)           │      │     (Backend API + TTS Inference)    │
│                                    │      │                                      │
│  index.html                        │ HTTP │  FastAPI app                         │
│  style.css                         │ REST │  POST /api/v1/synthesize             │
│  app.js                            │ ───► │  GET  /api/v1/health                 │
│  assets/                           │      │  Coqui XTTS v2 weights (1.8 GB)      │
│                                    │      │  Persistent HF Space storage         │
└────────────────────────────────────┘      └──────────────────────────────────────┘
```

**Alternative backend hosts** (if HF Spaces has issues):
- Render.com free tier (750 hrs/mo, 512 MB RAM, spins down after inactivity)
- Railway.app ($5 free credit/mo)
- Fly.io (3 shared VMs, 256 MB each)

**Known limitation**: Hugging Face Spaces free CPU tier has 16 GB RAM. XTTS v2 requires ~1.8 GB. CPU inference is slow (~0.3–0.5x real-time, expect 2–5 min for a full page). This is acceptable for MVP.

---

## 4. PROJECT FILE STRUCTURE

```
voice-tts-app/
│
├── frontend/                          # Deployed to GitHub Pages (gh-pages branch)
│   ├── index.html                     # Main SPA page
│   ├── css/
│   │   └── style.css                  # Custom CSS (Tailwind via CDN handles most)
│   ├── js/
│   │   ├── app.js                     # Main application logic
│   │   ├── uploader.js                # File upload + drag-and-drop logic
│   │   ├── player.js                  # Audio player controls
│   │   └── api.js                     # All fetch calls to backend
│   └── assets/
│       └── favicon.ico
│
├── backend/                           # Deployed to Hugging Face Spaces
│   ├── app.py                         # FastAPI entry point
│   ├── routers/
│   │   └── synthesize.py              # /api/v1/synthesize endpoint
│   ├── services/
│   │   ├── parser.py                  # Document text extraction (TXT/PDF/DOCX)
│   │   ├── tts_engine.py              # Coqui XTTS v2 wrapper
│   │   └── audio_cache.py             # In-memory TTL cache for generated audio
│   ├── middleware/
│   │   └── security.py                # Rate limiting, file validation
│   ├── utils/
│   │   └── file_utils.py              # Temp file management, UUID naming
│   ├── voice_data/
│   │   └── reference.wav              # Owner's reference audio clip (15 sec)
│   ├── requirements.txt
│   ├── Dockerfile                     # For HF Spaces deployment
│   └── README.md
│
├── voice_cloning/                     # Local use only — voice prep scripts
│   ├── record_guide.md
│   ├── extract_reference.py           # Extract best 15-sec clip from recording
│   ├── preprocess_audio.py            # Normalize, resample, trim silence
│   └── finetune/
│       ├── prepare_dataset.py         # Build metadata CSV from recordings
│       ├── finetune_xtts.py           # Fine-tuning script (run on Colab)
│       └── colab_finetune.ipynb       # Google Colab notebook
│
├── tests/
│   ├── test_parser.py                 # Unit tests for document parsers
│   ├── test_api.py                    # Integration tests for API endpoints
│   ├── test_security.py               # Security: file type rejection, size limits
│   └── fixtures/
│       ├── sample.txt
│       ├── sample.pdf
│       └── sample.docx
│
├── .github/
│   └── workflows/
│       ├── deploy-frontend.yml        # GitHub Actions: deploy to gh-pages
│       └── test-backend.yml           # GitHub Actions: run pytest on push
│
├── docs/
│   ├── 00_MASTER_CONTEXT.md           # This file
│   ├── 01_BACKEND_SPEC.md
│   ├── 02_FRONTEND_SPEC.md
│   ├── 03_VOICE_CLONING_GUIDE.md
│   ├── 04_DEPLOYMENT_GUIDE.md
│   ├── 05_SECURITY_CHECKLIST.md
│   └── 06_TESTING_PLAN.md
│
└── README.md                          # Root README with setup instructions
```

---

## 5. API SPECIFICATION — COMPLETE CONTRACT

### 5.1 Base URL

Development: `http://localhost:8000`
Production: `https://[your-username]-voice-tts.hf.space`

### 5.2 Endpoints

#### `GET /api/v1/health`
Health check. Frontend polls this on load to detect backend availability.

**Response 200**:
```json
{
  "status": "ok",
  "model_loaded": true,
  "version": "1.0.0"
}
```

**Response 503** (model not yet loaded):
```json
{
  "status": "loading",
  "model_loaded": false
}
```

---

#### `POST /api/v1/synthesize`
Main synthesis endpoint. Accepts a document file, returns audio.

**Request**: `multipart/form-data`
- `file`: The uploaded document (`.txt`, `.pdf`, `.docx`)

**Validation rules** (all enforced server-side):
- File extension: must be `.txt`, `.pdf`, or `.docx`
- MIME type: must match expected MIME for extension (independently verified)
- File size: max 10 MB (returns 413 if exceeded)
- Rate limit: 5 requests per IP per minute (returns 429 if exceeded)

**Response 200**:
```
Content-Type: audio/wav  (or audio/mpeg for MP3)
Content-Disposition: attachment; filename="output.wav"
[binary audio data]
```

**Error Responses**:
```json
// 400 Bad Request
{ "detail": "Unsupported file type. Accepted: .txt, .pdf, .docx" }

// 413 Payload Too Large
{ "detail": "File exceeds maximum allowed size of 10 MB" }

// 422 Unprocessable Entity
{ "detail": "Could not extract text from document. File may be corrupted or scanned image." }

// 429 Too Many Requests
{ "detail": "Rate limit exceeded. Max 5 requests per minute." }

// 500 Internal Server Error
{ "detail": "TTS synthesis failed. Please try again." }
```

### 5.3 CORS Configuration

Allowed origins (configure these exactly):
```python
origins = [
    "https://[YOUR-GITHUB-USERNAME].github.io",
    "http://localhost:3000",   # local development
    "http://127.0.0.1:5500",   # VS Code Live Server
]
```

---

## 6. DATA FLOW — STEP BY STEP

```
1. User opens browser → GitHub Pages serves index.html
2. Frontend JS calls GET /api/v1/health → shows backend status indicator
3. User selects/drags file → client-side validation (extension, size)
4. For TXT files: read client-side, show preview in confirmation dialog
   For PDF/DOCX: show filename only in confirmation dialog (parsed server-side)
5. User clicks "Read Aloud" → POST /api/v1/synthesize (multipart/form-data)
6. Backend validates: extension, MIME type, file size
7. Backend saves to tempfile (UUID filename, isolated temp dir)
8. Backend routes to parser:
   - .txt  → open() with UTF-8, fallback cp-1252
   - .pdf  → fitz.open() via PyMuPDF, extract_text() per page, join
   - .docx → docx.Document(), iterate paragraphs, join non-empty
9. Text is cleaned: strip excess whitespace, normalize unicode
10. Text is chunked: max 250 chars per chunk, split on sentence boundaries
11. XTTS v2 synthesizes each chunk with reference.wav as speaker
12. Audio chunks are concatenated into single WAV
13. Temp files deleted
14. WAV binary returned as HTTP response
15. Frontend creates blob URL from response binary
16. HTML5 <audio> element plays the blob URL
17. User can play/pause/seek/download
```

---

## 7. SECURITY IMPLEMENTATION — MANDATORY

All of these MUST be implemented. None are optional.

### File Upload Security
```python
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.docx'}
ALLOWED_MIMES = {
    '.txt':  ['text/plain'],
    '.pdf':  ['application/pdf'],
    '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
              'application/zip'],  # DOCX is a ZIP internally
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

# Always rename uploaded file to UUID before touching it
import uuid, tempfile, os
safe_filename = f"{uuid.uuid4()}.tmp"
temp_path = os.path.join(tempfile.gettempdir(), safe_filename)
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/synthesize")
@limiter.limit("5/minute")
async def synthesize(request: Request, file: UploadFile = File(...)):
    ...
```

### Text Sanitization (for confirmation dialog)
```python
import html
safe_preview = html.escape(extracted_text[:200])
```

### No Logging of Content
```python
# NEVER log extracted text
# OK to log: request timestamps, file type, file size, processing duration, errors
logger.info(f"Synthesis request: type={file_type}, size={file_size_bytes}B, duration={elapsed:.2f}s")
# NOT OK:
# logger.info(f"Extracted text: {text}")  ← FORBIDDEN
```

---

## 8. TTS ENGINE — INTEGRATION REFERENCE

### 8.1 Loading the Model (at startup, NOT per request)

```python
from TTS.api import TTS
import torch

# Load once at startup
device = "cuda" if torch.cuda.is_available() else "cpu"
tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
```

### 8.2 Synthesizing Audio

```python
import tempfile, os

def synthesize_text(text: str, reference_wav: str) -> bytes:
    """
    Synthesize text using cloned voice reference.
    Returns raw WAV bytes.
    """
    chunks = chunk_text(text, max_chars=250)
    audio_segments = []
    
    for chunk in chunks:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        
        tts_model.tts_to_file(
            text=chunk,
            speaker_wav=reference_wav,
            language="en",
            file_path=tmp_path
        )
        
        with open(tmp_path, "rb") as f:
            audio_segments.append(f.read())
        
        os.unlink(tmp_path)  # Delete immediately
    
    return concatenate_wav_bytes(audio_segments)
```

### 8.3 Text Chunking

```python
import re

def chunk_text(text: str, max_chars: int = 250) -> list[str]:
    """
    Split text into chunks at sentence boundaries.
    Max chunk size: max_chars characters.
    """
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            # Handle sentences longer than max_chars
            if len(sentence) > max_chars:
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i:i+max_chars])
            else:
                current = sentence
    
    if current:
        chunks.append(current)
    
    return [c for c in chunks if c.strip()]
```

### 8.4 WAV Concatenation

```python
import io
import wave

def concatenate_wav_bytes(wav_bytes_list: list[bytes]) -> bytes:
    """Concatenate multiple WAV byte sequences into one."""
    output = io.BytesIO()
    
    with wave.open(output, 'wb') as out_wav:
        first = True
        for wav_bytes in wav_bytes_list:
            with wave.open(io.BytesIO(wav_bytes), 'rb') as in_wav:
                if first:
                    out_wav.setparams(in_wav.getparams())
                    first = False
                out_wav.writeframes(in_wav.readframes(in_wav.getnframes()))
    
    return output.getvalue()
```

---

## 9. DOCUMENT PARSERS — REFERENCE IMPLEMENTATIONS

### TXT Parser
```python
def parse_txt(file_bytes: bytes) -> str:
    for encoding in ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']:
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode text file with any supported encoding.")
```

### PDF Parser
```python
import fitz  # PyMuPDF

def parse_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text.strip())
    doc.close()
    
    if not pages:
        raise ValueError("No extractable text found. PDF may be a scanned image.")
    
    return "\n\n".join(pages)
```

### DOCX Parser
```python
from docx import Document
import io

def parse_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    if not paragraphs:
        raise ValueError("No extractable text found in DOCX.")
    
    return "\n\n".join(paragraphs)
```

---

## 10. FRONTEND — KEY IMPLEMENTATION DETAILS

### 10.1 File Upload Flow

```javascript
// State machine: idle → selected → confirming → processing → playing → error
const AppState = {
  current: 'idle',
  file: null,
  audioBlob: null,
  previewText: '',
};

// Client-side validation BEFORE sending to server
function validateFile(file) {
  const ALLOWED_TYPES = ['.txt', '.pdf', '.docx'];
  const MAX_SIZE_BYTES = 10 * 1024 * 1024;
  
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!ALLOWED_TYPES.includes(ext)) {
    throw new Error(`Unsupported file type: ${ext}. Use TXT, PDF, or DOCX.`);
  }
  if (file.size > MAX_SIZE_BYTES) {
    throw new Error(`File too large: ${(file.size / 1024 / 1024).toFixed(1)} MB. Max 10 MB.`);
  }
}
```

### 10.2 API Call with Progress

```javascript
async function synthesize(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const BACKEND_URL = 'https://[YOUR-HF-USERNAME]-voice-tts.hf.space';
  
  setState('processing');
  showProgress('Sending document...');
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/synthesize`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Server error: ${response.status}`);
    }
    
    showProgress('Receiving audio...');
    const audioBlob = await response.blob();
    const audioURL = URL.createObjectURL(audioBlob);
    
    setState('playing');
    loadAudio(audioURL);
    
  } catch (err) {
    setState('error');
    showError(err.message);
  }
}
```

### 10.3 Audio Player Controls

```javascript
function initAudioPlayer(audioURL) {
  const audio = document.getElementById('audio-player');
  audio.src = audioURL;
  
  // Playback speed control
  document.getElementById('speed-select').addEventListener('change', (e) => {
    audio.playbackRate = parseFloat(e.target.value);
  });
  
  // Download button
  document.getElementById('download-btn').addEventListener('click', () => {
    const a = document.createElement('a');
    a.href = audioURL;
    a.download = 'narration.wav';
    a.click();
  });
}
```

### 10.4 Health Check on Page Load

```javascript
async function checkBackendHealth() {
  const indicator = document.getElementById('backend-status');
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/health`, { 
      signal: AbortSignal.timeout(5000) 
    });
    const data = await res.json();
    
    if (data.model_loaded) {
      indicator.textContent = '● Ready';
      indicator.className = 'status-ready';
    } else {
      indicator.textContent = '● Loading model...';
      indicator.className = 'status-loading';
      setTimeout(checkBackendHealth, 10000); // Retry in 10s
    }
  } catch {
    indicator.textContent = '● Backend offline';
    indicator.className = 'status-offline';
  }
}
```

---

## 11. ENVIRONMENT VARIABLES

All backend configuration through environment variables. Never hardcode.

```bash
# backend/.env (local development — DO NOT COMMIT)
REFERENCE_WAV_PATH=./voice_data/reference.wav
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
MAX_FILE_SIZE_MB=10
RATE_LIMIT_PER_MINUTE=5
AUDIO_CACHE_TTL_SECONDS=900
TTS_LANGUAGE=en
LOG_LEVEL=INFO

# Hugging Face Spaces secrets (set in HF Space settings UI)
REFERENCE_WAV_PATH=/data/reference.wav
ALLOWED_ORIGINS=https://[YOUR-USERNAME].github.io
```

```javascript
// frontend/js/config.js — Only non-secret config here
const CONFIG = {
  BACKEND_URL: 'https://[YOUR-HF-USERNAME]-voice-tts.hf.space',
  MAX_FILE_SIZE_MB: 10,
  ALLOWED_EXTENSIONS: ['.txt', '.pdf', '.docx'],
  HEALTH_CHECK_INTERVAL_MS: 30000,
};
```

---

## 12. DEPLOYMENT — QUICK REFERENCE

### GitHub Pages (Frontend)

```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend
on:
  push:
    branches: [main]
    paths: ['frontend/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend
```

### Hugging Face Spaces (Backend)

The backend is deployed as a Hugging Face Space with a `Dockerfile`. Key `README.md` header for HF Spaces:

```yaml
---
title: Voice TTS API
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---
```

### Dockerfile (backend)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download XTTS v2 model at build time to avoid cold-start delay
RUN python -c "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2')"

EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

**Note**: HF Spaces runs on port 7860 by default.

---

## 13. TESTING REQUIREMENTS

### Unit Tests (pytest)

Required test coverage:
- `test_parser.py`: TXT encoding edge cases, PDF with multiple pages, DOCX with tables, empty file → raises ValueError
- `test_api.py`: health endpoint, synthesize with each file type, rejected extensions, oversized file, CORS headers
- `test_security.py`: path traversal filenames, executable file disguised as txt, MIME mismatch

```bash
# Run all tests
cd backend && pytest tests/ -v --tb=short

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### Manual QA Checklist (pre-deployment)

- [ ] Upload sample.txt → audio plays
- [ ] Upload sample.pdf → audio plays
- [ ] Upload sample.docx → audio plays
- [ ] Upload .exe → rejected with clear error
- [ ] Upload 15 MB file → rejected with clear error
- [ ] Audio download button works
- [ ] Playback speed 0.5x, 1x, 1.5x, 2x works
- [ ] Tested on Chrome, Firefox, Safari, Edge
- [ ] Tested on iOS Safari and Android Chrome
- [ ] Disclaimer visible on page

---

## 14. PERFORMANCE EXPECTATIONS

| Metric | Expected Value | Notes |
|---|---|---|
| Page load time | < 1s | GitHub Pages CDN, lightweight HTML |
| Backend cold start | 30–120s | HF Spaces spins down; XTTS v2 model load |
| TTS generation speed | 0.3–0.5x real-time on CPU | 1 min of audio ≈ 2–3 min processing |
| 1 page (~300 words) | 2–5 minutes | Acceptable for MVP |
| Max concurrent users | 1–2 | CPU-only inference bottleneck |
| Audio quality (MOS) | 3.5+ target | Zero-shot with good reference |

**User expectation management**: Display a progress message like "Generating audio — this may take 2–5 minutes for a full page." Do not leave the user with a spinning indicator and no context.

---

## 15. KNOWN ISSUES AND MITIGATIONS

| Issue | Severity | Mitigation |
|---|---|---|
| HF Spaces cold start (30–120s delay) | Medium | Show "Backend waking up..." message; poll /health |
| Voice drift in long passages | Low | Chunk text at 250 chars max; use diverse reference clips |
| Scanned PDFs return no text | Medium | Return 422 with clear user message: "Scanned PDFs not supported" |
| DOCX with complex layouts | Low | Extract paragraph text only; tables may be incomplete |
| Slow CPU inference | Medium | Inform user of expected wait time in UI |
| Rate limit hits | Low | Show friendly "Too many requests, try in 1 minute" message |
| Model load OOM on small HF tiers | Medium | XTTS v2 needs ~2 GB RAM; use CPU tier with 16 GB |

---

## 16. LEGAL AND ETHICAL REQUIREMENTS

These are not optional. They must appear in the deployed application.

1. **AI disclosure notice** (visible on every page with audio):
   > "Audio generated using AI voice synthesis based on the voice of [Owner Name]. All audio is synthetic and is not an authentic recording."

2. **Privacy notice** (visible on upload page):
   > "Your uploaded documents are processed in memory and deleted immediately. No content is stored or shared."

3. **Terms of use statement** (footer or dedicated page):
   > "By uploading a document, you confirm that you have the right to process its contents. This service is provided for personal use only."

4. **EU AI Act / Deepfake compliance**: Do not facilitate impersonation. The service reads the user's uploaded content in the owner's voice; it does not allow users to input arbitrary voice targets.

---

## 17. CLAUDE CODE TASK PRIORITY ORDER

When implementing, build in this order:

1. **Backend: Core API skeleton** — FastAPI app, health endpoint, CORS, error handlers
2. **Backend: File parsers** — TXT, PDF, DOCX with error handling
3. **Backend: Security middleware** — MIME validation, rate limiting, file size enforcement
4. **Backend: TTS integration** — XTTS v2 loading, synthesis, chunking, WAV concatenation
5. **Backend: Tests** — pytest suite for all above
6. **Frontend: HTML structure** — Upload zone, confirmation dialog, audio player, status indicators
7. **Frontend: JavaScript** — File validation, API calls, audio playback, download
8. **Frontend: CSS/Tailwind** — Responsive styling, progress states, error states
9. **Deployment: Dockerfile** — Backend containerization for HF Spaces
10. **Deployment: GitHub Actions** — Frontend auto-deploy workflow
11. **Voice: Reference clip prep** — Audio preprocessing scripts
12. **Documentation: README** — Setup guide

---

*End of Master Context Document*
