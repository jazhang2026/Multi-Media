#!/usr/bin/env python3
"""Replace the text of a Whisper-generated SRT with the original TTS script,
resegmenting the source text so that each subtitle's length is proportional
 to its Whisper duration.

Usage (from 归真/):
    source .venv/bin/activate
    python3 correct_srt.py 15/chpt.srt 15/tts.txt 15/chpt_corrected.srt
"""

import re
import shutil
import sys

PUNCT = set('''，。？！、；：—–… ''')


def time_to_sec(t):
    h, m, s = t.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_srt(path):
    segments = []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == "":
            i += 1
            continue
        idx = lines[i].strip()
        i += 1
        if i >= len(lines):
            break
        time_line = lines[i].strip()
        i += 1
        text_lines = []
        while i < len(lines) and lines[i].strip() != "":
            text_lines.append(lines[i].strip())
            i += 1
        i += 1
        text = "\n".join(text_lines)
        start_str, _, end_str = time_line.split()
        start = time_to_sec(start_str)
        end = time_to_sec(end_str)
        duration = end - start
        segments.append({
            "id": idx,
            "start_str": start_str,
            "end_str": end_str,
            "time": time_line,
            "text": text,
            "start": start,
            "end": end,
            "duration": duration,
        })
    return segments


def write_srt(segments, path):
    with open(path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"{seg['id']}\n")
            f.write(f"{seg['time']}\n")
            f.write(f"{seg['text']}\n\n")


def build_source_text(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    # Concatenate non-empty lines; strip quotation marks (ASCII + Chinese) because
    # Whisper subtitles don't render spoken quotation marks.
    return "".join(line.strip() for line in lines if line.strip()).replace('"', '').replace('“', '').replace('”', '').replace('‘', '').replace('’', '')


def nearest_punct_boundary(source, pos, max_offset=25):
    """Find the next punctuation boundary at or after pos.
    Returns pos if none found within max_offset.
    Only looks forward so that boundaries never get stuck at the previous cut."""
    L = len(source)
    if pos <= 0:
        return 0
    if pos >= L:
        return L
    for d in range(0, max_offset + 1):
        if pos + d < L and source[pos + d] in PUNCT:
            # include the punctuation character in the previous chunk
            return pos + d + 1
    return pos


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 correct_srt.py <srt> <tts.txt> <output.srt>")
        sys.exit(1)
    srt_path, tts_path, out_path = sys.argv[1:]

    segments = parse_srt(srt_path)
    source = build_source_text(tts_path)
    if not source:
        print("Empty source text.")
        sys.exit(1)

    total_duration = sum(seg["duration"] for seg in segments)
    if total_duration <= 0:
        print("Zero total duration.")
        sys.exit(1)

    # Compute proportional boundaries, then snap to nearest punctuation.
    boundaries = []
    prev = 0
    cumulative = 0.0
    for seg in segments:
        cumulative += seg["duration"]
        raw_pos = int(round(len(source) * cumulative / total_duration))
        raw_pos = max(raw_pos, prev)
        snapped = nearest_punct_boundary(source, raw_pos)
        snapped = max(snapped, prev)
        boundaries.append(snapped)
        prev = snapped

    # Ensure final boundary covers source end.
    if boundaries:
        boundaries[-1] = len(source)

    corrected = []
    start = 0
    for seg, end in zip(segments, boundaries):
        chunk = source[start:end]
        # Avoid empty chunks (can happen at very short initial/ending segments)
        if not chunk:
            chunk = seg["text"]
        corrected.append({
            "id": seg["id"],
            "time": seg["time"],
            "text": chunk,
        })
        start = end

    shutil.copy2(srt_path, srt_path + ".bak")
    write_srt(corrected, out_path)
    print(f"Resynced {len(corrected)} segments -> {out_path}")
    print(f"Original backup: {srt_path}.bak")


if __name__ == "__main__":
    main()
