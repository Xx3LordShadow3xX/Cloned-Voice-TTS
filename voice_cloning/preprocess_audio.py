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
    print(f"\nReady to use as XTTS v2 reference audio.")


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
