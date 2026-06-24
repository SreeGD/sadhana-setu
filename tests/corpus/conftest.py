"""Shared fixtures for corpus pipeline tests (all hermetic — no network/whisper/ffmpeg)."""
from __future__ import annotations

from pathlib import Path

import pytest

from sadhana_setu.corpus.config import CorpusConfig
from sadhana_setu.corpus.manifest import Lecture, Manifest, SourceSet, Status


@pytest.fixture
def cfg(tmp_path: Path) -> CorpusConfig:
    corpus = tmp_path / "corpus"
    (corpus / "sources").mkdir(parents=True)
    return CorpusConfig(
        repo_root=tmp_path,
        audio_cache=corpus / ".audio-cache",
        transcripts_dir=corpus / "transcripts",
        manifest_path=corpus / "sources" / "manifest.yaml",
        model_dir=tmp_path / "models",
        model_name="ggml-test",
        fetch_rate_limit_seconds=0.0,
        chunk_seconds=600,
    )


@pytest.fixture
def manifest(cfg: CorpusConfig) -> Manifest:
    m = Manifest(
        source_sets=[
            SourceSet(id="bhurijana-prabhu", speaker="Bhūrijana Prabhu", kind="speaker"),
            SourceSet(id="holy-name-seminar", speaker="Holy Name Seminar", kind="seminar"),
        ],
        manifest_status="active",
        path=cfg.manifest_path,
    )
    m.save()
    return m


def add_lecture(manifest: Manifest, set_id: str, **kw) -> Lecture:
    lec = Lecture(
        id=kw.pop("id", "test-lecture"),
        title=kw.pop("title", "Test Holy Name Lecture"),
        urls=kw.pop("urls", ["https://example.test/a.mp3"]),
        **kw,
    )
    manifest.get_set(set_id).lectures.append(lec)
    return lec
