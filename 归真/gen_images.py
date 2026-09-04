#!/usr/bin/env python3
"""Generate missing scene images with Agnes AI and update shots.json.

Resumable: skips shots whose local PNG already exists; saves shots.json after
every image so partial progress survives interruption.
"""
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")
API_KEY = os.environ.get("AGNES_API_KEY")
API_URL = "https://apihub.agnes-ai.com/v1/images/generations"
MODEL = "agnes-image-2.5-flash"

STYLE = (
    ", ink-wash watercolor illustration, muted earthy tones, 1960s Chinese "
    "countryside, consistent character design, soft cinematic lighting, "
    "neat clean clothing, well-finished smooth surfaces, "
    "no text, no watermark"
)


def gen_image(prompt: str, ratio: str = "16:9") -> str:
    full_prompt = prompt.rstrip().rstrip("。") + STYLE
    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "size": "2K",
        "ratio": ratio,
        "extra_body": {"response_format": "url"},
    }
    last_exc = None
    for attempt in range(5):
        try:
            resp = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=180,
            )
            if resp.status_code in (429, 503, 500):
                last_exc = RuntimeError(f"HTTP {resp.status_code}")
                time.sleep(2 ** attempt * 3)
                continue
            resp.raise_for_status()
            data = resp.json()
            url = (data.get("data") or [{}])[0].get("url")
            if not url:
                raise RuntimeError(f"no url in response: {data}")
            return url
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 400:
                raise
            last_exc = exc
            time.sleep(2 ** attempt * 3)
    raise last_exc or RuntimeError("image generation failed")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", default="1", help="chapter directory name")
    args = ap.parse_args()

    chapter = args.chapter
    shots_path = BASE / chapter / "shots.json"
    shots = json.loads(shots_path.read_text(encoding="utf-8"))
    out_dir = BASE / chapter / "images_gen"
    out_dir.mkdir(parents=True, exist_ok=True)
    rel = f"{chapter}/images_gen"

    for i, shot in enumerate(shots, start=1):
        if shot.get("image"):
            continue
        prompt = shot.get("prompt")
        if not prompt:
            continue
        local = out_dir / f"shot_{i:02d}.png"
        if local.exists() and local.stat().st_size > 0:
            shot["image"] = str(Path(rel) / local.name)
            _save(shots_path, shots)
            print(f"[{i}] cached local image")
            continue
        print(f"[{i}/{len(shots)}] generating image: {shot['scene']} - {shot['speaker']}", flush=True)
        try:
            url = gen_image(prompt)
        except Exception as exc:
            print(f"  ERROR (skipped): {exc}", file=sys.stderr, flush=True)
            continue
        shot["image_url"] = url
        try:
            r = requests.get(url, timeout=180)
            r.raise_for_status()
            local.write_bytes(r.content)
            shot["image"] = str(Path(rel) / local.name)
        except Exception as exc:
            print(f"  download error: {exc}", file=sys.stderr, flush=True)
        _save(shots_path, shots)
        time.sleep(1)

    print("done")


def _save(path, shots):
    path.write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
