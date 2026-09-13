#!/usr/bin/env python3
"""Build the final book PDF: compile the interior, then prepend the full-bleed cover.

Pipeline:
  1. md_to_latex.py  -> generates book.tex from the manuscript.
  2. xelatex x2      -> compiles the interior (text title page is page 1; the cover
                        graphic is NOT embedded in the interior).
  3. pdfunite        -> prepend book/figures/fig_cover.pdf as page 1, so the book's
                        first page is the full-bleed cover (no margins), per the
                        Round-4 production note.

Run from book/ (or anywhere; paths are resolved relative to this file).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LATEX = os.path.join(HERE, "latex")
ROOT = os.path.dirname(HERE)
FINAL = os.path.join(HERE, "let-us-brew-an-ai-model-v20261001.pdf")
COVER = os.path.join(HERE, "figures", "fig_cover.pdf")


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAILED:", " ".join(cmd))
        print(r.stderr[-1500:])
        sys.exit(1)
    return r


def main():
    print("== step 1: generate book.tex ==")
    run(["python", "md_to_latex.py"], LATEX)

    print("== step 2: compile interior (xelatex x2) ==")
    for aux in ("book.aux", "book.out", "book.toc", "book.lof"):
        p = os.path.join(LATEX, aux)
        if os.path.exists(p):
            os.remove(p)
    for _ in (1, 2):
        run(["xelatex", "-interaction=nonstopmode", "book.tex"], LATEX)

    print("== step 3: merge full-bleed cover as page 1 ==")
    interior = os.path.join(LATEX, "book.pdf")
    run(["pdfunite", COVER, interior, FINAL], HERE)
    print("final:", FINAL)

    # report page count
    r = subprocess.run(["pdfinfo", FINAL], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("Pages"):
            print(line.strip())


if __name__ == "__main__":
    main()
