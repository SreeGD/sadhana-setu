"""Shared corpus-teaching retrieval (spec 003) — the single path for reviewed Hari-Nāma teachings.

Generalizes `005`'s pre-japa retrieval into a service any surface can call, with:
- **review gate** — only reviewed notes (live ChromaDB `kind=harinaam-note`, Constitution V);
- **per-day cache** — the ~2 s ChromaDB bridge runs at most once per theme per day (FR-012);
- **within-day stability** — a surface re-asks and gets the *same* teaching (SC-005);
- **cross-surface de-duplication** — different surfaces get different teachings the same day (FR-013);
- **clean text** — read from the note file on disk, not the mangled ChromaDB chunk (FR-003).

Streamlit-free and unit-testable: inject `querier` (theme → chunks) and a plain `state` dict. The
default querier bridges to vidya-karana's venv (chromadb + embedder live there); any failure ⇒
None so the caller falls back to curated content (FR-004).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_HARINAAM_KIND = "harinaam-note"
_VK_ROOT = os.environ.get("VIDYA_KARANA_ROOT", "/Users/sree/Projects/vidya-karana")
_VK_PY = os.environ.get("VIDYA_KARANA_PYTHON", os.path.join(_VK_ROOT, ".venv", "bin", "python"))
_QUERY_TIMEOUT = float(os.environ.get("HARINAAM_QUERY_TIMEOUT", "20"))
_REPO_ROOT = Path(__file__).resolve().parents[2]
_NOTES_DIR = Path(os.environ.get("CORPUS_NOTES_DIR", _REPO_ROOT / "corpus" / "notes"))
_TEACHING_RE = re.compile(r"^- \*\*\[[^\]]+\]\*\*\s*(.+)$", re.MULTILINE)


@dataclass
class Teaching:
    body: str
    citation: str
    lecture_id: str
    set_id: str
    source_kind: str = "corpus"


def new_state() -> dict:
    """Fresh per-day state: theme→candidates cache, surfaced lecture-ids, per-surface results."""
    return {"theme_cache": {}, "surfaced": set(), "resolved": {}}


def get_for_surface(theme: str, surface_id: str, *, date=None, state: dict | None = None,
                    querier=None) -> Teaching | None:
    """Return one reviewed, clean, cited teaching for ``surface_id`` (or None → curated)."""
    state = new_state() if state is None else state
    resolved = state["resolved"]
    if surface_id in resolved:  # within-day stability (SC-005)
        return resolved[surface_id]

    chosen: Teaching | None = None
    for c in _candidates(theme, state, querier):
        if _kind(c) != _HARINAAM_KIND:  # review gate (Constitution V)
            continue
        lid = _meta(c, "lecture_id")
        if lid and lid in state["surfaced"]:  # dedup only when we have an id (FR-013)
            continue
        body = clean_teaching_text(_meta(c, "set_id"), lid, theme) or (c.get("text") or "").strip()
        if not body:
            continue
        if lid:
            state["surfaced"].add(lid)
        chosen = Teaching(body=body, citation=_citation(c), lecture_id=lid or "",
                          set_id=_meta(c, "set_id") or "")
        break
    resolved[surface_id] = chosen
    return chosen


def _candidates(theme: str, state: dict, querier) -> list[dict]:
    cache = state["theme_cache"]
    if theme not in cache:  # per-(date,theme) cache; bridge runs once per theme/day (FR-012)
        q = querier or chromadb_querier
        try:
            cache[theme] = q(theme) or []
        except Exception:  # noqa: BLE001 — corpus offline ⇒ empty ⇒ curated fallback
            cache[theme] = []
    return cache[theme]


# -- clean text from the note file (sidesteps vidya-karana ingest mangling, FR-003) --

def clean_teaching_text(set_id: str | None, lecture_id: str | None, theme: str) -> str | None:
    if not (set_id and lecture_id):
        return None
    path = _NOTES_DIR / set_id / f"{lecture_id}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    section = re.search(r"## Key teachings\n(.*?)(?:\n## |\Z)", text, re.S)
    if not section:
        return None
    teachings = [t.strip() for t in _TEACHING_RE.findall(section.group(1)) if t.strip()]
    if not teachings:
        return None
    idx = (sum(map(ord, theme)) if theme else 0) % len(teachings)  # stable within a day
    return teachings[idx]


# -- live ChromaDB bridge (reviewed harinaam-note only) --

def chromadb_querier(theme: str) -> list[dict]:
    """Bridge to vidya-karana's venv: kind-filtered vector query over the live ChromaDB."""
    script = (
        "import sys,json;sys.path.insert(0,'.');"
        "from systems.chromadb_manager import ChromaDBManager;"
        "from vidya_karana.config import load_settings;"
        "db=ChromaDBManager(load_settings().chromadb_path);"
        "r=db.collection.query(query_texts=[sys.argv[1]],n_results=5,"
        "where={'kind':'harinaam-note'});"
        "metas=(r.get('metadatas') or [[]])[0];docs=(r.get('documents') or [[]])[0];"
        "print('@@'+json.dumps([{'text':d,'kind':(m or {}).get('kind'),"
        "'speaker':(m or {}).get('speaker'),'title':(m or {}).get('title'),"
        "'set_id':(m or {}).get('set_id'),'lecture_id':(m or {}).get('lecture_id')} "
        "for d,m in zip(docs,metas)]))"
    )
    proc = subprocess.run([_VK_PY, "-c", script, theme], cwd=_VK_ROOT,
                          capture_output=True, text=True, timeout=_QUERY_TIMEOUT)
    if proc.returncode != 0:
        return []
    for line in proc.stdout.splitlines():
        if line.startswith("@@"):
            return json.loads(line[2:])
    return []


def _kind(c: dict) -> str | None:
    return _meta(c, "kind")


def _meta(c: dict, key: str):
    return c.get(key) or (c.get("metadata") or {}).get(key)


def _citation(c: dict) -> str:
    speaker, title = _meta(c, "speaker"), _meta(c, "title")
    if speaker and title:
        return f"{speaker} — {title}"
    return speaker or title or "Hari-Nāma corpus"
