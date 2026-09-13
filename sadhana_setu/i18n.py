"""Internationalization core (spec 004).

Per-locale YAML message catalogs with English fallback (FR-002) and a review gate on translated
content (FR-003/004, Constitution V). Runtime-agnostic (Streamlit + static build).

- `t(key)` — UI string for the current locale, English fallback per key.
- `localize_content(library, id, field, english)` — the *reviewed* translation, else English.
- `set_locale`/`get_locale` — persisted in `data/i18n/settings.yaml` (and st.session_state).
- `maybe_transliterate(text)` — Sanskrit → vernacular script in a non-English locale.

Review gate (Constitution V): UI catalogs carry a catalog-level `_meta.reviewed`; content overlays
carry a per-item `reviewed`. Unreviewed material is withheld (English shown) unless the
practitioner has explicitly opted in via `show_machine_drafts: true` in `settings.yaml`
(default off; the pre-japa view shows a "machine-translated" banner while it is on).
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

from sadhana_setu import translit

LOCALES = ("en", "te", "kn", "ta")
META_KEY = "_meta"
_REPO = Path(__file__).resolve().parents[1]
_mtime_cache: dict[str, tuple[float, object]] = {}


def _i18n_dir() -> Path:
    return Path(os.environ.get("I18N_DIR", _REPO / "data" / "i18n"))


# -- settings (locale + opt-ins) -----------------------------------------

def _settings_path() -> Path:
    return _i18n_dir() / "settings.yaml"


def _settings() -> dict:
    data = _load(_settings_path())
    return dict(data) if isinstance(data, dict) else {}


def _write_settings(**changes) -> None:
    settings = _settings()
    settings.update(changes)
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(settings, sort_keys=True), encoding="utf-8")
    _mtime_cache.pop(str(path), None)


def show_machine_drafts() -> bool:
    """Explicit opt-in to see UNREVIEWED machine drafts (default False — Constitution V)."""
    return _settings().get("show_machine_drafts") is True


def set_show_machine_drafts(enabled: bool) -> None:
    _write_settings(show_machine_drafts=bool(enabled))


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
    if _settings().get("locale") != code:
        _write_settings(locale=code)


def _read_setting() -> str:
    loc = _settings().get("locale", "en")
    return loc if loc in LOCALES else "en"


# -- UI strings (FR-002) -------------------------------------------------

def t(key: str, **fmt) -> str:
    """UI string for the current locale; English fallback per key; never blank."""
    loc = get_locale()
    cat = _published_ui_catalog(loc)
    s = cat.get(key)
    if s is None and loc != "en":
        s = _ui_catalog("en").get(key)
    if s is None:
        s = key
    return s.format(**fmt) if fmt else s


def _ui_catalog(locale: str) -> dict:
    data = _load(_i18n_dir() / "ui" / f"{locale}.yaml")
    return data if isinstance(data, dict) else {}


def ui_catalog_reviewed(locale: str) -> bool:
    """True when the locale's UI catalog carries `_meta.reviewed: true` (English is the source)."""
    if locale == "en":
        return True
    meta = _ui_catalog(locale).get(META_KEY)
    return isinstance(meta, dict) and meta.get("reviewed") is True


def _published_ui_catalog(locale: str) -> dict:
    """The UI catalog the app may show: reviewed, or unreviewed only under the explicit opt-in."""
    if locale == "en":
        return _ui_catalog("en")
    if not (ui_catalog_reviewed(locale) or show_machine_drafts()):
        return {}
    return {k: v for k, v in _ui_catalog(locale).items() if k != META_KEY}


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


def localize_content_machine(library: str, item_id, field: str, english: str,
                             *, locale: str | None = None) -> str:
    """Translation of a content field INCLUDING unreviewed machine drafts — but only when the
    practitioner has opted in (`show_machine_drafts: true`); otherwise identical to the reviewed
    gate (Constitution V). Reads the live catalog, then the `.draft` one.
    """
    loc = locale or get_locale()
    if loc == "en":
        return english
    if not show_machine_drafts():
        return localize_content(library, item_id, field, english, locale=loc)
    base = _i18n_dir() / "content" / loc
    for fname in (f"{library}.yaml", f"{library}.draft.yaml"):
        rows = _load(base / fname) or []
        for row in rows if isinstance(rows, list) else []:
            if str(row.get("id")) == str(item_id):
                v = row.get(field)
                if v:
                    return v
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
