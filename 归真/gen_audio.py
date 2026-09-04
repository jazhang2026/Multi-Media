#!/usr/bin/env python3
"""Generate per-shot TTS audio with per-speaker voices and record durations."""
import asyncio
import json
import sys
from pathlib import Path

import edge_tts

BASE = Path(__file__).resolve().parent
OUT = None

# Narration is slowed slightly to stretch toward the 10-minute target.
RATE = {
    "zh-CN-YunyangNeural": "+6%",
    "zh-CN-YunxiNeural": "+0%",
    "zh-CN-YunjianNeural": "+0%",
    "zh-CN-XiaoxiaoNeural": "+0%",
    "zh-CN-XiaoyiNeural": "+0%",
    "zh-CN-YunxiaNeural": "+0%",
}


async def synth(text: str, voice: str, path: Path) -> float:
    rate = RATE.get(voice, "-4%")
    comm = edge_tts.Communicate(text, voice, rate=rate)
    await comm.save(str(path))
    return float(path.stat().st_size)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", default="1", help="chapter directory name")
    args = ap.parse_args()

    global OUT
    OUT = BASE / args.chapter / "audio"
    shots_path = BASE / args.chapter / "shots.json"
    shots = json.loads(shots_path.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    async def run():
        for i, shot in enumerate(shots, start=1):
            mp3 = OUT / f"shot_{i:02d}.mp3"
            text = shot["text"].strip()
            if mp3.exists() and mp3.stat().st_size > 0:
                print(f"[{i}] cached {shot['speaker']}")
                continue
            print(f"[{i}/{len(shots)}] TTS {shot['speaker']} ({shot['voice']})")
            try:
                await synth(text, shot["voice"], mp3)
            except Exception as exc:
                print(f"  ERROR: {exc}", file=sys.stderr)

    asyncio.run(run())
    print("done")


if __name__ == "__main__":
    main()
