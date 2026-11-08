#!/usr/bin/env python3
"""Generate CONCEPTUAL / ILLUSTRATIVE diagrams for the book (the "how it works"
architecture figures that complement the measured-data charts in make_figures.py).

These are reproducible vector diagrams rendered to PNG in a single consistent
visual language (rounded boxes, semantic color, hand-muted palette) that matches
the book's typeset graphs. Every label is plain text drawn directly -- no image
model, so every word is byte-correct.

LEGIBILITY CONTRACT (round-1 review R1P-004 / R4G-001 / R4G-002 / R4G-005):
  The book includes every figure at \\textwidth = 4.5in = 324pt
  (book.sty: paperwidth 6in - 2*0.75in; \\includegraphics[width=\\maxwidth{\\textwidth}]).
  A span's EFFECTIVE (printed) size is therefore

        eff_pt = fontsize * 324 / pdf_width_pt

  so the old 9-9.6in canvases printed 10pt labels at only 4.3-6.4pt.
  Every concept figure is now drawn on a 4.5in-wide canvas with the axes
  filling the figure, which makes the tight crop 4.56in and

        eff_pt ~= 0.987 * fontsize

  i.e. the fontsize you set IS the printed size.  All interior text is
  >= 8.5pt (8.39pt effective; >= 8.0pt floor for full sentences) and no
  label is smaller than 7.6pt (7.50pt effective; >= 7.0pt floor).
  Line breaks below are part of the layout: every line is wrapped to the
  width of the box it sits in (max chars ~= 0.69 * box_width_in_data_units
  at 8.5pt).

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

# ---- printed-size type scale (see LEGIBILITY CONTRACT above) ----
BOOK_W = 4.5    # inches every figure occupies in the book (\textwidth)
FS  = 8.5       # interior sentence text  -> 8.39pt printed (>= 8.0 floor)
FSS = 7.6       # interior short labels   -> 7.50pt printed (>= 7.0 floor)
FST = 10.5      # figure title            -> 10.36pt printed


def new_fig(w=BOOK_W, h=4.5):
    """Canvas at (or near) the book's printed size.

    The axes fill the figure so the tight crop is exactly figsize + 0.06in of
    padding -- that keeps eff_pt = fontsize * 324 / (72*w + 4.32) predictable
    and stops the crop from inflating (which silently shrank the type before).
    """
    fig, ax = plt.subplots(figsize=(w, h))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, label, fc=BLUE, ec=None, fs=FS, tc="white", rounded=True,
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


def note(ax, x, y, text, color=INK, fs=FS, ha="left", wrap=True):
    ax.text(x, y, text, ha=ha, va="top", fontsize=fs, color=color,
            wrap=wrap, style="italic")


def save(fig, name):
    p = os.path.join(FIG, name)
    # pad_inches=0.03 (vs tight's 0.1 default): the extra white margin inflates
    # the natural width and lowers the effective point size at the book's 4.5in
    # render -- a tighter crop keeps labels larger (P1-PROD-03).
    fig.savefig(p, dpi=150, bbox_inches="tight", pad_inches=0.03)
    # VECTOR copy: same tight crop, but text/paths are real vectors so the
    # labels are crisp at any print size (the manuscript references
    # figures/fig_X.pdf; the PNG stays for previews/EPUB raster fallbacks).
    v = os.path.join(FIG, os.path.splitext(name)[0] + ".pdf")
    fig.savefig(v, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("wrote", p, "|", v)
    return p


# =========================================================================
# 1. THE APPARATUS (ch04) — teacher -> dataset -> student -> judge -> verdict,
#    with the world as the enclosing boundary and both gates annotated.
# =========================================================================
def fig_apparatus():
    """Figure 4.1 -- the laboratory, two clean lanes inside the world boundary."""
    fig, ax = new_fig(w=BOOK_W, h=4.6)
    ax.add_patch(FancyBboxPatch((3, 3), 94, 90, boxstyle="round,pad=0.02,rounding_size=3",
                                fc="#fbfaf6", ec=GREY, lw=1.2, linestyle="--"))
    ax.text(50, 96.5, "THE WORLD — a bounded universe we control", ha="center",
            va="center", fontsize=FST, color=INK, fontweight="bold")

    # TRAINING lane
    ax.text(5, 89, "TRAINING", ha="left", fontsize=FS, fontweight="bold", color=BLUE)
    box(ax, 5, 75, 26, 12, "TEACHER\nsemantic record", fc=GREEN)
    box(ax, 37, 75, 26, 12, "PROMPT +\nREFERENCE", fc=BLUE)
    box(ax, 69, 75, 26, 12, "STUDENT\n0.9M", fc=ORANGE, tc="white")
    arrow(ax, 31, 81, 37, 81)
    arrow(ax, 63, 81, 69, 81)
    ax.text(50, 71, "→ training only", ha="center", fontsize=FS, color=BLUE,
            style="italic")

    # EVALUATION lane
    ax.text(5, 67, "EVALUATION", ha="left", fontsize=FS, fontweight="bold", color=PURPLE)
    box(ax, 4, 53, 27, 12, "REQUESTS\n(familiar prompts,\nnew inputs)", fc=BLUE)
    box(ax, 36, 53, 27, 12, "STUDENT\ngenerates", fc=ORANGE, tc="white")
    box(ax, 68, 53, 14, 12, "JUDGE", fc=PURPLE)
    box(ax, 84, 53, 13, 12, "VERDICT\npass/fail", fc="#dff0e3", ec=GREEN,
        tc="#1b5e20")
    arrow(ax, 31, 59, 36, 59)
    arrow(ax, 63, 59, 68, 59)
    arrow(ax, 82, 59, 84, 59, color=GREEN)

    # hidden tests box below the judge, feeding up into the judge
    box(ax, 54, 37, 24, 11, "HIDDEN TESTS\n(evaluator-only)", fc=PURPLE)
    arrow(ax, 66, 48, 66, 53)

    # bottom: full-width caveat + full-width call-out, each on its own row so
    # neither can collide with the other or with the lane above (R4G-001 class).
    box(ax, 4, 6, 93, 17,
        "Only the prompt + reference enter training; the hidden tests\n"
        "go to the judge, never to the model. The judge runs the model's\n"
        "generated program against those tests. Prompt novelty differs by\n"
        "split: see the novelty audit in Appendix C.",
        fc="#fbfaf6", ec=PURPLE)
    box(ax, 4, 25, 93, 10,
        "the model is the instrument; the experiment is the subject\n"
        "(the gates sit outside this view)",
        fc="#fbfaf6", ec=INK)
    save(fig, "fig_apparatus.png")

def fig_two_gates():
    fig, ax = new_fig(w=BOOK_W, h=4.0)
    ax.text(50, 96, "TWO GATES: neither lives inside the model", ha="center",
            va="center", fontsize=FST, fontweight="bold", color=INK)

    # incoming request
    box(ax, 2, 52, 17, 16, "REQUEST\n(natural\nlanguage)", fc=BLUE)
    box(ax, 24, 52, 15, 16, "GATE B\ninput\nvalidator", fc=RED)
    box(ax, 45, 52, 14, 16, "MODEL", fc=ORANGE, bold=True)
    box(ax, 65, 52, 14, 16, "GATE A\noutput\nsandbox", fc=RED)
    # PYTHON box right edge at 98 (not 100): a pad-extended edge on the axes
    # boundary is clipped by the crop.
    box(ax, 85, 52, 13, 16, "PYTHON\nexecutes", fc=GREEN)

    arrow(ax, 19, 60, 24, 60, color=INK)
    arrow(ax, 39, 60, 45, 60, color=INK)
    arrow(ax, 59, 60, 65, 60, color=INK)
    arrow(ax, 79, 60, 85, 60, color=GREEN)

    # rejection branches drop down from each gate (downward exit)
    arrow(ax, 31.5, 52, 31.5, 40, color=RED)        # Gate B rejection drops down
    arrow(ax, 72, 52, 72, 40, color=RED)            # Gate A rejection drops down
    box(ax, 22, 27, 20, 13, "REJECTED at\nGate B", fc="#f6dede", ec=RED, tc=RED)
    box(ax, 64, 27, 20, 13, "REJECTED at\nGate A", fc="#f6dede", ec=RED, tc=RED)

    # yes/no labels ON THE OUTGOING branches, offset clear of the shaft so no
    # glyph sits on the line (R4G-005 class).
    ax.text(33, 43, "no", ha="left", va="bottom", fontsize=FS, color=RED,
            style="italic", fontweight="bold")
    ax.text(41, 61.5, "yes", ha="left", va="bottom", fontsize=FS, color=GREEN,
            style="italic", fontweight="bold")
    ax.text(73.5, 43, "no", ha="left", va="bottom", fontsize=FS, color=RED,
            style="italic", fontweight="bold")
    ax.text(80, 61.5, "yes", ha="left", va="bottom", fontsize=FS, color=GREEN,
            style="italic", fontweight="bold")

    # short, non-overlapping annotations below each rejection box
    note(ax, 22, 24, "refused before it\nreaches the model", color=RED)
    note(ax, 64, 24, "refused before it\nruns", color=RED)
    note(ax, 4, 92,
         "Gate A prevents the program being accepted/executed, not the\n"
         "model from emitting text; Gate B was NOT in the reported\n"
         "surface/human tests.", color=INK)
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

    R4G-001: the gloss row and the call-out are separate rows with a >= 10pt
    gap, and the call-out box is 23 units tall for 5 lines of 3.08 units, so
    its first line sits ~9pt below the top border (>= 8pt top padding).
    """
    fig, ax = new_fig(w=BOOK_W, h=4.6)
    ax.text(50, 96, "THE TEACHER: one semantic record, three artefacts",
            ha="center", va="center", fontsize=FST, fontweight="bold", color=INK)
    # semantic record box — use the real record fields (operation / args / output_type)
    box(ax, 33, 74, 34, 17,
        "SEMANTIC RECORD\noperation=add\nargs=[a:int, b:int]\noutput_type=int",
        fc=GREEN)
    for dx in (21, 50, 79):
        arrow(ax, 50, 74, dx, 60)
    # three artefacts
    box(ax, 8, 44, 26, 15, "REFERENCE\nPROGRAM\n(ground truth)", fc=GREEN)
    box(ax, 37, 44, 26, 15, "NL TASK\n(what the model\nreads)", fc=BLUE)
    box(ax, 66, 44, 26, 15, "HIDDEN TESTS\n(input/expected\npairs)", fc=PURPLE)
    # italic gloss row (own row, wrapped to clear its neighbours)
    note(ax, 21, 42, "one correct\nimplementation", color=GREEN, ha="center")
    note(ax, 50, 42, "the instruction,\nin the teacher's\nphrasing", color=BLUE, ha="center")
    note(ax, 79, 42, "oracle outputs;\nchecked\nindependently", color=PURPLE, ha="center")
    # drift note in a clear call-out box at the bottom: its own row, 3.4 units
    # (≈10pt) below the gloss row, with ~9pt of padding above its first line.
    box(ax, 6, 5.5, 88, 23,
        "Semantic-first: the program, task, and tests all derive from ONE record.\n"
        "This reduces drift, but is not a guarantee — and the tests being\n"
        "independently implemented does not mean the oracle is independently\n"
        "validated. Renderer bugs or a shared wrong assumption can still make all\n"
        "three consistently wrong.",
        fc="#fbfaf6", ec=GREEN)
    save(fig, "fig_teacher.png")

