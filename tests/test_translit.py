"""T004/T016 — transliteration fidelity (the tattva-critical piece, Constitution I)."""
from sadhana_setu import translit


def test_maha_mantra_telugu():
    assert translit.to_script("Hare Kṛṣṇa", "te") == "హరే కృష్ణ"


def test_maha_mantra_kannada():
    assert translit.to_script("Hare Kṛṣṇa", "kn") == "ಹರೇ ಕೃಷ್ಣ"


def test_verse_transliterates_to_telugu():
    out = translit.to_script("sarva-dharmān parityajya", "te")
    assert out and out != "sarva-dharmān parityajya"  # actually transliterated
    assert "ధర్మ" in out  # 'dharma' renders in Telugu script


def test_english_locale_passthrough():
    assert translit.to_script("Hare Kṛṣṇa", "en") == "Hare Kṛṣṇa"


def test_unknown_locale_passthrough():
    assert translit.to_script("Hare Kṛṣṇa", "xx") == "Hare Kṛṣṇa"


def test_empty_passthrough():
    assert translit.to_script("", "te") == ""


def test_maha_mantra_tamil():
    # Tamil has no vocalic ṛ; sanscript marks it (ஹரே க்ரு'ஷ்ண) — the sounds are still preserved.
    out = translit.to_script("Hare Kṛṣṇa", "ta")
    assert out.startswith("ஹரே") and "ஷ்ண" in out and out != "Hare Kṛṣṇa"


def test_verse_transliterates_to_kannada_and_tamil():
    assert translit.to_script("sarva-dharmān parityajya", "kn") == "ಸರ್ವ-ಧರ್ಮಾನ್ ಪರಿತ್ಯಜ್ಯ"
    assert translit.to_script("sarva-dharmān parityajya", "ta") == "ஸர்வ-தர்மாந் பரித்யஜ்ய"


def test_failure_falls_back_to_iast(monkeypatch):
    # Any engine failure ⇒ the IAST input is returned unchanged (contracts/i18n.md, FR-010).
    def boom(*a, **k):
        raise RuntimeError("engine down")

    monkeypatch.setattr(translit, "transliterate", boom)
    assert translit.to_script("Hare Kṛṣṇa", "te") == "Hare Kṛṣṇa"
