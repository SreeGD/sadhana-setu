"""Review gate (US4, FR-007/008).

Approval is the only path from ``draft`` to ``reviewed``. Approving records reviewer + date and
(via the caller, e.g. the Streamlit UI) triggers back-ingest. Only ``reviewed`` notes are
publish/ingest-eligible (Constitution Principle V).
"""
from __future__ import annotations

from pathlib import Path

from sadhana_setu.corpus import notes as notes_mod
from sadhana_setu.corpus.notes import NoteError, NoteFrontMatter, NoteStatus, parse


class ReviewError(RuntimeError):
    pass


def list_drafts(notes_dir: Path) -> list[Path]:
    """All draft note files under ``notes_dir``."""
    out: list[Path] = []
    for path in sorted(notes_dir.rglob("*.md")):
        try:
            fm = notes_mod.read_front_matter(path)
        except NoteError:
            continue
        if fm.status is NoteStatus.DRAFT:
            out.append(path)
    return out


def approve(path: Path, reviewer: str, *, when: str | None = None) -> NoteFrontMatter:
    """Flip a draft note to ``reviewed``, stamping reviewer + date. Returns the new front-matter."""
    if not reviewer:
        raise ReviewError("reviewer required to approve")
    text = path.read_text(encoding="utf-8")
    fm_dict, body = parse(text)
    fm = NoteFrontMatter.from_dict(fm_dict)
    if fm.status is NoteStatus.REVIEWED:
        return fm  # idempotent
    fm.status = NoteStatus.REVIEWED
    fm.reviewer = reviewer
    fm.reviewed_at = when or notes_mod.now_iso()
    fm.validate()
    _rewrite_front_matter(path, fm, body)
    return fm


def is_publishable(fm: NoteFrontMatter) -> bool:
    """Only reviewed notes may be published/back-ingested (SC-003)."""
    return fm.status is NoteStatus.REVIEWED


def _rewrite_front_matter(path: Path, fm: NoteFrontMatter, body: str) -> None:
    import yaml

    header = yaml.safe_dump(fm.to_dict(), sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{header}\n---\n\n{body.lstrip(chr(10))}", encoding="utf-8")
