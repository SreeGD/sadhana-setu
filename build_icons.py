"""Generate the Sadhana Setu app icons.

One-shot script — run locally when the icon design changes. Output PNGs are
committed; CI does not regenerate them (the macOS Devanagari fonts are not
present on the GitHub runner).

Renders सा (the first syllable of साधना, in #B8860B gold) on a #FFFBF3 cream
square, in five sizes for PWA installability + favicons.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
OUT = ROOT / "static" / "icons"

BG = (255, 251, 243)          # #FFFBF3 — cream
FG = (184, 134, 11)           # #B8860B — gold
GLYPH = "सा"

CANDIDATE_FONTS = [
    "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
    "/System/Library/Fonts/Supplemental/Kohinoor.ttc",
    "/System/Library/Fonts/Kohinoor.ttc",
    "/Library/Fonts/Kohinoor.ttc",
    "/System/Library/Fonts/NotoSansDevanagari.ttf",
]


def find_font() -> str:
    for p in CANDIDATE_FONTS:
        if Path(p).exists():
            return p
    raise SystemExit(
        "No Devanagari font found. Install one of:\n  "
        + "\n  ".join(CANDIDATE_FONTS)
    )


def render_glyph_ink(font_path: str, font_size: int) -> Image.Image:
    """Render सा onto a transparent canvas and crop to the true ink bbox.

    Pillow's textbbox returns the font's metric box, which for Devanagari
    leaves substantial empty space above/below the actual strokes. We render
    big, then crop by actual rendered pixels."""
    scratch = font_size * 3
    img = Image.new("RGBA", (scratch, scratch), (0, 0, 0, 0))
    ImageDraw.Draw(img).text(
        (scratch // 2, scratch // 2),
        GLYPH,
        font=ImageFont.truetype(font_path, font_size),
        fill=FG + (255,),
        anchor="mm",
    )
    return img.crop(img.getbbox())


def render(size: int, fill_ratio: float, font_path: str) -> Image.Image:
    """Render an icon at the given pixel size, glyph height ≈ fill_ratio*size."""
    target_h = int(size * fill_ratio)
    # Pick a font size that produces an ink-height ≈ target_h.
    probe = render_glyph_ink(font_path, 200)
    actual = max(1, probe.height)
    font_size = max(8, int(200 * target_h / actual))
    ink = render_glyph_ink(font_path, font_size)
    canvas = Image.new("RGB", (size, size), BG)
    x = (size - ink.width) // 2
    y = (size - ink.height) // 2
    canvas.paste(ink, (x, y), ink)
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    font_path = find_font()
    print(f"Using font: {font_path}")
    specs = [
        ("icon-192.png", 192, 0.58),
        ("icon-512.png", 512, 0.58),
        ("icon-maskable-512.png", 512, 0.42),
        ("apple-touch-icon.png", 180, 0.58),
        ("favicon-32.png", 32, 0.72),
        ("favicon-16.png", 16, 0.78),
    ]
    for name, size, ratio in specs:
        img = render(size, ratio, font_path)
        out = OUT / name
        img.save(out, format="PNG", optimize=True)
        print(f"  {name:<25}  {size}×{size}  → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
