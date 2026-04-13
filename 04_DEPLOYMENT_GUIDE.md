# Deployment Guide
> **For Claude Code**: Generate all workflow YAML files and configuration files listed here. Update placeholder values (YOUR-USERNAME, etc.) with comments.

---

## ARCHITECTURE SUMMARY

```
Repository: github.com/[YOUR-USERNAME]/voice-tts-app
├── main branch           → source code
├── gh-pages branch       → auto-deployed by GitHub Actions (frontend only)
└── backend/              → deployed separately to Hugging Face Spaces
```

---

## PART 1: GITHUB PAGES (FRONTEND)

### 1.1 Repository Setup

```bash
# Initial setup
git init voice-tts-app
cd voice-tts-app
git remote add origin https://github.com/[YOUR-USERNAME]/voice-tts-app.git

# Create the project structure
mkdir -p frontend/{css,js,assets} backend tests .github/workflows

# Initial commit
git add .
git commit -m "Initial project structure"
git push -u origin main
```

### 1.2 Configure GitHub Pages

In your GitHub repository:
1. Go to **Settings → Pages**
2. Source: **GitHub Actions** (not "Deploy from a branch" — we use the workflow)
3. Save

### 1.3 GitHub Actions Workflow — Frontend Deploy

### COMPLETE FILE: `.github/workflows/deploy-frontend.yml`

```yaml
name: Deploy Frontend to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - '.github/workflows/deploy-frontend.yml'
  workflow_dispatch:  # Allow manual trigger

permissions:
  contents: read
  pages: write
  id-token: write

# Allow only one concurrent deployment
concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    name: Deploy to GitHub Pages
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: './frontend'

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### 1.4 GitHub Actions Workflow — Backend Tests

### COMPLETE FILE: `.github/workflows/test-backend.yml`

```yaml
name: Backend Tests

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - '.github/workflows/test-backend.yml'
  pull_request:
    branches: [main]

jobs:
  test:
    name: Run pytest
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'
          cache-dependency-path: 'backend/requirements.txt'

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y libmagic1 libsndfile1

      - name: Install Python dependencies
        working-directory: backend
        run: |
          pip install --upgrade pip
          # Install CPU-only torch to avoid huge download in CI
          pip install torch==2.3.1+cpu torchaudio==2.3.1+cpu \
            --extra-index-url https://download.pytorch.org/whl/cpu
          # Install remaining deps (skip TTS itself in CI — too large)
          pip install fastapi uvicorn[standard] python-multipart slowapi \
            pymupdf python-docx scipy python-magic httpx \
            pytest pytest-asyncio

      - name: Run parser and security tests (no TTS needed)
        working-directory: backend
        run: |
          pytest tests/test_parser.py tests/test_security.py -v --tb=short

      - name: Run API tests with mocked TTS
        working-directory: backend
        run: |
          pytest tests/test_api.py -v --tb=short
        env:
          REFERENCE_WAV_PATH: ./voice_data/reference.wav
          ALLOWED_ORIGINS: http://localhost:5500
```

---

## PART 2: HUGGING FACE SPACES (BACKEND)

### 2.1 Create a New HF Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Space name: `voice-tts` (your URL will be `https://[username]-voice-tts.hf.space`)
3. License: MIT
4. SDK: **Docker**
5. Hardware: **CPU basic** (free) — 2 vCPU, 16 GB RAM

### 2.2 HF Space README (required metadata)

### COMPLETE FILE: `backend/README.md`

```markdown
---
title: Voice TTS API
emoji: 🎙️
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
short_description: Document-to-speech API using cloned voice synthesis
---

# Voice TTS API

REST API backend for the Voice-Cloned TTS web application.

## Endpoints

- `GET /api/v1/health` — Health check and model status
- `POST /api/v1/synthesize` — Upload document, receive WAV audio

## Environment Variables

Set these in the HF Space **Settings → Variables and Secrets** tab:

| Variable | Description | Example |
|---|---|---|
| `REFERENCE_WAV_PATH` | Path to reference audio | `/data/reference.wav` |
| `ALLOWED_ORIGINS` | Frontend URL (comma-separated) | `https://username.github.io` |
| `RATE_LIMIT_PER_MINUTE` | Max requests per IP per minute | `5` |
| `TTS_LANGUAGE` | Default TTS language | `en` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Uploading the Reference Audio

Use the HF Spaces persistent storage (`/data`) to store the reference WAV.

From the HF Space "Files" tab, upload `reference.wav` to the `/data` directory,
then set `REFERENCE_WAV_PATH=/data/reference.wav` in environment variables.
```

### 2.3 Deploy Backend to HF Spaces

Option A: Git push (recommended)

```bash
# Clone your HF Space repo
git clone https://huggingface.co/spaces/[YOUR-HF-USERNAME]/voice-tts
cd voice-tts

