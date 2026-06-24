"""Hari-Nāma corpus pipeline (spec 001-corpus-pipeline).

A reproducible, manifest-driven pipeline that fetches Holy-Name lecture audio,
transcribes it verbatim with whisper.cpp, and commits timestamped transcripts plus
the source manifest. Audio is never committed (Constitution III/VI).

Stages (see ``contracts/cli.md``): ``seed`` → ``fetch`` → ``transcribe`` →
``status`` / ``verify``. Each stage is idempotent.
"""

from sadhana_setu.corpus.config import CorpusConfig, ToolMissingError
from sadhana_setu.corpus.manifest import (
    Lecture,
    Manifest,
    ProvenanceError,
    SourceSet,
    Status,
)

__all__ = [
    "CorpusConfig",
    "ToolMissingError",
    "Manifest",
    "Lecture",
    "SourceSet",
    "Status",
    "ProvenanceError",
]
