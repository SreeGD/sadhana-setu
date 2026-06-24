#!/usr/bin/env python3
"""Draft translations into per-locale catalogs via Claude Code headless (spec 004, FR-011).

Writes machine drafts to ``*.draft.yaml`` (which the app NEVER shows). A native-devotee reviewer
edits the draft, then promotes approved entries into the live catalog (UI: copy keys into
`<locale>.yaml`; content: copy items with `reviewed: true`). This enforces the review gate
(Constitution V) — nothing translated is published without devotee approval.

    python scripts/draft_translations.py --locale te --kind ui
    python scripts/draft_translations.py --locale te --kind content --library affirmations

Requires the `claude` CLI on PATH.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
I18N = REPO / "data" / "i18n"
DATA = REPO / "data"
_LANG = {"te": "Telugu", "kn": "Kannada", "ta": "Tamil"}
# Which field(s) carry the translatable prose per daily library (FR-009 scope).
_CONTENT_FIELDS = {
    "affirmations": ["text"], "faith_verses": ["summary"],
    "nama_tattva": ["title", "teaching"], "contemplations": ["prompt"],
}


def _translate_batch(strings: list[str], language: str) -> list[str]:
    """Translate a list of English strings into `language` via `claude -p` (JSON in/out)."""
    prompt = (
        f"Translate each of these English strings into {language} for a Gauḍīya Vaiṣṇava (ISKCON) "
        "devotional app. Keep Sanskrit terms/verses as-is (they are transliterated separately). "
        "Return ONLY a JSON array of the translations, in the same order, no prose:\n"
        + json.dumps(strings, ensure_ascii=False)
    )
    proc = subprocess.run(["claude", "-p", "--output-format", "json"], input=prompt,
                          capture_output=True, text=True, check=True)
    out = proc.stdout
    try:
        env = json.loads(out)
        out = env.get("result", out) if isinstance(env, dict) else out
    except json.JSONDecodeError:
        pass
    out = out.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(out)


def draft_ui(locale: str) -> Path:
    en = yaml.safe_load((I18N / "ui" / "en.yaml").read_text(encoding="utf-8")) or {}
    keys, vals = list(en), list(en.values())
    translated = _translate_batch(vals, _LANG[locale])
    out = I18N / "ui" / f"{locale}.draft.yaml"
    out.write_text(yaml.safe_dump(dict(zip(keys, translated)), allow_unicode=True), encoding="utf-8")
    return out


def draft_content(locale: str, library: str) -> Path:
    items = yaml.safe_load((DATA / f"{library}.yaml").read_text(encoding="utf-8")).get(library, [])
    fields = _CONTENT_FIELDS[library]
    flat = [it.get(f, "") for it in items for f in fields]
    translated = _translate_batch(flat, _LANG[locale])
    rows, k = [], 0
    for idx, _ in enumerate(items):
        row = {"id": idx, "reviewed": False}
        for f in fields:
            row[f] = translated[k]; k += 1
        rows.append(row)
    out = I18N / "content" / locale / f"{library}.draft.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(rows, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Draft translations via Claude Code (review required).")
    p.add_argument("--locale", required=True, choices=list(_LANG))
    p.add_argument("--kind", required=True, choices=["ui", "content"])
    p.add_argument("--library", choices=list(_CONTENT_FIELDS))
    a = p.parse_args(argv)
    if a.kind == "ui":
        print("drafted:", draft_ui(a.locale))
    else:
        if not a.library:
            print("--library required for --kind content", file=sys.stderr); return 2
        print("drafted:", draft_content(a.locale, a.library))
    print("Review the .draft.yaml, then promote approved entries (reviewed: true) to the live catalog.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
