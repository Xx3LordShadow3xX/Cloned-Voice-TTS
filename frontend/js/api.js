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