# Copy backend files
cp -r /path/to/your/project/backend/* .

# Add your reference audio
cp /path/to/your/reference.wav ./voice_data/reference.wav

# Push to HF
git add .
git commit -m "Initial backend deployment"
git push
```

Option B: HF Web UI

Upload files directly via the HF Space "Files" tab.

### 2.4 Set Environment Variables in HF Spaces

In your HF Space → **Settings → Variables and secrets**:

```
REFERENCE_WAV_PATH = /data/reference.wav
ALLOWED_ORIGINS    = https://[YOUR-GITHUB-USERNAME].github.io
RATE_LIMIT_PER_MINUTE = 5
TTS_LANGUAGE       = en
LOG_LEVEL          = INFO
```

### 2.5 Upload Reference Audio to HF Persistent Storage

HF Spaces provides `/data` as persistent storage. Upload your preprocessed reference.wav:

```python
# Run this locally once to upload your reference audio to HF Spaces
from huggingface_hub import HfApi

api = HfApi()
api.upload_file(
    path_or_fileobj="./voice_data/reference.wav",
    path_in_repo="reference.wav",
    repo_id="[YOUR-HF-USERNAME]/voice-tts",
    repo_type="space",
)
print("Uploaded reference.wav to HF Space")
```

Or use the HF web UI: Space → Files → Upload file → select reference.wav → set path to `/data/reference.wav`.

---

## PART 3: CONNECTING FRONTEND TO BACKEND

After deploying to HF Spaces, update the frontend config:

### Update `frontend/js/config.js`

```javascript
const CONFIG = Object.freeze({
  // ← Update this to your actual HF Spaces URL
  BACKEND_URL: 'https://[YOUR-HF-USERNAME]-voice-tts.hf.space',
  // ... rest of config
});
```

Commit and push — GitHub Actions will redeploy the frontend automatically.

---

## PART 4: LOCAL DEVELOPMENT SETUP

### 4.1 Backend (local)

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --extra-index-url https://download.pytorch.org/whl/cpu \
  -r requirements.txt

# Create voice_data directory and add your reference audio
mkdir -p voice_data
cp /path/to/reference.wav voice_data/reference.wav

# Set environment variables
export REFERENCE_WAV_PATH=./voice_data/reference.wav
export ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
export RATE_LIMIT_PER_MINUTE=100  # Relaxed for local dev

# Run development server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 4.2 Frontend (local)

```bash
# Option 1: VS Code Live Server (recommended)
# Install "Live Server" extension → right-click index.html → Open with Live Server
# Runs on http://127.0.0.1:5500

# Option 2: Python HTTP server
cd frontend
python -m http.server 5500
# Access at http://localhost:5500

# Option 3: npx serve (if Node.js available)
cd frontend
npx serve -p 5500
```

### 4.3 Update config.js for local dev

```javascript
const CONFIG = Object.freeze({
  BACKEND_URL: 'http://localhost:8000',  // Local backend
  // ...
});
```

---

## PART 5: POST-DEPLOYMENT VERIFICATION

After deploying both frontend and backend, verify the following:

### Smoke Tests

```bash
# 1. Backend health check
curl https://[YOUR-HF-USERNAME]-voice-tts.hf.space/api/v1/health
# Expected: {"status":"ok","model_loaded":true,"version":"1.0.0"}

# 2. Test synthesis with a TXT file
curl -X POST https://[YOUR-HF-USERNAME]-voice-tts.hf.space/api/v1/synthesize \
  -F "file=@/path/to/test.txt" \
  --output test_output.wav
# Expected: test_output.wav is a valid WAV file

# 3. Test file rejection
curl -X POST https://[YOUR-HF-USERNAME]-voice-tts.hf.space/api/v1/synthesize \
  -F "file=@/path/to/file.exe"
# Expected: {"detail":"Unsupported file type..."}
```

### Frontend Checks

- [ ] `https://[YOUR-GITHUB-USERNAME].github.io/voice-tts-app` loads
- [ ] Backend status indicator shows "● Ready" (may take 30–60s on cold start)
- [ ] Can upload a .txt file and receive audio
- [ ] Can upload a .pdf file and receive audio
- [ ] Can upload a .docx file and receive audio
- [ ] Download button produces a valid .wav file
- [ ] Playback speed control works
- [ ] Error message shown for unsupported file type
- [ ] Privacy notice visible in footer
- [ ] AI disclosure notice visible in audio player

---

## PART 6: CUSTOM DOMAIN (OPTIONAL)

### GitHub Pages Custom Domain

1. In repository Settings → Pages → Custom domain: enter `your-domain.com`
2. Create DNS records at your registrar:
   ```
   Type  Host  Value
   A     @     185.199.108.153
   A     @     185.199.109.153
   A     @     185.199.110.153
   A     @     185.199.111.153
   CNAME www   [YOUR-GITHUB-USERNAME].github.io
   ```
3. Wait for DNS propagation (up to 24 hours)
4. Enable "Enforce HTTPS" in GitHub Pages settings

### Update CORS after Custom Domain

In HF Spaces environment variables:
```
ALLOWED_ORIGINS = https://your-domain.com,https://www.your-domain.com,https://[YOUR-GITHUB-USERNAME].github.io
```

---

## TROUBLESHOOTING

| Problem | Solution |
|---|---|
| HF Space shows "Building" for 20+ minutes | Check Dockerfile — model download at build time takes long; this is expected first-time |
| 503 on synthesize endpoint | Model still loading; poll /health and wait |
| CORS error in browser console | Update ALLOWED_ORIGINS in HF Spaces env vars to match your GitHub Pages URL exactly |
| Audio plays but wrong voice | Check REFERENCE_WAV_PATH is set correctly and file exists |
| "Rate limit exceeded" | Wait 1 minute; or increase RATE_LIMIT_PER_MINUTE for testing |
| GitHub Pages shows 404 | Ensure `index.html` is in the root of the `frontend/` directory |
| Actions workflow fails | Check Actions logs; usually a dependency install issue |
