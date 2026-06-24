"""T023 — transcribe: front-matter, timestamps, chunk offsets, idempotency."""
import hashlib

import pytest

from sadhana_setu.corpus import audio as audio_mod
from sadhana_setu.corpus import transcribe as transcribe_mod
from sadhana_setu.corpus.audio import Chunk
from sadhana_setu.corpus.manifest import Status
from sadhana_setu.corpus.transcript import Segment, parse

from tests.corpus.conftest import add_lecture

CONTENT = b"fake-audio"
SHA = hashlib.sha256(CONTENT).hexdigest()


@pytest.fixture
def fetched(cfg, manifest):
    lec = add_lecture(manifest, "holy-name-seminar", id="talk-1", title="Holy Name Talk",
                      urls=["https://x.test/a.mp3"], sha256=SHA, duration_seconds=600,
                      status=Status.FETCHED)
    cfg.audio_cache.mkdir(parents=True, exist_ok=True)
    (cfg.audio_cache / f"{SHA}.mp3").write_bytes(CONTENT)
    return lec


@pytest.fixture(autouse=True)
def _stub_ffmpeg(monkeypatch):
    def fake_decode(cfg, src, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"wav")
        return dst
    monkeypatch.setattr(audio_mod, "decode_to_wav", fake_decode)
    monkeypatch.setattr(transcribe_mod.audio, "decode_to_wav", fake_decode)


def _single_chunk(cfg, wav, out_dir):
    return [Chunk(path=wav, offset_seconds=0.0)]


def _transcriber(segments):
    def run(cfg, wav):
        return list(segments)
    return run


def test_transcribe_writes_valid_transcript(cfg, manifest, fetched, monkeypatch):
    monkeypatch.setattr(transcribe_mod.audio, "segment", _single_chunk)
    segs = [Segment(0.0, 7.32, "Hare Kṛṣṇa, today we discuss the Holy Name."),
            Segment(7.32, 14.0, "Chant attentively.")]
    res = transcribe_mod.transcribe_set(cfg, manifest, transcriber=_transcriber(segs))
    assert res.transcribed == ["talk-1"]
    assert fetched.status is Status.TRANSCRIBED
    assert fetched.whisper_model == "ggml-test"

    path = cfg.transcripts_dir / "holy-name-seminar" / "talk-1.md"
    fm, body = parse(path.read_text(encoding="utf-8"))
    assert fm["lecture_id"] == "talk-1"
    assert fm["sha256"] == SHA
    assert fm["timestamp_granularity"] == "segment"
    assert "[00:00:00.000 → 00:00:07.320] Hare Kṛṣṇa" in body
    assert fetched.transcript_path == "corpus/transcripts/holy-name-seminar/talk-1.md"


def test_chunk_offsets_make_continuous_timeline(cfg, manifest, fetched, monkeypatch):
    def two_chunks(cfg, wav, out_dir):
        return [Chunk(path=wav, offset_seconds=0.0), Chunk(path=wav, offset_seconds=600.0)]
    monkeypatch.setattr(transcribe_mod.audio, "segment", two_chunks)
    # each chunk yields one segment at 0–5s relative
    transcribe_mod.transcribe_set(
        cfg, manifest, transcriber=_transcriber([Segment(0.0, 5.0, "line")]))
    _, body = parse((cfg.transcripts_dir / "holy-name-seminar" / "talk-1.md")
                    .read_text(encoding="utf-8"))
    assert "[00:00:00.000 → 00:00:05.000]" in body
    assert "[00:10:00.000 → 00:10:05.000]" in body  # second chunk offset by 600s


def test_transcribe_idempotent(cfg, manifest, fetched, monkeypatch):
    monkeypatch.setattr(transcribe_mod.audio, "segment", _single_chunk)
    t = _transcriber([Segment(0.0, 5.0, "line")])
    transcribe_mod.transcribe_set(cfg, manifest, transcriber=t)
    res2 = transcribe_mod.transcribe_set(cfg, manifest, transcriber=t)
    assert res2.skipped == ["talk-1"]
    assert res2.transcribed == []


def test_parse_whisper_json():
    raw = '{"transcription": [{"offsets": {"from": 0, "to": 7320}, "text": " Hare Kṛṣṇa"}]}'
    segs = transcribe_mod.parse_whisper_json(raw)
    assert segs[0].start == 0.0 and segs[0].end == 7.32
    assert segs[0].text == "Hare Kṛṣṇa"
