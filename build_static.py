"""Build static/ from the YAML content libraries.

Run once after editing any data/*.yaml. Output is static/content/*.json,
ready to be fetched by the browser. ekadasi.json is copied as-is.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
SRC = ROOT / "data"
DEST = ROOT / "static" / "content"
STATIC = ROOT / "static"

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
    "daily_verses": ("daily_verses", "items"),
    "weekly_verses": ("weekly_verses", "items"),
    "weekly_lectures": ("weekly_lectures", "items"),
    "sankalpas": ("sankalpas", "items"),
}

# Files where we just pass the entire YAML through (no rotation; the
# JS layer reads named keys directly).
PASSTHROUGH = {
    "weekly_form_options",
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

    # Passthrough libraries (no rotation logic; JS picks fields directly).
    for stem in PASSTHROUGH:
        src = SRC / f"{stem}.yaml"
        if not src.exists():
            print(f"  ! missing {src}")
            continue
        doc = yaml.safe_load(src.read_text())
        out = DEST / f"{stem}.json"
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
        print(f"  {src.name:<28} -> {out.relative_to(ROOT)} (passthrough)")

    # Ekadasi is already JSON; copy as-is.
    src_ek = SRC / "ekadasi.json"
    if src_ek.exists():
        shutil.copyfile(src_ek, DEST / "ekadasi.json")
        print(f"  ekadasi.json (copied through)")

    build_service_worker()


def cache_version() -> str:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if sha:
            return sha
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return str(int(time.time()))


def precache_list() -> list[str]:
    """Same-origin URLs to precache on SW install. Paths are relative to the
    served root (which on GitHub Pages is /sadhana-setu/static/... → we
    register the SW from /sadhana-setu/ so root-relative './' paths work)."""
    urls: list[str] = ["./", "./index.html", "./manifest.webmanifest"]
    for sub in ("css", "js", "content", "icons"):
        base = STATIC / sub
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and not p.name.startswith("."):
                rel = p.relative_to(STATIC).as_posix()
                urls.append(f"./{rel}")
    return urls


def build_service_worker() -> None:
    tmpl = STATIC / "sw.js.template"
    if not tmpl.exists():
        print("  ! sw.js.template missing — skipping SW build")
        return
    version = cache_version()
    urls = precache_list()
    out = tmpl.read_text()
    out = out.replace("__CACHE_VERSION__", version)
    out = out.replace("__PRECACHE_LIST__", json.dumps(urls, indent=2))
    (STATIC / "sw.js").write_text(out)
    print(f"  sw.js.template               -> static/sw.js (cache={version}, {len(urls)} urls)")


if __name__ == "__main__":
    main()
