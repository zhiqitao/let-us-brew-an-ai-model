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
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LATEX = os.path.join(HERE, "latex")
ROOT = os.path.dirname(HERE)
FINAL = os.path.join(HERE, "let-us-brew-an-ai-model-v20261001.pdf")
COVER = os.path.join(HERE, "figures", "fig_cover.pdf")


def _build_commit():
    """Build witness for the PDF metadata: git HEAD at build time (the commit
    this PDF was actually built from), falling back to the recorded
    docs/release_manifest.json -> pdf_build_commit. Round-1 QWEN-R2-02 /
    V3 build-stamp integrity: the witness must live in the PDF itself so the
    colophon, the manifest and the artifact can be cross-checked."""
    try:
        h = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True,
                           timeout=30).stdout.strip()
        if re.fullmatch(r"[0-9a-f]{40}", h):
            return h
    except Exception:
        pass
    try:
        import json
        with open(os.path.join(ROOT, "docs", "release_manifest.json"),
                  encoding="utf-8") as f:
            return json.load(f)["pdf_build_commit"]
    except Exception:
        return "unknown-build-commit"


def _merge(cover, interior, final):
    """Merge the full-bleed cover as page 1, preserving the interior's outline and
    setting document metadata. pdfunite discards the outline; a pymupdf merge does not."""
    import pymupdf
    src = pymupdf.open(interior)
    toc = [[lvl, title, page + 1] for (lvl, title, page) in src.get_toc()]
    out = pymupdf.open()
    out.insert_pdf(pymupdf.open(cover))
    out.insert_pdf(src)
    out.set_toc(toc)
    out.set_metadata({
        "title": "Let Us Brew an AI Model",
        "author": "Zhiqi Tao",
        "subject": "What tiny language models can actually learn when given one job",
        "keywords": ("language model, generalization, empirical investigation; "
                     f"BUILD_COMMIT={_build_commit()} "
                     "(pdf_build_commit in docs/release_manifest.json)"),
        "creator": "Hermes / xelatex + pymupdf",
        "producer": "pymupdf",
    })
    try:
        out.set_language("en-US")
    except Exception:
        pass
    out.save(final)
    out.close()
    src.close()


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
    _merge(COVER, interior, FINAL)
    print("final:", FINAL)

    # report page count
    r = subprocess.run(["pdfinfo", FINAL], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("Pages"):
            print(line.strip())


if __name__ == "__main__":
    main()
