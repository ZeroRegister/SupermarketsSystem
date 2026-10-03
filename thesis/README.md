# English thesis build

This is a multi-file, offline-compilable LaTeX project. It uses the standard `report` class and a locally authored MIT-licensed layout, not an institution-specific template. Compiler: pdfLaTeX through latexmk. Tested with TeX Live 2025.

Run `./thesis/build.sh` from the repository root. The final PDF is `dist/shelfwise-thesis.pdf`; compiler intermediates and logs live under ignored `thesis/build/`. On Ubuntu, `latexmk texlive-latex-extra texlive-fonts-recommended` provides the required packages. The committed PNG/PDF figures mean compilation does not need diagram tools or browser access.

Front-matter fields explicitly remain placeholders. Check the institution's actual requirements before submission. The page count is a planning target; the text reports the implementation and recorded local evidence without a field-study or production claim.

Editable diagrams are Graphviz `.dot` with SVG/PNG exports. `scripts/generate_diagrams.py` rebuilds them (Graphviz required). `scripts/browser-smoke.mjs` captures implemented screens (Playwright and a running application required). `scripts/plot-evaluation.py` produces the quantitative chart/table from raw benchmark JSON. No image is sourced from a stock-photo service.

The design choice records are in `docs/decisions/001-baseline.md`. Bibliography entries link to verified primary sources and were accessed on 2026-10-04. No online service is required to compile the document once its source and figures are checked out.
