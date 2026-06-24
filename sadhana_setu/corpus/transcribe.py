"""Transcribe fetched audio verbatim with whisper.cpp (US2).

Decodes to WAV, chunks long audio, runs ``whisper-cli`` per chunk, offsets each
chunk's segment timestamps by its start, stitches a continuous timeline, and writes a
provenance-bearing transcript. Idempotent: an existing transcript for the same
``sha256`` + model is left untouched unless ``retranscribe=True`` (FR-007).
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from sadhana_setu.corpus import audio
from sadhana_setu.corpus.config import CorpusConfig
from sadhana_setu.corpus.manifest import Lecture, Manifest, SourceSet, Status
from sadhana_setu.corpus.transcript import (
    Segment,
    TranscriptFrontMatter,
    now_iso,
    write,
)

PIPELINE_VERSION = "0.1.0"


class TranscribeResult:
    def __init__(self) -> None:
        self.transcribed: list[str] = []
        self.skipped: list[str] = []
        self.quarantined: list[str] = []


def transcribe_set(cfg: CorpusConfig, manifest: Manifest, set_id: str | None = None,
                   *, retranscribe: bool = False, transcriber=None) -> TranscribeResult:
    """Transcribe all ``fetched`` lectures (optionally scoped to ``set_id``)."""
    result = TranscribeResult()
    run_whisper = transcriber or _run_whisper
    for sset, lec in manifest.iter_lectures(set_id):
        if lec.status is not Status.FETCHED and not (
            retranscribe and lec.status is Status.TRANSCRIBED
        ):
            result.skipped.append(lec.id)
            continue
        out_path = _transcript_path(cfg, sset, lec)
        if lec.status is Status.TRANSCRIBED and out_path.exists() and not retranscribe:
            result.skipped.append(lec.id)
            continue
        try:
            _transcribe_one(cfg, manifest, sset, lec, run_whisper)
            result.transcribed.append(lec.id)
        except _ChunkError as exc:
            lec.notes = (lec.notes + f" quarantined:{exc}").strip()
            result.quarantined.append(lec.id)
    return result


def _transcribe_one(cfg, manifest, sset: SourceSet, lec: Lecture, run_whisper) -> None:
    src = _cache_file(cfg, lec)
    with tempfile.TemporaryDirectory(prefix=f"transcribe-{lec.id}-") as td:
        tmp = Path(td)
        wav = audio.decode_to_wav(cfg, src, tmp / "audio.wav")
        chunks = audio.segment(cfg, wav, tmp / "chunks")
        segments: list[Segment] = []
        for chunk in chunks:
            try:
                raw = run_whisper(cfg, chunk.path)
            except subprocess.CalledProcessError as exc:
                raise _ChunkError(f"whisper failed on {chunk.path.name}") from exc
            for seg in raw:
                segments.append(Segment(
                    start=seg.start + chunk.offset_seconds,
                    end=seg.end + chunk.offset_seconds,
                    text=seg.text,
                ))
    segments.sort(key=lambda s: s.start)

    fm = TranscriptFrontMatter(
        lecture_id=lec.id, set_id=sset.id, speaker=sset.speaker, title=lec.title,
        source_urls=list(lec.urls), sha256=lec.sha256, date=lec.date,
        duration_seconds=lec.duration_seconds
        or (int(round(segments[-1].end)) if segments else 0),
        language="en", whisper_model=cfg.model_name,
        whisper_flags=" ".join(cfg.whisper_flags),
        pipeline_version=PIPELINE_VERSION, transcribed_at=now_iso(),
    )
    out_path = _transcript_path(cfg, sset, lec)
    write(out_path, fm, segments)

    lec.whisper_model = cfg.model_name
    lec.transcript_path = str(out_path.relative_to(cfg.repo_root))
    if lec.duration_seconds is None and segments:
        lec.duration_seconds = int(round(segments[-1].end))
    if lec.status is not Status.TRANSCRIBED:
        lec.set_status(Status.TRANSCRIBED)


def _run_whisper(cfg: CorpusConfig, wav: Path) -> list[Segment]:
    """Invoke whisper.cpp and parse its JSON output into segments."""
    out_prefix = wav.with_suffix("")
    subprocess.run(
        [cfg.whisper_cli(), "-m", str(cfg.model_path), "-f", str(wav),
         "-of", str(out_prefix), *cfg.whisper_flags],
        check=True, capture_output=True,
    )
    return parse_whisper_json(Path(f"{out_prefix}.json").read_text(encoding="utf-8"))


def parse_whisper_json(text: str) -> list[Segment]:
    """Parse whisper.cpp ``--output-json`` into Segments (offsets are milliseconds)."""
    data = json.loads(text)
    segments: list[Segment] = []
    for item in data.get("transcription", []):
        off = item.get("offsets", {})
        segments.append(Segment(
            start=off.get("from", 0) / 1000.0,
            end=off.get("to", 0) / 1000.0,
            text=item.get("text", "").strip(),
        ))
    return segments


def _transcript_path(cfg: CorpusConfig, sset: SourceSet, lec: Lecture) -> Path:
    return cfg.transcripts_dir / sset.id / f"{lec.id}.md"


def _cache_file(cfg: CorpusConfig, lec: Lecture) -> Path:
    if not lec.sha256:
        raise _ChunkError(f"{lec.id}: no sha256 (not fetched)")
    matches = sorted(cfg.audio_cache.glob(f"{lec.sha256}.*"))
    if not matches:
        raise _ChunkError(f"{lec.id}: cached audio {lec.sha256[:12]} missing")
    return matches[0]


class _ChunkError(RuntimeError):
    pass
