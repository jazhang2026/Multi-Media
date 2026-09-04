#!/usr/bin/env python3
"""Assemble shots.json + per-shot audio + images/videos into a subtitled video."""
import argparse
import json
import subprocess
from pathlib import Path

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)

BASE = Path(__file__).resolve().parent


def ken_burns(img_clip, dur, size=(1920, 1080), zoom=1.08):
    """Slow centered zoom on a static image (Ken Burns effect)."""
    ow, oh = int(size[0] * zoom), int(size[1] * zoom)
    base = fit_cover(img_clip, (ow, oh))
    base = base.resized(lambda t: 1 + (zoom - 1) * (t / dur))
    bg = ColorClip(size=size, color=(0, 0, 0), duration=dur)
    comp = CompositeVideoClip([bg, base.with_position("center")], size=size)
    return comp.with_duration(dur)


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


def fit_cover(clip: object, size=(1920, 1080)) -> object:
    """Scale + center-crop so the clip fills `size` without distortion."""
    w, h = size
    cw, ch = clip.w, clip.h
    scale = max(w / cw, h / ch)
    clip = clip.resized(scale)
    return clip.cropped(
        x_center=int(clip.w / 2),
        y_center=int(clip.h / 2),
        width=w,
        height=h,
    )


def make_visual(shot: dict, dur: float, size=(1920, 1080)) -> object:
    video = shot.get("video")
    if video and Path(video).is_file():
        clip = VideoFileClip(str(video)).without_audio()
        clip = fit_cover(clip, size).with_duration(dur)
    else:
        img = shot.get("image")
        if not img or not Path(img).is_file():
            clip = ColorClip(size=size, color=(0, 0, 0), duration=dur)
        else:
            clip = fit_cover(ImageClip(str(img)), size).with_duration(dur)
    return clip


def fmt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", default="1", help="chapter directory name")
    parser.add_argument("--narr-pause", type=float, default=2.2, help="gap after narration shots in seconds")
    parser.add_argument("--dial-pause", type=float, default=0.8, help="gap after dialogue shots in seconds")
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()

    chapter = args.chapter
    shots = json.loads((BASE / chapter / "shots.json").read_text(encoding="utf-8"))
    audio_dir = BASE / chapter / "audio"
    output = BASE / chapter / f"chpt{chapter}_ai.mp4"

    clips = []
    t = 0.0
    for i, shot in enumerate(shots, start=1):
        mp3 = audio_dir / f"shot_{i:02d}.mp3"
        if not mp3.is_file():
            continue
        d = audio_duration(mp3)
        pause = args.narr_pause if shot.get("speaker") == "旁白" else args.dial_pause
        clip_dur = d + pause

        visual = make_visual(shot, clip_dur)
        audio = AudioFileClip(str(mp3))
        clip = visual.with_audio(audio)

        clips.append(clip)
        t += clip_dur
        print(f"[{i}/{len(shots)}] {shot['scene']} {shot['speaker']} dur={d:.1f}s total={t:.1f}s", flush=True)

    print(f"total timeline before render: {t:.1f}s ({t/60:.2f} min)")

    final = concatenate_videoclips(clips, method="chain")
    final.write_videofile(
        str(output),
        fps=args.fps,
        codec="libx264",
        audio_codec="aac",
    )
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
