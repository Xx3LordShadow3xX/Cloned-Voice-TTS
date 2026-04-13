# Voice-Cloned TTS Web Application

A zero-cost, web-based document-to-speech platform using a custom cloned voice.
Upload TXT, PDF, or DOCX files and have them read aloud in the site owner's AI-cloned voice.

**Stack**: Python FastAPI (backend) + Vanilla JS (frontend)
**Hosting**: GitHub Pages (frontend) + Hugging Face Spaces (backend)
**TTS Engine**: Coqui XTTS v2 (open source, free)
**Budget**: $0

---

## Quick Start

### Prerequisites

- Python 3.10+
- Git
- A microphone (or smartphone) for recording your reference voice

### 1. Clone and set up

```bash
git clone https://github.com/[YOUR-USERNAME]/voice-tts-app.git
cd voice-tts-app
```

### 2. Record your voice

See `docs/03_VOICE_CLONING_GUIDE.md` for detailed instructions.

Short version:
1. Record 15–30 minutes of yourself reading aloud (WAV format)
2. Run: `python voice_cloning/preprocess_audio.py --input recording.wav --output backend/voice_data/reference.wav --duration 15`
3. Test: `python voice_cloning/test_zero_shot.py --reference backend/voice_data/reference.wav`

### 3. Set up backend locally

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export REFERENCE_WAV_PATH=./voice_data/reference.wav
export ALLOWED_ORIGINS=http://localhost:5500
uvicorn app:app --reload --port 8000
```

### 4. Run frontend locally

```bash
cd frontend
python -m http.server 5500
# Open http://localhost:5500
```

### 5. Deploy

See `docs/04_DEPLOYMENT_GUIDE.md` for GitHub Pages + Hugging Face Spaces deployment.

---

## Documentation

| File | Contents |
|---|---|
| `docs/00_MASTER_CONTEXT.md` | Complete project context, architecture, all decisions |
| `docs/01_BACKEND_SPEC.md` | Full backend code with all Python files |
| `docs/02_FRONTEND_SPEC.md` | Full frontend code (HTML/CSS/JS) |
| `docs/03_VOICE_CLONING_GUIDE.md` | Voice recording, preprocessing, fine-tuning |
| `docs/04_DEPLOYMENT_GUIDE.md` | GitHub Pages + HF Spaces deployment |
| `docs/05_SECURITY_AND_TESTING.md` | Security checklist, test plan, QA protocol |

---

## Project Structure

```
voice-tts-app/
├── frontend/           → GitHub Pages static site
│   ├── index.html
│   ├── css/style.css
│   └── js/{app,api,uploader,player,config}.js
├── backend/            → Hugging Face Spaces Docker app
│   ├── app.py
│   ├── routers/synthesize.py
│   ├── services/{parser,tts_engine,audio_cache}.py
│   ├── middleware/security.py
│   ├── voice_data/reference.wav  ← Your reference audio
│   ├── requirements.txt
│   └── Dockerfile
├── voice_cloning/      → Voice prep scripts (local use)
│   ├── preprocess_audio.py
│   ├── test_zero_shot.py
│   └── finetune/
├── tests/              → pytest suite
└── docs/               → Implementation documentation
```

---

## Legal & Ethics

- Audio is generated using AI voice synthesis. Not authentic recordings.
- Uploaded documents are processed in memory and deleted immediately.
- Users are responsible for having the right to process their uploaded content.

---

*Built with Coqui XTTS v2 · Hosted on GitHub Pages + Hugging Face Spaces · Zero cost*
