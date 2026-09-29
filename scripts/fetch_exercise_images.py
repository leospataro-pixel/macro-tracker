#!/usr/bin/env python3
"""Download and resize exercise / stretch photos into static/ex/.

Source: Free Exercise DB (public domain, https://github.com/yuhonas/free-exercise-db).
Run once after adding exercises:  pip install pillow && python scripts/fetch_exercise_images.py
"""
import io
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import exercises  # noqa: E402
import stretches  # noqa: E402

BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/"
OUT = ROOT / "static" / "ex"


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    db = {x["name"]: x for x in json.loads(fetch(BASE + "dist/exercises.json"))}
    wanted = {exercises.slugify(k): v for k, v in exercises.IMAGE_SOURCES.items()}
    wanted.update({s["slug"]: s["img"] for s in stretches.STRETCHES})
    for slug, source in sorted(wanted.items()):
        for i, path in enumerate(db[source]["images"][:2]):
            dest = OUT / f"{slug}_{i}.jpg"
            if dest.exists():
                continue
            img = Image.open(io.BytesIO(fetch(BASE + "exercises/" + urllib.parse.quote(path))))
            img = img.convert("RGB")
            img.thumbnail((480, 480))
            img.save(dest, "JPEG", quality=72, optimize=True, progressive=True)
            print("✓", dest.name)


if __name__ == "__main__":
    main()
