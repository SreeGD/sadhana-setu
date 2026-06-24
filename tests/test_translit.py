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
