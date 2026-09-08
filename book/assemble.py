#!/usr/bin/env python3
"""Assemble the manuscript chapters into a single compiled book (PDF via pandoc).
The book is written from the measured experiment record; this compiles what exists
into a draft. Missing chapter numbers simply are omitted from the outline for now.
"""
import os, subprocess, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MANU = os.path.join(ROOT, "book", "manuscript")
OUT = os.path.join(ROOT, "book", "let-us-brew-an-ai-model-draft.pdf")

# The order the manuscript should be read. Chapters we have drafted:
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
    "ch12_how_much_brain.md",
    "ch13_same_data_more_diverse_data.md",
    "ch14_the_model_that_memorized_everything.md",
    "ch15_new_words_same_problem.md",
    "ch16_same_pieces_new_combination.md",
    "ch17_redteam_the_judge.md",
    "ch20_what_happens_when_we_teach_it_something_new.md",
    "ch21_the_cost_of_capability.md",
    "ch22_the_capability_map.md",
    "ch23_what_small_models_can_actually_learn.md",
    "ch24_the_model_wasnt_the_point.md",
]

TITLE = """---
title: "Let us brew an AI Model"
subtitle: "What tiny language models can actually learn when given one job"
author: "Zhiqi Research"
---

"""

def main():
    parts = [TITLE]
    for fn in ORDER:
        p = os.path.join(MANU, fn)
        if not os.path.exists(p):
            print(f"[skip] {fn} (missing)")
            continue
        parts.append("\n\n\\newpage\n\n" + open(p, encoding="utf-8").read())
        print(f"[add] {fn}")
    md = os.path.join(ROOT, "book", "_assembled.md")
    open(md, "w", encoding="utf-8").write("".join(parts))
    print(f"assembled -> {md}")

    # Compile with pandoc -> pdf (via a LaTeX engine if available)
    exts = ["--pdf-engine=xelatex", "--pdf-engine=pdflatex", ""]
    done = False
    for ext in exts:
        cmd = ["pandoc", md, "-o", OUT, "-V", "geometry:margin=1in",
               "-V", "fontsize=11pt"] + ([ext] if ext else [])
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print(f"compiled -> {OUT}")
            done = True
            break
    if not done:
        print("pandoc pdf compile failed; checking for alternative.")
        # try markdown->html for a readable artifact
        r = subprocess.run(["pandoc", md, "-o", OS := os.path.join(ROOT, "book", "_assembled.html"),
                            "--standalone"], capture_output=True, text=True)
        print("html fallback exit", r.returncode, "->", OS)

if __name__ == "__main__":
    main()
