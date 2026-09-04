#!/usr/bin/env python3
"""Generate a perfectly-synced SRT directly from shots.json + per-shot audio.

Because the video audio is assembled from these same per-shot mp3 files, we can
derive each subtitle's start/end time exactly instead of relying on Whisper's
approximate segmentation.
"""
import argparse
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent


def audio_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    )
    return float(out.strip())


def fmt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", default="1")
    ap.add_argument("--narr-pause", type=float, default=2.2)
    ap.add_argument("--dial-pause", type=float, default=0.8)
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    chapter = args.chapter
    shots = json.loads((BASE / chapter / "shots.json").read_text(encoding="utf-8"))
    audio_dir = BASE / chapter / "audio"
    output = args.output or f"{chapter}/chpt{chapter}_ai_synced.srt"

    entries = []
    t = 0.0
    for i, shot in enumerate(shots, start=1):
        mp3 = audio_dir / f"shot_{i:02d}.mp3"
        if not mp3.is_file():
            continue
        d = audio_duration(mp3)
        entries.append(f"{len(entries) + 1}\n{fmt_time(t)} --> {fmt_time(t + d)}\n{shot['text']}\n")
        pause = args.narr_pause if shot.get("speaker") == "旁白" else args.dial_pause
        t += d + pause

    (BASE / output).write_text("\n".join(entries), encoding="utf-8")
    print(f"wrote {len(entries)} cues -> {output}")
    print(f"total timeline: {t:.1f}s ({t/60:.2f} min)")


if __name__ == "__main__":
    main()
