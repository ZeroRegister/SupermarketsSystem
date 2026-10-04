#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/thesis/chinese"
mkdir -p build
latexmk -g -xelatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
cp build/main.pdf "$ROOT/dist/shelfwise-chinese-companion.pdf"
printf 'PDF: %s\n' "$ROOT/dist/shelfwise-chinese-companion.pdf"
