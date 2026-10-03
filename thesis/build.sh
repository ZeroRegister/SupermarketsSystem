#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/thesis"
mkdir -p build/chapters "$ROOT/dist"
latexmk -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
cp build/main.pdf "$ROOT/dist/shelfwise-thesis.pdf"
if rg -q 'undefined references|Citation .* undefined|Reference .* undefined' build/main.log;then echo 'Unresolved references in thesis' >&2;exit 1;fi
printf 'PDF: %s\n' "$ROOT/dist/shelfwise-thesis.pdf"
