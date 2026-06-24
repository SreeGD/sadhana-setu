"""T012 — section-wise enrich: draft note from stubbed provider; --regenerate resets reviewed→draft."""
import json

from sadhana_setu.corpus import notes as notes_mod
from sadhana_setu.corpus.enrich import enrich_set, split_windows
from sadhana_setu.corpus.manifest import Status
from sadhana_setu.corpus.notes import NoteStatus

from tests.corpus.conftest import add_lecture, write_transcript

SECTION_JSON = json.dumps({
    "key_teachings": [{"point": "Chant without offense", "timestamp": "00:00:01.000",
                       "candidate_verses": [{"ref": "BG 18.66", "gloss": "surrender to Kṛṣṇa"}]}],
    "candidate_cross_refs": [{"query": "taking shelter of the holy name"}],
    "sic_flags": [],
})
SYNTHESIS_JSON = json.dumps({
    "theme_summary": "Attentive chanting of the Holy Name.",
    "practical_application": "Rise before 4:45 AM for japa.",
    "glossary": [{"term": "japa", "gloss": "soft individual chanting"}],
})


class StubProvider:
    """Returns section vs synthesis output based on the prompt's TASK marker."""
    def complete(self, prompt):
        return SYNTHESIS_JSON if "TASK: SYNTHESIS" in prompt else SECTION_JSON


def _caller(name, args):
    if name == "kg_status":
        return {"ok": True}
    if name == "get_verse":
        return {"verse_ref": args["verse_ref"], "found": True,
                "iast": "sarva-dharmān parityajya", "translation": "Abandon all dharmas"}
    if name == "search_corpus":
        return {"chunks": [{"source": "CC Madhya 22.107", "text": "Take shelter of the Name."}]}
    return None


def _transcribed_lecture(cfg, manifest, lec_id="talk-1"):
    body = "\n".join(f"[00:0{i}:00.000 → 00:0{i}:30.000] Teaching line {i}." for i in range(3))
    tpath = write_transcript(cfg, "holy-name-seminar", lec_id, body=body)
    return add_lecture(manifest, "holy-name-seminar", id=lec_id, title="Holy Name Talk",
                       sha256="a" * 64, status=Status.TRANSCRIBED, transcript_path=tpath,
                       whisper_model="m")


def test_split_windows_groups_by_ten_minutes():
    body = "[00:02:00.000 → x] a\n[00:11:00.000 → x] b\n[00:25:00.000 → x] c"
    wins = split_windows(body)
    assert len(wins) == 3  # 0–10, 10–20, 20–30


def test_enrich_writes_draft_note_with_grounded_verse(cfg, manifest):
    lec = _transcribed_lecture(cfg, manifest)
    res = enrich_set(cfg, manifest, provider=StubProvider(), caller=_caller)
    assert res.enriched == [lec.id]
    path = notes_mod.note_path(cfg, "holy-name-seminar", lec.id)
    fm = notes_mod.read_front_matter(path)
    assert fm.status is NoteStatus.DRAFT
    body = path.read_text(encoding="utf-8")
    assert "sarva-dharmān" in body          # KG-grounded verse (SC-001)
    assert "CC Madhya 22.107" in body        # grounded cross-reference, clean source (FR-004)
    assert "Error executing tool" not in body  # no leaked kg-mcp error payloads


def test_enrich_idempotent(cfg, manifest):
    _transcribed_lecture(cfg, manifest)
    enrich_set(cfg, manifest, provider=StubProvider(), caller=_caller)
    res2 = enrich_set(cfg, manifest, provider=StubProvider(), caller=_caller)
    assert res2.skipped and not res2.enriched


def test_regenerate_resets_reviewed_to_draft(cfg, manifest):
    lec = _transcribed_lecture(cfg, manifest)
    enrich_set(cfg, manifest, provider=StubProvider(), caller=_caller)
    path = notes_mod.note_path(cfg, "holy-name-seminar", lec.id)
    from sadhana_setu.corpus.review import approve
    approve(path, "Reviewer Dāsa")
    assert notes_mod.read_front_matter(path).status is NoteStatus.REVIEWED
    enrich_set(cfg, manifest, provider=StubProvider(), caller=_caller, regenerate=True)
    assert notes_mod.read_front_matter(path).status is NoteStatus.DRAFT


def test_failed_lecture_does_not_abort_batch(cfg, manifest):
    """A claude/parse failure on one lecture is recorded but the batch continues (scale)."""
    from sadhana_setu.corpus.llm import EnrichmentError

    for lid, title in [("bad-1", "BAD LECTURE"), ("good-1", "GOOD LECTURE")]:
        body = "\n".join(f"[00:0{i}:00.000 → 00:0{i}:30.000] Line {i}." for i in range(3))
        tpath = write_transcript(cfg, "holy-name-seminar", lid, body=body)
        add_lecture(manifest, "holy-name-seminar", id=lid, title=title, sha256="b" * 64,
                    status=Status.TRANSCRIBED, transcript_path=tpath, whisper_model="m")

    class FlakyProvider:
        def complete(self, prompt):
            if "TASK: SYNTHESIS" in prompt:
                if "BAD LECTURE" in prompt:
                    raise EnrichmentError("`claude -p` failed after 3 attempts (exit 1): Overloaded")
                return SYNTHESIS_JSON
            return SECTION_JSON

    res = enrich_set(cfg, manifest, provider=FlakyProvider(), caller=_caller)
    assert "good-1" in res.enriched              # the healthy lecture still gets a note
    assert any("bad-1" in f for f in res.failed)  # the failure is recorded, not raised


def test_kg_offline_marks_unverifiable(cfg, manifest):
    _transcribed_lecture(cfg, manifest)

    def offline(name, args):
        if name == "kg_status":
            raise RuntimeError("down")
        return None

    res = enrich_set(cfg, manifest, provider=StubProvider(), caller=offline)
    assert res.unverifiable and not res.enriched
