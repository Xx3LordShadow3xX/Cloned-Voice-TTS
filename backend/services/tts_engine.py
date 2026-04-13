"""
TTS Engine wrapper for Coqui XTTS v2.
Loaded once at startup, reused for all requests.
"""

import io
import os
import logging
import tempfile
import wave
import re
from typing import Optional

logger = logging.getLogger(__name__)


class TTSEngine:
    """Singleton wrapper for Coqui XTTS v2 model."""

    def __init__(self):
        self._model = None
        self.is_loaded = False

    def load(self):
        """Load XTTS v2 model into memory. Call once at startup."""
        try:
            from TTS.api import TTS
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading XTTS v2 on device: {device}")

            self._model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            self.is_loaded = True
            logger.info("XTTS v2 loaded successfully.")

        except ImportError:
            logger.error("Coqui TTS not installed. Run: pip install TTS")
            raise
        except Exception as e:
            logger.error(f"XTTS v2 load failed: {e}")
            raise

    def synthesize(self, text: str, reference_wav: str, language: str = "en") -> bytes:
        """
        Synthesize text using the cloned voice reference.
        Returns WAV audio as bytes.
        """
        if not self.is_loaded or self._model is None:
            raise RuntimeError("TTS model is not loaded.")

        if not os.path.exists(reference_wav):
            raise FileNotFoundError(f"Reference WAV not found: {reference_wav}")

        chunks = self._chunk_text(text)
        logger.info(f"Synthesizing {len(chunks)} chunks for {len(text)} chars of text.")

        wav_segments = []

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                self._model.tts_to_file(
                    text=chunk,
                    speaker_wav=reference_wav,
                    language=language,
                    file_path=tmp_path,
                )
                with open(tmp_path, "rb") as f:
                    wav_segments.append(f.read())

                logger.debug(f"Chunk {i+1}/{len(chunks)} synthesized.")

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        if not wav_segments:
            raise ValueError("No audio was generated.")

        return self._concatenate_wav_bytes(wav_segments)

    @staticmethod
    def _chunk_text(text: str, max_chars: int = 250) -> list:
        """Split text into sentence-boundary-aware chunks."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current) + len(sentence) + 1 <= max_chars:
                current = (current + " " + sentence).strip() if current else sentence
            else:
                if current:
                    chunks.append(current)
                # Handle oversized individual sentences
                if len(sentence) > max_chars:
                    for i in range(0, len(sentence), max_chars):
                        sub = sentence[i:i + max_chars].strip()
                        if sub:
                            chunks.append(sub)
                    current = ""
                else:
                    current = sentence

        if current:
            chunks.append(current)

        return [c for c in chunks if c.strip()]

    @staticmethod
    def _concatenate_wav_bytes(wav_bytes_list: list) -> bytes:
        """Merge multiple WAV byte sequences into a single WAV."""
        output = io.BytesIO()

        with wave.open(output, 'wb') as out_wav:
            params_set = False
            for wav_bytes in wav_bytes_list:
                with wave.open(io.BytesIO(wav_bytes), 'rb') as in_wav:
                    if not params_set:
                        out_wav.setparams(in_wav.getparams())
                        params_set = True
                    out_wav.writeframes(in_wav.readframes(in_wav.getnframes()))

        return output.getvalue()
