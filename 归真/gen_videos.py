#!/usr/bin/env python3
"""Generate Agnes video clips (image-to-video) for shots that have an image_url."""
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
CREATE_URL = "https://apihub.agnes-ai.com/v1/videos"
GET_URL = "https://apihub.agnes-ai.com/agnesapi"
MODEL = "agnes-video-v2.0"

MOTION = (
    ", slow cinematic camera movement, gentle natural motion, soft breathing "
    "movement of leaves and clothing, subtle light changes, no text, no watermark"
)


def local_data_uri(path) -> str:
    import base64
    ext = Path(path).suffix.lower().lstrip(".") or "png"
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def create_task(image_url: str, prompt: str, local_image: str = "", num_frames: int = 241, frame_rate: int = 24) -> str:
    image = local_data_uri(local_image) if local_image and Path(local_image).is_file() else image_url
    payload = {
        "model": MODEL,
        "prompt": prompt + MOTION,
        "image": image,
        "num_frames": num_frames,
        "frame_rate": frame_rate,
    }
    last_exc = None
    for attempt in range(8):
        try:
            resp = requests.post(
                CREATE_URL,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json=payload,
                timeout=180,
            )
            if resp.status_code in (429, 503, 500):
                last_exc = RuntimeError(f"HTTP {resp.status_code}")
                time.sleep(15 + attempt * 20)
                continue
            resp.raise_for_status()
            data = resp.json()
            vid = data.get("video_id") or data.get("id") or data.get("task_id")
            if not vid:
                raise RuntimeError(f"no video id: {data}")
            return vid
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 400:
                raise
            last_exc = exc
            time.sleep(15 + attempt * 20)
    raise last_exc or RuntimeError("create video task failed")


def poll(video_id: str, timeout_s: int = 600) -> str:
    start = time.time()
    while time.time() - start < timeout_s:
        resp = requests.get(
            GET_URL,
            params={"video_id": video_id},
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        url = data.get("url") or data.get("video_url") or (data.get("data") or {}).get("url")
        if status in ("completed", "succeeded", "done") and url:
            return url
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"video task failed: {data}")
        print(f"    status={status} progress={data.get('progress')}", flush=True)
        time.sleep(15)
    raise TimeoutError(f"video task {video_id} timed out")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", default="1", help="chapter directory name")
    args = ap.parse_args()

    chapter = args.chapter
    shots_path = BASE / chapter / "shots.json"
    shots = json.loads(shots_path.read_text(encoding="utf-8"))
    out_dir = BASE / chapter / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    rel = f"{chapter}/output"

    for i, shot in enumerate(shots, start=1):
        if not shot.get("gen_video"):
            continue
        if not shot.get("image_url") and not shot.get("image"):
            continue
        local = out_dir / f"scene_{i:02d}.mp4"
        if local.exists() and local.stat().st_size > 0:
            shot["video"] = str(Path(rel) / local.name)
            _save(shots_path, shots)
            print(f"[{i}] cached video", flush=True)
            continue
        print(f"[{i}/{len(shots)}] creating video task: {shot['scene']}", flush=True)
        try:
            vid = create_task(shot.get("image_url", ""), shot["text"], local_image=shot.get("image", ""))
        except Exception as exc:
            print(f"  ERROR create: {exc}", file=sys.stderr, flush=True)
            continue
        try:
            url = poll(vid)
        except Exception as exc:
            print(f"  ERROR poll: {exc}", file=sys.stderr, flush=True)
            continue
        try:
            r = requests.get(url, timeout=300)
            r.raise_for_status()
            local.write_bytes(r.content)
            shot["video"] = str(Path(rel) / local.name)
        except Exception as exc:
            print(f"  ERROR download: {exc}", file=sys.stderr, flush=True)
        _save(shots_path, shots)
        time.sleep(1)

    print("done")


def _save(path, shots):
    path.write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