def fig_judge():
    """Figure 6.1 -- TWO LAYERS (external review P1-14).

    Layer 1 = the DESIRED four diagnostic stages (the design's vocabulary).
    Layer 2 = the ACTUAL saved instrumentation: one combined parse+allowlist
    validation gate, then the execution/test loop feeding two nested counters
    (tests_passed >= 1  and  ALL tests pass). A clear note states that a
    per-candidate failure taxonomy (which stage failed) was NOT collected.

    Sized ~5.0in wide with >=11pt type so primary labels stay ~10pt at the
    book's 4.507in render width (P1-PROD-03).  Long lines are wrapped so the
    tight-cropped natural width stays ~= figsize width (otherwise the crop
    widens and the effective point size drops).  Inter-box arrows sit at the
    top of each box (above the label row) so they never overlap the text.
    """
    fig, ax = new_fig(w=5.0, h=5.6)
    # Fill the figure with the axes (new_fig uses matplotlib's default inset
    # margins) so data 0-100 maps to the full 0-5.0in and left-aligned headers
    # do not start ~0.6in in and overflow the right edge (which widened the
    # tight-crop and dropped the effective point size).
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    ax.text(50, 97, "THE JUDGE: design stages vs what is recorded",
            ha="center", va="center", fontsize=12, fontweight="bold", color=INK)

    # ---------------- LAYER 1: desired diagnostic stages ----------------
    ax.text(2, 91, "LAYER 1 \u2014 DESIGN: four diagnostic stages (desired)",
            ha="left", va="center", fontsize=11, fontweight="bold", color=PURPLE)
    ax.text(2, 87, "which stage failed was NOT saved per candidate",
            ha="left", va="center", fontsize=10.5, color=INK, style="italic")
    stages = ["1\nparse", "2\nAST\nallowlist", "3\nexecute", "4\nsemantic"]
    sx = [2, 27, 52, 77]
    for i, (x0, lab) in enumerate(zip(sx, stages)):
        box(ax, x0, 69, 21, 14, lab, fc=PURPLE, fs=11, tc="white", bold=True)
        if i < 3:
            # arrow at the TOP of the boxes (y=81), above the label row (74-78),
            # so the arrowhead never lands on the next box's first letter.
            arrow(ax, x0 + 21, 81, sx[i + 1], 81, color=INK)
    ax.text(50, 65, "ideal taxonomy \u2014 NOT recorded per candidate",
            ha="center", va="center", fontsize=10.5, color=RED, style="italic")

    # ---------------- LAYER 2: actual saved instrumentation ----------------
    ax.text(2, 59, "LAYER 2 \u2014 RECORDED: combined gate + 2 counters",
            ha="left", va="center", fontsize=11, fontweight="bold", color=GREEN)

    # combined validation gate (parse + allowlist in ONE call)
    box(ax, 2, 42, 96, 13,
        "COMBINED VALIDATION GATE \u2014 sandbox.validate_source()\n"
        "parses AND checks the allowlist in ONE call \u2192 sets\n"
        "syntax_ok & capability_ok together",
        fc="#e8f0fb", ec=BLUE, fs=11, tc=INK)
    ax.text(50, 39, "\u2192 validation_pass   (any fail \u2192 score 0)",
            ha="center", va="center", fontsize=10.5, color=RED, fontweight="bold")
    ax.text(50, 35.5, "'syntax' rate includes capability rejects",
            ha="center", va="center", fontsize=10.5, color=RED, fontweight="bold")
    arrow(ax, 50, 32, 50, 29, color=INK)

    # execution / test loop
    box(ax, 2, 20, 96, 9,
        "EXECUTE program against the hidden tests (loop)",
        fc="#e9f5eb", ec=GREEN, fs=11, tc=INK)
    arrow(ax, 27, 20, 27, 17, color=INK)
    arrow(ax, 73, 20, 73, 17, color=INK)

    # two nested counters
    box(ax, 2, 5, 46, 12,
        "tests_passed \u2265 1\n\u2192 'executable'\n(at_least_one_test_pass)",
        fc="#fbfaf6", ec=ORANGE, fs=11, tc=INK)
    box(ax, 52, 5, 46, 12,
        "ALL tests pass\n\u2192 pass@1 = 1\n(all_tests_pass)",
        fc="#fbfaf6", ec=RED, fs=11, tc=INK, bold=True)
    ax.text(50, 2.5, "'executable' = passed \u2265 1 hidden test, not merely 'ran'",
            ha="center", va="center", fontsize=10.5, color=INK, style="italic")

    # honest limit: no per-candidate failure taxonomy (wrapped to keep width)
    ax.text(50, 0, "per-candidate failure taxonomy\n(which stage failed) was NOT collected",
            ha="center", va="top", fontsize=10.5, color=RED, fontweight="bold")
    save(fig, "fig_judge.png")


