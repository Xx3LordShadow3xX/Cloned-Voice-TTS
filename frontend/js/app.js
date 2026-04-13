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
