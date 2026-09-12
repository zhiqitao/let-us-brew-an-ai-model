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
    """Figure 4.1 -- the laboratory, two clean lanes inside the world boundary."""
    fig, ax = new_fig(w=9.6, h=5.8)
    ax.add_patch(FancyBboxPatch((4, 4), 92, 88, boxstyle="round,pad=0.02,rounding_size=3",
                                fc="#fbfaf6", ec=GREY, lw=1.2, linestyle="--"))
    ax.text(50, 90, "THE WORLD — a bounded universe we control", ha="center",
            va="center", fontsize=10.5, color=INK, fontweight="bold")

    # gate notes in their own clear band (above the lanes, no flow boxes there)
    box(ax, 6, 78, 44, 9, "GATE B (input): an off-scope request is rejected\nbefore the model sees it.", fc="#f6dede", ec=RED, fs=6.8, tc=RED)
    box(ax, 56, 78, 38, 9, "GATE A (output): a program outside the whitelist\nis refused before running.", fc="#f6dede", ec=RED, fs=6.8, tc=RED)

    # TRAINING lane
    ax.text(6, 73, "TRAINING", ha="left", fontsize=8, fontweight="bold", color=BLUE)
    box(ax, 26, 68, 20, 11, "TEACHER\nsemantic\nrecord", fc=GREEN, fs=8)
    box(ax, 52, 68, 24, 11, "PROMPT +\nREFERENCE", fc=BLUE, fs=8)
    box(ax, 80, 68, 16, 11, "STUDENT\n0.9M", fc=ORANGE, fs=8, tc="white")
    arrow(ax, 46, 73, 52, 73)
    arrow(ax, 76, 73, 80, 73)
    ax.text(64, 64, "→ training only", ha="center", fontsize=6.8, color=BLUE, style="italic")

    # EVALUATION lane
    ax.text(6, 55, "EVALUATION", ha="left", fontsize=8, fontweight="bold", color=PURPLE)
    box(ax, 26, 48, 20, 11, "NL SPEC\n(new)", fc=BLUE, fs=8)
    box(ax, 52, 48, 24, 11, "STUDENT\ngenerates", fc=ORANGE, fs=8, tc="white")
    box(ax, 80, 48, 16, 11, "JUDGE", fc=PURPLE, fs=8)
    arrow(ax, 46, 53, 52, 53)
    arrow(ax, 76, 53, 80, 53)

    # hidden tests box below judge, feeding up
    box(ax, 66, 26, 30, 14, "HIDDEN TESTS\n(evaluator-only)", fc=PURPLE, fs=8)
    arrow(ax, 88, 40, 88, 48)   # up into judge (at x=88, judge spans 80-96)

    # verdict below judge's right
    ax.text(88, 22, "→ VERDICT\npass / fail", ha="center", fontsize=7, color=PURPLE, style="italic")

    # bottom: explanation caption on the LEFT half, call-out on the RIGHT half
    box(ax, 6, 8, 50, 12,
        "Only the prompt + reference enter training; the hidden tests\ngo to the judge, never to the model. The judge runs the model's\ngenerated program against those tests.",
        fc="#fbfaf6", ec=PURPLE, fs=7.2, tc=INK)
    box(ax, 60, 8, 34, 12, "the model is the instrument;\nthe experiment is the subject",
        fc="#fbfaf6", ec=INK, fs=8, tc=INK)
    save(fig, "fig_apparatus.png")

