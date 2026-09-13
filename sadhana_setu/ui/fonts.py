"""Bundled Indic web fonts for the Streamlit app (spec 004, FR-005 / T024).

The Noto Sans Telugu/Kannada/Tamil subsets live in `static/fonts/*.woff2` (shared with the static
build) and are embedded as data-URI `@font-face` rules so rendering needs no network and no system
fonts (Constitution VI: offline). Built once per process.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

_FONTS_DIR = Path(__file__).resolve().parents[2] / "static" / "fonts"
FACES = (
    ("Noto Sans Telugu", "NotoSansTelugu.woff2"),
    ("Noto Sans Kannada", "NotoSansKannada.woff2"),
    ("Noto Sans Tamil", "NotoSansTamil.woff2"),
)


@lru_cache(maxsize=1)
def indic_font_faces_css() -> str:
    """`@font-face` rules (data URIs) for every bundled face that exists on disk."""
    rules = []
    for family, fname in FACES:
        path = _FONTS_DIR / fname
        if not path.exists():
            continue
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            f"@font-face {{ font-family: '{family}'; font-style: normal; font-weight: 400; "
            f"font-display: swap; src: url(data:font/woff2;base64,{b64}) format('woff2'); }}"
        )
    return "\n".join(rules)
