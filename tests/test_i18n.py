"""T006/T010/T014 — i18n: locale, UI fallback, content reviewed-gate, citation preservation."""
import importlib

import pytest

import sadhana_setu.i18n as i18n


@pytest.fixture
def i18n_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("I18N_DIR", str(tmp_path))
    i18n._mtime_cache.clear()
    (tmp_path / "ui").mkdir()
    (tmp_path / "ui" / "en.yaml").write_text(
        "view.notes: Notes\nview.today: Today\n", encoding="utf-8")
    # A REVIEWED Telugu UI catalog (T027: `_meta.reviewed` gates unreviewed catalogs).
    (tmp_path / "ui" / "te.yaml").write_text(
        "_meta:\n  reviewed: true\n  reviewer: devotee\nview.notes: గమనికలు\n", encoding="utf-8")
    (tmp_path / "content" / "te").mkdir(parents=True)
    (tmp_path / "content" / "te" / "affirmations.yaml").write_text(
        "- id: 0\n  text: అనువాదం\n  reviewed: true\n"
        "- id: 1\n  text: ముసాయిదా\n  reviewed: false\n", encoding="utf-8")
    return tmp_path


def test_set_get_locale_persists(i18n_dir):
    i18n.set_locale("te")
    assert i18n.get_locale() == "te"
    with pytest.raises(ValueError):
        i18n.set_locale("xx")


def test_ui_string_localized(i18n_dir):
    i18n.set_locale("te")
    assert i18n.t("view.notes") == "గమనికలు"


def test_ui_fallback_to_english(i18n_dir):
    i18n.set_locale("te")
    assert i18n.t("view.today") == "Today"      # missing in te.yaml ⇒ English (SC-001)
    assert i18n.t("view.missing") == "view.missing"  # absent everywhere ⇒ key, never blank


def test_content_reviewed_shown_unreviewed_falls_back(i18n_dir):
    # reviewed item → translation; unreviewed → English original (SC-002, Constitution V)
    assert i18n.localize_content("affirmations", 0, "text", "EN-0", locale="te") == "అనువాదం"
    assert i18n.localize_content("affirmations", 1, "text", "EN-1", locale="te") == "EN-1"


def test_english_locale_returns_english(i18n_dir):
    assert i18n.localize_content("affirmations", 0, "text", "EN-0", locale="en") == "EN-0"


def test_citation_preserved(i18n_dir):
    # No translated 'source' field ⇒ the English citation is preserved (SC-004 / FR-006).
    assert i18n.localize_content("affirmations", 0, "source", "CC Madhya 20.108",
                                 locale="te") == "CC Madhya 20.108"


def test_localize_content_machine_gated_by_default(i18n_dir):
    # T021 / Constitution V: without the explicit opt-in, the machine path == the reviewed gate.
    (i18n_dir / "content" / "te" / "tips.draft.yaml").write_text(
        "- id: 0\n  tip: తెలుగు చిట్కా\n  reviewed: false\n", encoding="utf-8")
    assert i18n.show_machine_drafts() is False
    assert i18n.localize_content_machine("tips", 0, "tip", "EN", locale="te") == "EN"
    assert i18n.localize_content("tips", 0, "tip", "EN", locale="te") == "EN"


def test_localize_content_machine_shows_drafts_only_with_opt_in(i18n_dir):
    (i18n_dir / "content" / "te" / "tips.draft.yaml").write_text(
        "- id: 0\n  tip: తెలుగు చిట్కా\n  reviewed: false\n", encoding="utf-8")
    i18n.set_show_machine_drafts(True)
    assert i18n.show_machine_drafts() is True
    assert i18n.localize_content_machine("tips", 0, "tip", "EN", locale="te") == "తెలుగు చిట్కా"
    assert i18n.localize_content("tips", 0, "tip", "EN", locale="te") == "EN"  # gate still withholds
    assert i18n.localize_content_machine("tips", 0, "tip", "EN", locale="en") == "EN"  # English untouched
    i18n.set_show_machine_drafts(False)
    assert i18n.localize_content_machine("tips", 0, "tip", "EN", locale="te") == "EN"


def test_opt_in_survives_locale_change(i18n_dir):
    i18n.set_show_machine_drafts(True)
    i18n.set_locale("te")
    i18n.set_locale("en")
    assert i18n.show_machine_drafts() is True  # set_locale must not clobber other settings


def test_ui_catalog_unreviewed_falls_back_to_english(i18n_dir):
    # T027 / FR-004: a UI catalog carrying `_meta.reviewed: false` is withheld unless opted in.
    (i18n_dir / "ui" / "te.yaml").write_text(
        "_meta:\n  reviewed: false\nview.notes: గమనికలు\n", encoding="utf-8")
    i18n.set_locale("te")
    assert i18n.ui_catalog_reviewed("te") is False
    assert i18n.t("view.notes") == "Notes"
    i18n.set_show_machine_drafts(True)
    assert i18n.t("view.notes") == "గమనికలు"
    i18n.set_show_machine_drafts(False)
    (i18n_dir / "ui" / "te.yaml").write_text(
        "_meta:\n  reviewed: true\n  reviewer: devotee\nview.notes: గమనికలు\n", encoding="utf-8")
    assert i18n.ui_catalog_reviewed("te") is True
    assert i18n.t("view.notes") == "గమనికలు"
    assert i18n.t("_meta") == "_meta"  # the status block is never a UI string


def test_prejapa_citation_preserved_in_vernacular_locale(i18n_dir, monkeypatch):
    # T026 / FR-006: localization never alters a citation — verbatim in te, drafts on or off.
    from datetime import date

    from sadhana_setu.flows.prejapa_reading import build_reading
    from sadhana_setu.content.affirmations import pick_for_today
    from sadhana_setu.content import faith_verses as faith_mod

    d = date(2026, 9, 13)
    aff = pick_for_today(d)
    faith = faith_mod.pick_for_today(d)
    expected = (aff.source if aff else None) or (faith.verse_ref if faith else None)
    for opt in (False, True):
        i18n.set_show_machine_drafts(opt)
        r = build_reading(d, querier=lambda *a, **k: None, checkin_loader=lambda d: None, locale="te")
        assert r.orient.citation == expected
        assert r.deepen.citation is None or r.deepen.citation == r.deepen.citation.strip()


def test_maybe_transliterate(i18n_dir):
    i18n.set_locale("te")
    assert i18n.maybe_transliterate("Hare Kṛṣṇa") == "హరే కృష్ణ"
    i18n.set_locale("en")
    assert i18n.maybe_transliterate("Hare Kṛṣṇa") == "Hare Kṛṣṇa"
