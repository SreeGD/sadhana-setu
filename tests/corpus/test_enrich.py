"""T012 — enrich: draft note from stubbed provider; --regenerate resets reviewed→draft."""
import json

from sadhana_setu.corpus import notes as notes_mod
from sadhana_setu.corpus.enrich import enrich_set
from sadhana_setu.corpus.manifest import Status
from sadhana_setu.corpus.notes import NoteStatus

from tests.corpus.conftest import add_lecture, write_transcript

ENRICH_JSON = json.dumps({
    "theme_summary": "Attentive chanting of the Holy Name.",
    "key_teachings": [{"point": "Chant without offense", "timestamp": "00:00:01.000",
                       "candidate_verse_refs": ["BG 18.66"]}],
    "practical_application": "Rise before 4:45 AM for japa.",
    "glossary": [{"term": "japa", "gloss": "soft individual chanting"}],
})


class StubProvider:
    def complete(self, prompt):
        return ENRICH_JSON


def _caller(name, args):
    if name == "kg_status":
        return {"ok": True}
    if name == "get_verse":
        return {"iast": "sarva-dharmān parityajya", "translation": "Abandon all dharmas"}
    return []


def _transcribed_lecture(cfg, manifest, lec_id="talk-1"):
    tpath = write_transcript(cfg, "holy-name-seminar", lec_id)
    return add_lecture(manifest, "holy-name-seminar", id=lec_id, title="Holy Name Talk",
                       sha256="a" * 64, status=Status.TRANSCRIBED, transcript_path=tpath,
                       whisper_model="m")


def test_enrich_writes_draft_note(cfg, manifest):
    lec = _transcribed_lecture(cfg, manifest)
    res = enrich_set(cfg, manifest, provider=StubProvider(), caller=_caller)
    assert res.enriched == [lec.id]
    path = notes_mod.note_path(cfg, "holy-name-seminar", lec.id)
    fm = notes_mod.read_front_matter(path)
    assert fm.status is NoteStatus.DRAFT
    assert fm.enrichment_engine == "claude-code"
    body = path.read_text(encoding="utf-8")
    assert "sarva-dharmān" in body  # KG-grounded verse substituted


def test_enrich_idempotent(cfg, manifest):
    _transcribed_lecture(cfg, manifest)
    enrich_set(cfg, manifest, provider=StubProvider(), caller=_caller)
    res2 = enrich_set(cfg, manifest, provider=StubProvider(), caller=_caller)
    assert res2.skipped and not res2.enriched


def test_regenerate_resets_reviewed_to_draft(cfg, manifest):
    lec = _transcribed_lecture(cfg, manifest)
    enrich_set(cfg, manifest, provider=StubProvider(), caller=_caller)
    path = notes_mod.note_path(cfg, "holy-name-seminar", lec.id)
    # simulate approval
    from sadhana_setu.corpus.review import approve
    approve(path, "Reviewer Dāsa")
    assert notes_mod.read_front_matter(path).status is NoteStatus.REVIEWED
    # regenerate must reset to draft (FR-009, not silently invalidated)
    enrich_set(cfg, manifest, provider=StubProvider(), caller=_caller, regenerate=True)
    assert notes_mod.read_front_matter(path).status is NoteStatus.DRAFT


def test_kg_offline_marks_unverifiable(cfg, manifest):
    _transcribed_lecture(cfg, manifest)

    def offline(name, args):
        raise RuntimeError("down")

    res = enrich_set(cfg, manifest, provider=StubProvider(), caller=offline)
    assert res.unverifiable and not res.enriched
