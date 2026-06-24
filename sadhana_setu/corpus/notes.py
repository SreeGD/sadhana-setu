"""Class-note data model, front-matter, rendering, and review state machine (spec 002).

A note is a Markdown file: YAML front-matter (per ``contracts/note-frontmatter.schema.json``)
followed by the rendered body. Notes are one-per-transcript (FR-013).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import yaml

from sadhana_setu.corpus.config import CorpusConfig

REQUIRED_FM = (
    "lecture_id", "set_id", "transcript_path", "sha256", "speaker", "title",
    "status", "enrichment_engine", "enrichment_version", "enriched_at",
)


class NoteStatus(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"


class NoteError(ValueError):
    pass


@dataclass
class Citation:
    """A grounded reference (verse or cross-ref). Text fields come from kg-mcp, not the LLM."""
    kind: str  # "verse" | "cross_ref"
    candidate: str
    source: str = ""
    verse_ref: str | None = None
    iast: str | None = None
    translation: str | None = None
    verified: bool = False


@dataclass
class KeyTeaching:
    point: str
    timestamp: str
    citations: list[Citation] = field(default_factory=list)


@dataclass
class NoteContent:
    """The enriched, grounded body of a note."""
    theme_summary: str
    key_teachings: list[KeyTeaching]
    practical_application: str
    glossary: list[tuple[str, str]] = field(default_factory=list)
    cross_references: list[Citation] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    sic_flags: list[dict] = field(default_factory=list)


@dataclass
class NoteFrontMatter:
    lecture_id: str
    set_id: str
    transcript_path: str
    sha256: str
    speaker: str
    title: str
    enrichment_version: str
    enriched_at: str
    status: NoteStatus = NoteStatus.DRAFT
    enrichment_engine: str = "claude-code"
    reviewer: str | None = None
    reviewed_at: str | None = None
    ingested_at: str | None = None

    def validate(self) -> None:
        for f in REQUIRED_FM:
            if getattr(self, f, None) in (None, ""):
                raise NoteError(f"note front-matter missing: {f}")
        if self.status is NoteStatus.REVIEWED and not (self.reviewer and self.reviewed_at):
            raise NoteError("reviewed note requires reviewer + reviewed_at")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_dict(cls, d: dict) -> "NoteFrontMatter":
        d = dict(d)
        d["status"] = NoteStatus(d.get("status", "draft"))
        return cls(**d)


# -- rendering ------------------------------------------------------------

def render_body(content: NoteContent) -> str:
    lines: list[str] = []
    lines.append("## Theme\n")
    lines.append(content.theme_summary.strip() + "\n")

    lines.append("## Key teachings\n")
    for kt in content.key_teachings:
        lines.append(f"- **[{kt.timestamp}]** {kt.point.strip()}")
        for c in kt.citations:
            if c.verified:
                lines.append(f"    - {c.source}: *{c.iast}* — {c.translation}")
    lines.append("")

    verses = [c for kt in content.key_teachings for c in kt.citations if c.verified]
    if verses:
        lines.append("## Verses cited\n")
        for c in verses:
            lines.append(f"- **{c.source}** — *{c.iast}*\n  {c.translation}")
        lines.append("")

    if content.cross_references:
        lines.append("## Cross-references\n")
        for c in content.cross_references:
            if c.verified:
                lines.append(f"- {c.source}: {c.translation or c.candidate}")
        lines.append("")

    lines.append("## Practical application\n")
    lines.append(content.practical_application.strip() + "\n")

    if content.glossary:
        lines.append("## Glossary\n")
        for term, gloss in content.glossary:
            lines.append(f"- **{term}** — {gloss}")
        lines.append("")

    if content.unverified or content.sic_flags:
        lines.append("## Review notes (not published)\n")
        for u in content.unverified:
            lines.append(f"- `[UNVERIFIED]` {u}")
        for s in content.sic_flags:
            lines.append(
                f"- `[sic?: heard '{s.get('heard')}' → '{s.get('suspected')}' "
                f"@ {s.get('timestamp')}]`"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def verified_body(content: NoteContent) -> str:
    """The body MINUS the review-notes section — what gets back-ingested (FR-011)."""
    stripped = NoteContent(
        theme_summary=content.theme_summary,
        key_teachings=content.key_teachings,
        practical_application=content.practical_application,
        glossary=content.glossary,
        cross_references=content.cross_references,
        unverified=[],
        sic_flags=[],
    )
    return render_body(stripped)


def render(fm: NoteFrontMatter, content: NoteContent) -> str:
    fm.validate()
    header = yaml.safe_dump(fm.to_dict(), sort_keys=False, allow_unicode=True).strip()
    return f"---\n{header}\n---\n\n# {fm.title}\n\n{render_body(content)}"


def parse(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise NoteError("note missing front-matter")
    _, fm_block, body = text.split("---", 2)
    return yaml.safe_load(fm_block) or {}, body.lstrip("\n")


def note_path(cfg: CorpusConfig, set_id: str, lecture_id: str) -> Path:
    return cfg.notes_dir / set_id / f"{lecture_id}.md"


def write(path: Path, fm: NoteFrontMatter, content: NoteContent) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(fm, content), encoding="utf-8")


def read_front_matter(path: Path) -> NoteFrontMatter:
    fm, _ = parse(path.read_text(encoding="utf-8"))
    return NoteFrontMatter.from_dict(fm)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
