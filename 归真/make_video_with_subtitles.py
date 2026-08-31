#!/usr/bin/env python3
"""Generate a story video and burn in Chinese subtitles in one step.

If an SRT file already exists next to the audio file, Whisper/correction is
skipped and the existing SRT is used directly.

Usage (from 归真/):
    source .venv/bin/activate
    python3 make_video_with_subtitles.py 13/video_config.json

The script produces:
    - <config.output>                     (base video, e.g. 13/chpt13.mp4)
    - <output_stem>_subtitled.mp4       (video with burned-in subtitles)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Import helpers from the existing add_subtitles module.
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))
from add_subtitles import (
    build_initial_prompt,
    find_chinese_font,
    run_ffmpeg,
    run_whisper,
)


def make_base_video(config_path: Path) -> None:
    """Run make_video.py with the given JSON config."""
    cmd = [sys.executable, str(script_dir / "make_video.py"), str(config_path)]
    subprocess.run(cmd, check=True)


def correct_srt(srt_path: Path, text_path: Path) -> None:
    """Run correct_srt.py to fix typos against the original narration text."""
    if not text_path.is_file():
        print(f"No text file found at {text_path}; skipping typo correction.")
        return
    cmd = [
        sys.executable,
        str(script_dir / "correct_srt.py"),
        str(srt_path),
        str(text_path),
        str(srt_path),
    ]
    subprocess.run(cmd, check=True)


def generate_or_reuse_srt(audio_path: Path, text_path: Path, model: str, language: str) -> Path:
    """Return the SRT path, generating + correcting it only if it does not exist."""
    srt_path = audio_path.with_suffix(".srt")

    if srt_path.is_file() and srt_path.stat().st_size > 0:
        print(f"Using existing SRT: {srt_path}")
        return srt_path

    if not shutil.which("whisper"):
        print("Error: whisper is not installed. Run: pip install openai-whisper", file=sys.stderr)
        sys.exit(1)

    print(f"No SRT found; generating one from {audio_path} with Whisper ({model})...")
    initial_prompt = build_initial_prompt(str(text_path)) if text_path.is_file() else None
    run_whisper(str(audio_path), model, language, str(audio_path.parent), initial_prompt)

    print(f"Correcting SRT against {text_path}...")
    correct_srt(srt_path, text_path)

    return srt_path


def subtitled_output_path(base_output: Path) -> Path:
    """Insert '_subtitled' before the extension."""
    return base_output.with_name(f"{base_output.stem}_subtitled{base_output.suffix}")


def main():
    parser = argparse.ArgumentParser(
        description="Make a video and burn in Chinese subtitles. Reuse existing SRT if available."
    )
    parser.add_argument("config", help="Path to the JSON video config file")
    parser.add_argument(
        "--text",
        default=None,
        help="Path to the original narration text (default: <config_dir>/tts.txt)",
    )
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size when generating SRT (default: small)",
    )
    parser.add_argument(
        "--language",
        default="Chinese",
        help="Whisper language when generating SRT (default: Chinese)",
    )
    parser.add_argument(
        "--keep-srt",
        action="store_true",
        help="Keep the generated/corrected SRT file next to the audio file",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_file():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    audio_path = Path(config["audio"])
    base_output = Path(config["output"])

    # Default narration text is in the same directory as the config file.
    text_path = Path(args.text) if args.text else config_path.with_name("tts.txt")

    # 1. Generate base video
    print(f"Generating base video: {base_output}")
    make_base_video(config_path)

    # 2. Obtain SRT (reuse if it exists)
    srt_path = generate_or_reuse_srt(audio_path, text_path, args.model, args.language)

    if not srt_path.is_file():
        print(f"Error: SRT not available at {srt_path}", file=sys.stderr)
        sys.exit(1)

    # 3. Burn subtitles
    font_name = find_chinese_font()
    if not font_name:
        print("Error: no Chinese font found. Install fonts-noto-cjk.", file=sys.stderr)
        sys.exit(1)

    subtitled_output = subtitled_output_path(base_output)
    print(f"Burning subtitles into {subtitled_output}")
    run_ffmpeg(str(base_output), str(srt_path), str(subtitled_output), font_name)

    if args.keep_srt:
        kept_srt = subtitled_output.with_suffix(".srt")
        shutil.copy(srt_path, kept_srt)
        print(f"Kept SRT: {kept_srt}")

    print(f"Done:\n  {base_output}\n  {subtitled_output}")


if __name__ == "__main__":
    main()
