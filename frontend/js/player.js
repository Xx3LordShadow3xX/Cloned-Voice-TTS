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
