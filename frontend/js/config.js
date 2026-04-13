/**
 * Frontend configuration.
 * Update BACKEND_URL after deploying to Hugging Face Spaces.
 */
const CONFIG = Object.freeze({
  // ← Replace [YOUR-HF-USERNAME] with your Hugging Face username after deployment
  BACKEND_URL: 'https://YOUR-HF-USERNAME-voice-tts.hf.space',

  MAX_FILE_SIZE_MB: 10,
  MAX_FILE_SIZE_BYTES: 10 * 1024 * 1024,

  ALLOWED_EXTENSIONS: ['.txt', '.pdf', '.docx'],

  // How often to poll /health when backend is loading (ms)
  HEALTH_POLL_INTERVAL_MS: 15000,

  // How many characters of extracted text to preview (TXT only)
  PREVIEW_CHARS: 300,
});
