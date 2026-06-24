"""Surface one reviewed Hari-Nāma teaching from the corpus (spec 005, FR-003).

Two-step, to keep the displayed text clean:

1. **Find** the relevant reviewed note — query vidya-karana's *live* ChromaDB, filtered to
   metadata ``kind == "harinaam-note"`` (reviewed `002` notes only, Constitution V), ranked by the
   day's theme. This bypasses kg-mcp's static snapshot (verified 2026-06-24).
2. **Display** a clean teaching — read the note file on disk and pick a key teaching, rather than
   showing the ChromaDB chunk text (vidya-karana's ingest mangles plain text to IAST, e.g.
   ``ḥaṛ-ṇāma``). Falls back to the chunk text only if the note file is unavailable.

Cross-venv: chromadb + the embedder live in vidya-karana's venv, so the default querier bridges to
it via a subprocess. Any failure returns None ⇒ the caller falls back to curated content (FR-008).
The querier is injectable for tests.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from sadhana_setu.flows.prejapa_reading import ReadingStage

_HARINAAM_KIND = "harinaam-note"
_VK_ROOT = os.environ.get("VIDYA_KARANA_ROOT", "/Users/sree/Projects/vidya-karana")
_VK_PY = os.environ.get("VIDYA_KARANA_PYTHON", os.path.join(_VK_ROOT, ".venv", "bin", "python"))
_QUERY_TIMEOUT = float(os.environ.get("HARINAAM_QUERY_TIMEOUT", "20"))
_REPO_ROOT = Path(__file__).resolve().parents[2]
_NOTES_DIR = Path(os.environ.get("CORPUS_NOTES_DIR", _REPO_ROOT / "corpus" / "notes"))
_TEACHING_RE = re.compile(r"^- \*\*\[[^\]]+\]\*\*\s*(.+)$", re.MULTILINE)


def fetch_teaching(theme: str, *, querier=None) -> ReadingStage | None:
    """Return one reviewed Hari-Nāma teaching for ``theme``, or None (never raises)."""
    q = querier or _chromadb_querier
    try:
        chunks = q(theme) or []
    except Exception:  # noqa: BLE001 — bridge/query failure ⇒ curated fallback
        return None
    for c in chunks:
        if not isinstance(c, dict) or _kind(c) != _HARINAAM_KIND:
            continue
        # Prefer a clean teaching from the note file; fall back to the (possibly mangled) chunk.
        body = _clean_teaching(_meta(c, "set_id"), _meta(c, "lecture_id"), theme) \
            or (c.get("text") or "").strip()
        if body:
            return ReadingStage(label="A teaching on the Holy Name", body=body,
                                citation=_citation(c), source_kind="corpus")
    return None


def _clean_teaching(set_id: str | None, lecture_id: str | None, theme: str) -> str | None:
    """Pick a clean key teaching from the on-disk note (date/theme-stable selection)."""
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


def _chromadb_querier(theme: str) -> list[dict]:
    """Bridge to vidya-karana's venv: kind-filtered vector query over the live ChromaDB."""
    script = (
        "import sys,json;sys.path.insert(0,'.');"
        "from systems.chromadb_manager import ChromaDBManager;"
        "from vidya_karana.config import load_settings;"
        "db=ChromaDBManager(load_settings().chromadb_path);"
        "r=db.collection.query(query_texts=[sys.argv[1]],n_results=3,"
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
