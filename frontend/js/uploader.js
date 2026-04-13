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