# =========================================================================
# 5. THE CAPABILITY LADDER (ch02) — four levels of trust.
# =========================================================================
def fig_ladder():
    """Figure 2.1 -- four DISTINCT questions about a result, not an ordered trust ladder."""
    fig, ax = new_fig(w=BOOK_W, h=4.0)
    ax.text(50, 96, "THE FOUR EVALUATION QUESTIONS", ha="center", va="center",
            fontsize=FST, fontweight="bold", color=INK)
    ax.text(50, 91,
            "four distinct questions -- they are not a ladder, and passing one\n"
            "does not establish the next.",
            ha="center", va="top", fontsize=FS, color=INK)
    levels = [
        (68, "Q1  MEMORIZATION\nCould it just be remembering a stored answer?", "#c44e52"),
        (52, "Q2  DISTRIBUTIONAL GENERALIZATION\nDoes it work on new examples of the same task?", "#dd8452"),
        (36, "Q3  SURFACE GENERALIZATION\nDoes it survive a change of wording or identifiers?", "#55a868"),
        (20, "Q4  STRUCTURAL GENERALIZATION\nCan it combine things it knows in a way it never saw?", "#4c72b0"),
    ]
    for y, lab, c in levels:
        box(ax, 6, y, 88, 12, lab, fc=c)
    # compact footer; the fuller qualification lives in the chapter text
    note(ax, 6, 16,
         "Report these separately — passing one question does not\n"
         "establish the next.", color=INK)
    save(fig, "fig_ladder.png")

