# Frontend Implementation Spec
> **For Claude Code**: Build every file listed here exactly as specified. No build tools. No npm. Raw HTML/CSS/JS deployed to GitHub Pages.

---

## COMPLETE FILE: `frontend/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Document Reader — Voice TTS</title>
  <meta name="description" content="Upload a document and have it read aloud in a personalized AI voice." />

  <!-- Tailwind CSS via CDN (no build step) -->
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet" />

  <!-- Custom styles -->
  <link rel="stylesheet" href="css/style.css" />
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen flex flex-col">

  <!-- ── Header ── -->
  <header class="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <span class="text-2xl">🎙️</span>
      <h1 class="text-xl font-semibold tracking-tight">Document Reader</h1>
    </div>
    <div id="backend-status" class="text-sm font-mono px-3 py-1 rounded-full bg-gray-800 text-gray-400">
      ● Checking...
    </div>
  </header>

  <!-- ── Main ── -->
  <main class="flex-1 flex flex-col items-center justify-center px-4 py-12">

    <!-- Upload Section -->
    <section id="upload-section" class="w-full max-w-xl">

      <div class="text-center mb-8">
        <h2 class="text-3xl font-bold mb-2">Read Any Document Aloud</h2>
        <p class="text-gray-400">Upload a TXT, PDF, or DOCX file and hear it in a personalized AI voice.</p>
      </div>

      <!-- Drop Zone -->
      <div id="drop-zone"
           class="border-2 border-dashed border-gray-600 rounded-2xl p-12
                  flex flex-col items-center justify-center gap-4
                  cursor-pointer transition-all duration-200
                  hover:border-indigo-500 hover:bg-gray-900"
           role="button"
           aria-label="Upload zone — click or drag a file here"
           tabindex="0">

        <div id="drop-icon" class="text-5xl">📄</div>
        <div class="text-center">
          <p class="text-lg font-medium">Drag &amp; drop your document here</p>
          <p class="text-sm text-gray-500 mt-1">or click to browse files</p>
        </div>
        <p class="text-xs text-gray-600">TXT · PDF · DOCX &nbsp;|&nbsp; Max 10 MB</p>

        <!-- Hidden file input -->
        <input type="file"
               id="file-input"
               class="hidden"
               accept=".txt,.pdf,.docx"
               aria-hidden="true" />
      </div>

      <!-- Error message -->
      <div id="upload-error" class="hidden mt-4 p-4 bg-red-900 border border-red-700 rounded-xl text-red-200 text-sm">
        <span id="upload-error-text"></span>
      </div>
    </section>

    <!-- Confirmation Dialog (hidden initially) -->
    <section id="confirm-section" class="hidden w-full max-w-xl">

      <div class="bg-gray-900 border border-gray-700 rounded-2xl p-6">
        <h3 class="text-lg font-semibold mb-1">Ready to synthesize</h3>
        <p class="text-sm text-gray-400 mb-4">
          File: <span id="confirm-filename" class="text-gray-200 font-mono"></span>
          &nbsp;·&nbsp;
          <span id="confirm-filesize" class="text-gray-400"></span>
        </p>

        <div id="text-preview-container" class="mb-4">
          <p class="text-xs text-gray-500 uppercase tracking-widest mb-2">Preview</p>
          <div id="text-preview"
               class="bg-gray-800 rounded-lg p-4 text-sm text-gray-300 max-h-32 overflow-y-auto font-mono leading-relaxed">
          </div>
        </div>

        <p class="text-xs text-gray-500 mb-4 italic">
          ⚠️ Audio generation may take 2–5 minutes for a full page on this free service.
        </p>

        <div class="flex gap-3">
          <button id="confirm-btn"
                  class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white
                         font-semibold py-3 rounded-xl transition-colors duration-150">
            🎙️ Read Aloud
          </button>
          <button id="cancel-btn"
                  class="px-6 bg-gray-700 hover:bg-gray-600 text-gray-200
                         font-medium py-3 rounded-xl transition-colors duration-150">
            Cancel
          </button>
        </div>
      </div>
    </section>

    <!-- Processing Section (hidden initially) -->
    <section id="processing-section" class="hidden w-full max-w-xl text-center">

      <div class="bg-gray-900 border border-gray-700 rounded-2xl p-10">
        <div id="processing-spinner" class="text-6xl mb-4 animate-spin-slow">⚙️</div>
        <h3 class="text-xl font-semibold mb-2">Generating Audio</h3>
        <p id="processing-status" class="text-gray-400 text-sm mb-6">
          Processing your document...
        </p>

        <!-- Progress bar -->
        <div class="bg-gray-800 rounded-full h-2 overflow-hidden">
          <div id="progress-bar" class="h-full bg-indigo-500 rounded-full transition-all duration-500"
               style="width: 10%;"></div>
        </div>
        <p class="text-xs text-gray-600 mt-3">This may take 2–5 minutes. Please keep this tab open.</p>
      </div>
    </section>

    <!-- Audio Player Section (hidden initially) -->
    <section id="player-section" class="hidden w-full max-w-xl">

      <div class="bg-gray-900 border border-gray-700 rounded-2xl p-6">

        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">🎧 Your Audio</h3>
          <span id="player-filename" class="text-sm text-gray-400 font-mono truncate max-w-xs"></span>
        </div>

        <!-- Native HTML5 audio element -->
        <audio id="audio-player"
               controls
               class="w-full rounded-lg mb-4"
               aria-label="Generated audio player">
          Your browser does not support the audio element.
        </audio>

        <!-- Controls row -->
        <div class="flex flex-wrap items-center gap-3 mb-4">

          <!-- Playback speed -->
          <div class="flex items-center gap-2">
            <label for="speed-select" class="text-xs text-gray-400">Speed</label>
            <select id="speed-select"
                    class="bg-gray-800 border border-gray-600 text-sm rounded-lg
                           px-3 py-1.5 text-gray-200 focus:ring-2 focus:ring-indigo-500">
              <option value="0.5">0.5×</option>
              <option value="0.75">0.75×</option>
              <option value="1" selected>1×</option>
              <option value="1.25">1.25×</option>
              <option value="1.5">1.5×</option>
              <option value="2">2×</option>
            </select>
          </div>

          <!-- Download button -->
          <button id="download-btn"
                  class="flex items-center gap-2 bg-gray-700 hover:bg-gray-600
                         text-gray-200 text-sm font-medium px-4 py-2 rounded-lg
                         transition-colors duration-150">
            ⬇️ Download WAV
          </button>

          <!-- New file button -->
          <button id="new-file-btn"
                  class="ml-auto text-sm text-indigo-400 hover:text-indigo-300
                         underline underline-offset-2 transition-colors duration-150">
            Upload another
          </button>
        </div>

        <!-- AI disclosure notice -->
        <p class="text-xs text-gray-500 border-t border-gray-800 pt-3 mt-2">
          🤖 Audio generated using AI voice synthesis. This is a synthetic recording, not an authentic human voice.
        </p>
      </div>
    </section>

  </main>

  <!-- ── Footer ── -->
  <footer class="border-t border-gray-800 px-6 py-4 text-center text-xs text-gray-600">
    <p>Uploaded documents are processed in memory and deleted immediately. No content is stored or shared.</p>
    <p class="mt-1">
      By uploading, you confirm you have the right to process this document's contents.
      &nbsp;|&nbsp;
      Voice synthesis powered by <a href="https://github.com/coqui-ai/TTS" class="underline hover:text-gray-400" target="_blank" rel="noopener">Coqui XTTS v2</a>.
    </p>
  </footer>

  <!-- JavaScript modules -->
  <script src="js/config.js"></script>
  <script src="js/api.js"></script>
  <script src="js/uploader.js"></script>
  <script src="js/player.js"></script>
  <script src="js/app.js"></script>

