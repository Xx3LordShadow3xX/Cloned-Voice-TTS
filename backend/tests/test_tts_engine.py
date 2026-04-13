"""Unit tests for TTSEngine helper methods (no actual model loading)."""
import pytest
import io
import wave
from unittest.mock import patch, MagicMock
from services.tts_engine import TTSEngine


engine = TTSEngine()


class TestChunkText:
    def test_short_text_stays_one_chunk(self):
        chunks = engine._chunk_text("Hello world.", max_chars=250)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world."

    def test_long_text_split_on_sentences(self):
        text = "First sentence. Second sentence. Third sentence."
        chunks = engine._chunk_text(text, max_chars=25)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 35  # Some tolerance for long words

    def test_empty_text_returns_empty(self):
        chunks = engine._chunk_text("", max_chars=250)
        assert chunks == []

    def test_whitespace_only_returns_empty(self):
        chunks = engine._chunk_text("   \n\t  ", max_chars=250)
        assert chunks == []

    def test_oversized_single_sentence_split_by_length(self):
        long_sentence = "A" * 500
        chunks = engine._chunk_text(long_sentence, max_chars=250)
        assert len(chunks) == 2
        for chunk in chunks:
            assert len(chunk) <= 250

    def test_normalizes_excess_whitespace(self):
        text = "Hello    world.   How are   you?"
        chunks = engine._chunk_text(text, max_chars=250)
        assert len(chunks) == 1
        assert "  " not in chunks[0]

    def test_preserves_all_content(self):
        text = "First sentence. Second sentence."
        chunks = engine._chunk_text(text, max_chars=20)
        rejoined = " ".join(chunks)
        # All words should still be present
        assert "First" in rejoined
        assert "Second" in rejoined


class TestConcatenateWavBytes:
    def make_wav(self, num_frames=100, frame_rate=22050):
        """Create minimal WAV bytes."""
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(frame_rate)
            w.writeframes(b'\x00\x00' * num_frames)
        return buf.getvalue()

    def test_concatenate_two_segments(self):
        seg1 = self.make_wav(100)
        seg2 = self.make_wav(100)
        result = engine._concatenate_wav_bytes([seg1, seg2])

        buf = io.BytesIO(result)
        with wave.open(buf, 'rb') as w:
            assert w.getnframes() == 200

    def test_single_segment_unchanged(self):
        seg = self.make_wav(150)
        result = engine._concatenate_wav_bytes([seg])

        buf = io.BytesIO(result)
        with wave.open(buf, 'rb') as w:
            assert w.getnframes() == 150

    def test_valid_wav_header(self):
        result = engine._concatenate_wav_bytes([self.make_wav(50)])
        assert result[:4] == b'RIFF'
        assert result[8:12] == b'WAVE'