def fig_task():
    """D01 -- WHO SEES WHAT (ch03): the model generates source; Python executes it;
    hidden tests are evaluator-only. Two lanes so the model / execution / tests are
    impossible to conflate."""
    fig, ax = new_fig(w=BOOK_W, h=5.0)
    ax.text(50, 96.5, "WHO SEES WHAT: the model generates code, Python runs it",
            ha="center", va="center", fontsize=10, fontweight="bold", color=INK)
    # TRAINING lane (top)
    ax.text(4, 92, "TRAINING lane", ha="left", fontsize=FS, fontweight="bold", color=BLUE)
    box(ax, 4, 78, 30, 13, "NL SPEC + REFERENCE\n(the teacher's pair)", fc=BLUE)
    box(ax, 40, 78, 30, 13, "MODEL\n(0.9M, trained)", fc=ORANGE, tc="white")
    arrow(ax, 34, 84.5, 40, 84.5)
    note(ax, 6, 74, "learns a mapping\nrequest → program text", color=ORANGE)
    # trained checkpoint transfer (training MODEL -> eval MODEL)
    arrow(ax, 48, 78, 44, 65, color=ORANGE, lw=1.4)
    ax.text(50, 74, "trained checkpoint", ha="left", va="top", fontsize=FS,
            color=ORANGE, style="italic")

    # EVALUATION lane (bottom), two rows
    ax.text(4, 66, "EVALUATION lane", ha="left", fontsize=FS, fontweight="bold", color=PURPLE)
    # row 1: request -> model -> candidate -> python
    box(ax, 2, 50, 21, 15, "REQUESTS\n(familiar\nprompts,\nnew inputs)", fc=BLUE)
    box(ax, 27, 50, 21, 15, "TRAINED MODEL\n(generates\nsource)", fc=ORANGE, tc="white")
    box(ax, 52, 50, 21, 15, "CANDIDATE\nSOURCE\n(the program\ntext)", fc=GREEN)
    box(ax, 77, 50, 21, 15, "PYTHON\nRUNNER\n(executes)", fc="#e9f5eb", ec=GREEN, tc=INK)
    arrow(ax, 23, 57.5, 27, 57.5)
    arrow(ax, 48, 57.5, 52, 57.5)
    arrow(ax, 73, 57.5, 77, 57.5)

    # row 2: test inputs -> python, expected & actual -> comparator
    box(ax, 2, 34, 30, 13, "TEST INPUTS\n(go to the\nPython runner)", fc="#eaf2fb", ec=BLUE, tc=INK)
    box(ax, 38, 34, 28, 13, "EXPECTED VALUES\n(from the\nsemantics)", fc=PURPLE)
    box(ax, 80, 34, 18, 13, "ACTUAL\nVALUES", fc=GREEN, tc="white")
    box(ax, 20, 16, 76, 12,
        "COMPARATOR — compares the Python output to the\n"
        "expected values and issues the verdict",
        fc="white", ec=PURPLE, tc=INK)
    # wiring: test inputs -> python runner (through the clear corridor between
    # the two rows); expected / actual -> comparator
    arrow(ax, 17, 48.5, 87, 48.5, color=BLUE)
    arrow(ax, 52, 34, 52, 28, color=PURPLE)
    arrow(ax, 89, 34, 89, 28, color=GREEN)

    # constraint strip, scoped to candidate execution
    ax.text(50, 12,
            "CANDIDATE EXECUTION · PURE FUNCTION (no I/O, no network,\n"
            "no random) · AST-WHITELISTED",
            ha="center", va="top", fontsize=FS, color="#333333", style="italic")
    save(fig, "fig_task.png")


# =========================================================================
# 7. THE RIVALS (ch07) — model vs template vs retrieval baselines.
# =========================================================================
def fig_rivals():
    fig, ax = new_fig(w=BOOK_W, h=3.8)
    ax.text(50, 96, "THE RIVALS: baselines keep us honest", ha="center",
            va="center", fontsize=FST, fontweight="bold", color=INK)
    box(ax, 6, 64, 28, 16, "TEMPLATE\n'if task==add:\nreturn a+b'", fc=GREY, tc=INK)
    box(ax, 38, 64, 26, 16, "RETRIEVAL\nnearest-neighbour\ncopy", fc=GREY, tc=INK)
    box(ax, 68, 64, 26, 16, "OUR MODEL\n0.88M", fc=ORANGE)
    note(ax, 6, 61, "a fixed\nhand-written pattern.\nA sanity floor.", color=INK)
    note(ax, 38, 61, "copies the\nclosest memory.\nA sanity check.", color=INK)
    note(ax, 68, 61, "the actual\nquestion: does it\nbeat them?", color=INK)
    box(ax, 6, 14, 88, 16,
        "The baselines are sanity checks, not a score ceiling. A\n"
        "result is truthful if we know which baseline already\n"
        "solves it and whether the model adds anything.",
        fc="#fbfaf6", ec=INK)
    save(fig, "fig_rivals.png")


