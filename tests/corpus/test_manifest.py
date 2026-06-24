"""T008 — manifest schema validation, status transitions, round-trip, dedup."""
import pytest

from sadhana_setu.corpus.manifest import (
    Lecture,
    Manifest,
    ManifestError,
    SourceSet,
    Status,
    StatusTransitionError,
)


def test_round_trip(manifest, cfg):
    manifest.get_set("bhurijana-prabhu").lectures.append(
        Lecture(id="a-talk", title="A Talk", urls=["https://x.test/a.mp3"])
    )
    manifest.save()
    reloaded = Manifest.load(cfg.manifest_path)
    assert reloaded.get_set("bhurijana-prabhu").lectures[0].id == "a-talk"


def test_invalid_slug_rejected():
    lec = Lecture(id="Not Slug", title="t", urls=["https://x/a.mp3"])
    with pytest.raises(ManifestError):
        lec.validate()


def test_transcribed_requires_provenance():
    lec = Lecture(id="x", title="t", urls=["https://x/a.mp3"], status=Status.TRANSCRIBED)
    with pytest.raises(ManifestError):
        lec.validate()


def test_non_english_must_be_deferred():
    lec = Lecture(id="x", title="t", urls=["https://x/a.mp3"], language="hi",
                  status=Status.PENDING)
    with pytest.raises(ManifestError):
        lec.validate()


def test_status_transition_legal_and_illegal():
    lec = Lecture(id="x", title="t", urls=["https://x/a.mp3"])
    lec.sha256 = "0" * 64
    lec.set_status(Status.FETCHED)
    assert lec.status is Status.FETCHED
    with pytest.raises(StatusTransitionError):
        lec.set_status(Status.PENDING)  # fetched → pending not allowed


def test_status_self_assert_is_noop():
    lec = Lecture(id="x", title="t", urls=["https://x/a.mp3"])
    lec.set_status(Status.PENDING)
    assert lec.status is Status.PENDING


def test_duplicate_id_across_corpus_rejected(cfg):
    m = Manifest(source_sets=[
        SourceSet(id="s1", speaker="A", kind="speaker",
                  lectures=[Lecture(id="dup", title="t", urls=["https://x/a.mp3"])]),
        SourceSet(id="s2", speaker="B", kind="speaker",
                  lectures=[Lecture(id="dup", title="t", urls=["https://x/b.mp3"])]),
    ], path=cfg.manifest_path)
    with pytest.raises(ManifestError):
        m.validate()


def test_dedupe_by_checksum(manifest):
    sha = "a" * 64
    manifest.get_set("bhurijana-prabhu").lectures.append(
        Lecture(id="orig", title="t", urls=["https://x/a.mp3"], sha256=sha,
                status=Status.TRANSCRIBED, transcript_path="p.md", whisper_model="m")
    )
    manifest.get_set("holy-name-seminar").lectures.append(
        Lecture(id="copy", title="t", urls=["https://y/b.mp3"], sha256=sha,
                status=Status.FETCHED)
    )
    merged = manifest.dedupe_by_checksum()
    assert merged == [("copy", "orig")]
    orig = manifest.get_set("bhurijana-prabhu").lectures[0]
    copy = manifest.get_set("holy-name-seminar").lectures[0]
    assert "https://y/b.mp3" in orig.urls
    assert copy.status is Status.EXCLUDED
    assert "duplicate-of:orig" in copy.notes
