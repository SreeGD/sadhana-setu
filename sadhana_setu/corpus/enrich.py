"""Enrich transcripts into draft class notes (US1/US2/US3).

Pipeline per transcript: read verbatim transcript → Claude Code proposes structured candidates
→ grounding resolves verses/cross-refs against kg-mcp → render a draft note. Idempotent;
``regenerate`` re-enriches and resets a reviewed note to draft (FR-009).
"""
from __future__ import annotations

from sadhana_setu.corpus import notes as notes_mod
from sadhana_setu.corpus import transcript as transcript_mod
from sadhana_setu.corpus.config import CorpusConfig
from sadhana_setu.corpus.grounding import KGUnavailable, ground
from sadhana_setu.corpus.llm import ClaudeCodeProvider, parse_enrichment
from sadhana_setu.corpus.manifest import Manifest, SourceSet, Status
from sadhana_setu.corpus.notes import NoteFrontMatter, NoteStatus


class EnrichResult:
    def __init__(self) -> None:
        self.enriched: list[str] = []
        self.skipped: list[str] = []
        self.unverifiable: list[str] = []


def enrich_set(cfg: CorpusConfig, manifest: Manifest, set_id: str | None = None,
               *, provider=None, caller=None, regenerate: bool = False) -> EnrichResult:
    result = EnrichResult()
    prov = provider or ClaudeCodeProvider(cfg)
    for sset, lec in manifest.iter_lectures(set_id):
        if lec.status is not Status.TRANSCRIBED or not lec.transcript_path:
            continue
        out_path = notes_mod.note_path(cfg, sset.id, lec.id)
        if out_path.exists() and not regenerate:
            fm = notes_mod.read_front_matter(out_path)
            if fm.enrichment_version == cfg.enrichment_version:
                result.skipped.append(lec.id)
                continue
        try:
            _enrich_one(cfg, sset, lec, prov, caller, out_path)
            result.enriched.append(lec.id)
        except KGUnavailable as exc:
            result.unverifiable.append(f"{lec.id}: {exc}")
    return result


def _enrich_one(cfg, sset: SourceSet, lec, prov, caller, out_path) -> None:
    transcript_file = cfg.repo_root / lec.transcript_path
    _, body = transcript_mod.parse(transcript_file.read_text(encoding="utf-8"))

    enrichment = parse_enrichment(prov.complete(build_prompt(lec.title, sset.speaker, body)))
    content = ground(enrichment, caller=caller)  # raises KGUnavailable ⇒ caller withholds

    fm = NoteFrontMatter(
        lecture_id=lec.id, set_id=sset.id, transcript_path=lec.transcript_path,
        sha256=lec.sha256, speaker=sset.speaker, title=lec.title,
        enrichment_version=cfg.enrichment_version, enriched_at=notes_mod.now_iso(),
        status=NoteStatus.DRAFT,  # re-enrich always resets to draft (FR-009)
    )
    notes_mod.write(out_path, fm, content)


def build_prompt(title: str, speaker: str, transcript_body: str) -> str:
    """The enrichment prompt contract (see contracts/enrichment-output.schema.json)."""
    return f"""You are enriching a verbatim transcript of a Gauḍīya Vaiṣṇava (ISKCON) Holy-Name \
lecture into structured study notes. Speaker: {speaker}. Title: {title}.

Return ONLY a single JSON object (no prose, no code fences) with these keys:
- "theme_summary": string
- "key_teachings": array of {{ "point": string, "timestamp": "HH:MM:SS.mmm" (copied from the \
transcript line where the point is made), "candidate_verse_refs": [string]  // e.g. "BG 18.66" \
— IDENTIFIERS ONLY, never the verse text }}
- "practical_application": string (how it applies to japa / Hari-Nāma)
- "glossary": array of {{ "term": string, "gloss": string }}
- "candidate_cross_refs": array of {{ "query": string, "value_id": string (optional) }}
- "sic_flags": array of {{ "timestamp": "HH:MM:SS.mmm", "heard": string, "suspected": string }} \
for suspected mis-transcribed Sanskrit (DO NOT alter the transcript)

Rules: never invent verse text or translations — propose verse references only; the system \
fills authoritative text from the knowledge graph. Preserve the speaker's meaning; do not \
paraphrase the speaker as a quotation.

TRANSCRIPT:
{transcript_body}
"""
