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

The expanded English manuscript compiles to 100 A4 pages and includes 71 figures,
26 tables and 14 references. Edit `main.tex` and `chapters/*.tex` directly for
LaTeX revisions. Figure paths resolve to `../figure-assets/`; keep that directory
alongside this project. The build uses pdfLaTeX and BibTeX through `latexmk`.

The `content/*.md` files and `scripts/build-expanded-thesis.py` retain the
assembly source used for this revision. Running that generator overwrites the
LaTeX files, so incorporate direct edits into its source before regenerating.

After compiling, run `scripts/verify-expanded-thesis.py` from the repository root
with Python and `pypdf` to check page count, headings, captions and references.
Generated PDFs and compiler intermediates remain ignored by Git; tracked LaTeX
and figure assets are sufficient to reproduce the PDF.