def fig_two_gates():
    fig, ax = new_fig()
    ax.text(50, 95, "TWO GATES: neither lives inside the model", ha="center",
            va="center", fontsize=11, fontweight="bold", color=INK)

    # incoming request
    box(ax, 4, 44, 20, 16, "REQUEST\n(natural language)", fc=BLUE, fs=9)
    box(ax, 30, 44, 16, 16, "GATE B\ninput\nvalidator", fc=RED, fs=8.5)
    box(ax, 52, 44, 18, 16, "MODEL", fc=ORANGE, fs=10, bold=True)
    box(ax, 76, 44, 16, 16, "GATE A\noutput\nsandbox", fc=RED, fs=8.5)

    arrow(ax, 24, 52, 30, 52, color=INK)
    arrow(ax, 46, 52, 52, 52, color=INK)
    arrow(ax, 70, 52, 76, 52, color=INK)
    # rejection branches at GATE B (not at the request), and the accepted path
    # continues through the gates. Gate A rejection branches at Gate A.
    arrow(ax, 38, 44, 38, 30, color=RED)          # Gate B rejection drops down
    arrow(ax, 84, 44, 84, 30, color=RED)          # Gate A rejection drops down
    box(ax, 28, 12, 20, 14, "REJECTED at Gate B\n(before the model\nis consulted)", fc="#f6dede", ec=RED, fs=7.5, tc=RED)
    box(ax, 74, 12, 20, 14, "REJECTED at Gate A\n(program refused\nbefore running)", fc="#f6dede", ec=RED, fs=7.5, tc=RED)
    note(ax, 28, 70, "is this request one of the\ndesigned tasks? (yes/no)", fs=8, color=RED)
    note(ax, 74, 70, "is this program inside\nthe whitelist? (yes/no)", fs=8, color=RED)
    note(ax, 50, 30, "off-scope request → declined\nbefore it reaches the model", fs=7, color=RED)
    note(ax, 50, 22, "disallowed construct → program\nrefused before it runs", fs=7, color=RED)
    save(fig, "fig_two_gates.png")