</body>
</html>
```

---

## COMPLETE FILE: `frontend/css/style.css`

```css
/* ── Custom styles for Voice TTS App ── */

/* Slow spin animation for processing icon */
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.animate-spin-slow {
  animation: spin-slow 3s linear infinite;
}

/* Backend status indicator */
#backend-status.status-ready  { color: #4ade80; background: rgba(74, 222, 128, 0.1); }
#backend-status.status-loading { color: #facc15; background: rgba(250, 204, 21, 0.1); }
#backend-status.status-offline { color: #f87171; background: rgba(248, 113, 113, 0.1); }

/* Drop zone active (file hovering over it) */
#drop-zone.drag-over {
  border-color: #6366f1;
  background-color: rgba(99, 102, 241, 0.05);
}

/* Audio player styling */
audio {
  background-color: #1f2937;
  border-radius: 8px;
}
audio::-webkit-media-controls-panel {
  background-color: #1f2937;
}

/* Smooth section transitions */
section {
  animation: fadeIn 0.2s ease-in;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Focus styles for accessibility */
#drop-zone:focus {
  outline: 2px solid #6366f1;
  outline-offset: 4px;
}

/* Mobile responsive audio player */
@media (max-width: 640px) {
  audio { width: 100%; }
  .flex-wrap > button { width: 100%; justify-content: center; }
}
```

---

## COMPLETE FILE: `frontend/js/config.js`

```javascript
/**
 * Frontend configuration.
 * Update BACKEND_URL after deploying to Hugging Face Spaces.
 */
