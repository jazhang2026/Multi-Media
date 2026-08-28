#!/usr/bin/env python3
"""Add burned-in Chinese subtitles to a video using Whisper + FFmpeg."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_chinese_font():
    """Find a Chinese font available to libass/fontconfig."""
    candidates = [
        "Noto Sans CJK SC",
        "Noto Sans CJK SC Regular",
        "Noto Sans Mono CJK SC",
        "Source Han Sans SC",
        "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei",
        "Microsoft YaHei",
    ]
    try:
        result = subprocess.run(
            ["fc-list", ":lang=zh", "family"],
            capture_output=True,
            text=True,
            check=True,
        )
        available = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    for candidate in candidates:
        if candidate in available:
            return candidate
    return None


def build_initial_prompt(text_path):
    """Use the original script as an initial prompt to guide Whisper."""
    if not text_path or not Path(text_path).is_file():
        return None
    text = Path(text_path).read_text(encoding="utf-8")
    # Whisper expects a short prompt; take the first ~1000 characters.
    return text[:1000]


def run_whisper(audio_path, model, language, output_dir, initial_prompt=None):
    """Run OpenAI Whisper to generate an SRT file."""
    cmd = [
        "whisper",
        str(audio_path),
        "--model", model,
        "--language", language,
        "--output_format", "srt",
        "--output_dir", str(output_dir),
        "--word_timestamps", "False",
    ]
    if initial_prompt:
        cmd.extend(["--initial_prompt", initial_prompt])
    subprocess.run(cmd, check=True)

    base = Path(audio_path).stem
    srt_path = Path(output_dir) / f"{base}.srt"
    if not srt_path.exists():
        raise FileNotFoundError(f"Whisper did not generate {srt_path}")
    return srt_path


def run_ffmpeg(video_path, srt_path, output_path, font_name):
    """Burn subtitles into the video using FFmpeg."""
    style = (
        f"FontName={font_name},"
        "FontSize=28,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=50"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vf", f"subtitles={srt_path}:force_style='{style}'",
        "-c:a", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Add burned-in Chinese subtitles to a video using Whisper + FFmpeg."
    )
    parser.add_argument("--video", required=True, help="Input video file")
    parser.add_argument("--audio", required=True, help="Audio file used to generate subtitles")
    parser.add_argument("--output", required=True, help="Output video file with burned-in subtitles")
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: small)",
    )
    parser.add_argument("--language", default="Chinese", help="Language for Whisper (default: Chinese)")
    parser.add_argument("--text", default=None, help="Original Chinese script file used for an initial prompt (improves accuracy)")
    parser.add_argument("--keep-srt", action="store_true", help="Keep the generated SRT file next to the output")
    args = parser.parse_args()

    for path in (args.video, args.audio):
        if not os.path.isfile(path):
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)

    if not shutil.which("whisper"):
        print("Error: whisper is not installed. Run:", file=sys.stderr)
        print("  pip install openai-whisper", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("ffmpeg"):
        print("Error: ffmpeg is not installed. Run:", file=sys.stderr)
        print("  sudo apt install ffmpeg", file=sys.stderr)
        sys.exit(1)

    font_name = find_chinese_font()
    if not font_name:
        print("Error: no Chinese font found. Install one with:", file=sys.stderr)
        print("  sudo apt install fonts-noto-cjk", file=sys.stderr)
        sys.exit(1)

    print(f"Using Chinese font: {font_name}")
    print(f"Running Whisper ({args.model}) on {args.audio}...")
    if args.text:
        print(f"Using original script for initial prompt: {args.text}")

    initial_prompt = build_initial_prompt(args.text)
    with tempfile.TemporaryDirectory() as tmpdir:
        srt_path = run_whisper(args.audio, args.model, args.language, tmpdir, initial_prompt)
        if args.keep_srt:
            saved_srt = Path(args.output).with_suffix(".srt")
            shutil.copy(srt_path, saved_srt)
            print(f"Saved SRT: {saved_srt}")

        print(f"Burning subtitles into {args.output}...")
        run_ffmpeg(args.video, srt_path, args.output, font_name)

    print(f"Done: {args.output}")


if __name__ == "__main__":
    main()
