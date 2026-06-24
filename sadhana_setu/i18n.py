"""Internationalization core (spec 004).

Per-locale YAML message catalogs with English fallback (FR-002) and a review gate on translated
content (FR-003/004, Constitution V). Runtime-agnostic (Streamlit + static build).

- `t(key)` — UI string for the current locale, English fallback per key.
- `localize_content(library, id, field, english)` — the *reviewed* translation, else English.
- `set_locale`/`get_locale` — persisted in `data/i18n/settings.yaml` (and st.session_state).
- `maybe_transliterate(text)` — Sanskrit → vernacular script in a non-English locale.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

from sadhana_setu import translit

LOCALES = ("en", "te", "kn", "ta")
_REPO = Path(__file__).resolve().parents[1]
_mtime_cache: dict[str, tuple[float, object]] = {}


def _i18n_dir() -> Path:
    return Path(os.environ.get("I18N_DIR", _REPO / "data" / "i18n"))


# -- locale state --------------------------------------------------------

def get_locale() -> str:
    try:
        import streamlit as st

        loc = st.session_state.get("locale")
        if loc in LOCALES:
            return loc
    except Exception:  # noqa: BLE001 — no Streamlit runtime
        pass
    return _read_setting()


def set_locale(code: str) -> None:
    if code not in LOCALES:
        raise ValueError(f"unsupported locale: {code}")
    try:
        import streamlit as st

        st.session_state["locale"] = code
    except Exception:  # noqa: BLE001
        pass
    settings = _i18n_dir() / "settings.yaml"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(yaml.safe_dump({"locale": code}), encoding="utf-8")


def _read_setting() -> str:
    data = _load(_i18n_dir() / "settings.yaml")
    return data.get("locale", "en") if isinstance(data, dict) else "en"


# -- UI strings (FR-002) -------------------------------------------------

def t(key: str, **fmt) -> str:
    """UI string for the current locale; English fallback per key; never blank."""
    loc = get_locale()
    cat = _ui_catalog(loc)
    s = cat.get(key) if isinstance(cat, dict) else None
    if s is None and loc != "en":
        en = _ui_catalog("en")
        s = en.get(key) if isinstance(en, dict) else None
    if s is None:
        s = key
    return s.format(**fmt) if fmt else s


def _ui_catalog(locale: str) -> dict:
    return _load(_i18n_dir() / "ui" / f"{locale}.yaml") or {}


# -- content (FR-003/004, review gate) -----------------------------------

def localize_content(library: str, item_id, field: str, english: str, *, locale: str | None = None) -> str:
    """Return the REVIEWED translation of a content field, else the English original."""
    loc = locale or get_locale()
    if loc == "en":
        return english
    rows = _content_catalog(loc, library)
    for row in rows if isinstance(rows, list) else []:
        if str(row.get("id")) == str(item_id) and row.get("reviewed") is True:
            return row.get(field, english) or english
    return english


def _content_catalog(locale: str, library: str) -> list:
    return _load(_i18n_dir() / "content" / locale / f"{library}.yaml") or []


# -- transliteration (FR-010) --------------------------------------------

def maybe_transliterate(text: str, *, src: str = "iast", locale: str | None = None) -> str:
    """Transliterate Sanskrit into the current locale's script (no-op for English)."""
    return translit.to_script(text, locale or get_locale(), src=src)


# -- mtime-invalidated YAML cache ----------------------------------------

def _load(path: Path):
    if not path.exists():
        return None
    mt = path.stat().st_mtime
    key = str(path)
    cached = _mtime_cache.get(key)
    if cached is None or cached[0] != mt:
        _mtime_cache[key] = (mt, yaml.safe_load(path.read_text(encoding="utf-8")))
    return _mtime_cache[key][1]
