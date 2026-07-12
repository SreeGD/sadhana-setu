#!/usr/bin/env bash
# Build nama-tattva-DRAFT.pdf from the markdown sources.
# Requires: pandoc + Google Chrome (headless). macOS.
set -euo pipefail
cd "$(dirname "$0")"

TMP="$(mktemp -d)"
MASTER="$TMP/master.md"; HEADER="$TMP/header.html"; BEFORE="$TMP/before.html"; HTML="$TMP/book.html"
OUT="$PWD/nama-tattva-DRAFT.pdf"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 1) assemble in reading order: front matter -> chapters 1..21 -> glossary -> references
: > "$MASTER"
cat FRONT-MATTER.md >> "$MASTER"; printf '\n\n' >> "$MASTER"
for f in $(ls ch*.md | sort); do cat "$f" >> "$MASTER"; printf '\n\n' >> "$MASTER"; done
cat GLOSSARY.md >> "$MASTER"; printf '\n\n' >> "$MASTER"
cat REFERENCES.md >> "$MASTER"

# 2) print CSS (serif book style + repeating DRAFT watermark)
cat > "$HEADER" <<'CSS'
<style>
@page { size: Letter; margin: 19mm 17mm; }
body { font-family: "Iowan Old Style","Palatino","Baskerville",Georgia,"Times New Roman","Kohinoor Devanagari","Devanagari MN",serif; font-size:11.5pt; line-height:1.5; color:#1a1a1a; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
h1 { page-break-before:always; font-size:20pt; color:#5b3a1a; border-bottom:2px solid #c9a24b; padding-bottom:5px; }
h1:first-of-type { page-break-before:avoid; }
h2 { font-size:14pt; color:#7a4a12; margin-top:1.3em; }
h3 { font-size:12pt; color:#8a5a2a; }
blockquote { border-left:3px solid #c9a24b; margin:1em 0; padding:.2em 1em; color:#3a3a3a; background:#faf6ec; }
table { border-collapse:collapse; width:100%; font-size:9.6pt; margin:1em 0; }
th,td { border:1px solid #d8ccb0; padding:4px 7px; text-align:left; vertical-align:top; }
th { background:#f3ead2; }
pre,code { font-family:"Menlo","Courier New",monospace; font-size:9.5pt; }
pre { background:#f6f2e8; padding:8px; border-radius:4px; white-space:pre-wrap; word-wrap:break-word; }
a { color:#7a4a12; text-decoration:none; }
hr { border:0; border-top:1px solid #d8ccb0; margin:1.5em 0; }
.draft-wm { position:fixed; top:42%; left:0; width:100%; text-align:center; transform:rotate(-28deg); font-size:130pt; color:rgba(180,140,60,0.09); font-weight:bold; letter-spacing:14px; z-index:-1; }
#TOC { page-break-after:always; } #TOC ul { list-style:none; padding-left:0; } #TOC a { color:#5b3a1a; }
</style>
CSS
echo '<div class="draft-wm">DRAFT</div>' > "$BEFORE"

# 3) markdown -> standalone HTML (TOC of chapter titles only)
pandoc "$MASTER" -f gfm -t html5 --standalone --toc --toc-depth=1 \
  --metadata title="Nāma-Tattva — Why My Chanting Isn't Working (and How to Fix It)" \
  --include-in-header="$HEADER" --include-before-body="$BEFORE" -o "$HTML"

# 4) HTML -> PDF (Chrome headless)
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf-no-header \
  --run-all-compositor-stages-before-draw --virtual-time-budget=20000 \
  --print-to-pdf="$OUT" "file://$HTML"

rm -rf "$TMP"
echo "Built $OUT ($(du -h "$OUT" | cut -f1))"
