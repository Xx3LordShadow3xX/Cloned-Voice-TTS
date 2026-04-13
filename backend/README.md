---
title: Voice TTS API
emoji: 🎙️
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
short_description: Document-to-speech API using cloned voice synthesis
---

# Voice TTS API

REST API backend for the Voice-Cloned TTS web application.

## Endpoints

- `GET /api/v1/health` — Health check and model status
- `POST /api/v1/synthesize` — Upload document, receive WAV audio

## Environment Variables

Set these in the HF Space **Settings → Variables and Secrets** tab:

| Variable | Description | Example |
|---|---|---|
| `REFERENCE_WAV_PATH` | Path to reference audio | `/data/reference.wav` |
| `ALLOWED_ORIGINS` | Frontend URL (comma-separated) | `https://username.github.io` |
| `RATE_LIMIT_PER_MINUTE` | Max requests per IP per minute | `5` |
| `TTS_LANGUAGE` | Default TTS language | `en` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Uploading the Reference Audio

Use the HF Spaces persistent storage (`/data`) to store the reference WAV.

From the HF Space "Files" tab, upload `reference.wav` to the `/data` directory,
then set `REFERENCE_WAV_PATH=/data/reference.wav` in environment variables.
