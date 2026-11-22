#!/bin/bash
# Render a resume HTML file to PDF with headless Chrome (same route for every resume).
# Usage: tools/render_pdf.sh path/to/resume.html [path/to/out.pdf]
set -euo pipefail
HTML="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="${2:-${HTML%.html}.pdf}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$CHROME" ] || { echo "Chrome not found at $CHROME" >&2; exit 1; }
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=8000 \
  --print-to-pdf="$OUT" "file://$HTML" 2>&1 | grep -E "written|rror" | grep -v CVDisplayLink || true
[ -s "$OUT" ] || { echo "PDF was not created" >&2; exit 1; }
echo "PDF: $OUT"
pdfinfo "$OUT" | grep -E "^Pages|^Page size"
