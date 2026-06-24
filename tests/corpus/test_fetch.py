"""T016 — fetch: checksum, idempotency, provenance mismatch, deferred/unavailable."""
import hashlib

import pytest

from sadhana_setu.corpus import fetch as fetch_mod
from sadhana_setu.corpus.fetch import _Unavailable, fetch_set
from sadhana_setu.corpus.manifest import ProvenanceError, Status

from tests.corpus.conftest import add_lecture

CONTENT = b"fake-audio-bytes"
SHA = hashlib.sha256(CONTENT).hexdigest()


def _writer(content=CONTENT):
    def download(url, dest, cfg):
        dest.write_bytes(content)
    return download


@pytest.fixture(autouse=True)
def _no_ffprobe(monkeypatch):
    monkeypatch.setattr(fetch_mod, "probe_duration", lambda cfg, p: 123.0)


def test_fetch_records_checksum_and_caches(cfg, manifest):
    lec = add_lecture(manifest, "holy-name-seminar", id="l1",
                      urls=["https://x.test/a.mp3"])
    res = fetch_set(cfg, manifest, downloader=_writer())
    assert res.fetched == ["l1"]
    assert lec.status is Status.FETCHED
    assert lec.sha256 == SHA
    assert lec.duration_seconds == 123
    assert (cfg.audio_cache / f"{SHA}.mp3").read_bytes() == CONTENT
    # no leftover .part file
    assert not list(cfg.audio_cache.glob("*.part"))


def test_fetch_idempotent_reuses_cache(cfg, manifest):
    add_lecture(manifest, "holy-name-seminar", id="l1", sha256=SHA,
                urls=["https://x.test/a.mp3"])
    cfg.audio_cache.mkdir(parents=True, exist_ok=True)
    (cfg.audio_cache / f"{SHA}.mp3").write_bytes(CONTENT)

    def explode(url, dest, cfg):  # must not be called
        raise AssertionError("download should not run on cache hit")

    res = fetch_set(cfg, manifest, downloader=explode)
    assert res.skipped == ["l1"]


def test_fetch_checksum_mismatch_raises(cfg, manifest):
    wrong = "b" * 64
    add_lecture(manifest, "holy-name-seminar", id="l1", sha256=wrong,
                urls=["https://x.test/a.mp3"])
    cfg.audio_cache.mkdir(parents=True, exist_ok=True)
    (cfg.audio_cache / f"{wrong}.mp3").write_bytes(CONTENT)  # hash != wrong
    with pytest.raises(ProvenanceError):
        fetch_set(cfg, manifest, downloader=_writer())


def test_non_english_deferred_without_download(cfg, manifest):
    add_lecture(manifest, "holy-name-seminar", id="l1", language="hi",
                urls=["https://x.test/a.mp3"])

    def explode(url, dest, cfg):
        raise AssertionError("should not download deferred audio")

    res = fetch_set(cfg, manifest, downloader=explode)
    assert res.deferred == ["l1"]
    assert manifest.get_set("holy-name-seminar").lectures[0].status is Status.DEFERRED


def test_dead_url_marked_unavailable(cfg, manifest):
    add_lecture(manifest, "holy-name-seminar", id="l1", urls=["https://x.test/a.mp3"])

    def dead(url, dest, cfg):
        raise _Unavailable("HTTP 404")

    res = fetch_set(cfg, manifest, downloader=dead)
    assert res.unavailable == ["l1"]
    assert manifest.get_set("holy-name-seminar").lectures[0].status is Status.UNAVAILABLE


def test_duplicate_audio_excluded(cfg, manifest):
    add_lecture(manifest, "bhurijana-prabhu", id="orig", urls=["https://x.test/a.mp3"])
    add_lecture(manifest, "holy-name-seminar", id="copy", urls=["https://y.test/b.mp3"])
    res = fetch_set(cfg, manifest, downloader=_writer())
    assert "orig" in res.fetched
    assert "copy" in res.excluded
    copy = manifest.get_set("holy-name-seminar").lectures[0]
    assert copy.status is Status.EXCLUDED
    assert "duplicate-of:orig" in copy.notes
