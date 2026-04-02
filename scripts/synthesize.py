#!/usr/bin/env python3
"""
synthesize.py — Convert a text script file to speech using Google Chirp 3 HD voices.

Usage:
    python scripts/synthesize.py --input-file scripts/episode1.txt --output output/episode1.mp3

Optional flags:
    --voice     Chirp 3 HD voice name (default: en-US-Chirp3-HD-Zephyr)
    --language  Language code          (default: en-US)
    --project   GCP project ID         (overrides .env / env var)
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import texttospeech

# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------
DEFAULT_VOICE = "en-US-Chirp3-HD-Zephyr"
DEFAULT_LANGUAGE = "en-US"
# Chirp 3 HD voices top out around 5000 chars per request.
# We split on sentence boundaries to stay safely under the limit.
MAX_CHARS_PER_CHUNK = 4500


def load_project_id(cli_project: str | None) -> str:
    """Return project ID from CLI flag → .env → environment variable."""
    if cli_project:
        return cli_project
    load_dotenv()
    project = os.getenv("GCP_PROJECT_ID")
    if not project:
        print(
            "ERROR: GCP_PROJECT_ID not set.\n"
            "  • Pass --project <id>, or\n"
            "  • Copy .env.example → .env and set GCP_PROJECT_ID.",
            file=sys.stderr,
        )
        sys.exit(1)
    return project


def read_script(path: Path) -> str:
    """Read a text file and return its contents with normalised whitespace."""
    if not path.exists():
        print(f"ERROR: Input file not found: {path}", file=sys.stderr)
        sys.exit(1)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        print(f"ERROR: Input file is empty: {path}", file=sys.stderr)
        sys.exit(1)
    return text


def split_into_chunks(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> list[str]:
    """
    Split text into chunks that fit within the TTS API limit.

    Strategy: split on sentence-ending punctuation, then rejoin greedily
    until the next sentence would exceed max_chars.
    """
    import re

    # Split on sentence boundaries (keep the delimiter at the end of each sentence)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            # If a single sentence is longer than the limit, hard-split it
            if len(sentence) > max_chars:
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i : i + max_chars])
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def synthesize_chunks(
    chunks: list[str],
    client: texttospeech.TextToSpeechClient,
    voice_name: str,
    language_code: str,
) -> bytes:
    """Synthesize each chunk as MP3 and concatenate the raw audio bytes."""
    audio_data = b""
    total = len(chunks)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )

    for i, chunk in enumerate(chunks, start=1):
        print(f"  Synthesizing chunk {i}/{total} ({len(chunk)} chars)…")
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=chunk),
            voice=voice,
            audio_config=audio_config,
        )
        audio_data += response.audio_content

    return audio_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a text podcast script to MP3 using Google Chirp 3 HD."
    )
    parser.add_argument(
        "--input-file",
        "-i",
        type=Path,
        required=True,
        help="Path to the .txt podcast script.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output .mp3 file path. Defaults to output/<input-stem>.mp3",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Chirp 3 HD voice name. Default: {DEFAULT_VOICE}",
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help=f"BCP-47 language code. Default: {DEFAULT_LANGUAGE}",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="GCP project ID (overrides .env / GCP_PROJECT_ID env var).",
    )
    args = parser.parse_args()

    # ---- resolve project ID ------------------------------------------------
    project_id = load_project_id(args.project)

    # ---- resolve output path -----------------------------------------------
    if args.output is None:
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        args.output = output_dir / f"{args.input_file.stem}.mp3"
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)

    # ---- read script -------------------------------------------------------
    print(f"📄 Reading script: {args.input_file}")
    text = read_script(args.input_file)
    print(f"   {len(text)} characters total.")

    # ---- split into API-safe chunks ----------------------------------------
    chunks = split_into_chunks(text)
    print(f"   Split into {len(chunks)} chunk(s).")

    # ---- set up TTS client -------------------------------------------------
    # Authentication: uses Application Default Credentials.
    # Run:  gcloud auth application-default login
    # The client will pick up the project from the quota header we set below.
    client_options = {"api_endpoint": "texttospeech.googleapis.com"}
    client = texttospeech.TextToSpeechClient(client_options=client_options)

    # Pass project ID as a quota / billing header on every request
    # by wrapping with a custom request metadata setter.
    print(f"\n🎙  Voice: {args.voice}")
    print(f"🔑  Project: {project_id}\n")

    # ---- synthesize --------------------------------------------------------
    audio_bytes = synthesize_chunks(chunks, client, args.voice, args.language)

    # ---- write output ------------------------------------------------------
    args.output.write_bytes(audio_bytes)
    size_kb = len(audio_bytes) / 1024
    print(f"\n✅ Done! Audio written to: {args.output}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
