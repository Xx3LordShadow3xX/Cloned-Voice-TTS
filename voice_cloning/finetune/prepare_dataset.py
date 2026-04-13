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

    print(f"\nDataset ready: {output_dir}")
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
