import argparse
import json
import os
import sys

from moviepy import AudioFileClip, ImageClip, concatenate_videoclips


SAMPLE_COMMAND = "source .venv/bin/activate && python3 make_video.py 13/video_config.json"


def main():
    parser = argparse.ArgumentParser(description="Make a story video from an audio file and a list of images.")
    parser.add_argument("config", help="Path to the JSON config file")
    args = parser.parse_args()

    if not args.config:
        print("Error: missing config file argument", file=sys.stderr)
        print(f"Example: {SAMPLE_COMMAND}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(args.config):
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        print(f"Example: {SAMPLE_COMMAND}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"Error: failed to parse JSON config file: {exc}", file=sys.stderr)
        print(f"Example: {SAMPLE_COMMAND}", file=sys.stderr)
        sys.exit(1)

    # Required fields
    if "audio" not in config:
        print("Error: config is missing required 'audio' field", file=sys.stderr)
        sys.exit(1)
    if "images" not in config:
        print("Error: config is missing required 'images' field", file=sys.stderr)
        sys.exit(1)
    if "output" not in config:
        print("Error: config is missing required 'output' field", file=sys.stderr)
        sys.exit(1)

    audio_path = config["audio"]
    image_files = config["images"]
    output = config["output"]
    size = config.get("size", [1920, 1080])
    fps = config.get("fps", 24)
    durations = config.get("durations", None)

    if not image_files:
        print("Error: 'images' list is empty", file=sys.stderr)
        sys.exit(1)

    audio = AudioFileClip(audio_path)

    if durations is None:
        # Split audio evenly across all images
        per_image = audio.duration / len(image_files)
        durations = [per_image] * len(image_files)
    elif isinstance(durations, (int, float)):
        # Same duration for every image
        durations = [durations] * len(image_files)

    if len(durations) != len(image_files):
        print(
            f"Error: number of durations ({len(durations)}) does not match number of images ({len(image_files)})",
            file=sys.stderr,
        )
        sys.exit(1)

    # Scale durations so the total image time matches the audio length
    total_image_time = sum(durations)
    if total_image_time > 0:
        scale = audio.duration / total_image_time
        durations = [d * scale for d in durations]

    clips = []
    for img, dur in zip(image_files, durations):
        clip = ImageClip(img).with_duration(dur)
        if size:
            clip = clip.resized(new_size=tuple(size))
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    video = video.with_audio(audio)

    video.write_videofile(
        output,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
    )


if __name__ == "__main__":
    main()
