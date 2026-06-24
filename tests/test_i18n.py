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
    (tmp_path / "ui" / "te.yaml").write_text("view.notes: గమనికలు\n", encoding="utf-8")
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


def test_maybe_transliterate(i18n_dir):
    i18n.set_locale("te")
    assert i18n.maybe_transliterate("Hare Kṛṣṇa") == "హరే కృష్ణ"
    i18n.set_locale("en")
    assert i18n.maybe_transliterate("Hare Kṛṣṇa") == "Hare Kṛṣṇa"
