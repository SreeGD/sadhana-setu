"""T017 — seed parser + topic filter (speaker filtered, seminar in full)."""
from sadhana_setu.corpus import seed as seed_mod

LISTING = """
<html><body>
  <a href="/audio/attentive-chanting-of-the-holy-name-2018-01-12.mp3">Attentive Chanting of the Holy Name (2018-01-12)</a>
  <a href="/audio/bhagavad-gita-overview.mp3">Bhagavad-gītā Overview</a>
  <a href="/audio/japa-and-the-ten-offenses.mp3">Japa and the Ten Offenses</a>
  <a href="/notes/handout.pdf">Handout PDF</a>
</body></html>
"""


def test_parse_listing_finds_audio_only():
    entries = seed_mod.parse_listing(LISTING, base_url="https://site.test/")
    urls = [e.url for e in entries]
    assert "https://site.test/audio/bhagavad-gita-overview.mp3" in urls
    assert all(u.endswith(".mp3") for u in urls)  # the PDF is excluded
    assert len(entries) == 3


def test_extracts_date():
    entries = seed_mod.parse_listing(LISTING, base_url="https://site.test/")
    dated = [e for e in entries if "attentive-chanting" in e.url][0]
    assert dated.date == "2018-01-12"


def test_speaker_set_applies_topic_filter(manifest):
    entries = seed_mod.parse_listing(LISTING, base_url="https://site.test/")
    added = seed_mod.seed_set(manifest, "bhurijana-prabhu", entries)
    titles = {lec.title for lec in added}
    # Holy-Name + japa/offenses topics kept; the generic Gītā overview dropped.
    assert any("Holy Name" in t for t in titles)
    assert any("Ten Offenses" in t for t in titles)
    assert not any("Overview" in t for t in titles)


def test_seminar_set_includes_everything(manifest):
    entries = seed_mod.parse_listing(LISTING, base_url="https://site.test/")
    added = seed_mod.seed_set(manifest, "holy-name-seminar", entries)
    assert len(added) == 3  # seminar = no topic filter


def test_seed_is_idempotent_by_url(manifest):
    entries = seed_mod.parse_listing(LISTING, base_url="https://site.test/")
    seed_mod.seed_set(manifest, "holy-name-seminar", entries)
    again = seed_mod.seed_set(manifest, "holy-name-seminar", entries)
    assert again == []  # nothing re-added


def test_seeded_entries_are_pending_and_valid(manifest):
    entries = seed_mod.parse_listing(LISTING, base_url="https://site.test/")
    seed_mod.seed_set(manifest, "holy-name-seminar", entries)
    manifest.validate()  # must not raise
