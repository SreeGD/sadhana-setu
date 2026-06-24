"""T007 — enrichment output parse + validation; claude envelope extraction."""
import json

import pytest

from sadhana_setu.corpus.llm import EnrichmentError, _extract_result, parse_enrichment

GOOD = {
    "theme_summary": "On attentive chanting.",
    "key_teachings": [
        {"point": "Chant without offense", "timestamp": "00:01:02.000",
         "candidate_verse_refs": ["BG 18.66"]}
    ],
    "practical_application": "Begin japa before 4:45 AM.",
}


def test_parse_valid():
    obj = parse_enrichment(json.dumps(GOOD))
    assert obj["key_teachings"][0]["timestamp"] == "00:01:02.000"


def test_parse_strips_code_fences():
    fenced = "```json\n" + json.dumps(GOOD) + "\n```"
    assert parse_enrichment(fenced)["theme_summary"].startswith("On attentive")


def test_extract_result_from_envelope():
    env = json.dumps({"type": "result", "result": json.dumps(GOOD)})
    assert parse_enrichment(_extract_result(env))["practical_application"]


def test_missing_required_rejected():
    bad = dict(GOOD); del bad["theme_summary"]
    with pytest.raises(EnrichmentError):
        parse_enrichment(json.dumps(bad))


def test_bad_timestamp_rejected():
    bad = {"theme_summary": "t", "practical_application": "a",
           "key_teachings": [{"point": "p", "timestamp": "1:02"}]}
    with pytest.raises(EnrichmentError):
        parse_enrichment(json.dumps(bad))


def test_non_json_rejected():
    with pytest.raises(EnrichmentError):
        parse_enrichment("not json at all")