# =========================================================================
# 3. THE TEACHER (ch05) — one semantic record fans out into the artefacts.
# =========================================================================
def fig_teacher():
    """Figure 5.1 -- one semantic record fans into three artefacts.

    The three artefacts are the reference program, the NL task, and the hidden
    tests. The note about reducing drift is placed in a clear call-out, fully
    contained, and states that a shared record reduces drift but does not make
    disagreement impossible (renderer bugs can still occur).
    """
    fig, ax = new_fig(w=9.0, h=5.0)
    ax.text(50, 95, "THE TEACHER: one semantic record, three artefacts",
            ha="center", va="center", fontsize=10.5, fontweight="bold", color=INK)
    # semantic record box
    box(ax, 34, 66, 32, 16, "SEMANTIC RECORD\nop=add, ins=2 nums,\naggr=sum", fc=GREEN, fs=8.5)
    for dx in (21, 50, 79):
        arrow(ax, 50, 66, dx, 52)
    # three artefacts
    box(ax, 8, 34, 26, 16, "REFERENCE\nPROGRAM\n(ground truth)", fc=GREEN, fs=8.5)
    box(ax, 37, 34, 26, 16, "NL TASK\n(what the model\nreads)", fc=BLUE, fs=8.5)
    box(ax, 66, 34, 26, 16, "HIDDEN TESTS\n(input/expected\npairs)", fc=PURPLE, fs=8.5)
    note(ax, 10, 30, "one correct\nimplementation", fs=7.5, color=GREEN, ha="center")
    note(ax, 50, 30, "the instruction, in\nthe teacher's phrasing", fs=7.5, color=BLUE, ha="center")
    note(ax, 79, 30, "oracle outputs;\nchecked independently", fs=7.5, color=PURPLE, ha="center")
    # drift note in a clear call-out box at the bottom (no overlap, fully contained)
    box(ax, 6, 6, 88, 16,
        "Semantic-first: the program, task, and tests all derive from ONE record.\n"
        "This reduces drift, but does not make disagreement impossible — renderer\n"
        "bugs or shared assumptions can still make all three consistently wrong.",
        fc="#fbfaf6", ec=GREEN, fs=8, tc=INK)
    save(fig, "fig_teacher.png")

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
    # put the stage column on the LEFT half, explicit YES/NO branches on the right.
    for y, lab, c in stages:
        box(ax, 20, y, 38, 14, lab, fc=c, fs=8.5)
        # "NO -> reject" branch off the right of every stage
        arrow(ax, 58, y + 7, 66, y + 7, color=RED)
        box(ax, 68, y + 2, 24, 10, "NO\n→ rejected\n(score 0)", fc="#f6dede", ec=RED, fs=7, tc=RED)
        # "YES" tag between stages (except after the last)
        if y > 10:
            ax.text(39, y - 1.5, "yes", ha="center", fontsize=6.5, color=GREEN, style="italic")
    # short clean arrows in the gap between boxes
    for i in range(3):
        y = 70 - (i * 20)
        arrow(ax, 39, y + 4, 39, y - 2)
    note(ax, 74, 90, "any 'no' → whole program\nrejected, then zero", fs=8, color=RED)
    box(ax, 30, 2, 46, 7,
        "Only a program that clears all four gets credit.\nOne number would hide which stage failed.",
        fc="#fbfaf6", ec=INK, fs=7.5, tc=INK)
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
    """D01 -- WHO SEES WHAT (ch03): the model generates source; Python executes it;
    hidden tests are evaluator-only. Two lanes so the model / execution / tests are
    impossible to conflate."""
    fig, ax = new_fig(w=9.2, h=5.2)
    ax.text(50, 96, "WHO SEES WHAT: the model generates code, Python runs it", ha="center",
            va="center", fontsize=10.5, fontweight="bold", color=INK)
    # TRAINING lane (top)
    ax.text(8, 84, "TRAINING lane", ha="left", fontsize=8, fontweight="bold", color=BLUE)
    box(ax, 6, 66, 24, 14, "NL SPEC + REFERENCE\n(the teacher's pair)", fc=BLUE, fs=8)
    box(ax, 38, 66, 24, 14, "MODEL\n(0.9M, trained)", fc=ORANGE, fs=8, tc="white")
    arrow(ax, 30, 73, 38, 73)
    note(ax, 38, 60, "the model learns a mapping\nfrom request to program text", fs=7, color=ORANGE)

    # EVALUATION lane (bottom)
    ax.text(8, 50, "EVALUATION lane", ha="left", fontsize=8, fontweight="bold", color=PURPLE)
    box(ax, 6, 34, 24, 14, "NL SPEC\n(new, unseen)", fc=BLUE, fs=8)
    box(ax, 38, 34, 24, 14, "MODEL\n(generates)", fc=ORANGE, fs=8, tc="white")
    box(ax, 70, 34, 24, 14, "PYTHON\n(executes the program)", fc=GREEN, fs=8)
    box(ax, 6, 12, 44, 14, "HIDDEN TESTS\n(evaluator-only: inputs + expected)", fc=PURPLE, fs=8)
    box(ax, 70, 12, 24, 14, "JUDGE\n(compares outputs)", fc=PURPLE, fs=8)
    arrow(ax, 30, 41, 38, 41)
    arrow(ax, 62, 41, 70, 41)
    arrow(ax, 82, 34, 82, 26)
    arrow(ax, 50, 19, 70, 19)
    note(ax, 14, 6, "The model emits source code; Python executes it. The hidden tests\nare evaluator-only artifacts -- they never enter training. Passing establishes\nagreement on these tests, not correctness on every possible input.",
         fs=7.2, color=INK)
    constraint = box
    box(ax, 6, 90, 88, 0, "", fc="none", ec="none", fs=8)
    # constraints strip
    box(ax, 6, 88, 88, 6,
        "PURE FUNCTION · NO I/O · NO NETWORK · NO RANDOM · AST-WHITELISTED",
        fc="#fbfaf6", ec=INK, fs=7.5, tc=INK)
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