const CONFIG = Object.freeze({
  // ← Replace with your HF Spaces URL after deployment
  BACKEND_URL: 'https://YOUR-HF-USERNAME-voice-tts.hf.space',

  MAX_FILE_SIZE_MB: 10,
  MAX_FILE_SIZE_BYTES: 10 * 1024 * 1024,

  ALLOWED_EXTENSIONS: ['.txt', '.pdf', '.docx'],

  // How often to poll /health when backend is loading (ms)
  HEALTH_POLL_INTERVAL_MS: 15000,

  // How many characters of extracted text to preview (TXT only)
  PREVIEW_CHARS: 300,
});
```

---

## COMPLETE FILE: `frontend/js/api.js`

```javascript
/**
 * All communication with the backend API.
 */

const API = {

  /**
   * Check backend health.
   * Returns: { status, model_loaded, version } or null on network error.
   */
  async health() {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 8000);

      const res = await fetch(`${CONFIG.BACKEND_URL}/api/v1/health`, {
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (!res.ok) return { status: 'error', model_loaded: false };
      return await res.json();

    } catch (err) {
      if (err.name === 'AbortError') {
        return { status: 'timeout', model_loaded: false };
      }
      return { status: 'offline', model_loaded: false };
    }
  },

  /**
   * Submit a file for synthesis.
   * Returns: Blob (audio/wav) on success.
   * Throws: Error with user-friendly message on failure.
   *
   * @param {File} file
   * @param {function(string): void} onProgress - callback for status messages
   * @returns {Promise<Blob>}
   */
  async synthesize(file, onProgress = () => {}) {
    const formData = new FormData();
    formData.append('file', file);

    onProgress('Sending document to server...');

    let response;
    try {
      response = await fetch(`${CONFIG.BACKEND_URL}/api/v1/synthesize`, {
        method: 'POST',
        body: formData,
      });
    } catch (networkErr) {
      throw new Error(
        'Could not reach the server. The backend may be offline or starting up. ' +
        'Please wait a moment and try again.'
      );
    }

    if (!response.ok) {
      let detail = `Server error (${response.status})`;
      try {
        const errBody = await response.json();
        detail = errBody.detail || detail;
      } catch { /* ignore JSON parse error */ }

      // Map status codes to friendly messages
      if (response.status === 413) throw new Error('File is too large. Maximum size is 10 MB.');
      if (response.status === 429) throw new Error('Too many requests. Please wait a minute and try again.');
      if (response.status === 422) throw new Error(detail);
      if (response.status === 503) throw new Error('Server is still loading. Please wait and try again.');
      throw new Error(detail);
    }

    onProgress('Receiving audio...');
    const blob = await response.blob();

    if (blob.size === 0) {
      throw new Error('Received empty audio file. Please try again.');
    }

    return blob;
  },
};
```

---

## COMPLETE FILE: `frontend/js/uploader.js`

```javascript
/**
 * File upload UI: drag-and-drop + file picker.
 * Fires APP.onFileSelected(file) when a valid file is chosen.
 */

