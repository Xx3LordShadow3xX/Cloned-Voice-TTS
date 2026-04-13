# Voice Cloning Setup Guide
> **For Claude Code**: Generate the scripts listed here. This guide also serves as the human-readable reference for the site owner's voice recording process.

---

## OVERVIEW

The quality of the cloned voice is **entirely determined by the reference audio**. Everything else (model, code, infrastructure) is constant. The site owner must complete the recording steps before the TTS engine can produce good output.

```
Quality Tier       Recording  Expected Output
─────────────────────────────────────────────────────────────────
Zero-shot          6–15 sec   Captures tone/timbre, some artifacts
Extended reference 1–5 min    Better consistency, demo-ready
High quality       15–30 min  Strong similarity, production-ready
Professional       1–3 hours  Near-indistinguishable, GPU training required
```

**Minimum viable**: 15-second clean reference clip for zero-shot.
**Recommended**: 20–30 minutes of recordings + fine-tuning.

---

## STEP 1: RECORDING SETUP

### Equipment

| Option | Equipment | Notes |
|---|---|---|
| Best | USB condenser mic (Blue Yeti, AT2020USB+) | Clean audio, low noise floor |
| Good | Modern smartphone | Hold 6–8 inches away at 45° angle |
| Minimum | Any mic | Must be in a quiet room |

### Environment

- **Room**: Bedroom with carpet and curtains is ideal. Avoid tile/concrete rooms.
- **Time**: Record during quiet hours (early morning, late night).
- **Off**: Turn off fans, AC, appliances. Close windows.
- **Distance**: 6–10 inches from microphone consistently throughout.

### Recording Settings

```
Format:      WAV (uncompressed) — NOT MP3
Sample rate: 44.1 kHz
Bit depth:   16-bit
Channels:    Mono
Software:    Audacity (free), GarageBand, Voice Memos (then convert)
```

### Sample Reading Script (for 15–20 minute session)

Read the following naturally, as if explaining to a friend. No performance voice needed — speak normally.

```
Section 1 — News style (varied sentences):
Today's weather forecast shows clear skies through the weekend, 
with temperatures rising to the mid-seventies by Saturday afternoon. 
Local officials announced a new community center project, expected 
to break ground in the spring. The proposal received unanimous 
approval from the city council after months of public comment.

Section 2 — Technical content (to capture pronunciation range):
The application uses a Python-based backend with FastAPI for 
request handling. Files are validated against an allowlist of 
supported extensions, including TXT, PDF, and DOCX formats. 
Each upload is assigned a UUID filename to prevent path traversal 
vulnerabilities during temporary storage.

Section 3 — Questions and varied prosody:
Have you ever wondered how voice synthesis technology actually works? 
The process involves training a model on hours of speech recordings. 
What makes it remarkable is the ability to generalize from just a 
few seconds of reference audio. Incredible, isn't it?

Section 4 — Lists and enumerations:
There are three key requirements for a good recording environment. 
First, minimize background noise as much as possible. Second, 
maintain a consistent distance from the microphone. Third, speak 
at your natural pace — not too fast, not too slow.

Section 5 — Numbers, abbreviations, and special terms:
The file size limit is ten megabytes per upload. Processing 
typically takes between two and five minutes for a full page 
of text. The API returns audio in WAV format, at twenty-two 
kilohertz, mono channel. Version one point zero includes 
basic playback and download capabilities.
```

Repeat sections, add your own content, and read for 15–30 minutes total.

---

## STEP 2: AUDIO PREPROCESSING

After recording, run the preprocessing script to clean and prepare the audio.

### COMPLETE FILE: `voice_cloning/preprocess_audio.py`