# =========================================================================
# 8. THE SMALLEST BRAIN (ch08) — tokens -> embedding -> transformer -> output.
# =========================================================================
def fig_brain():
    """Figure 8.1 -- the architecture with actual numbers (emb dim, layers, heads).

    R4G-005: the autoregressive feedback loop is routed down the RIGHT edge,
    along y=46 and back up the LEFT edge at x=12 -- the parameters block moved
    to x=30..98, y=53..66, so no shaft crosses it.
    """
    fig, ax = new_fig(w=BOOK_W, h=4.6)
    ax.text(50, 96, "THE SMALLEST BRAIN: a 0.88M decoder-only GPT", ha="center",
            va="center", fontsize=FST, fontweight="bold", color=INK)
    # pipeline with real dimensions
    box(ax, 2, 74, 20, 16, "TOKENS\n(291 vocab)", fc=BLUE)
    box(ax, 27, 74, 21, 16, "EMBED\ntok=291×128\npos=128×128", fc=BLUE)
    box(ax, 53, 74, 25, 16, "4 BLOCKS\ncausal attention\nMLP 128→512→128", fc=ORANGE)
    box(ax, 81, 74, 17, 16, "OUTPUT\n291 logits\n→ sampled\ntoken", fc=GREEN)
    arrow(ax, 22, 82, 27, 82)
    arrow(ax, 48, 82, 53, 82)
    arrow(ax, 78, 82, 81, 82)
    # autoregressive feedback loop: down the right edge, along y=46, up the
    # left edge into the TOKENS box -- clear of every label.
    arrow(ax, 89, 74, 89, 46, color=INK, lw=1.2, style="-|>", ls="--")
    arrow(ax, 89, 46, 12, 46, color=INK, lw=1.2, ls="--")
    arrow(ax, 12, 46, 12, 74, color=INK, lw=1.2, style="-|>", ls="--")
    # label centred below the loop line so neither touches the other
    ax.text(50, 43, "the sampled output token is fed back as the next input",
            ha="center", va="top", fontsize=FS, color=INK, style="italic")
    # key dimensions note -- right of the loop's left riser (x=12)
    note(ax, 30, 66,
         "parameters: 884,224 total (53,632 embedding\n"
         "+ 830,592 non-embedding). 4 layers × 4 heads,\n"
         "n_embd=128, block_size=128, temperature-0.8\n"
         "sampled decoding.", color=INK)
    # ORN-R2-GEOM-01: both bottom callouts used box()'s default WHITE text on a
    # near-white fill (#fbfaf6) — faint grey-on-cream at print size. Text is now
    # near-black on a slightly deeper cream, so callout text contrast (>= ~16:1)
    # exceeds body-prose contrast (INK on white, ~14:1); the edge stays INK.
    CALLOUT_FC, CALLOUT_TC = "#f4efe3", "#111111"
    box(ax, 52, 22, 46, 14,
        "same architecture, just wider /\n"
        "deeper for the size sweep\n"
        "(6.5M, 10.2M, 29.3M).",
        fc=CALLOUT_FC, ec=INK, tc=CALLOUT_TC)
    box(ax, 2, 3, 96, 11,
        "This is the instrument. The experiment is the subject — the\n"
        "book is about what the model learns, not about how big it is.",
        fc=CALLOUT_FC, ec=INK, tc=CALLOUT_TC)
    save(fig, "fig_brain.png")

def fig_brew():
    """Figure 9.1 -- the brew loop, distinguishing training from the final audit."""
    fig, ax = new_fig(w=BOOK_W, h=4.6)
    ax.text(50, 97, "THE BREW LOOP", ha="center", va="center", fontsize=11,
            fontweight="bold", color=INK)
    # --- DEV LOOP (top): generate -> train -> dev evaluate (-> back to generate) ---
    box(ax, 6, 72, 28, 14, "GENERATE DATA\n(semantic-first)", fc=GREEN)
    box(ax, 40, 72, 28, 14, "TRAIN\nfixed step budget\n(e.g. 1500 steps)", fc=ORANGE)
    box(ax, 73, 72, 25, 14, "DEV EVALUATE\n(informs iteration)", fc=PURPLE)
    arrow(ax, 34, 79, 40, 79)
    arrow(ax, 68, 79, 73, 79)
    # dev feedback edge: a separate loop above the boxes, back to GENERATE DATA
    arrow(ax, 85, 93, 20, 93, color=PURPLE, lw=1.2)
    arrow(ax, 20, 93, 20, 86, color=PURPLE, lw=1.2)
    # its label sits in its own column (x>=56) so the audit arrow (x=54) and
    # the label can never cross.
    ax.text(56, 68,
            "dev feedback: what we\n"
            "measure (loss / dev\n"
            "score) shapes the next\n"
            "round of data & hyperparams.",
            ha="left", va="top", fontsize=FS, color=PURPLE, style="italic")

    # --- FINAL AUDIT (bottom, separate lane) ---
    box(ax, 6, 46, 34, 14, "FINAL AUDIT\n(one report on the\nfrozen test records)", fc=BLUE)
    arrow(ax, 54, 72, 54, 60, color=BLUE)
    note(ax, 6, 44, "the dev loop that iterates is separate\nfrom the one-time final audit.",
         color=INK)
    note(ax, 6, 34,
         "recommended workflow: the final audit runs once on the frozen\n"
         "records and is NOT fed back to change training. (In our runs\n"
         "the pilot test records reused the training prompt strings -- see\n"
         "the novelty audit -- so 'frozen' refers to the record list, not\n"
         "to genuinely-seen-new prompts.)",
         color=INK)
    save(fig, "fig_brew.png")

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
        ("Stage 1 pilot (0.88M)",        "0.897", "0.000", "0.000",  "-",      "0.000", "NT"),
        ("6.5M",                         "0.897", "-",      "-",      "-",      "0.000", "NT"),
        ("10.2M",                        "0.773", "-",      "-",      "-",      "0.000", "NT"),
        ("29.3M",                        "0.897", "-",      "-",      "-",      "0.000", "NT"),
        ("High-diversity (same count)",  "0.743", "-",      "0.550",  "NT",     "NT",    "NT"),
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
            fontsize=10, color=RED, va="bottom")
    for c in range(ncol):
        x = left + c*cw
        ax.add_patch(FancyBboxPatch((x, top-6), cw-0.6, 7, boxstyle="round,pad=0.01,rounding_size=0.8",
                                    fc="#eef1f5", ec=INK, lw=0.6))
        ax.text(x+(cw-0.6)/2, top-6+3.5, cols[c], ha="center", va="center", fontsize=10, color=INK, fontweight="bold")
    for r in range(nrow):
        y = top - 6 - 7 - rh*(r+1)
        name, vals = rows[r][0], rows[r][1:]
        ax.add_patch(FancyBboxPatch((left, y), cw-0.6, rh*0.9, boxstyle="round,pad=0.01,rounding_size=0.8",
                                    fc="#fdfbf7", ec=GREY, lw=0.6))
        ax.text(left+(cw-0.6)/2, y+rh*0.45, name, ha="center", va="center", fontsize=10, color=INK, fontweight="bold")
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
                txt, tc = v, "#2e7d32"
            ax.text(x+(cw-0.6)/2, y+rh*0.45, txt, ha="center", va="center", fontsize=10, color=tc)
    note(ax, 3, 4, "Green = measured strong result. Red = measured zero. NT = not tested. " +
          "Corrected equal-count run: high-diversity 0.743 in-dist / 0.550 held-out family (the earlier 1.000 was coverage of a 42-record pool, P0-02).",
         fs=10, color=INK)
    save(fig, "fig_capability_map.png")