const Uploader = (() => {

  const dropZone  = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  function init() {
    // Click to open file dialog
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') fileInput.click();
    });

    // File picker change
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        handleFile(fileInput.files[0]);
        fileInput.value = ''; // Reset so the same file can be re-selected
      }
    });

    // Drag events
    dropZone.addEventListener('dragenter', onDragEnter);
    dropZone.addEventListener('dragover',  onDragOver);
    dropZone.addEventListener('dragleave', onDragLeave);
    dropZone.addEventListener('drop',      onDrop);

    // Prevent browser from opening the file on accidental drop outside zone
    document.addEventListener('dragover',  (e) => e.preventDefault());
    document.addEventListener('drop',      (e) => e.preventDefault());
  }

  function onDragEnter(e) {
    e.preventDefault();
    dropZone.classList.add('drag-over');
    document.getElementById('drop-icon').textContent = '📂';
  }

  function onDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  }

  function onDragLeave(e) {
    if (!dropZone.contains(e.relatedTarget)) {
      dropZone.classList.remove('drag-over');
      document.getElementById('drop-icon').textContent = '📄';
    }
  }

  function onDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    document.getElementById('drop-icon').textContent = '📄';

    const files = e.dataTransfer.files;
    if (files.length === 0) return;
    if (files.length > 1) {
      APP.showError('Please upload one file at a time.');
      return;
    }
    handleFile(files[0]);
  }

  function handleFile(file) {
    try {
      validateFile(file);
      APP.onFileSelected(file);
    } catch (err) {
      APP.showError(err.message);
    }
  }

  function validateFile(file) {
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!CONFIG.ALLOWED_EXTENSIONS.includes(ext)) {
      throw new Error(
        `"${file.name}" is not supported. Please use a TXT, PDF, or DOCX file.`
      );
    }

    if (file.size > CONFIG.MAX_FILE_SIZE_BYTES) {
      const mb = (file.size / 1024 / 1024).toFixed(1);
      throw new Error(
        `File is ${mb} MB. Maximum allowed size is ${CONFIG.MAX_FILE_SIZE_MB} MB.`
      );
    }

    if (file.size === 0) {
      throw new Error('File appears to be empty.');
    }
  }

  return { init };

})();
```

---

## COMPLETE FILE: `frontend/js/player.js`

```javascript
/**
 * Audio player controls.
 * Manages playback speed, download, and blob URL lifecycle.
 */