def fig_continual_timelines():
    """D05 -- SEQUENTIAL, JOINT, AND REPLAY ARE DIFFERENT EXPERIMENTS (ch20).

    Three horizontal timelines. Solid outline = measured regime; dashed = a true
    replay-after-A-first design, which we did NOT run. Shows that the book's
    'replay/mixed' condition is actually JOINT training.
    """
    fig, ax = new_fig(w=9.2, h=5.2)
    ax.text(50, 96, "SEQUENTIAL VS JOINT VS REPLAY: three different designs", ha="center",
            va="center", fontsize=10, fontweight="bold", color=INK)
    labels = ["1. Sequential  (measured)", "2. Joint  (measured, called 'replay' in ch20)", "3. True replay-after-A  (not run)"]
    for row, (lab, style) in enumerate(zip(labels, ["solid", "solid", "dashed"])):
        y = 78 - row*24
        ax.text(2, y+4, lab, ha="left", fontsize=8, color=INK)
        # timeline bar
        ax.add_patch(FancyBboxPatch((30, y), 62, 6, boxstyle="round,pad=0.02,rounding_size=1",
                                    fc="#eef1f5", ec=INK, lw=1.0, linestyle="--" if style=="dashed" else "-"))
        # A and B segments
        seg = (30, 30, 30)  # x start widths for A, B
        if row == 0:   # sequential: full A then full B
            ax.add_patch(FancyBboxPatch((30, y+1), 31, 4, fc=BLUE, ec=BLUE, lw=0.5))
            ax.add_patch(FancyBboxPatch((61, y+1), 31, 4, fc=GREEN, ec=GREEN, lw=0.5))
            ax.text(45.5, y+3, "A", ha="center", va="center", fontsize=7, color="white")
            ax.text(76.5, y+3, "B", ha="center", va="center", fontsize=7, color="white")
        elif row == 1: # joint: A and B interleaved
            ax.add_patch(FancyBboxPatch((30, y+1), 62, 4, fc=GREY, ec=GREY, lw=0.5))
            ax.text(61, y+3, "A and B interleaved together from the start", ha="center", va="center", fontsize=6.5, color=INK)
        else:          # true replay (not run)
            ax.add_patch(FancyBboxPatch((30, y+1), 31, 4, fc=BLUE, ec=BLUE, lw=0.5))
            ax.add_patch(FancyBboxPatch((44, y+1), 48, 4, fc=GREEN, ec=GREEN, lw=0.5))
            ax.text(45.5, y+3, "A", ha="center", va="center", fontsize=7, color="white")
            ax.text(68, y+3, "B (+ A replay)", ha="center", va="center", fontsize=6, color="white")
    note(ax, 2, 6, "The book's ch20 'replay/mixed' condition interleaves A and B from the start --- that is JOINT training (row 2), not replay-after-A-first (row 3). Solid rows were measured; the dashed row is a design we did not run.",
         fs=7.2, color=INK)
    save(fig, "fig_continual_timelines.png")


def fig_same_ops():
    """D03 -- SAME OPERATORS, DIFFERENT PROGRAMS (ch16).

    Side-by-side expression trees for abs(a+b) vs abs(a)+abs(b), with the input
    a=-3, b=2, intermediate values, and outputs 1 and 5. Purely a mathematical
    illustration of the abs_add ambiguity, not a model outcome.
    """
    fig, ax = new_fig(w=9.0, h=4.8)
    ax.text(50, 95, "SAME OPERATORS, DIFFERENT PROGRAMS", ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=INK)
    ax.text(50, 88, "Knowing the operators does not fix the order in which they are applied.",
            ha="center", va="center", fontsize=8, color=INK)
    # left: abs(a + b)
    ax.text(25, 76, "abs(a + b)", ha="center", fontsize=10, fontweight="bold", color=BLUE)
    ax.text(25, 66, "absolute value of the sum", ha="center", fontsize=7.5, color=INK)
    # tree: sum node -> abs
    box(ax, 19, 46, 12, 8, "a + b", fc=BLUE, fs=8)
    ax.text(25, 38, "a = -3, b = 2  →  a+b = -1", ha="center", fontsize=7.5, color=INK)
    box(ax, 19, 26, 12, 8, "abs(-1)", fc=BLUE, fs=8)
    ax.text(25, 18, "= 1", ha="center", fontsize=9, fontweight="bold", color=BLUE)
    arrow(ax, 25, 46, 25, 34)
    arrow(ax, 25, 34, 25, 26)

    # right: abs(a) + abs(b)
    ax.text(75, 76, "abs(a) + abs(b)", ha="center", fontsize=10, fontweight="bold", color=GREEN)
    ax.text(75, 66, "sum of the absolute values  (this is abs_add)", ha="center", fontsize=7.5, color=INK)
    box(ax, 62, 50, 11, 8, "abs(a)", fc=GREEN, fs=8)
    box(ax, 78, 50, 11, 8, "abs(b)", fc=GREEN, fs=8)
    ax.text(66, 42, "abs(-3) = 3", ha="center", fontsize=7, color=INK)
    ax.text(82, 42, "abs(2) = 2", ha="center", fontsize=7, color=INK)
    box(ax, 70, 30, 12, 8, "3 + 2", fc=GREEN, fs=8)
    ax.text(76, 22, "= 5", ha="center", fontsize=9, fontweight="bold", color=GREEN)
    arrow(ax, 68, 50, 73, 38); arrow(ax, 82, 50, 80, 38)
    arrow(ax, 76, 38, 76, 30)

    note(ax, 50, 8, "These are mathematically different functions (outputs 1 vs 5 for the same input). "
          + "The composite in this book, abs_add, is the right-hand one: abs(a) + abs(b).",
         fs=7.5, color=INK)
    save(fig, "fig_same_ops.png")


