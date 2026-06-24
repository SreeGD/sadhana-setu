"""Source-set grouping and the status report (US3, FR-010)."""
from __future__ import annotations

from sadhana_setu.corpus.manifest import Manifest, Status

_ORDER = [s.value for s in Status]


def status_report(manifest: Manifest, set_id: str | None = None) -> dict:
    """Return per-set counts of each Lecture status plus a total row."""
    sets: list[dict] = []
    totals = {s.value: 0 for s in Status}
    for sset in manifest.source_sets:
        if set_id and sset.id != set_id:
            continue
        counts = {s.value: 0 for s in Status}
        for lec in sset.lectures:
            counts[lec.status.value] += 1
            totals[lec.status.value] += 1
        sets.append({
            "id": sset.id,
            "speaker": sset.speaker,
            "kind": sset.kind,
            "total": len(sset.lectures),
            "counts": counts,
        })
    return {"sets": sets, "totals": totals, "grand_total": sum(totals.values())}


def format_status(report: dict) -> str:
    """Render the status report as a human-readable table."""
    cols = _ORDER
    header = f"{'set':24} {'total':>5} " + " ".join(f"{c[:5]:>5}" for c in cols)
    lines = [header, "-" * len(header)]
    for s in report["sets"]:
        row = f"{s['id'][:24]:24} {s['total']:>5} " + " ".join(
            f"{s['counts'][c]:>5}" for c in cols
        )
        lines.append(row)
    t = report["totals"]
    lines.append("-" * len(header))
    lines.append(
        f"{'TOTAL':24} {report['grand_total']:>5} " + " ".join(f"{t[c]:>5}" for c in cols)
    )
    return "\n".join(lines)
