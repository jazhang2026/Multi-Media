#!/usr/bin/env python3
"""Fix image extensions in all chapter video_config.json files."""

import json
from pathlib import Path


def find_actual_image(path: Path) -> Path | None:
    """If path doesn't exist, try common image extensions."""
    if path.is_file():
        return path
    for ext in (".jpeg", ".jpg", ".png"):
        candidate = path.with_suffix(ext)
        if candidate.is_file():
            return candidate
    return None


def fix_config(config_path: Path) -> list[str]:
    """Return list of changes made."""
    changes = []
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    images = config.get("images", [])
    for i, img in enumerate(images):
        img_path = Path(img)
        if not img_path.is_file():
            actual = find_actual_image(img_path)
            if actual:
                images[i] = str(actual)
                changes.append(f"{img} -> {actual}")
            else:
                changes.append(f"MISSING: {img}")

    if changes:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            f.write("\n")

    return changes


def main():
    base = Path(__file__).resolve().parent
    all_changes = []
    for n in range(1, 41):
        config_path = base / str(n) / "video_config.json"
        if not config_path.is_file():
            print(f"{n}: no video_config.json")
            continue
        changes = fix_config(config_path)
        if changes:
            print(f"{n}: updated")
            for c in changes:
                print(f"  {c}")
            all_changes.extend((n, c) for c in changes)
        else:
            print(f"{n}: OK")

    total = len(all_changes)
    print(f"\nTotal changes: {total}")


if __name__ == "__main__":
    main()