def fig_continual_timelines():
    """D05 -- SEQUENTIAL, JOINT, AND REPLAY ARE DIFFERENT EXPERIMENTS (ch20).

    Three horizontal timelines. Solid outline = measured regime; dashed = a true
    replay-after-A-first design, which we did NOT run. Shows that the book's
    joint/interleaved condition (A+B from start, formerly labeled 'replay/mixed')
    is actually JOINT training.
    """
    fig, ax = new_fig(w=BOOK_W, h=4.4)
    ax.text(50, 96, "SEQUENTIAL VS JOINT VS REPLAY: three different designs",
            ha="center", va="center", fontsize=10, fontweight="bold", color=INK)
    # labels wrapped so the longest line clears the bars (which start at x=36)
    labels = ["1. Sequential\n(measured)",
              "2. Joint (measured)\nA and B interleaved",
              "3. True replay-after-A\n(not run)"]
    for row, (lab, style) in enumerate(zip(labels, ["solid", "solid", "dashed"])):
        y = 76 - row*24
        ax.text(2, y+3, lab, ha="left", va="center", fontsize=FS, color=INK)
        # timeline bar
        ax.add_patch(FancyBboxPatch((36, y), 60, 6, boxstyle="round,pad=0.02,rounding_size=1",
                                    fc="#eef1f5", ec=INK, lw=1.0, linestyle="--" if style=="dashed" else "-"))
        if row == 0:   # sequential: full A then full B
            ax.add_patch(FancyBboxPatch((37, y+1), 29, 4, fc=BLUE, ec=BLUE, lw=0.5))
            ax.add_patch(FancyBboxPatch((66, y+1), 29, 4, fc=GREEN, ec=GREEN, lw=0.5))
            ax.text(51.5, y+3, "A", ha="center", va="center", fontsize=FS, color="white")
            ax.text(80.5, y+3, "B", ha="center", va="center", fontsize=FS, color="white")
        elif row == 1: # joint: A and B interleaved
            ax.add_patch(FancyBboxPatch((37, y+1), 58, 4, fc=GREY, ec=GREY, lw=0.5))
            ax.text(66, y+3, "A + B (interleaved)", ha="center", va="center",
                    fontsize=FS, color=INK)
        else:          # true replay (not run)
            ax.add_patch(FancyBboxPatch((37, y+1), 29, 4, fc=BLUE, ec=BLUE, lw=0.5))
            ax.add_patch(FancyBboxPatch((66, y+1), 29, 4, fc=GREEN, ec=GREEN, lw=0.5))
            ax.text(51.5, y+3, "A", ha="center", va="center", fontsize=FS, color="white")
            ax.text(80.5, y+3, "B (+ replay of A)", ha="center", va="center",
                    fontsize=FS, color="white")
    note(ax, 4, 24,
         "The book's joint/interleaved condition (A+B from start, formerly\n"
         "labeled 'replay/mixed') interleaves A and B from the start --- that\n"
         "is JOINT training (row 2), not replay-after-A-first (row 3). Solid\n"
         "rows were measured; the dashed row is a design we did not run.\n"
         "(Rows are schematic, not to scale.)",
         color=INK)
    save(fig, "fig_continual_timelines")


