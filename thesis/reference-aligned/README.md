# Reference-aligned LaTeX thesis

This draft reorganizes the Shelfwise paper around the structure of the supplied Master Thesis example:

1. Work Overview
2. Introduction
3. Object Analysis
4. Assignment of Tasks
5. Design
6. Implementation
7. System Testing
8. Conclusion and References

It follows the reference's chapter logic and front matter while using Shelfwise's own inventory domain, source code, test results, figures, and bibliography. It does not copy the reference thesis's claims or institutional identity.

Build from the repository root with:

```sh
./thesis/reference-aligned/build.sh
```

Output: `dist/shelfwise-reference-aligned-thesis.pdf`. Author, institution, degree, supervisor, and student metadata are placeholders pending the university's actual rules.

The condensed English manuscript compiles to 73 A4 pages and includes 42 figures,
20 tables and 14 references. Field-level schema tables live in
`supplementary/schema-catalogue.md`; the design chapter keeps summary tables only.
Tables of up to 14 data rows are emitted as non-breaking floats, and `a.png+b.png`
in an `@fig` line renders two related diagrams as one paired figure.
It has no running header; centered page numbers remain. Edit `main.tex` and `chapters/*.tex` directly for
LaTeX revisions. Figure paths resolve to `../figure-assets/`; keep that directory
alongside this project. The build uses pdfLaTeX and BibTeX through `latexmk`.

The `content/*.md` files and `scripts/build-expanded-thesis.py` retain the
assembly source used for this revision. Running that generator overwrites the
LaTeX files, so incorporate direct edits into its source before regenerating.

After compiling, run `scripts/verify-expanded-thesis.py` from the repository root
with Python and `pypdf` to check page count, headings, captions and references.
Generated PDFs and compiler intermediates remain ignored by Git; tracked LaTeX
and figure assets are sufficient to reproduce the PDF.

Independent prose, evidence and visual reviews are recorded in `review/`. The
writing-skill comparison is in `review/skills-research.md`. Backend and frontend
results were rerun on 7 October 2026: 45 integration cases and 3 threshold cases
passed. Current UI provenance records 30 captures on 6 October UTC. Figures,
code excerpts, captions and generation sources are synchronized; `scripts/layout_paper_diagrams.py`
preserves explicit edge routes and label positions during regeneration.

The former 80–100-page verification limit was removed: readable figures take
precedence over an artificial page cap. Structural verification checks every
heading, caption and reference plus non-empty data tables; rendered-page review
checks the actual display. University and author metadata still require completion.
