"""Read reviewed enriched notes from disk for the study/Notes view (spec 003, US4).

No ChromaDB — just the committed `corpus/notes/<set>/<id>.md` files. Only notes whose front-matter
``status`` is ``reviewed`` are listed (Constitution Principle V); drafts never appear.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_NOTES_DIR = Path(os.environ.get("CORPUS_NOTES_DIR", _REPO_ROOT / "corpus" / "notes"))


@dataclass(frozen=True)
class NoteRef:
    set_id: str
    lecture_id: str
    speaker: str
    title: str
    path: Path


def list_reviewed_notes(notes_dir: Path | None = None) -> list[NoteRef]:
    """All reviewed notes, sorted by speaker then title (drafts excluded)."""
    base = Path(notes_dir) if notes_dir else _NOTES_DIR
    out: list[NoteRef] = []
    if not base.exists():
        return out
    for path in sorted(base.rglob("*.md")):
        fm, _ = read_note(path)
        if not fm or fm.get("status") != "reviewed":
            continue
        out.append(NoteRef(
            set_id=fm.get("set_id", path.parent.name),
            lecture_id=fm.get("lecture_id", path.stem),
            speaker=fm.get("speaker", path.parent.name),
            title=fm.get("title", path.stem),
            path=path,
        ))
    out.sort(key=lambda n: (n.speaker, n.title))
    return out


def read_note(path: Path) -> tuple[dict, str]:
    """Return (front-matter dict, body markdown). ({}, "") if the file lacks front-matter."""
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    _, fm_block, body = text.split("---", 2)
    return (yaml.safe_load(fm_block) or {}), body.lstrip("\n")