def fig_three_meanings():
    """D08 -- ONE TASK, THREE MEANINGS OF 'NEW' (ch2 / ch9 box).

    Three cases that all get loosely called 'a new task' but differ in what is
    actually new to the MODEL INPUT: (1) new task ID, same prompt+program, only the
    hidden tests change; (2) genuinely new prompt, same target program; (3) an unseen
    program structure (composition). Only #2/#3 are new to the model input; #1 is new
    only to the evaluator.
    """
    fig, ax = new_fig(w=BOOK_W, h=5.4)
    ax.text(50, 96.5, "ONE TASK, THREE MEANINGS OF 'NEW'", ha="center", va="center",
            fontsize=FST, fontweight="bold", color=INK)
    ax.text(50, 91.5, "What is actually new to the MODEL INPUT?\n"
                      "(green = new to model; grey = not)",
            ha="center", va="top", fontsize=FS, color=INK)
    rows = [
        ("1. New task ID,\nsame prompt +\nprogram", "same", "same", "different", "grey",
         "only the evaluator's hidden tests change\n-- NOT a new example for the model"),
        ("2. New prompt,\nsame target\nprogram", "different", "same", "same", "green",
         "a new surface, same computation\n-- genuinely a new model input"),
        ("3. Unseen\nprogram\nstructure", "different", "different", "different", "green",
         "composing pieces never combined\n-- new input AND new target structure"),
    ]
    cols = ["case", "prompt", "target\nprogram", "hidden\ntests", "new to\nmodel input?"]
    colx = [14, 36, 54, 72, 87]
    for c, h in zip(colx, cols):
        ax.text(c, 84, h, ha="center", va="top", fontsize=FS, fontweight="bold", color=INK)
    for r, (lab, pr, prog, test, kind, cap) in enumerate(rows):
        ytop = 77 - r*21.1
        box(ax, 2, ytop - 12, 24, 12, lab, fc="#eef1f5", tc=INK)
        ymid = ytop - 6
        ax.text(36, ymid, pr, ha="center", va="center", fontsize=FS, color=INK)
        ax.text(54, ymid, prog, ha="center", va="center", fontsize=FS, color=INK)
        ax.text(72, ymid, test, ha="center", va="center", fontsize=FS, color=INK)
        ax.text(87, ymid, "YES" if kind=="green" else "NO", ha="center", va="center",
                fontsize=FS, fontweight="bold",
                color="#2b8a3e" if kind=="green" else "#888888")
        ax.text(50, ytop - 14, cap, ha="center", va="top", fontsize=FS, color=INK,
                style="italic")
    note(ax, 3, 13.5,
         "A 'new task ID' that only changes the hidden tests is NOT a\n"
         "new model input. Report prompt/program novelty, not just\n"
         "task-ID counts.", color=INK)
    save(fig, "fig_three_meanings.png")


def fig_same_ops():
    """D03 -- SAME OPERATORS, DIFFERENT PROGRAMS (ch16).

    Side-by-side expression trees for abs(a+b) vs abs(a)+abs(b), with the input
    a=-3, b=2, intermediate values, and outputs 1 and 5. Purely a mathematical
    illustration of the abs_add ambiguity, not a model outcome.

    R4G-005: every arrowhead terminates ON the border of its target box (y=43
    for the sum box), so the shaft never crosses the '3 + 2' label and the '+'
    stays readable.
    """
    fig, ax = new_fig(w=BOOK_W, h=4.4)
    ax.text(50, 96, "SAME OPERATORS, DIFFERENT PROGRAMS", ha="center", va="center",
            fontsize=FST, fontweight="bold", color=INK)
    ax.text(50, 91,
            "Knowing the operators does not fix the order in which they\n"
            "are applied.",
            ha="center", va="top", fontsize=FS, color=INK)
    # left: abs(a + b)
    ax.text(25, 81, "abs(a + b)", ha="center", va="center", fontsize=FS,
            fontweight="bold", color=BLUE)
    ax.text(25, 76, "absolute value of the sum", ha="center", va="center",
            fontsize=FS, color=INK)
    box(ax, 19, 58, 12, 9, "a + b", fc=BLUE)
    ax.text(13, 51, "a = -3, b = 2\n→ a+b = -1", ha="center", va="center",
            fontsize=FS, color=INK)
    box(ax, 19, 38, 12, 9, "abs(-1)", fc=BLUE)
    ax.text(25, 32, "= 1", ha="center", va="center", fontsize=FS,
            fontweight="bold", color=BLUE)
    arrow(ax, 25, 58, 25, 47)
    arrow(ax, 25, 38, 25, 34.5)

    # right: abs(a) + abs(b)
    ax.text(75, 81, "abs(a) + abs(b)", ha="center", va="center", fontsize=FS,
            fontweight="bold", color=GREEN)
    ax.text(75, 76, "sum of the absolute values\n(this is abs_add)", ha="center",
            va="top", fontsize=FS, color=INK)
    box(ax, 62, 58, 11, 9, "abs(a)", fc=GREEN)
    box(ax, 78, 58, 11, 9, "abs(b)", fc=GREEN)
    ax.text(64, 52, "abs(-3) = 3", ha="center", va="center", fontsize=FS, color=INK)
    ax.text(87, 52, "abs(2) = 2", ha="center", va="center", fontsize=FS, color=INK)
    box(ax, 70, 34, 12, 9, "3 + 2", fc=GREEN)
    ax.text(76, 28, "= 5", ha="center", va="center", fontsize=FS,
            fontweight="bold", color=GREEN)
    # all three arrowheads stop at the box border (y=43), never inside it
    arrow(ax, 67.5, 58, 73, 43)
    arrow(ax, 83.5, 58, 77, 43)
    arrow(ax, 76, 49, 76, 43)

    note(ax, 4, 20,
         "These are mathematically different functions (outputs 1 vs 5 for the\n"
         "same input). The composite in this book, abs_add, is the right-hand\n"
         "one: abs(a) + abs(b).",
         color=INK)
    save(fig, "fig_same_ops.png")