def fig_coverage():
    """D02 -- COVERAGE IS NOT A HELD-OUT FAMILY TEST (ch13).

    Rows = training condition (minimal / high diversity); the surface evaluation is a
    cell in the same family set the model trained on, so high-diversity 1.000 is
    coverage, not transfer to an excluded family. A second (proposed, not measured)
    panel shows what a true holdout would require.
    """
    import numpy as np
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    ax.text(50, 96, "COVERAGE IS NOT A HELD-OUT FAMILY TEST", ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=INK)

    # main panel: same family set
    ax.text(23, 86, "what was measured", ha="center", fontsize=8.5, fontweight="bold", color=INK)
    # family set axis
    ax.add_patch(FancyBboxPatch((6, 30), 34, 6, boxstyle="round,pad=0.02,rounding_size=1",
                                fc="#eef1f5", ec=GREY, lw=0.8))
    # model trained on all families
    for i, fam in enumerate(["fam A", "fam B", "fam C"]):
        x = 8 + i*10
        ax.add_patch(FancyBboxPatch((x, 46), 9, 9, boxstyle="round,pad=0.02,rounding_size=1",
                                    fc="#cfe0f5", ec=INK, lw=0.8))
        ax.text(x+4.5, 50.5, fam, ha="center", fontsize=6.5, color=INK)
    ax.text(21, 41, "high-diversity training: sees fam A / B / C", ha="center", fontsize=6.4, color=INK)
    # surface test point (well above the families, not overlapping)
    ax.add_patch(FancyBboxPatch((24, 66), 9, 8, boxstyle="round,pad=0.02,rounding_size=1",
                                fc="#e0f0e4", ec=GREEN, lw=0.8))
    ax.text(28.5, 70, "surface test", ha="center", fontsize=6.4, color=INK)
    ax.text(28.5, 60, "test is IN the training family set\n→ 1.000 is coverage", ha="center",
            fontsize=6.4, color=GREEN)
    ax.text(23, 20, "So the high-diversity 1.000 is COVERAGE of surfaces it was trained on,\nnot generalization to a wording family it never saw.",
            ha="center", fontsize=7.2, color=INK)

    # proposed holdout panel (right, dashed)
    ax.text(74, 86, "what a true holdout needs  (proposed, not measured)", ha="center",
            fontsize=7.6, fontweight="bold", color=PURPLE)
    ax.add_patch(FancyBboxPatch((58, 24), 32, 62, boxstyle="round,pad=0.02,rounding_size=2",
                                fc="#fbfaf6", ec=PURPLE, lw=1.0, linestyle="--"))
    for i, fam in enumerate(["fam A", "fam B", "fam C", "fam D"]):
        fc = "#cfe0f5" if i < 3 else "#f6dede"
        x = 60 + i*7.5
        ax.add_patch(FancyBboxPatch((x, 66), 6.5, 9, boxstyle="round,pad=0.02,rounding_size=1",
                                    fc=fc, ec=INK, lw=0.7))
        ax.text(x+3.2, 70.5, fam, ha="center", fontsize=6.2, color=INK)
    ax.text(74, 60, "train on A/B/C, hold out D", ha="center", fontsize=6.4, color=INK)
    ax.add_patch(FancyBboxPatch((64, 40), 20, 9, boxstyle="round,pad=0.02,rounding_size=1",
                                fc="#f6dede", ec=RED, lw=0.8))
    ax.text(74, 44.5, "test on family D (never seen)", ha="center", fontsize=6.4, color=RED)
    ax.text(74, 30, "only this tests generalization\nto an EXCLUDED family", ha="center", fontsize=6.6, color=INK)
    save(fig, "fig_coverage.png")


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
    fig_same_ops()
    fig_coverage()
    fig_continual_timelines()
