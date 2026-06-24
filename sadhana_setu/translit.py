"""Sanskrit → vernacular-script transliteration (spec 004, FR-010).

Wraps `indic-transliteration` (`sanscript`) to render IAST/Devanāgarī into Telugu / Kannada /
Tamil, preserving the exact Sanskrit **sounds** (Constitution I — the Holy Name's vibration is
unchanged). Returns the input unchanged for `en` or on any failure (IAST fallback).
"""
from __future__ import annotations

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

_TARGET = {"te": sanscript.TELUGU, "kn": sanscript.KANNADA, "ta": sanscript.TAMIL}
_SOURCE = {"iast": sanscript.IAST, "devanagari": sanscript.DEVANAGARI}


def to_script(text: str, locale: str, *, src: str = "iast") -> str:
    """Transliterate ``text`` into ``locale``'s script. ``en``/unknown/failure ⇒ unchanged."""
    if not text or locale == "en" or locale not in _TARGET:
        return text
    try:
        return transliterate(text, _SOURCE.get(src, sanscript.IAST), _TARGET[locale])
    except Exception:  # noqa: BLE001 — any transliteration failure ⇒ IAST fallback
        return text
