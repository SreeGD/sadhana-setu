"""T027 — set scoping + status report counts."""
from sadhana_setu.corpus import sets as sets_mod
from sadhana_setu.corpus.manifest import Status

from tests.corpus.conftest import add_lecture


def test_status_counts_per_set_and_total(manifest):
    add_lecture(manifest, "bhurijana-prabhu", id="a", status=Status.PENDING)
    add_lecture(manifest, "bhurijana-prabhu", id="b", sha256="0" * 64,
                status=Status.FETCHED)
    add_lecture(manifest, "holy-name-seminar", id="c", language="hi",
                status=Status.DEFERRED)

    report = sets_mod.status_report(manifest)
    by_id = {s["id"]: s for s in report["sets"]}
    assert by_id["bhurijana-prabhu"]["counts"]["pending"] == 1
    assert by_id["bhurijana-prabhu"]["counts"]["fetched"] == 1
    assert by_id["holy-name-seminar"]["counts"]["deferred"] == 1
    assert report["totals"]["pending"] == 1
    assert report["grand_total"] == 3


def test_status_scoped_to_one_set(manifest):
    add_lecture(manifest, "bhurijana-prabhu", id="a", status=Status.PENDING)
    add_lecture(manifest, "holy-name-seminar", id="c", status=Status.PENDING)
    report = sets_mod.status_report(manifest, set_id="bhurijana-prabhu")
    assert [s["id"] for s in report["sets"]] == ["bhurijana-prabhu"]
    assert report["grand_total"] == 1


def test_format_status_renders_table(manifest):
    add_lecture(manifest, "bhurijana-prabhu", id="a", status=Status.PENDING)
    text = sets_mod.format_status(sets_mod.status_report(manifest))
    assert "bhurijana-prabhu" in text
    assert "TOTAL" in text
