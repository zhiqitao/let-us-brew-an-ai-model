#!/usr/bin/env python3
"""Build the reflowable EPUB (Kindle-compatible) edition.

Assembles the manuscript chapters in canonical order into a single clean
markdown file (no LaTeX-only \newpage markers), injects front matter
(copyright + preface), and converts with pandoc --to=epub3 using the SVG cover
already rasterized for ebook display.

The EPUB is reflowable: it does NOT reproduce the print pagination, and figures
render at viewport width rather than at fixed print dimensions.
"""
import os, subprocess

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MANU = os.path.join(ROOT, "book", "manuscript")
BOOK = os.path.join(ROOT, "book")
FIG = os.path.join(BOOK, "figures")

ORDER = [
    "ch01_let_us_brew.md",
    "ch02_what_does_it_mean_to_learn.md",
    "ch03_give_the_model_one_job.md",
    "ch04_build_a_world_we_can_control.md",
    "ch05_build_the_teacher.md",
    "ch06_build_the_judge.md",
    "ch07_build_the_rivals.md",
    "ch08_the_smallest_brain.md",
    "ch09_the_first_brew.md",
    "ch10_does_it_actually_work.md",
    "ch11_how_much_data.md",
    "ch12_how_much_brain.md",
    "ch13_same_data_more_diverse_data.md",
    "ch14_the_model_that_memorized_everything.md",
    "ch15_new_words_same_problem.md",
    "ch16_same_pieces_new_combination.md",
    "ch17_redteam_the_judge.md",
    "ch18_now_give_it_more_python.md",
    "ch19_the_capability_ladder_revisited.md",
    "ch20_what_happens_when_we_teach_it_something_new.md",
    "ch21_the_cost_of_capability.md",
    "ch22_the_capability_map.md",
    "ch23_what_small_models_can_actually_learn.md",
    "ch24_the_model_wasnt_the_point.md",
    "ch25_conclusion.md",
    "appendix_a_generator.md",
    "appendix_b_failure_ledger.md",
    "appendix_c_experiment_registry.md",
    "appendix_d_glossary.md",
]

FRONT = """\
# Preface

This book is a controlled empirical investigation into what a small language model
can actually learn when it is given exactly one narrowly defined, objectively
testable job.

The task: read a natural-language programming request and produce a Python program,
which is then run and checked against hidden tests. This is *not* a claim that tiny
models can reason — it is a measurement of how far a small transformer can go on a
single, narrow mapping before its limits become measurable.

## Who this book is for

If you have ever trained a small model and wondered whether it "really learned"
something or just memorized it, this is for you. No research background is required;
everything is built from first principles with code and measurements.

## What the book claims (and doesn't)

We claim to have *measured*, in one controlled laboratory, where a small model's
capability ends. We do **not** claim to have found a universal ceiling for all small
models under all conditions. Every number in this book is scoped to the architecture,
training schedule, and task we ran.

## How to use the book

Read the body for the argument. Each chapter opens with a concrete image before the
mechanics. Reproducibility details live in the appendices.

---

## Copyright and license

Copyright (c) 2026 Zhiqi Tao. All rights reserved.

**License.** This work is licensed under a custom source-available license. The book
text, diagrams, and figures may be freely read, studied, shared, and redistributed
non-commercially with attribution. The accompanying source code examples and build
scripts may be used, adapted, modified, and reused — including in commercial
projects — provided attribution is retained.

---
"""


def main():
    parts = []
    for fn in ORDER:
        p = os.path.join(MANU, fn)
        if os.path.exists(p):
            txt = open(p, encoding="utf-8").read().strip()
            parts.append(txt)
    body = "\n\n---\n\n".join(parts)
    md = FRONT + "\n" + body + "\n"

    out_md = os.path.join(BOOK, "_epub.md")
    open(out_md, "w", encoding="utf-8").write(md)
    print(f"[epub] assembled -> {out_md}")

    cover = os.path.join(FIG, "fig_cover.png")
    # ensure a raster cover exists for the ebook
    if not os.path.exists(cover):
        r = subprocess.run(
            ["inkscape", os.path.join(FIG, "fig_cover.svg"), "-o", cover,
             "--export-width=1000", "--export-height=1500"],
            capture_output=True, text=True)
        print("[epub] rendered cover:", r.returncode, cover)

    out_epub = os.path.join(BOOK, "let-us-brew-an-ai-model-v20261001.epub")
    cmd = [
        "pandoc", out_md, "-o", out_epub, "--to=epub3",
        "--epub-cover-image", cover,
        "--metadata", "title=Let Us Brew an AI Model",
        "--metadata", "subtitle=What Tiny Language Models Can Actually Learn When Given One Job",
        "--metadata", "author=Zhiqi Tao",
        "--metadata", "lang=en",
        "--metadata", "date=2026-09-11",
        "--resource-path", BOOK,
        "--toc", "--toc-depth=2",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=BOOK)
    print("[epub] pandoc rc:", r.returncode)
    if r.returncode != 0:
        print("[epub] stderr:", r.stderr[-2000:])
    else:
        print("[epub] ->", out_epub)
        print("[epub] size:", os.path.getsize(out_epub))


if __name__ == "__main__":
    main()
