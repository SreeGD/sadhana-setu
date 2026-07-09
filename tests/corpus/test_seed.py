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


# Apache autoindex truncates the visible link text but keeps the full filename in href.
AUTOINDEX = """
<html><body><pre>
  <a href="BJP_Seminar_-_Holyname-01_-_2010-02-19_ISKCON_Chowpatty.mp3">BJP_Seminar_-_Holyna..&gt;</a>
  <a href="BJP_Seminar_-_Holyname-01_-_2010-02-20_ISKCON_Chowpatty.mp3">BJP_Seminar_-_Holyna..&gt;</a>
</pre></body></html>
"""


def test_truncated_anchor_uses_filename_for_title_and_date():
    entries = seed_mod.parse_listing(AUTOINDEX, base_url="https://site.test/folder/")
    titles = [e.title for e in entries]
    # Title recovered from the href filename, not the "Holyna..>" stub.
    assert all("Holyname" in t for t in titles)
    assert all(".." not in t and ">" not in t for t in titles)
    assert {e.date for e in entries} == {"2010-02-19", "2010-02-20"}


# Percent-encoded spaces in the href must be decoded before slugging, or "%20"
# collapses to a stray "20" glued to the next word (sonicate-20your-20life).
PERCENT_ENCODED = """
<html><body><pre>
  <a href="Vaisesika_Pr_Holy_Name_-_Sonicate%20Your%20Life_-_2017-08-13.mp3">Vaisesika_Pr_Holy..&gt;</a>
</pre></body></html>
"""


def test_percent_encoded_href_decoded_in_title_and_slug():
    entries = seed_mod.parse_listing(PERCENT_ENCODED, base_url="https://site.test/folder/")
    title = entries[0].title
    assert "Sonicate Your Life" in title
    assert "%20" not in title and "20Your" not in title
    slug = seed_mod.make_slug(title, entries[0].date)
    assert "sonicate-your-life" in slug
    assert "-20your" not in slug


def test_holyname_one_word_matches_topic_filter(manifest):
    entries = seed_mod.parse_listing(AUTOINDEX, base_url="https://site.test/folder/")
    added = seed_mod.seed_set(manifest, "bhurijana-prabhu", entries)
    assert len(added) == 2  # both 'Holyname' lectures kept by the speaker-set filter
    assert all("holyname" in lec.topic_tags for lec in added)


def test_speaker_set_applies_topic_filter(manifest):
    entries = seed_mod.parse_listing(LISTING, base_url="https://site.test/")
    added = seed_mod.seed_set(manifest, "bhurijana-prabhu", entries)
    titles = {lec.title for lec in added}
    # Holy-Name + japa/offenses topics kept; the generic Gītā overview dropped.
    assert any("Holy Name" in t for t in titles)
    assert any("Ten Offenses" in t for t in titles)
    assert not any("Overview" in t for t in titles)


def test_force_all_bypasses_topic_filter_on_speaker_set(manifest):
    # A dedicated Holy-Name folder: keep every lecture even if a title lacks a keyword.
    entries = seed_mod.parse_listing(LISTING, base_url="https://site.test/")
    added = seed_mod.seed_set(manifest, "bhurijana-prabhu", entries, force_all=True)
    assert len(added) == 3  # incl. the generic 'Bhagavad-gītā Overview' the filter would drop


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
