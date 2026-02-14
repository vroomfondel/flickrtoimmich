#!/usr/bin/env bash
# Convert Markdown files to PDF using pandoc + pdflatex
#
# Usage:
#   ./repo_scripts/md2pdf.sh <input.md> [output.pdf]
#
# If output is omitted, the PDF is created next to the input file
# with the same basename (e.g. README.md -> README.pdf).
#
# Requirements: pandoc, pdflatex (texlive-latex-base)

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $(basename "$0") <input.md> [output.pdf]"
    exit 1
fi

INPUT="$1"

if [[ ! -f "$INPUT" ]]; then
    echo "Error: File not found: $INPUT"
    exit 1
fi

OUTPUT="${2:-${INPUT%.md}.pdf}"

# Check dependencies
for cmd in pandoc pdflatex; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: '$cmd' not found. Install pandoc and texlive-latex-base."
        exit 1
    fi
done

echo "Converting: $INPUT -> $OUTPUT"

pandoc "$INPUT" \
    -o "$OUTPUT" \
    --pdf-engine=pdflatex \
    -V geometry:margin=2.5cm \
    -V fontsize=11pt \
    -V colorlinks=true \
    -V linkcolor=blue

echo "Done: $OUTPUT ($(du -h "$OUTPUT" | cut -f1))"
