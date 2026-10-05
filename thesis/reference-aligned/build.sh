#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/thesis/reference-aligned"
mkdir -p build/chapters "$ROOT/dist"
BIBINPUTS="$ROOT/thesis:" latexmk -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
cp build/main.pdf "$ROOT/dist/shelfwise-reference-aligned-thesis.pdf"
printf 'PDF: %s\n' "$ROOT/dist/shelfwise-reference-aligned-thesis.pdf"
