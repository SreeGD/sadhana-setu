"""Enrich transcripts into draft class notes (US1/US2/US3).

Section-wise pipeline: the verbatim transcript is split into ~10-minute windows; Claude Code
enriches each window (preserving the seminar's detail and interactive flow), then a synthesis
pass produces the theme / practical application / glossary. Grounding resolves all verse and
cross-reference candidates against kg-mcp. Idempotent; ``regenerate`` resets a reviewed note to
draft (FR-009).
"""
from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor

from sadhana_setu.corpus import notes as notes_mod
from sadhana_setu.corpus import transcript as transcript_mod
from sadhana_setu.corpus.config import CorpusConfig
from sadhana_setu.corpus.grounding import KGUnavailable, ground
from sadhana_setu.corpus.llm import ClaudeCodeProvider, parse_section, parse_synthesis
from sadhana_setu.corpus.manifest import Manifest, SourceSet, Status
from sadhana_setu.corpus.notes import NoteFrontMatter, NoteStatus

_SEG_RE = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\.\d{3}")
WINDOW_SECONDS = 600  # ~10-minute enrichment windows
# Window enrichments are independent → run several `claude -p` calls concurrently.
ENRICH_CONCURRENCY = int(os.environ.get("CORPUS_ENRICH_CONCURRENCY", "4"))


class EnrichResult:
    def __init__(self) -> None:
        self.enriched: list[str] = []
        self.skipped: list[str] = []
        self.unverifiable: list[str] = []
        self.failed: list[str] = []


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
        except Exception as exc:  # one lecture's LLM/parse failure must not abort the batch
            result.failed.append(f"{lec.id}: {exc}")
    return result


def _enrich_one(cfg, sset: SourceSet, lec, prov, caller, out_path) -> None:
    transcript_file = cfg.repo_root / lec.transcript_path
    _, body = transcript_mod.parse(transcript_file.read_text(encoding="utf-8"))

    windows = split_windows(body)

    def _section(win: tuple[str, str]) -> dict:
        label, text = win
        return parse_section(prov.complete(build_section_prompt(sset.speaker, lec.title, label, text)))

    fragments = _map_windows(_section, windows)  # parallel `claude -p`, order preserved

    teachings: list[dict] = []
    cross_refs: list[dict] = []
    sic_flags: list[dict] = []
    for frag in fragments:
        teachings.extend(frag.get("key_teachings", []) or [])
        cross_refs.extend(frag.get("candidate_cross_refs", []) or [])
        sic_flags.extend(frag.get("sic_flags", []) or [])

    synth = parse_synthesis(prov.complete(build_synthesis_prompt(sset.speaker, lec.title, teachings)))
    enrichment = {
        "theme_summary": synth["theme_summary"],
        "practical_application": synth["practical_application"],
        "glossary": synth.get("glossary", []) or [],
        "key_teachings": teachings,
        "candidate_cross_refs": cross_refs,
        "sic_flags": sic_flags,
    }
    # Live runs: ground every candidate through ONE persistent kg-mcp session (the 145K-node
    # graph loads once, not per lookup). Tests pass a mocked `caller` and skip the session.
    if caller is None:
        from sadhana_setu.mcp_client import kg_session

        with kg_session() as sess:
            content = ground(enrichment, caller=sess.call)  # raises KGUnavailable ⇒ withhold
    else:
        content = ground(enrichment, caller=caller)

    fm = NoteFrontMatter(
        lecture_id=lec.id, set_id=sset.id, transcript_path=lec.transcript_path,
        sha256=lec.sha256, speaker=sset.speaker, title=lec.title,
        enrichment_version=cfg.enrichment_version, enriched_at=notes_mod.now_iso(),
        status=NoteStatus.DRAFT,
    )
    notes_mod.write(out_path, fm, content)


def _map_windows(fn, items: list) -> list:
    """Map ``fn`` over windows, concurrently when worthwhile (order preserved)."""
    if ENRICH_CONCURRENCY <= 1 or len(items) <= 1:
        return [fn(x) for x in items]
    with ThreadPoolExecutor(max_workers=min(ENRICH_CONCURRENCY, len(items))) as ex:
        return list(ex.map(fn, items))


def split_windows(body: str, window_seconds: int = WINDOW_SECONDS) -> list[tuple[str, str]]:
    """Group segment-timestamped transcript lines into ~window_seconds windows."""
    buckets: dict[int, list[str]] = {}
    for line in body.splitlines():
        m = _SEG_RE.match(line.strip())
        if not m:
            continue
        secs = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
        buckets.setdefault(secs // window_seconds, []).append(line)
    if not buckets:
        return [("full", body)]
    out: list[tuple[str, str]] = []
    for w in sorted(buckets):
        start = w * window_seconds
        label = f"{start // 60:02d}:00–{(start + window_seconds) // 60:02d}:00"
        out.append((label, "\n".join(buckets[w])))
    return out


def build_section_prompt(speaker: str, title: str, window_label: str, window_text: str) -> str:
    return f"""TASK: SECTION — distill one ~10-minute window of a Gauḍīya Vaiṣṇava (ISKCON) \
Holy-Name lecture into a STUDY NOTE. Speaker: {speaker}. Lecture: {title}. Window: {window_label}.

Extract the **substantive teachings** of this window — distinct instructions, principles, and \
insights. Aim for roughly **3–6 key teachings** for the window (fewer if little is taught). \
CONSOLIDATE related points into one teaching; do NOT narrate the transcript blow-by-blow. Skip \
pure mechanics and chit-chat. For an interactive seminar, fold a participant exchange in ONLY \
when it carries a teaching, and state the teaching (not the play-by-play). This is a note for \
study, not a transcript replay — favour insight and brevity over completeness.

Return ONLY a JSON object (no prose, no code fences):
- "key_teachings": array of {{ "point": string, "timestamp": "HH:MM:SS.mmm" copied from the \
transcript line, "candidate_verses": [ {{ "ref": "e.g. BG 18.66", "gloss": "one-line meaning to \
search if the exact verse is uncached" }} ] }}
- "candidate_cross_refs": array of {{ "query": "a phrase to find a related corpus passage" }}
- "sic_flags": array of {{ "timestamp": "HH:MM:SS.mmm", "heard": string, "suspected": string }} \
for suspected mis-transcribed Sanskrit (DO NOT alter the transcript)

Rules: propose verse REFERENCES and glosses only — never invent verse text; the system fills \
authoritative text from the knowledge graph. Preserve the speaker's meaning; never paraphrase \
the speaker as a direct quotation.

TRANSCRIPT WINDOW:
{window_text}
"""


def build_synthesis_prompt(speaker: str, title: str, teachings: list[dict]) -> str:
    points = "\n".join(f"- [{kt.get('timestamp', '')}] {kt.get('point', '')}" for kt in teachings)
    return f"""TASK: SYNTHESIS — given the key teachings already extracted from a Holy-Name \
lecture by {speaker} ("{title}"), write the connective tissue. Return ONLY a JSON object:
- "theme_summary": string (a faithful overview of the whole lecture's arc)
- "practical_application": string (how a devotee applies this to daily japa / Hari-Nāma)
- "glossary": array of {{ "term": string, "gloss": string }} for the Sanskrit/technical terms used

Do not invent content beyond what the teachings support.

KEY TEACHINGS:
{points}
"""
