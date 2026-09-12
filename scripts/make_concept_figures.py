#!/usr/bin/env python3
"""Generate CONCEPTUAL / ILLUSTRATIVE diagrams for the book (the "how it works"
architecture figures that complement the measured-data charts in make_figures.py).

These are reproducible vector diagrams rendered to PNG in a single consistent
visual language (rounded boxes, semantic color, hand-muted palette) that matches
the book's typeset graphs. Every label is plain text drawn directly -- no image
model, so every word is byte-correct.

Run: python scripts/make_concept_figures.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIG = os.path.join(ROOT, "book", "figures")
os.makedirs(FIG, exist_ok=True)

# ---- shared visual language (matches make_figures.py + book palette) ----
INK      = "#2b2b2b"
BLUE     = "#4C72B0"   # input / structure
GREEN    = "#55A868"   # computation / flow
ORANGE   = "#DD8452"   # learner / model
PURPLE   = "#8172B2"   # judge / decision
RED      = "#C44E52"   # rejection / bottleneck / annotation
GREY     = "#c7c7c7"
PAPER    = "#fdfbf7"


def new_fig(w=9.0, h=5.4):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, label, fc=BLUE, ec=None, fs=10, tc="white", rounded=True,
        bold=False, lw=1.6):
    ec = ec or "#00000000"
    style = "round,pad=0.02,rounding_size=2.2" if rounded else "square,pad=0.02"
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style,
                                fc=fc, ec=ec, lw=lw, mutation_aspect=1.0))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, color=tc, wrap=True,
            fontweight="bold" if bold else "normal")
    return (x, y, w, h)


def arrow(ax, x1, y1, x2, y2, color=INK, lw=1.6, style="-|>", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 color=color, lw=lw, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}",
                                 mutation_scale=14))


def note(ax, x, y, text, color=INK, fs=9, ha="left", wrap=True):
    ax.text(x, y, text, ha=ha, va="top", fontsize=fs, color=color,
            wrap=wrap, style="italic")


def save(fig, name):
    p = os.path.join(FIG, name)
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)
    return p


# =========================================================================
# 1. THE APPARATUS (ch03) — teacher -> dataset -> student -> judge -> verdict,
#    with the world as the enclosing boundary and both gates annotated.
# =========================================================================
def fig_apparatus():
    fig, ax = new_fig()
    # world boundary
    ax.add_patch(FancyBboxPatch((6, 8), 88, 80, boxstyle="round,pad=0.02,rounding_size=3",
                                fc="#fbfaf6", ec=GREY, lw=1.2, linestyle="--"))
    ax.text(50, 90, "THE WORLD — a bounded universe we control", ha="center",
            va="center", fontsize=11, color=INK, fontweight="bold")

    # one clean horizontal chain of five stages
    xs = [11, 31, 51, 71, 88]
    w = 15
    y, h = 50, 16
    box(ax, xs[0], y, w, h, "TEACHER\n(semantic\ngenerator)", fc=GREEN, fs=8.5)
    box(ax, xs[1], y, w, h, "DATASET\n(task + program\n+ tests)", fc=BLUE, fs=8.5)
    box(ax, xs[2], y, w, h, "STUDENT\n(0.9M model)", fc=ORANGE, fs=8.5, tc="white")
    box(ax, xs[3], y, w, h, "JUDGE\n(4-stage)", fc=PURPLE, fs=8.5)
    box(ax, xs[4], y, w - 4, h, "VERDICT\npass/fail", fc=PURPLE, fs=8.5)
    for i in range(4):
        arrow(ax, xs[i] + w, y + h / 2, xs[i + 1], y + h / 2)

    # gate annotations in the clear upper band
    note(ax, 10, 76, "GATE B (input): an off-scope request is\nrejected before the model sees it.", fs=8, color=RED)
    note(ax, 70, 76, "GATE A (output): a program outside\nthe whitelist is refused before running.", fs=8, color=RED)

    # what each stage produces / what the judge compares, in the lower band
    note(ax, 8, 42, "one semantic record fans out into the\nprogram, the NL task, and the hidden tests.", fs=8, color=GREEN)
    note(ax, 52, 42, "the judge compares the model's program\nagainst the reference on hidden tests.", fs=8, color=PURPLE)
    box(ax, 26, 8, 48, 12, "the model is the instrument;\nthe experiment is the subject", fc="#fbfaf6",
        ec=INK, fs=8.5, tc=INK)
    save(fig, "fig_apparatus.png")


# =========================================================================
# 2. THE TWO GATES (ch04) — Gate B on the way in, Gate A on the way out.
# =========================================================================
def fig_two_gates():
    fig, ax = new_fig()
    ax.text(50, 95, "TWO GATES: neither lives inside the model", ha="center",
            va="center", fontsize=11, fontweight="bold", color=INK)

    # incoming request
    box(ax, 4, 44, 20, 16, "REQUEST\n(natural language)", fc=BLUE, fs=9)
    box(ax, 30, 44, 16, 16, "GATE B\ninput\nvalidator", fc=RED, fs=8.5)
    box(ax, 52, 44, 18, 16, "MODEL", fc=ORANGE, fs=10, bold=True)
    box(ax, 76, 44, 16, 16, "GATE A\noutput\nsandbox", fc=RED, fs=8.5)
    box(ax, 3, 12, 24, 14, "REJECTED\nbefore the model\nis consulted", fc="#f6dede", ec=RED, fs=8, tc=RED)

    arrow(ax, 24, 52, 30, 52, color=INK)
    arrow(ax, 46, 52, 52, 52, color=INK)
    arrow(ax, 70, 52, 76, 52, color=INK)
    note(ax, 33, 66, "is this request one of the\ndesigned tasks?", fs=8, color=RED)
    note(ax, 77, 66, "is this program inside\nthe whitelist?", fs=8, color=RED)
    arrow(ax, 13, 44, 13, 26, color=RED, ls="--")
    arrow(ax, 8, 18, 8, 22, color=RED)
    note(ax, 28, 20, "off-scope → decline\n(never reaches the model)", fs=7.5, color=RED)
    note(ax, 72, 20, "disallowed construct →\nprogram refused before running", fs=7.5, color=RED)
    save(fig, "fig_two_gates.png")


# =========================================================================
# 3. THE TEACHER (ch05) — one semantic record fans out into the artefacts.
# =========================================================================
def fig_teacher():
    fig, ax = new_fig()
    ax.text(50, 95, "THE TEACHER: one semantic record, three artefacts",
            ha="center", va="center", fontsize=11, fontweight="bold", color=INK)
    box(ax, 34, 62, 32, 20, "SEMANTIC RECORD\nop=add, ins=2 nums,\naggr=sum", fc=GREEN, fs=9)
    box(ax, 8, 28, 26, 20, "REFERENCE\nPROGRAM\n(the ground truth)", fc=GREEN, fs=8.5)
    box(ax, 37, 28, 26, 20, "NL TASK\n(what the model\nreads)", fc=BLUE, fs=8.5)
    box(ax, 66, 28, 26, 20, "HIDDEN TESTS\n(input/expected\npairs)", fc=PURPLE, fs=8.5)
    for dx in (21, 50, 79):
        arrow(ax, 50, 62, dx, 48)
    note(ax, 12, 20, "one correct\nimplementation", fs=7.5, color=GREEN)
    note(ax, 40, 20, "the instruction, in\nthe teacher's phrasing", fs=7.5, color=BLUE)
    note(ax, 70, 20, "oracle outputs;\nchecked independently", fs=7.5, color=PURPLE)
    # leakage note
    note(ax, 8, 88, "semantic-first: the program, task,\nand tests all derive from ONE record,\nreducing drift (renderer bugs can still occur)", fs=8, color=GREEN)
    save(fig, "fig_teacher.png")


# =========================================================================
# 4. THE JUDGE (ch06) — the four-stage funnel.
# =========================================================================
def fig_judge():
    fig, ax = new_fig()
    ax.text(50, 95, "THE JUDGE: a four-stage funnel", ha="center",
            va="center", fontsize=11, fontweight="bold", color=INK)
    stages = [
        (70, "1. SYNTAX\nparses?", PURPLE),
        (50, "2. AST / CAPABILITY\nwhitelisted subset?", PURPLE),
        (30, "3. EXECUTION\nruns cleanly?", PURPLE),
        (10, "4. SEMANTIC\nmatches expected?", ORANGE),
    ]
    # put the stage column on the LEFT half, notes in a clean right column
    for y, lab, c in stages:
        box(ax, 20, y, 38, 14, lab, fc=c, fs=8.5)
    # short clean arrows in the gap between boxes
    for i in range(3):
        y = 70 - (i * 20)          # top box bottom
        arrow(ax, 39, y + 4, 39, y - 2)  # down into next box
    note(ax, 12, 86, "any 'no' → whole program\nrejected, then zero", fs=8, color=RED)
    note(ax, 63, 55, "short-circuit:\nfail at any stage", fs=8, color=RED)
    box(ax, 63, 14, 34, 20,
        "Only a program that clears all\nfour gets credit. One number\nwould hide which stage failed.",
        fc="#fbfaf6", ec=INK, fs=8.5, tc=INK)
    save(fig, "fig_judge.png")


# =========================================================================
# 5. THE CAPABILITY LADDER (ch02) — four levels of trust.
# =========================================================================
def fig_ladder():
    fig, ax = new_fig()
    ax.text(50, 95, "THE CAPABILITY LADDER", ha="center", va="center",
            fontsize=11, fontweight="bold", color=INK)
    ax.text(50, 89, "four levels of how much we should trust a result", ha="center",
            va="center", fontsize=9, color=INK, style="italic")
    levels = [
        (16, "LEVEL 1\nMemorization\n'probably just\nremembering'", RED),
        (34, "LEVEL 2\nSame task,\nnew examples", ORANGE),
        (52, "LEVEL 3\nSame problem,\ndifferent surface", GREEN),
        (70, "LEVEL 4\nNew combination\n'genuinely\ncombined'", BLUE),
    ]
    for y, lab, c in levels:
        box(ax, 14, y, 72, 15, lab, fc=c, fs=8.2)
    # ascending arrow to the RIGHT of the ladder, clear of the boxes
    arrow(ax, 90, 16, 90, 84, color=INK)
    ax.text(93, 50, "more trust", fontsize=8, rotation=90, va="center", color=INK)
    note(ax, 14, 4, "we never mash these into one number: 90% on familiar + 0% on\nreworded is NOT generalization — it memorized the phrasing.", fs=8.5, color=RED)
    save(fig, "fig_ladder.png")


# =========================================================================
# 6. THE ONE-JOB CONTRACT (ch03) — the task: NL spec -> program -> hidden tests.
# =========================================================================
def fig_task():
    fig, ax = new_fig()
    ax.text(50, 95, "THE ONE JOB", ha="center", va="center", fontsize=11,
            fontweight="bold", color=INK)
    box(ax, 6, 58, 28, 22, "NL SPEC\n'return the sum of\ntwo numbers'", fc=BLUE, fs=8.5)
    box(ax, 40, 58, 24, 22, "PROGRAM\n(def solve)", fc=ORANGE, fs=9)
    box(ax, 70, 58, 24, 22, "HIDDEN TESTS\n(10 cases)", fc=PURPLE, fs=8.5)
    arrow(ax, 34, 68, 40, 68)
    arrow(ax, 64, 68, 70, 68)
    # constraints row
    box(ax, 6, 24, 88, 16,
        "PURE FUNCTION · NO I/O · NO NETWORK · NO RANDOM · AST-WHITELISTED",
        fc="#fbfaf6", ec=INK, fs=8.5, tc=INK)
    note(ax, 6, 10, "every task is synthetic and self-verifying, so we can generate as much\ncontrolled data as we want and grade every program exactly.", fs=8.5, color=INK)
    save(fig, "fig_task.png")


# =========================================================================
# 7. THE RIVALS (ch07) — model vs template vs retrieval baselines.
# =========================================================================
def fig_rivals():
    fig, ax = new_fig()
    ax.text(50, 95, "THE RIVALS: baselines keep us honest", ha="center",
            va="center", fontsize=11, fontweight="bold", color=INK)
    box(ax, 6, 62, 28, 18, "TEMPLATE\n'if task==add:\nreturn a+b'", fc=GREY, fs=8, tc=INK)
    box(ax, 38, 62, 26, 18, "RETRIEVAL\nnearest-neighbour\ncopy", fc=GREY, fs=8, tc=INK)
    box(ax, 70, 62, 24, 18, "OUR MODEL\n0.88M", fc=ORANGE, fs=9)
    note(ax, 6, 48, "a fixed hand-written\npattern. A sanity floor.", fs=8, color=INK)
    note(ax, 39, 48, "copies the closest\nmemory. A sanity check.", fs=8, color=INK)
    note(ax, 71, 48, "the actual question:\ndoes it clear both?", fs=8, color=INK)
    box(ax, 6, 14, 88, 18,
        "The baselines are sanity checks, not a score ceiling. A result is truthful\nif we know which baseline already solves it and whether the model adds anything.",
        fc="#fbfaf6", ec=INK, fs=9, tc=INK)
    save(fig, "fig_rivals.png")


# =========================================================================
# 8. THE SMALLEST BRAIN (ch08) — tokens -> embedding -> transformer -> output.
# =========================================================================
def fig_brain():
    fig, ax = new_fig()
    ax.text(50, 95, "THE SMALLEST BRAIN: 0.88M parameters", ha="center",
            va="center", fontsize=11, fontweight="bold", color=INK)
    box(ax, 5, 62, 18, 18, "TOKENS\n(291 vocab)", fc=BLUE, fs=8)
    box(ax, 30, 62, 16, 18, "EMBED\n+pos", fc=BLUE, fs=8)
    box(ax, 52, 62, 16, 18, "TRANSFORMER\nblocks\n(attention)", fc=ORANGE, fs=8)
    box(ax, 74, 62, 18, 18, "OUTPUT\nlogits → token", fc=GREEN, fs=8)
    arrow(ax, 23, 71, 30, 71)
    arrow(ax, 46, 71, 52, 71)
    arrow(ax, 68, 71, 74, 71)
    note(ax, 5, 50, "a tiny decoder-only\nGPT. Small enough to\ntrain on one CPU core,\nbut with real attention.", fs=8, color=INK)
    note(ax, 55, 50, "everything is measured:\nthe same architecture,\njust wider / deeper.", fs=8, color=INK)
    box(ax, 5, 18, 88, 18, "This is the instrument. The experiment is the subject — the book\nis about what the model learns, not about how big it is.",
        fc="#fbfaf6", ec=INK, fs=9, tc=INK)
    save(fig, "fig_brain.png")


# =========================================================================
# 9. THE BREW LOOP (ch09) — the train / measure cycle that runs the book.
# =========================================================================
def fig_brew():
    fig, ax = new_fig()
    ax.text(50, 95, "THE BREW LOOP", ha="center", va="center", fontsize=11,
            fontweight="bold", color=INK)
    box(ax, 10, 68, 24, 16, "GENERATE DATA\n(semantic-first)", fc=GREEN, fs=8.5)
    box(ax, 58, 68, 24, 16, "TRAIN\n(full pass)", fc=ORANGE, fs=9)
    box(ax, 58, 38, 24, 16, "MEASURE\n(judge on hidden\n+ reword + new)", fc=PURPLE, fs=8.5)
    box(ax, 10, 38, 24, 16, "LEARN FROM\nTHE LOOP", fc=BLUE, fs=8.5)
    arrow(ax, 34, 76, 58, 76)                 # generate -> train
    arrow(ax, 70, 68, 70, 54)                 # train -> measure
    arrow(ax, 58, 46, 34, 46)                 # measure -> learn
    arrow(ax, 22, 54, 22, 68, style="-|>", color=INK)  # learn -> generate (close the loop)
    note(ax, 25, 30, "each pass feeds the next: what\nwe measure shapes what we generate", fs=8, color=INK, ha="center")
    note(ax, 10, 14, "the book is written discipline-first: measure in-distribution,\nthen push each boundary one at a time, and never mash levels together.",
        fs=8, color=INK)
    save(fig, "fig_brew.png")


# =========================================================================
# 10. THE CAPABILITY MAP (ch22) — the 2-axis landscape of what it learned.
# =========================================================================
def fig_capability_map():
    """The EVIDENCE MATRIX (D06): replaces the old schematic region map.

    Rows = specific training conditions / checkpoints; columns = what was actually
    measured. Every cell is a measured number or an explicit "not tested" (NT).
    This is a readable inventory of what was measured, not a schematic region that
    implies an unmeasured extent of capability.
    """
    import numpy as np
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    ax.text(50, 96, "THE EVIDENCE MATRIX  (what was measured, run by run)",
            ha="center", va="center", fontsize=10.5, fontweight="bold", color=INK)

    rows = [
        # name, familiar-accuracy, new-IDs, excluded-family, cover-surface, held-out-compose, final-A/B
        ("Stage 1 pilot (0.88M)",        "0.897", "0.350", "0.000",  "-",      "0.000", "NT"),
        ("6.5M",                         "0.897", "-",      "-",      "-",      "0.000", "NT"),
        ("10.2M",                        "0.773", "-",      "-",      "-",      "0.000", "NT"),
        ("29.3M",                        "0.897", "-",      "-",      "-",      "0.000", "NT"),
        ("High-diversity (same count)",  "1.000", "-",      "NT",     "1.000",  "NT",    "NT"),
        ("Sequential A then B",          "-",     "-",      "-",      "-",      "NT",    "A 0.000 / B 0.889"),
        ("Joint A+B",                    "-",     "-",      "-",      "-",      "NT",    "A 1.000 / B 0.889"),
    ]
    cols = ["run / condition", "familiar\nprompt", "new\nidentifiers",
            "excluded\nwording", "covered\nalternate\nsurface",
            "held-out\ncomposite", "final A / B\ntask accuracy"]
    nrow, ncol = len(rows), len(cols)
    top, left, cw, rh = 82, 2, 13.6, 9.0
    # header
    ax.text(left, top+4, "NT = not tested (not run or not applicable); '-' = not measured for this run",
            fontsize=6.6, color=RED, va="bottom")
    for c in range(ncol):
        x = left + c*cw
        ax.add_patch(FancyBboxPatch((x, top-6), cw-0.6, 7, boxstyle="round,pad=0.01,rounding_size=0.8",
                                    fc="#eef1f5", ec=INK, lw=0.6))
        ax.text(x+(cw-0.6)/2, top-6+3.5, cols[c], ha="center", va="center", fontsize=6.6, color=INK, fontweight="bold")
    for r in range(nrow):
        y = top - 6 - 7 - rh*(r+1)
        name, vals = rows[r][0], rows[r][1:]
        ax.add_patch(FancyBboxPatch((left, y), cw-0.6, rh*0.9, boxstyle="round,pad=0.01,rounding_size=0.8",
                                    fc="#fdfbf7", ec=GREY, lw=0.6))
        ax.text(left+(cw-0.6)/2, y+rh*0.45, name, ha="center", va="center", fontsize=6.4, color=INK, fontweight="bold")
        for c in range(1, ncol):
            v = vals[c-1]
            x = left + c*cw
            fc = "#f6faf6" if v in ("1.000","0.897","0.773","A 1.000 / B 0.889") else ("#fdf3f3" if (v and "0.000" in v) else "#ffffff")
            ax.add_patch(FancyBboxPatch((x, y), cw-0.6, rh*0.9, boxstyle="round,pad=0.01,rounding_size=0.8",
                                        fc=fc, ec=GREY, lw=0.4))
            if v == "NT":
                txt, tc = "NT", RED
            elif v.startswith("0.000") or v == "0.000":
                txt, tc = v, RED
            elif v == "-":
                txt, tc = "-", "#888888"
            else:
                txt, tc = v, "#2b8a3e"
            ax.text(x+(cw-0.6)/2, y+rh*0.45, txt, ha="center", va="center", fontsize=6.3, color=tc)
    note(ax, 3, 4, "Green = measured strong result. Red = measured zero. NT = not tested. " +
          "The high-diversity 1.000 is *coverage* of surfaces in its training family, not transfer to an excluded wording family.",
         fs=7.0, color=INK)
    save(fig, "fig_capability_map.png")


if __name__ == "__main__":
    fig_apparatus()
    fig_two_gates()
    fig_teacher()
    fig_judge()
    fig_ladder()
    fig_task()
    fig_rivals()
    fig_brain()
    fig_brew()
    fig_capability_map()
