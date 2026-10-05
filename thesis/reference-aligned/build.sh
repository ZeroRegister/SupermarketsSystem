#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/thesis/reference-aligned"
mkdir -p build/chapters "$ROOT/dist"
BIBINPUTS="$ROOT/thesis/reference-aligned:$ROOT/thesis:" latexmk -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
if rg -q 'undefined references|Citation .* undefined|Reference .* undefined' build/main.log;then echo 'Unresolved references in thesis' >&2;exit 1;fi
cp build/main.pdf "$ROOT/dist/shelfwise-reference-aligned-thesis.pdf"
printf 'PDF: %s\n' "$ROOT/dist/shelfwise-reference-aligned-thesis.pdf"