```python
#!/usr/bin/env python3
"""
Preprocess a raw voice recording for XTTS v2.
- Converts to mono
- Resamples to 22.05 kHz (for zero-shot reference)
- Normalizes volume
- Removes silence from start/end
- Exports as WAV

Usage:
    python preprocess_audio.py --input my_recording.wav --output voice_data/reference.wav
    python preprocess_audio.py --input my_recording.wav --output voice_data/reference.wav --duration 15
"""

import argparse
import sys
import os


def preprocess(input_path: str, output_path: str, duration_sec: float = None):
    """
    Preprocess audio file for XTTS v2 reference use.
    """
    try:
        from pydub import AudioSegment
        from pydub.effects import normalize
        import librosa
        import soundfile as sf
        import numpy as np
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install pydub librosa soundfile numpy")
        sys.exit(1)

    print(f"Loading: {input_path}")
    audio = AudioSegment.from_file(input_path)

    print(f"Original: {len(audio)/1000:.1f}s, {audio.frame_rate}Hz, {audio.channels}ch")

    # Convert to mono
    audio = audio.set_channels(1)

    # Trim silence from start and end
    from pydub.silence import detect_leading_silence
    start_trim = detect_leading_silence(audio, silence_threshold=-40)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=-40)
    duration = len(audio)
    audio = audio[start_trim:duration - end_trim]

    # Normalize volume to -3 dBFS
    audio = normalize(audio, headroom=3.0)

    # Trim to desired duration if specified
    if duration_sec:
        target_ms = int(duration_sec * 1000)
        if len(audio) > target_ms:
            audio = audio[:target_ms]
            print(f"Trimmed to {duration_sec}s")
        else:
            print(f"Warning: audio is shorter than requested {duration_sec}s duration")

    # Resample to 22050 Hz using librosa for quality
    raw_samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    raw_samples = raw_samples / (2**15)  # Normalize 16-bit PCM to [-1, 1]

    target_sr = 22050
    if audio.frame_rate != target_sr:
        resampled = librosa.resample(raw_samples, orig_sr=audio.frame_rate, target_sr=target_sr)
        print(f"Resampled: {audio.frame_rate}Hz → {target_sr}Hz")
    else:
        resampled = raw_samples
        print(f"Sample rate already {target_sr}Hz, no resample needed")

    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    # Save as WAV
    sf.write(output_path, resampled, target_sr, subtype='PCM_16')

    print(f"\nOutput saved: {output_path}")
    print(f"Duration: {len(resampled)/target_sr:.2f}s")
    print(f"Sample rate: {target_sr}Hz")
    print(f"Channels: 1 (mono)")
    print(f"\n✅ Ready to use as XTTS v2 reference audio.")


def main():
    parser = argparse.ArgumentParser(description="Preprocess voice audio for XTTS v2")
    parser.add_argument('--input',    required=True,  help='Input audio file path')
    parser.add_argument('--output',   required=True,  help='Output WAV file path')
    parser.add_argument('--duration', type=float, default=15.0,
                        help='Clip duration in seconds (default: 15.0). Use 0 to keep full length.')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    duration = args.duration if args.duration > 0 else None
    preprocess(args.input, args.output, duration)


if __name__ == '__main__':
    main()
```

---

## STEP 3: TEST ZERO-SHOT CLONING

After preprocessing, test that the reference clip produces acceptable voice output.

### COMPLETE FILE: `voice_cloning/test_zero_shot.py`

```python
#!/usr/bin/env python3
"""
Quick test of zero-shot voice cloning with the reference audio.
Generates a few test sentences and saves them as WAV files.

Usage:
    python test_zero_shot.py --reference voice_data/reference.wav --output test_outputs/
"""

import argparse
import os
import sys


TEST_SENTENCES = [
    "Hello, this is a test of the voice cloning system.",
    "The quick brown fox jumps over the lazy dog.",
    "Welcome to the document reader. Upload any text file and I'll read it for you.",
    "This is a longer sentence to test how the model handles extended speech synthesis across multiple words.",
    "Is the voice quality acceptable? Does it sound natural to you?",
]


def run_test(reference_wav: str, output_dir: str):
    """Generate test audio from each test sentence."""
    try:
        from TTS.api import TTS
        import torch
    except ImportError:
        print("Coqui TTS not installed. Run: pip install TTS")
        sys.exit(1)

    if not os.path.exists(reference_wav):
        print(f"Reference WAV not found: {reference_wav}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading XTTS v2 on {device}... (this may take 1–2 minutes)")

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    print("Model loaded.\n")

    for i, sentence in enumerate(TEST_SENTENCES):
        output_path = os.path.join(output_dir, f"test_{i+1:02d}.wav")
        print(f"Generating [{i+1}/{len(TEST_SENTENCES)}]: {sentence[:60]}...")

        tts.tts_to_file(
            text=sentence,
            speaker_wav=reference_wav,
            language="en",
            file_path=output_path,
        )
        print(f"  → Saved: {output_path}")

    print(f"\n✅ All test files saved to: {output_dir}")
    print("Listen to each file and evaluate:")
    print("  - Does it sound like your voice?")
    print("  - Is the pronunciation correct?")
    print("  - Are there notable artifacts or glitches?")
    print("\nIf quality is not acceptable, try:")
    print("  1. A different 15-second clip from your recording")
    print("  2. Record more audio (1–5 minutes)")
    print("  3. Proceed to fine-tuning (see STEP 4)")


def main():
    parser = argparse.ArgumentParser(description="Test zero-shot voice cloning")
    parser.add_argument('--reference', default='voice_data/reference.wav')
    parser.add_argument('--output',    default='test_outputs/')
    args = parser.parse_args()

    run_test(args.reference, args.output)


if __name__ == '__main__':
    main()
```

