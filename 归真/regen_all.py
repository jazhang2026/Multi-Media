#!/usr/bin/env python3
"""Rebuild shots.json + regenerate ALL scene images for chapters 1-4
(clothes without holes; written characters match the story), then pause."""
import json
import subprocess
import sys
import time
from pathlib import Path

import requests
import gen_images as G

BASE = Path(__file__).resolve().parent

# chapter -> key video shot ids (for gen_video flag + video field reassignment)
KEY_VIDEO = {
    "1": [2, 11, 13, 14, 17, 29, 30, 31, 34, 47, 48],
    "2": [14, 25, 31, 49, 62, 71, 73, 102, 105],
    "3": [4, 5, 11, 24, 27, 30, 33, 63, 70, 74, 88],
    "4": [19, 24, 32, 45, 54, 64, 72],  # to be refined after images confirmed
}


def rebuild(chapter):
    builder = BASE / f"build_shots{chapter}.py"
    if not builder.is_file():
        print(f"no builder for chapter {chapter}")
        return False
    subprocess.run([sys.executable, str(builder)], check=True)
    return True


def regen(chapter):
    shots_path = BASE / chapter / "shots.json"
    shots = json.loads(shots_path.read_text(encoding="utf-8"))
    outdir = BASE / chapter / "images_gen"
    outdir.mkdir(parents=True, exist_ok=True)

    # re-apply key video flags
    key = set(KEY_VIDEO[chapter])
    for s in shots:
        s["gen_video"] = s["id"] in key

    scenes = []
    for s in shots:
        if s["scene"] not in scenes:
            scenes.append(s["scene"])
    prompt_map = {s["scene"]: s["prompt"] for s in shots}

    scene_img, scene_url = {}, {}
    for k, scene in enumerate(scenes, start=1):
        dst = outdir / f"scene_{k:02d}.png"
        print(f"  [{k}/{len(scenes)}] regenerating {scene}", flush=True)
        url = None
        for attempt in range(6):
            try:
                url = G.gen_image(prompt_map[scene])
                break
            except Exception as e:
                print(f"    retry {attempt} {type(e).__name__}", flush=True)
                time.sleep(10 * (attempt + 1))
        if url is None:
            print(f"    FAILED {scene}", flush=True)
            continue
        r = requests.get(url, timeout=180)
        r.raise_for_status()
        dst.write_bytes(r.content)
        scene_img[scene] = str(Path(f"{chapter}/images_gen") / dst.name)
        scene_url[scene] = url
        time.sleep(1)

    for s in shots:
        s["image"] = scene_img[s["scene"]]
        if s["scene"] in scene_url:
            s["image_url"] = scene_url[s["scene"]]
        # re-associate existing dynamic video clips from disk
        vid = BASE / chapter / "output" / f"scene_{s['id']:02d}.mp4"
        if s["id"] in key and vid.is_file():
            s["video"] = str(Path(f"{chapter}/output") / vid.name)
        else:
            s.pop("video", None)

    shots_path.write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(scenes)


def main():
    for ch in ["1", "2", "3", "4"]:
        print(f"=== chapter {ch} ===", flush=True)
        if not rebuild(ch):
            continue
        n = regen(ch)
        print(f"  regenerated {n} scenes", flush=True)


if __name__ == "__main__":
    main()
