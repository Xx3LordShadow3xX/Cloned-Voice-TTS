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

    print(f"\nAll test files saved to: {output_dir}")
    print("Listen to each file and evaluate:")
    print("  - Does it sound like your voice?")
    print("  - Is the pronunciation correct?")
    print("  - Are there notable artifacts or glitches?")
    print("\nIf quality is not acceptable, try:")
    print("  1. A different 15-second clip from your recording")
    print("  2. Record more audio (1–5 minutes)")
    print("  3. Proceed to fine-tuning (see finetune/)")


def main():
    parser = argparse.ArgumentParser(description="Test zero-shot voice cloning")
    parser.add_argument('--reference', default='voice_data/reference.wav')
    parser.add_argument('--output',    default='test_outputs/')
    args = parser.parse_args()

    run_test(args.reference, args.output)


if __name__ == '__main__':
    main()