---

## STEP 4: FINE-TUNING (For Production Quality)

Fine-tuning significantly improves voice similarity. Requires 15–30 minutes of recordings and a GPU (Google Colab T4 is free).

### COMPLETE FILE: `voice_cloning/finetune/prepare_dataset.py`

```python
#!/usr/bin/env python3
"""
Prepare a fine-tuning dataset for XTTS v2.
Splits a long recording into 5–15 second segments and creates a metadata CSV.

Usage:
    python prepare_dataset.py \
        --input my_long_recording.wav \
        --output_dir dataset/ \
        --transcript "Path to transcript.txt (optional)"
"""

import argparse
import os
import csv
import sys


def prepare_dataset(input_wav: str, output_dir: str, transcript_file: str = None):
    """
    Split audio into segments and create XTTS fine-tuning metadata.
    """
    try:
        import librosa
        import soundfile as sf
        from pydub import AudioSegment
        from pydub.silence import split_on_silence
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install: pip install librosa soundfile pydub")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    wavs_dir = os.path.join(output_dir, 'wavs')
    os.makedirs(wavs_dir, exist_ok=True)

    print(f"Loading audio: {input_wav}")
    audio = AudioSegment.from_file(input_wav)

    # Convert to mono, 22050 Hz
    audio = audio.set_channels(1).set_frame_rate(22050)

    # Split on silence (silence < -40 dBFS for > 500ms)
    print("Splitting on silence...")
    chunks = split_on_silence(
        audio,
        min_silence_len=500,
        silence_thresh=-40,
        keep_silence=200,
    )

    # Merge short chunks, split long ones
    target_min_ms = 5000    # 5 seconds
    target_max_ms = 12000   # 12 seconds

    segments = []
    current = AudioSegment.empty()

    for chunk in chunks:
        if len(current) + len(chunk) < target_max_ms:
            current += chunk
        else:
            if len(current) >= target_min_ms:
                segments.append(current)
            current = chunk

    if len(current) >= target_min_ms:
        segments.append(current)

    print(f"Created {len(segments)} segments")

    # Load transcript if provided
    transcripts = []
    if transcript_file and os.path.exists(transcript_file):
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcripts = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(transcripts)} transcript lines")

    # Save segments and create metadata
    metadata_path = os.path.join(output_dir, 'metadata.csv')
    speaker_name = "speaker"

    with open(metadata_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        writer.writerow(['audio_file', 'text', 'speaker_name'])

        for i, segment in enumerate(segments):
            filename = f"seg_{i+1:04d}.wav"
            filepath = os.path.join(wavs_dir, filename)

            # Export segment
            segment.export(filepath, format='wav')

            # Use transcript if available, else placeholder
            if i < len(transcripts):
                text = transcripts[i]
            else:
                text = f"[NEEDS TRANSCRIPT - Segment {i+1}]"

            writer.writerow([os.path.join('wavs', filename), text, speaker_name])
            print(f"  Segment {i+1:04d}: {len(segment)/1000:.1f}s → {text[:50]}")

    print(f"\n✅ Dataset ready: {output_dir}")
    print(f"   Segments:  {len(segments)} files in {wavs_dir}/")
    print(f"   Metadata:  {metadata_path}")
    print("\nNext steps:")
    print("  1. Open metadata.csv and fill in any missing [NEEDS TRANSCRIPT] entries")
    print("  2. Upload dataset to Google Drive")
    print("  3. Open colab_finetune.ipynb in Google Colab")


def main():
    parser = argparse.ArgumentParser(description="Prepare XTTS v2 fine-tuning dataset")
    parser.add_argument('--input',      required=True, help='Input WAV file')
    parser.add_argument('--output_dir', required=True, help='Output directory')
    parser.add_argument('--transcript', default=None,  help='Optional transcript text file')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}")
        sys.exit(1)

    prepare_dataset(args.input, args.output_dir, args.transcript)


if __name__ == '__main__':
    main()
```

---

## STEP 4b: Google Colab Fine-Tuning Notebook

### COMPLETE FILE: `voice_cloning/finetune/colab_finetune.ipynb`

