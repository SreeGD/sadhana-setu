"""Build static/ from the YAML content libraries.

Run once after editing any data/*.yaml. Output is static/content/*.json,
ready to be fetched by the browser. ekadasi.json is copied as-is.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
SRC = ROOT / "data"
DEST = ROOT / "static" / "content"

# Map: yaml file stem -> (key in the YAML to extract, key in the output JSON).
LIBRARIES = {
    "affirmations": ("affirmations", "items"),
    "faith_verses": ("faith_verses", "items"),
    "inspirations": ("inspirations", "items"),
    "tips": ("tips", "items"),
    "nama_tattva": ("nama_tattva", "items"),
    "bhajans": ("bhajans", "items"),
    "book_tips": ("book_tips", "items"),
    "weekly_readings": ("readings", "items"),
    "weekly_stories": ("stories", "items"),
    "japa_methods": ("methods", "items"),
    "weekly_questions": ("questions", "items"),
}


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)

    for stem, (yaml_key, out_key) in LIBRARIES.items():
        src = SRC / f"{stem}.yaml"
        if not src.exists():
            print(f"  ! missing {src}")
            continue
        doc = yaml.safe_load(src.read_text())
        items = doc.get(yaml_key)
        if items is None:
            print(f"  ! key '{yaml_key}' not in {src.name}")
            continue
        out = DEST / f"{stem}.json"
        out.write_text(json.dumps({out_key: items}, ensure_ascii=False, indent=2))
        print(f"  {src.name:<28} -> {out.relative_to(ROOT)} ({len(items)} entries)")

    # Ekadasi is already JSON; copy as-is.
    src_ek = SRC / "ekadasi.json"
    if src_ek.exists():
        shutil.copyfile(src_ek, DEST / "ekadasi.json")
        print(f"  ekadasi.json (copied through)")


if __name__ == "__main__":
    main()