const Player = (() => {

  const audioEl       = document.getElementById('audio-player');
  const speedSelect   = document.getElementById('speed-select');
  const downloadBtn   = document.getElementById('download-btn');
  const newFileBtn    = document.getElementById('new-file-btn');
  const playerFilename = document.getElementById('player-filename');

  let currentBlobURL = null;

  function init() {
    speedSelect.addEventListener('change', () => {
      audioEl.playbackRate = parseFloat(speedSelect.value);
    });

    downloadBtn.addEventListener('click', download);
    newFileBtn.addEventListener('click', () => APP.reset());

    audioEl.addEventListener('error', () => {
      APP.showError('Audio playback failed. Try downloading the file instead.');
    });
  }

  /**
   * Load and auto-play a new audio blob.
   * @param {Blob} audioBlob
   * @param {string} originalFilename
   */
  function load(audioBlob, originalFilename) {
    // Revoke previous blob URL to free memory
    if (currentBlobURL) {
      URL.revokeObjectURL(currentBlobURL);
    }

    currentBlobURL = URL.createObjectURL(audioBlob);
    audioEl.src = currentBlobURL;
    playerFilename.textContent = originalFilename;

    // Reset playback speed to 1x
    speedSelect.value = '1';
    audioEl.playbackRate = 1;

    // Attempt autoplay
    audioEl.play().catch(() => {
      // Autoplay blocked by browser — user will see the play button
      console.log('Autoplay blocked; user must press play manually.');
    });
  }

  function download() {
    if (!currentBlobURL) return;
    const a = document.createElement('a');
    a.href = currentBlobURL;
    a.download = 'narration.wav';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function cleanup() {
    audioEl.pause();
    audioEl.src = '';
    if (currentBlobURL) {
      URL.revokeObjectURL(currentBlobURL);
      currentBlobURL = null;
    }
  }

  return { init, load, cleanup };

})();
```

---

## COMPLETE FILE: `frontend/js/app.js`

```javascript
/**
 * Main application controller.
 * Manages state machine: idle → selected → processing → playing → error
 */

const APP = (() => {

  // ── State ──────────────────────────────────────────────────────────────────
  let state = 'idle';
  let selectedFile = null;
  let healthPollTimer = null;

  // ── Section elements ──────────────────────────────────────────────────────
  const sections = {
    upload:     document.getElementById('upload-section'),
    confirm:    document.getElementById('confirm-section'),
    processing: document.getElementById('processing-section'),
    player:     document.getElementById('player-section'),
  };

  const uploadError     = document.getElementById('upload-error');
  const uploadErrorText = document.getElementById('upload-error-text');
  const confirmBtn      = document.getElementById('confirm-btn');
  const cancelBtn       = document.getElementById('cancel-btn');
  const processingStatus = document.getElementById('processing-status');
  const progressBar     = document.getElementById('progress-bar');
  const backendStatus   = document.getElementById('backend-status');

  // ── Init ──────────────────────────────────────────────────────────────────
  function init() {
    Uploader.init();
    Player.init();
    checkHealth();
    startHealthPoll();

    confirmBtn.addEventListener('click', startSynthesis);
    cancelBtn.addEventListener('click',  reset);
  }

  // ── State machine ─────────────────────────────────────────────────────────
  function showOnly(sectionKey) {
    Object.entries(sections).forEach(([key, el]) => {
      el.classList.toggle('hidden', key !== sectionKey);
    });
    uploadError.classList.add('hidden');
  }

  // ── File selected callback (called by Uploader) ───────────────────────────
  function onFileSelected(file) {
    selectedFile = file;
    state = 'selected';

    // Populate confirmation dialog
    document.getElementById('confirm-filename').textContent = file.name;
    document.getElementById('confirm-filesize').textContent =
      `${(file.size / 1024).toFixed(0)} KB`;

    // For TXT files, read and preview content client-side
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (ext === '.txt') {
      const reader = new FileReader();
      reader.onload = (e) => {
        const preview = e.target.result.slice(0, CONFIG.PREVIEW_CHARS);
        const previewEl = document.getElementById('text-preview');
        previewEl.textContent = preview + (e.target.result.length > CONFIG.PREVIEW_CHARS ? '…' : '');
        document.getElementById('text-preview-container').classList.remove('hidden');
      };
      reader.readAsText(file);
    } else {
      document.getElementById('text-preview').textContent =
        'Preview not available for this file type. The text will be extracted server-side.';
      document.getElementById('text-preview-container').classList.remove('hidden');
    }

    showOnly('confirm');
  }

  // ── Synthesis flow ────────────────────────────────────────────────────────
  async function startSynthesis() {
    if (!selectedFile) return;
    state = 'processing';

    showOnly('processing');
    updateProgress(10, 'Sending document to server...');

    // Animate progress bar during long wait
    let fakeProgress = 10;
    const progressInterval = setInterval(() => {
      if (fakeProgress < 85) {
        fakeProgress += Math.random() * 4;
        updateProgress(Math.min(fakeProgress, 85), 'Generating audio...');
      }
    }, 4000);

    try {
      const audioBlob = await API.synthesize(selectedFile, (msg) => {
        updateProgress(null, msg);
      });

      clearInterval(progressInterval);
      updateProgress(100, 'Done!');

      state = 'playing';
      Player.load(audioBlob, selectedFile.name);
      showOnly('player');

    } catch (err) {
      clearInterval(progressInterval);
      state = 'error';
      showOnly('upload');
      showError(err.message);
    }
  }

  function updateProgress(percent, message) {
    if (percent !== null) {
      progressBar.style.width = `${Math.round(percent)}%`;
    }
    if (message) {
      processingStatus.textContent = message;
    }
  }

  // ── Error display ─────────────────────────────────────────────────────────
  function showError(message) {
    uploadErrorText.textContent = message;
    uploadError.classList.remove('hidden');
  }

  // ── Reset to idle ─────────────────────────────────────────────────────────
  function reset() {
    state = 'idle';
    selectedFile = null;
    Player.cleanup();
    showOnly('upload');
    progressBar.style.width = '10%';
  }

  // ── Health check ──────────────────────────────────────────────────────────
  async function checkHealth() {
    const data = await API.health();

    if (data.status === 'ok' && data.model_loaded) {
      backendStatus.textContent = '● Ready';
      backendStatus.className = 'text-sm font-mono px-3 py-1 rounded-full bg-gray-800 status-ready';
    } else if (data.status === 'loading') {
      backendStatus.textContent = '● Model loading...';
      backendStatus.className = 'text-sm font-mono px-3 py-1 rounded-full bg-gray-800 status-loading';
    } else if (data.status === 'offline' || data.status === 'timeout') {
      backendStatus.textContent = '● Backend offline';
      backendStatus.className = 'text-sm font-mono px-3 py-1 rounded-full bg-gray-800 status-offline';
    } else {
      backendStatus.textContent = '● Waking up...';
      backendStatus.className = 'text-sm font-mono px-3 py-1 rounded-full bg-gray-800 status-loading';
    }
  }

  function startHealthPoll() {
    healthPollTimer = setInterval(checkHealth, CONFIG.HEALTH_POLL_INTERVAL_MS);
  }

  // ── Public API ────────────────────────────────────────────────────────────
  return {
    init,
    onFileSelected,
    showError,
    reset,
  };

})();

// Boot
document.addEventListener('DOMContentLoaded', APP.init);
```

---

## NOTES FOR CLAUDE CODE

1. **Script loading order** in `index.html` is critical: `config.js` → `api.js` → `uploader.js` → `player.js` → `app.js`. Each module depends on the ones before it.

2. **No ES modules** (`type="module"`) for maximum browser compatibility with GitHub Pages. Everything is in global scope via IIFEs.

3. **Tailwind CDN version** is pinned at 2.2.19. Do not upgrade — the play CDN URL for v3 works differently and may break styles.

4. **Blob URL lifecycle**: The `Player.cleanup()` method calls `URL.revokeObjectURL()` to prevent memory leaks. Always call cleanup before creating a new blob URL.

5. **`BACKEND_URL` in config.js** — This must be updated after HF Spaces deployment. The placeholder `YOUR-HF-USERNAME` will cause CORS failures. Document this clearly in README.

6. **Progress bar is fake** — Real progress tracking would require WebSockets or Server-Sent Events. The fake incremental progress prevents users from thinking the app is frozen. This is intentional and acceptable for MVP.

7. **Accessibility**: The drop zone has `role="button"`, `tabindex="0"`, and keyboard event support for Enter/Space. Keep this.
