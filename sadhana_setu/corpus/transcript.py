"""Transcript files: provenance front-matter + segment-timestamped body.

Mirrors ``contracts/transcript-frontmatter.schema.json``. A transcript is a Markdown
file: a YAML front-matter block delimited by ``---`` followed by the verbatim,
segment-timestamped body (Constitution I; FR-005).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

REQUIRED_FIELDS = (
    "lecture_id", "set_id", "speaker", "title", "source_urls", "sha256",
    "duration_seconds", "language", "whisper_model", "whisper_flags",
    "timestamp_granularity", "transcribed_at", "pipeline_version",
)


@dataclass
class Segment:
    start: float  # seconds
    end: float
    text: str

    def format(self) -> str:
        return f"[{_hms(self.start)} → {_hms(self.end)}] {self.text.strip()}"


@dataclass
class TranscriptFrontMatter:
    lecture_id: str
    set_id: str
    speaker: str
    title: str
    source_urls: list[str]
    sha256: str
    duration_seconds: int
    whisper_model: str
    whisper_flags: str
    pipeline_version: str
    transcribed_at: str
    date: str | None = None
    language: str = "en"
    timestamp_granularity: str = "segment"

    def validate(self) -> None:
        missing = [f for f in REQUIRED_FIELDS if getattr(self, f, None) in (None, "")]
        if missing:
            raise ValueError(f"transcript front-matter missing: {', '.join(missing)}")
        if self.language != "en":
            raise ValueError("committed Round 1 transcripts must be English")
        if self.timestamp_granularity != "segment":
            raise ValueError("timestamp_granularity must be 'segment'")

    def to_dict(self) -> dict:
        d = {k: v for k, v in asdict(self).items() if v is not None}
        return d


def render(fm: TranscriptFrontMatter, segments: list[Segment]) -> str:
    """Render a transcript Markdown document (front-matter + body)."""
    fm.validate()
    header = yaml.safe_dump(fm.to_dict(), sort_keys=False, allow_unicode=True).strip()
    body = "\n".join(seg.format() for seg in segments)
    return f"---\n{header}\n---\n\n{body}\n"


def parse(text: str) -> tuple[dict, str]:
    """Split a transcript file into (front-matter dict, body)."""
    if not text.startswith("---"):
        raise ValueError("transcript missing front-matter")
    _, fm_block, body = text.split("---", 2)
    return yaml.safe_load(fm_block) or {}, body.lstrip("\n")


def write(path: Path, fm: TranscriptFrontMatter, segments: list[Segment]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(fm, segments), encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _hms(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
