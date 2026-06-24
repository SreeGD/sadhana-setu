"""T030 — verify: checksum match / mismatch reproducibility."""
import hashlib

from sadhana_setu.corpus import verify as verify_mod
from sadhana_setu.corpus.manifest import Status

from tests.corpus.conftest import add_lecture

CONTENT = b"fake-audio"
SHA = hashlib.sha256(CONTENT).hexdigest()


def _writer(content):
    def download(url, dest, cfg):
        dest.write_bytes(content)
    return download


def test_verify_matches(cfg, manifest):
    add_lecture(manifest, "holy-name-seminar", id="l1", sha256=SHA,
                status=Status.FETCHED, urls=["https://x.test/a.mp3"])
    report = verify_mod.verify_set(cfg, manifest, downloader=_writer(CONTENT))
    assert report.ok
    assert report.matched == ["l1"]


def test_verify_detects_drift(cfg, manifest):
    add_lecture(manifest, "holy-name-seminar", id="l1", sha256=SHA,
                status=Status.TRANSCRIBED, transcript_path="p.md", whisper_model="m",
                urls=["https://x.test/a.mp3"])
    report = verify_mod.verify_set(cfg, manifest, downloader=_writer(b"different"))
    assert not report.ok
    assert report.mismatched[0][0] == "l1"


def test_verify_skips_unfetched(cfg, manifest):
    add_lecture(manifest, "holy-name-seminar", id="l1", status=Status.PENDING,
                urls=["https://x.test/a.mp3"])

    def explode(url, dest, cfg):
        raise AssertionError("should not fetch a pending entry")

    report = verify_mod.verify_set(cfg, manifest, downloader=explode)
    assert report.matched == [] and report.ok