Create this notebook with the following cell structure (JSON format for .ipynb):

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.10.0"}
 },
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["# XTTS v2 Fine-Tuning — Voice TTS App\n\n**Runtime**: GPU (T4 recommended)\n\nChange runtime: Runtime → Change runtime type → T4 GPU\n\n**Estimated time**: 5–20 hours depending on dataset size"]
  },
  {
   "cell_type": "code",
   "metadata": {},
   "source": [
    "# Cell 1: Check GPU\n",
    "import torch\n",
    "print(f'CUDA available: {torch.cuda.is_available()}')\n",
    "if torch.cuda.is_available():\n",
    "    print(f'GPU: {torch.cuda.get_device_name(0)}')\n",
    "    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')\n",
    "else:\n",
    "    print('WARNING: No GPU detected. Fine-tuning will be very slow.')"
   ]
  },
  {
   "cell_type": "code",
   "metadata": {},
   "source": [
    "# Cell 2: Install dependencies\n",
    "!pip install -q TTS[all]\n",
    "!pip install -q datasets"
   ]
  },
  {
   "cell_type": "code",
   "metadata": {},
   "source": [
    "# Cell 3: Mount Google Drive (upload your dataset folder here)\n",
    "from google.colab import drive\n",
    "drive.mount('/content/drive')\n",
    "\n",
    "# Update this path to your dataset location in Google Drive\n",
    "DATASET_PATH = '/content/drive/MyDrive/voice_dataset/'\n",
    "OUTPUT_PATH  = '/content/drive/MyDrive/xtts_finetuned/'"
   ]
  },
  {
   "cell_type": "code",
   "metadata": {},
   "source": [
    "# Cell 4: Run fine-tuning\n",
    "import os\n",
    "os.makedirs(OUTPUT_PATH, exist_ok=True)\n",
    "\n",
    "from TTS.bin.train_tts import main as train\n",
    "# See Coqui TTS docs for fine-tune config options:\n",
    "# https://tts.readthedocs.io/en/latest/training_a_model.html\n",
    "\n",
    "# Fine-tune command (adjust config path as needed)\n",
    "!tts --model_name tts_models/multilingual/multi-dataset/xtts_v2 \\\n",
    "     # Note: Fine-tuning XTTS v2 uses the Coqui fine-tuning script\n",
    "     # Refer to: https://github.com/coqui-ai/TTS/tree/dev/recipes/ljspeech\n",
    "     # for the most up-to-date fine-tuning approach"
   ]
  },
  {
   "cell_type": "code",
   "metadata": {},
   "source": [
    "# Cell 5: Test fine-tuned model\n",
    "from TTS.api import TTS\n",
    "\n",
    "# Load the fine-tuned model from output directory\n",
    "tts = TTS(model_path=OUTPUT_PATH)\n",
    "\n",
    "tts.tts_to_file(\n",
    "    text='This is a test of the fine-tuned voice model.',\n",
    "    speaker_wav=f'{DATASET_PATH}/reference.wav',\n",
    "    language='en',\n",
    "    file_path='/content/finetuned_test.wav'\n",
    ")\n",
    "\n",
    "from IPython.display import Audio\n",
    "Audio('/content/finetuned_test.wav')"
   ]
  }
 ]
}
```

---

## VOICE QUALITY CHECKLIST

Before using the reference clip in production:

- [ ] Recording is at least 10 seconds (15 seconds recommended)
- [ ] No background noise audible
- [ ] No clipping (audio waveform never hits maximum)
- [ ] Consistent volume throughout
- [ ] Natural speaking pace (not rushed, not exaggerated)
- [ ] Saved as WAV (not MP3)
- [ ] Preprocessed: 22.05 kHz, mono, normalized
- [ ] Zero-shot test produces recognizable voice output
- [ ] Test sentences play back without major artifacts
- [ ] MOS rating ≥ 3.5 from 3+ listeners (for production)

---

## TROUBLESHOOTING

| Problem | Cause | Solution |
|---|---|---|
| Voice sounds robotic | Poor reference audio quality | Re-record in quieter environment |
| Voice sounds like different person | Reference too short | Use longer clip (15+ sec) |
| Mispronunciation of names/acronyms | Model limitation | Use phonetic spelling in text |
| Voice drifts in long passages | Long-form synthesis limitation | Chunk at 250 chars (already done) |
| Slow generation | CPU inference | Expected — 0.3–0.5x real-time |
| TTS install fails | Python/torch version mismatch | Use Python 3.10, follow requirements.txt |
