"""Surface one reviewed Hari-Nāma teaching from the corpus (spec 005, FR-003).

Queries vidya-karana's **live ChromaDB** directly, filtered to metadata ``kind == "harinaam-note"``
— i.e. reviewed `002` notes only (Constitution V) — ranked by the day's theme. This bypasses
kg-mcp, which serves a *static snapshot* that won't contain freshly-ingested notes (verified
2026-06-24; see `specs/002-note-enrichment/contracts/ingest.md`).

Cross-venv: chromadb + the embedder live in vidya-karana's venv, so the default querier bridges to
it via a subprocess. Any failure (venv missing, timeout, no match) returns None so the caller
falls back to curated content (FR-008). The querier is injectable for tests.
"""
from __future__ import annotations

import json
import os
import subprocess

from sadhana_setu.flows.prejapa_reading import ReadingStage

_HARINAAM_KIND = "harinaam-note"
_VK_ROOT = os.environ.get("VIDYA_KARANA_ROOT", "/Users/sree/Projects/vidya-karana")
_VK_PY = os.environ.get("VIDYA_KARANA_PYTHON", os.path.join(_VK_ROOT, ".venv", "bin", "python"))
_QUERY_TIMEOUT = float(os.environ.get("HARINAAM_QUERY_TIMEOUT", "20"))


def fetch_teaching(theme: str, *, querier=None) -> ReadingStage | None:
    """Return one reviewed Hari-Nāma teaching for ``theme``, or None (never raises).

    ``querier(theme) -> list[dict]`` returns candidate chunks (each ``{text, kind, speaker,
    title}``); only ``kind == "harinaam-note"`` chunks are accepted (the review gate).
    """
    q = querier or _chromadb_querier
    try:
        chunks = q(theme) or []
    except Exception:  # noqa: BLE001 — bridge/query failure ⇒ curated fallback
        return None
    for c in chunks:
        if not isinstance(c, dict) or _kind(c) != _HARINAAM_KIND:
            continue
        body = (c.get("text") or "").strip()
        if body:
            return ReadingStage(label="A teaching on the Holy Name", body=body,
                                citation=_citation(c), source_kind="corpus")
    return None


def _chromadb_querier(theme: str) -> list[dict]:
    """Bridge to vidya-karana's venv: kind-filtered vector query over the live ChromaDB."""
    script = (
        "import sys,json;sys.path.insert(0,'.');"
        "from systems.chromadb_manager import ChromaDBManager;"
        "from vidya_karana.config import load_settings;"
        "db=ChromaDBManager(load_settings().chromadb_path);"
        "r=db.collection.query(query_texts=[sys.argv[1]],n_results=3,"
        "where={'kind':'harinaam-note'});"
        "docs=(r.get('documents') or [[]])[0];metas=(r.get('metadatas') or [[]])[0];"
        "print('@@'+json.dumps([{'text':d,'kind':(m or {}).get('kind'),"
        "'speaker':(m or {}).get('speaker'),'title':(m or {}).get('title')} "
        "for d,m in zip(docs,metas)]))"
    )
    proc = subprocess.run([_VK_PY, "-c", script, theme], cwd=_VK_ROOT,
                          capture_output=True, text=True, timeout=_QUERY_TIMEOUT)
    if proc.returncode != 0:
        return []
    # Our payload is tagged with '@@' so vidya-karana's own stdout logging is ignored.
    for line in proc.stdout.splitlines():
        if line.startswith("@@"):
            return json.loads(line[2:])
    return []


def _kind(c: dict) -> str | None:
    return c.get("kind") or (c.get("metadata") or {}).get("kind")


def _citation(c: dict) -> str:
    speaker, title = c.get("speaker"), c.get("title")
    if speaker and title:
        return f"{speaker} — {title}"
    return speaker or title or "Hari-Nāma corpus"
