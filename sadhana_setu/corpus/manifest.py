"""Source manifest: load, validate, mutate, and persist.

The manifest (``corpus/sources/manifest.yaml``) is the single source of truth for
which lectures belong to the corpus (FR-001). This module mirrors
``contracts/manifest.schema.json`` and ``data-model.md`` in pure Python (no extra
runtime dependency), enforcing the Lecture status state machine and provenance rules.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterator

import yaml

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class Status(str, Enum):
    PENDING = "pending"
    FETCHED = "fetched"
    TRANSCRIBED = "transcribed"
    DEFERRED = "deferred"
    UNAVAILABLE = "unavailable"
    EXCLUDED = "excluded"


# Allowed status transitions (data-model.md state machine). A status may always
# re-assert itself (idempotent no-op).
_TRANSITIONS: dict[Status, set[Status]] = {
    Status.PENDING: {Status.FETCHED, Status.DEFERRED, Status.UNAVAILABLE, Status.EXCLUDED},
    Status.FETCHED: {Status.TRANSCRIBED, Status.EXCLUDED, Status.UNAVAILABLE},
    Status.TRANSCRIBED: {Status.EXCLUDED},
    Status.DEFERRED: {Status.PENDING, Status.EXCLUDED},
    Status.UNAVAILABLE: {Status.PENDING, Status.EXCLUDED},
    Status.EXCLUDED: set(),
}


class ManifestError(ValueError):
    """The manifest violates its schema or an invariant."""


class ProvenanceError(RuntimeError):
    """A checksum mismatch broke the provenance chain (CLI exit code 1)."""


class StatusTransitionError(ManifestError):
    """An illegal Lecture status transition was attempted."""


@dataclass
class Lecture:
    id: str
    title: str
    urls: list[str]
    status: Status = Status.PENDING
    date: str | None = None
    sha256: str | None = None
    duration_seconds: int | None = None
    language: str = "en"
    topic_tags: list[str] = field(default_factory=list)
    transcript_path: str | None = None
    whisper_model: str | None = None
    notes: str = ""

    # -- validation -------------------------------------------------------
    def validate(self) -> None:
        if not _SLUG_RE.match(self.id):
            raise ManifestError(f"lecture id not kebab-case: {self.id!r}")
        if not self.title:
            raise ManifestError(f"lecture {self.id}: title required")
        if not self.urls:
            raise ManifestError(f"lecture {self.id}: at least one url required")
        if self.sha256 is not None and not _SHA256_RE.match(self.sha256):
            raise ManifestError(f"lecture {self.id}: sha256 not 64 hex chars")
        if self.status is Status.FETCHED and not self.sha256:
            raise ManifestError(f"lecture {self.id}: fetched requires sha256")
        if self.status is Status.TRANSCRIBED and not (
            self.sha256 and self.transcript_path and self.whisper_model
        ):
            raise ManifestError(
                f"lecture {self.id}: transcribed requires sha256, transcript_path, whisper_model"
            )
        if self.language != "en" and self.status not in (
            Status.DEFERRED,
            Status.EXCLUDED,
            Status.UNAVAILABLE,
        ):
            raise ManifestError(
                f"lecture {self.id}: non-English ({self.language}) must be deferred in Round 1"
            )

    # -- state machine ----------------------------------------------------
    def set_status(self, new: Status) -> None:
        if new == self.status:
            return
        if new not in _TRANSITIONS[self.status]:
            raise StatusTransitionError(
                f"lecture {self.id}: {self.status.value} → {new.value} not allowed"
            )
        self.status = new

    # -- serialization ----------------------------------------------------
    @classmethod
    def from_dict(cls, d: dict) -> "Lecture":
        return cls(
            id=d["id"],
            title=d["title"],
            urls=list(d["urls"]),
            status=Status(d.get("status", "pending")),
            date=d.get("date"),
            sha256=d.get("sha256"),
            duration_seconds=d.get("duration_seconds"),
            language=d.get("language", "en"),
            topic_tags=list(d.get("topic_tags", [])),
            transcript_path=d.get("transcript_path"),
            whisper_model=d.get("whisper_model"),
            notes=d.get("notes", ""),
        )

    def to_dict(self) -> dict:
        out: dict = {"id": self.id, "title": self.title, "urls": list(self.urls)}
        if self.date is not None:
            out["date"] = self.date
        out["status"] = self.status.value
        if self.sha256 is not None:
            out["sha256"] = self.sha256
        if self.duration_seconds is not None:
            out["duration_seconds"] = self.duration_seconds
        out["language"] = self.language
        if self.topic_tags:
            out["topic_tags"] = list(self.topic_tags)
        if self.transcript_path is not None:
            out["transcript_path"] = self.transcript_path
        if self.whisper_model is not None:
            out["whisper_model"] = self.whisper_model
        if self.notes:
            out["notes"] = self.notes
        return out


@dataclass
class SourceSet:
    id: str
    speaker: str
    kind: str  # "speaker" | "seminar"
    lectures: list[Lecture] = field(default_factory=list)

    def validate(self) -> None:
        if not _SLUG_RE.match(self.id):
            raise ManifestError(f"source set id not kebab-case: {self.id!r}")
        if self.kind not in ("speaker", "seminar"):
            raise ManifestError(f"source set {self.id}: kind must be speaker|seminar")
        for lec in self.lectures:
            lec.validate()

    @classmethod
    def from_dict(cls, d: dict) -> "SourceSet":
        return cls(
            id=d["id"],
            speaker=d["speaker"],
            kind=d["kind"],
            lectures=[Lecture.from_dict(x) for x in d.get("lectures", [])],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "speaker": self.speaker,
            "kind": self.kind,
            "lectures": [lec.to_dict() for lec in self.lectures],
        }


class Manifest:
    """In-memory manifest with load/validate/save and lecture lookups."""

    def __init__(self, source_sets: list[SourceSet], version: int = 0,
                 manifest_status: str = "active", path: Path | None = None):
        self.source_sets = source_sets
        self.version = version
        self.manifest_status = manifest_status
        self.path = path

    # -- io ---------------------------------------------------------------
    @classmethod
    def load(cls, path: Path | str) -> "Manifest":
        path = Path(path)
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        m = cls(
            source_sets=[SourceSet.from_dict(s) for s in data.get("source_sets", [])],
            version=int(data.get("version", 0)),
            manifest_status=data.get("manifest_status", "active"),
            path=path,
        )
        m.validate()
        return m

    def save(self, path: Path | str | None = None) -> None:
        target = Path(path) if path else self.path
        if target is None:
            raise ManifestError("no path to save manifest to")
        self.validate()
        doc = {
            "version": self.version,
            "manifest_status": self.manifest_status,
            "source_sets": [s.to_dict() for s in self.source_sets],
        }
        target.write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )

    # -- validation -------------------------------------------------------
    def validate(self) -> None:
        seen_ids: set[str] = set()
        for s in self.source_sets:
            s.validate()
            for lec in s.lectures:
                if lec.id in seen_ids:
                    raise ManifestError(f"duplicate lecture id across corpus: {lec.id}")
                seen_ids.add(lec.id)

    # -- lookups ----------------------------------------------------------
    def get_set(self, set_id: str) -> SourceSet:
        for s in self.source_sets:
            if s.id == set_id:
                return s
        raise KeyError(set_id)

    def iter_lectures(self, set_id: str | None = None) -> Iterator[tuple[SourceSet, Lecture]]:
        for s in self.source_sets:
            if set_id and s.id != set_id:
                continue
            for lec in s.lectures:
                yield s, lec

    def find_by_sha256(self, sha256: str, *, exclude_id: str | None = None) -> Lecture | None:
        for _, lec in self.iter_lectures():
            if lec.sha256 == sha256 and lec.id != exclude_id:
                return lec
        return None

    # -- dedup (FR-009) ---------------------------------------------------
    def dedupe_by_checksum(self) -> list[tuple[str, str]]:
        """Fold duplicate-audio lectures into the first occurrence.

        Returns a list of ``(duplicate_id, kept_id)`` pairs. The duplicate keeps any
        unique URLs (merged into the kept entry) and is marked ``excluded`` with a
        ``duplicate-of:<id>`` note.
        """
        kept: dict[str, Lecture] = {}
        merged: list[tuple[str, str]] = []
        for _, lec in self.iter_lectures():
            if not lec.sha256:
                continue
            primary = kept.get(lec.sha256)
            if primary is None:
                kept[lec.sha256] = lec
                continue
            for url in lec.urls:
                if url not in primary.urls:
                    primary.urls.append(url)
            if lec.status is not Status.EXCLUDED:
                lec.set_status(Status.EXCLUDED)
            lec.notes = (lec.notes + f" duplicate-of:{primary.id}").strip()
            merged.append((lec.id, primary.id))
        return merged