def fig_coverage():
    """D02 -- COVERAGE IS NOT A HELD-OUT FAMILY TEST (ch13) -> Figure 13.2.

    Top section    = the flawed original's coverage test (surface test drawn
                     from the training family set -> 1.000 is coverage of a
                     42-record pool).
    Bottom section = 'flawed original vs corrected measured (n=100)': the
                     corrected equal-count run DID measure a true holdout
                     (h01/h02 excluded from both arms, 100 tasks per arm):
                     0.000 (low) vs 0.550 (high) mean.

    LAYOUT (round-1 R4G-002 + R1P-004):
      * the axes fill a 6.0 x 6.2in canvas (subplots_adjust 0.01..0.99), so
        11pt type prints at 11 * 324 / ~364 = 9.7pt at the book's 4.5in text
        width, and the 51-character 'corrected: ...' line (298pt) fits INSIDE
        the dashed panel (~310pt wide) instead of hanging out of both sides;
      * every annotation in the dashed panel is its OWN row, stacked with
        >= 1.4 y-units (>= 6pt) of clear space: family chips (y 31-38), the
        three-line 'flawed original' block (top y=29 -> bottom 19.9),
        'corrected: ...' (top 18.5 -> 15.5), '-> 0.000 ...' (top 14 -> 11),
        'only the corrected ...' (top 9.5 -> 6.5).  No two multi-word lines
        ever share a y-band, so 'corrected: ...' can never sit on
        '-> 1.000 = coverage' again (it used to overlap it by ~10pt).
    """
    fig, ax = plt.subplots(figsize=(6.0, 6.2))
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    FS = 11          # >= 9.7pt printed at the book's 4.5in text width
    FSB = 12         # bold headings, >= 10.6pt printed

    # ======================= TOP: the flawed original =======================
    ax.text(50, 96.5, "COVERAGE IS NOT A HELD-OUT FAMILY TEST", ha="center",
            va="center", fontsize=FSB, fontweight="bold", color=INK)
    ax.text(50, 90.5, "flawed original: what it measured", ha="center",
            va="center", fontsize=FS, fontweight="bold", color=INK)
    ax.text(50, 86, "the surface test is INSIDE the training family set\n"
                    "\u2192 1.000 is coverage, not a new-family result "
                    "(42-record pool)", ha="center", va="top",
            fontsize=FS, color=GREEN)
    # family row + the training-family-set box (y 66-73)
    for i, fam in enumerate(["\u03b1", "\u03b2", "\u03b3"]):
        x = 10 + i * 12
        ax.add_patch(FancyBboxPatch((x, 66), 10, 7,
                                    boxstyle="round,pad=0.02,rounding_size=1",
                                    fc="#cfe0f5", ec=INK, lw=0.8))
        ax.text(x + 5, 69.5, fam, ha="center", va="center", fontsize=FS,
                color=INK)
    ax.add_patch(FancyBboxPatch((46, 66), 40, 7,
                                boxstyle="round,pad=0.02,rounding_size=1",
                                fc="#eef1f5", ec=GREY, lw=0.8))
    ax.text(66, 69.5, "the training family set", ha="center", va="center",
            fontsize=FS, color="#333333")
    ax.text(50, 62, "high-diversity training sees all families (illustrative)",
            ha="center", va="top", fontsize=FS, color=INK)
    ax.text(50, 57, "So the flawed run's 1.000 is COVERAGE of surfaces it "
                    "trained on,\nnot generalization to a family it never saw.",
            ha="center", va="top", fontsize=FS, color=INK)
    ax.plot([6, 94], [47.5, 47.5], color=GREY, lw=0.8)

    # ================ BOTTOM: flawed original vs corrected measured =========
    ax.text(50, 43.5, "flawed original vs corrected measured (n=100)",
            ha="center", va="center", fontsize=FS, fontweight="bold",
            color=PURPLE)
    ax.add_patch(FancyBboxPatch((6, 1), 88, 39,
                                boxstyle="round,pad=0.02,rounding_size=2",
                                fc="#fbfaf6", ec=PURPLE, lw=1.0, linestyle="--"))
    for i, fam in enumerate(["\u03b1", "\u03b2", "\u03b3", "\u03b4"]):
        fc = "#cfe0f5" if i < 3 else "#f6dede"
        x = 8 + i * 11
        ax.add_patch(FancyBboxPatch((x, 31), 9, 7,
                                    boxstyle="round,pad=0.02,rounding_size=1",
                                    fc=fc, ec=INK, lw=0.7))
        ax.text(x + 4.5, 34.5, fam, ha="center", va="center", fontsize=FS,
                color=INK)
    ax.text(71, 34.5, "train on \u03b1/\u03b2/\u03b3, hold out \u03b4",
            ha="center", va="center", fontsize=FS, color=INK)
    ax.add_patch(FancyBboxPatch((10, 20), 34, 9,
                                boxstyle="round,pad=0.02,rounding_size=1",
                                fc="#f6dede", ec=RED, lw=0.8))
    ax.text(27, 24.5, "test on family \u03b4\n(never seen)", ha="center",
            va="center", fontsize=FS, color=RED)
    # --- ONE ROW per annotation; >= 1.4 y-units (>= 6pt) between rows ---
    ax.text(71, 29, "flawed original: test drawn\nfrom training families\n"
                    "\u2192 1.000 = coverage", ha="center", va="top",
            fontsize=FS, color=INK)
    ax.text(50, 18.5, "corrected: h01/h02 excluded from both arms, n = 100",
            ha="center", va="top", fontsize=FS, color=INK)
    ax.text(50, 14, "\u2192 0.000 (low) vs 0.550 (high) mean", ha="center",
            va="top", fontsize=FS, color=INK, fontweight="bold")
    ax.text(50, 9.5, "only the corrected run tests an EXCLUDED family",
            ha="center", va="top", fontsize=FS, color=INK, fontweight="bold")
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
# fig_capability_map() replaced by native checkpoint-keyed tables (R3-02)
    fig_same_ops()
    fig_coverage()
    fig_three_meanings()
    fig_continual_timelines()