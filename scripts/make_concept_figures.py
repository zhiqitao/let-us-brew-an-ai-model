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


def note(ax, x, y, text, color=INK, fs=10, ha="left", wrap=True):
    ax.text(x, y, text, ha=ha, va="top", fontsize=fs, color=color,
            wrap=wrap, style="italic")


def save(fig, name):
    p = os.path.join(FIG, name)
    # pad_inches=0.03 (vs tight's 0.1 default): the extra white margin inflates
    # the natural width and lowers the effective point size at the book's 4.5in
    # render -- a tighter crop keeps labels larger (P1-PROD-03).
    fig.savefig(p, dpi=150, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("wrote", p)
    return p


# =========================================================================
# 1. THE APPARATUS (ch03) — teacher -> dataset -> student -> judge -> verdict,
#    with the world as the enclosing boundary and both gates annotated.
# =========================================================================
def fig_apparatus():
    """Figure 4.1 -- the laboratory, two clean lanes inside the world boundary."""
    fig, ax = new_fig(w=9.6, h=6.0)
    ax.add_patch(FancyBboxPatch((3, 3), 94, 94, boxstyle="round,pad=0.02,rounding_size=3",
                                fc="#fbfaf6", ec=GREY, lw=1.2, linestyle="--"))
    ax.text(50, 97, "THE WORLD — a bounded universe we control", ha="center",
            va="center", fontsize=10.5, color=INK, fontweight="bold")

    # TRAINING lane
    ax.text(6, 88, "TRAINING", ha="left", fontsize=10, fontweight="bold", color=BLUE)
    box(ax, 8, 72, 22, 11, "TEACHER\nsemantic\nrecord", fc=GREEN, fs=10)
    box(ax, 36, 72, 26, 11, "PROMPT +\nREFERENCE", fc=BLUE, fs=10)
    box(ax, 68, 72, 20, 11, "STUDENT\n0.9M", fc=ORANGE, fs=10, tc="white")
    arrow(ax, 30, 77.5, 36, 77.5)
    arrow(ax, 62, 77.5, 68, 77.5)
    ax.text(52, 68, "→ training only", ha="center", fontsize=10, color=BLUE, style="italic")

    # EVALUATION lane
    ax.text(6, 64, "EVALUATION", ha="left", fontsize=10, fontweight="bold", color=PURPLE)
    box(ax, 8, 50, 22, 11, "REQUESTS\n(familiar prompts,\nnew inputs)", fc=BLUE, fs=10)
    box(ax, 36, 50, 26, 11, "STUDENT\ngenerates", fc=ORANGE, fs=10, tc="white")
    box(ax, 68, 50, 16, 11, "JUDGE", fc=PURPLE, fs=10)
    arrow(ax, 30, 55.5, 36, 55.5)
    arrow(ax, 62, 55.5, 68, 55.5)

    # hidden tests box below the judge, feeding up into the judge
    box(ax, 66, 34, 18, 11, "HIDDEN TESTS\n(evaluator-only)", fc=PURPLE, fs=10)
    arrow(ax, 75, 45, 75, 50)

    # verdict node after/right of the judge, INSIDE the boundary
    box(ax, 88, 50, 9, 11, "VERDICT\npass/fail", fc="#dff0e3", ec=GREEN, fs=10, tc="#1b5e20")
    arrow(ax, 84, 55.5, 88, 55.5, color=GREEN)

    # bottom: explanation caption on the LEFT half, call-out on the RIGHT half
    # These two dense caveat paragraphs stay at ~7.2pt (original): at 10pt the
    # long left paragraph overflows its box and collides with the right call-out.
    # The review (4.1) says to enlarge the internal node labels (done: 10pt)
    # and move caveats to the caption -- so the caveats remain small secondary
    # text while the primary node labels are large.
    box(ax, 6, 16, 52, 12,
        "Only the prompt + reference enter training; the hidden tests go to the judge,\nnever to the model. The judge runs the model's generated program against those\ntests. Prompt novelty differs by split: see the novelty audit in Appendix C.",
        fc="#fbfaf6", ec=PURPLE, fs=7.2, tc=INK)
    box(ax, 62, 16, 34, 12, "the model is the instrument;\nthe experiment is the subject\n(the gates sit outside this view)",
        fc="#fbfaf6", ec=INK, fs=7.2, tc=INK)
    save(fig, "fig_apparatus.png")

def fig_two_gates():
    fig, ax = new_fig()
    ax.text(50, 95, "TWO GATES: neither lives inside the model", ha="center",
            va="center", fontsize=11, fontweight="bold", color=INK)

    # incoming request
    box(ax, 2, 44, 18, 16, "REQUEST\n(natural language)", fc=BLUE, fs=10)
    box(ax, 26, 44, 16, 16, "GATE B\ninput\nvalidator", fc=RED, fs=10)
    box(ax, 48, 44, 18, 16, "MODEL", fc=ORANGE, fs=10, bold=True)
    box(ax, 72, 44, 16, 16, "GATE A\noutput\nsandbox", fc=RED, fs=10)
    # PYTHON box moved to x=90 (right edge 98, not 100): at x=100 its
    # pad-extended edge sat on the axes boundary and was clipped by the crop.
    box(ax, 90, 44, 8, 16, "PYTHON\nexecutes", fc=GREEN, fs=10)

    arrow(ax, 20, 52, 26, 52, color=INK)
    arrow(ax, 42, 52, 48, 52, color=INK)
    arrow(ax, 66, 52, 72, 52, color=INK)
    arrow(ax, 88, 52, 90, 52, color=GREEN)

    # rejection branches drop down from each gate (downward exit)
    arrow(ax, 34, 44, 34, 34, color=RED)          # Gate B rejection drops down
    arrow(ax, 80, 44, 80, 34, color=RED)          # Gate A rejection drops down
    box(ax, 24, 16, 20, 14, "REJECTED at\nGate B", fc="#f6dede", ec=RED, fs=10, tc=RED)
    box(ax, 70, 16, 20, 14, "REJECTED at\nGate A", fc="#f6dede", ec=RED, fs=10, tc=RED)

    # yes/no labels ON THE OUTGOING branches: "no" on the downward rejection edge,
    # "yes" on the rightward accepted edge past each gate.
    ax.text(34, 39, "no", ha="center", va="bottom", fontsize=10, color=RED, style="italic", fontweight="bold")
    ax.text(45, 55, "yes", ha="center", va="bottom", fontsize=10, color=GREEN, style="italic", fontweight="bold")
    ax.text(80, 39, "no", ha="center", va="bottom", fontsize=10, color=RED, style="italic", fontweight="bold")
    ax.text(69, 55, "yes", ha="center", va="bottom", fontsize=10, color=GREEN, style="italic", fontweight="bold")

    # short, non-overlapping annotations above each gate
    note(ax, 24, 68, "is this request one of the\ndesigned tasks?", fs=10, color=RED)
    note(ax, 70, 68, "is this program inside\nthe whitelist?", fs=10, color=RED)
    note(ax, 24, 14, "refused before it\nreaches the model", fs=10, color=RED)
    note(ax, 70, 14, "refused before it\nruns", fs=10, color=RED)
    note(ax, 4, 90, "Gate A prevents the program being accepted/executed, not the model from\nemitting text; Gate B was NOT in the reported surface/human tests.",
         fs=10, color=INK)
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
    # semantic record box — use the real record fields (operation / args / output_type)
    box(ax, 34, 66, 32, 16, "SEMANTIC RECORD\noperation=add\nargs=[a:int, b:int]\noutput_type=int", fc=GREEN, fs=10)
    for dx in (21, 50, 79):
        arrow(ax, 50, 66, dx, 52)
    # three artefacts
    box(ax, 8, 34, 26, 16, "REFERENCE\nPROGRAM\n(ground truth)", fc=GREEN, fs=10)
    box(ax, 37, 34, 26, 16, "NL TASK\n(what the model\nreads)", fc=BLUE, fs=10)
    box(ax, 66, 34, 26, 16, "HIDDEN TESTS\n(input/expected\npairs)", fc=PURPLE, fs=10)
    note(ax, 10, 30, "one correct\nimplementation", fs=10, color=GREEN, ha="center")
    note(ax, 50, 30, "the instruction, in\nthe teacher's phrasing", fs=10, color=BLUE, ha="center")
    note(ax, 79, 30, "oracle outputs;\nchecked independently", fs=10, color=PURPLE, ha="center")
    # drift note in a clear call-out box at the bottom (no overlap, fully contained)
    # moved down (y6 -> y3) so the 10pt italic captions above clear its top border
    box(ax, 6, 3, 88, 16,
        "Semantic-first: the program, task, and tests all derive from ONE record.\n"
        "This reduces drift, but is not a guarantee — and the tests being\n"
        "independently implemented does not mean the oracle is independently\n"
        "validated. Renderer bugs or a shared wrong assumption can still make all\n"
        "three consistently wrong.",
        fc="#fbfaf6", ec=GREEN, fs=10, tc=INK)
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
    fig, ax = new_fig(w=9.0, h=5.2)
    ax.text(50, 95, "THE FOUR EVALUATION QUESTIONS", ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=INK)
    ax.text(50, 89, "four distinct questions -- they are not a ladder, and passing one\ndoes not establish the next.", ha="center", va="center", fontsize=10, color=INK)
    levels = [
        (64, "Q1  MEMORIZATION\nCould it just be remembering\na stored answer?", "bar1", "#c44e52"),
        (46, "Q2  DISTRIBUTIONAL GENERALIZATION\nDoes it work on new examples\nof the same task?", "bar2", "#dd8452"),
        (28, "Q3  SURFACE GENERALIZATION\nDoes it survive a change of\nwording or identifiers?", "bar3", "#55a868"),
        (10, "Q4  STRUCTURAL GENERALIZATION\nCan it combine things it knows\nin a way it never saw?", "bar4", "#4c72b0"),
    ]
    for y, lab, _k, c in levels:
        box(ax, 6, y, 88, 14, lab, fc=c, fs=10)
    # compact footer; the fuller qualification lives in the chapter text
    note(ax, 6, 5, "Report these separately — passing one question does not establish the next.", fs=10, color=INK)
    save(fig, "fig_ladder.png")

def fig_task():
    """D01 -- WHO SEES WHAT (ch03): the model generates source; Python executes it;
    hidden tests are evaluator-only. Two lanes so the model / execution / tests are
    impossible to conflate."""
    fig, ax = new_fig(w=9.2, h=5.6)
    ax.text(50, 96, "WHO SEES WHAT: the model generates code, Python runs it", ha="center",
            va="center", fontsize=10.5, fontweight="bold", color=INK)
    # TRAINING lane (top)
    ax.text(7, 86, "TRAINING lane", ha="left", fontsize=10, fontweight="bold", color=BLUE)
    box(ax, 7, 70, 26, 13, "NL SPEC + REFERENCE\n(the teacher's pair)", fc=BLUE, fs=10)
    box(ax, 40, 70, 26, 13, "MODEL\n(0.9M, trained)", fc=ORANGE, fs=10, tc="white")
    arrow(ax, 33, 76.5, 40, 76.5)
    note(ax, 30, 66, "learns a mapping\nrequest → program text", fs=10, color=ORANGE)

    # EVALUATION lane (bottom), two rows
    ax.text(7, 56, "EVALUATION lane", ha="left", fontsize=10, fontweight="bold", color=PURPLE)
    # row 1: request -> model -> candidate -> python
    box(ax, 7, 40, 21, 13, "REQUESTS\n(familiar prompts,\nnew inputs)", fc=BLUE, fs=10)
    box(ax, 32, 40, 21, 13, "TRAINED MODEL\n(generates source)", fc=ORANGE, fs=10, tc="white")
    box(ax, 57, 40, 21, 13, "CANDIDATE SOURCE\n(the program text)", fc=GREEN, fs=10)
    box(ax, 82, 40, 15, 13, "PYTHON\nRUNNER\n(executes)", fc="#e9f5eb", ec=GREEN, fs=10, tc=INK)
    arrow(ax, 28, 46.5, 32, 46.5)
    arrow(ax, 53, 46.5, 57, 46.5)
    arrow(ax, 78, 46.5, 82, 46.5)
    # trained checkpoint transfer (training MODEL -> eval MODEL) - placed to avoid overlap
    arrow(ax, 53, 70, 53, 55, color=ORANGE, lw=1.4)
    ax.text(55.5, 62.5, "trained checkpoint", ha="left", fontsize=10, color=ORANGE, style="italic")

    # row 2: test inputs -> python, expected & actual -> comparator
    box(ax, 7, 22, 30, 12, "TEST INPUTS\n(go to the Python runner)", fc="#eaf2fb", ec=BLUE, fs=10, tc=INK)
    box(ax, 41, 22, 28, 12, "EXPECTED VALUES\n(from the semantics)", fc=PURPLE, fs=10)
    box(ax, 82, 22, 15, 12, "ACTUAL\nVALUES", fc=GREEN, fs=10, tc="white")
    box(ax, 41, 4, 56, 12, "COMPARATOR — compares the Python output to the\nexpected values and issues the verdict", fc="white", ec=PURPLE, fs=10, tc=INK)
    # wiring: test inputs -> python runner; expected -> comparator; actual -> comparator
    arrow(ax, 22, 34, 82, 34, color=BLUE, rad=-0.15)          # test inputs rise to the runner
    arrow(ax, 69, 22, 69, 16, color=PURPLE)                   # expected -> comparator
    arrow(ax, 89.5, 22, 89.5, 16, color=GREEN)                # actual -> comparator

    # constraint strip, scoped to candidate execution
    ax.text(50, 1.5, "CANDIDATE EXECUTION · PURE FUNCTION (no I/O, no network, no random) · AST-WHITELISTED",
            ha="center", va="center", fontsize=10, color="#333333", style="italic")
    save(fig, "fig_task.png")


# =========================================================================
# 7. THE RIVALS (ch07) — model vs template vs retrieval baselines.
# =========================================================================
def fig_rivals():
    fig, ax = new_fig()
    ax.text(50, 95, "THE RIVALS: baselines keep us honest", ha="center",
            va="center", fontsize=11, fontweight="bold", color=INK)
    box(ax, 6, 62, 28, 18, "TEMPLATE\n'if task==add:\nreturn a+b'", fc=GREY, fs=10, tc=INK)
    box(ax, 38, 62, 26, 18, "RETRIEVAL\nnearest-neighbour\ncopy", fc=GREY, fs=10, tc=INK)
    box(ax, 70, 62, 24, 18, "OUR MODEL\n0.88M", fc=ORANGE, fs=10)
    note(ax, 6, 48, "a fixed hand-written\npattern. A sanity floor.", fs=10, color=INK)
    note(ax, 39, 48, "copies the closest\nmemory. A sanity check.", fs=10, color=INK)
    note(ax, 71, 48, "the actual question:\ndoes it beat them?", fs=10, color=INK)
    box(ax, 6, 14, 88, 18,
        "The baselines are sanity checks, not a score ceiling. A result is truthful\nif we know which baseline already solves it and whether the model adds anything.",
        fc="#fbfaf6", ec=INK, fs=10, tc=INK)
    save(fig, "fig_rivals.png")


# =========================================================================
# 8. THE SMALLEST BRAIN (ch08) — tokens -> embedding -> transformer -> output.
# =========================================================================
def fig_brain():
    """Figure 8.1 -- the architecture with actual numbers (emb dim, layers, heads)."""
    fig, ax = new_fig(w=9.4, h=5.0)
    ax.text(50, 96, "THE SMALLEST BRAIN: a 0.88M decoder-only GPT", ha="center",
            va="center", fontsize=10.5, fontweight="bold", color=INK)
    # pipeline with real dimensions
    box(ax, 4, 70, 20, 14, "TOKENS\n(291 vocab)", fc=BLUE, fs=10)
    box(ax, 31, 70, 18, 14, "EMBED\ntok=291×128\npos=128×128", fc=BLUE, fs=10)
    box(ax, 56, 70, 20, 14, "4 BLOCKS\ncausal attention\nMLP 128→512→128", fc=ORANGE, fs=10)
    box(ax, 82, 70, 16, 14, "OUTPUT\n291 logits\n→ sampled token", fc=GREEN, fs=10)
    arrow(ax, 24, 77, 31, 77)
    arrow(ax, 49, 77, 56, 77)
    arrow(ax, 76, 77, 82, 77)
    # autoregressive feedback loop routed BELOW the block (high-contrast, avoids the title)
    arrow(ax, 90, 70, 90, 46, color=INK, lw=1.2, style="-|>", ls="--")
    arrow(ax, 90, 46, 8, 46, color=INK, lw=1.2, ls="--")
    arrow(ax, 8, 46, 8, 70, color=INK, lw=1.2, style="-|>", ls="--")
    # label centred at x=27 (left of the size-sweep box at x=56) so the 10pt
    # line does not overflow/collide with that box.
    ax.text(27, 42, "the sampled output token is fed back as the next input",
            ha="center", fontsize=10, color=INK, style="italic")
    # key dimensions note
    note(ax, 4, 64, "parameters: 884,224 total (53,632 embedding\n+ 830,592 non-embedding). 4 layers × 4 heads,\nn_embd=128, block_size=128, temperature-0.8\nsampled decoding.", fs=10, color=INK)
    box(ax, 56, 26, 42, 22, "same architecture, just wider / deeper\nfor the size sweep (6.5M, 10.2M, 29.3M).",
        fc="#fbfaf6", ec=INK, fs=10, tc=INK)
    box(ax, 4, 6, 94, 14, "This is the instrument. The experiment is the subject — the book is about what\nthe model learns, not about how big it is.",
        fc="#fbfaf6", ec=INK, fs=10, tc=INK)
    save(fig, "fig_brain.png")

def fig_brew():
    """Figure 9.1 -- the brew loop, distinguishing training from the final audit."""
    fig, ax = new_fig(w=9.4, h=5.6)
    ax.text(50, 96, "THE BREW LOOP", ha="center", va="center", fontsize=11,
            fontweight="bold", color=INK)
    # --- DEV LOOP (top): generate -> train -> dev evaluate (-> back to generate) ---
    box(ax, 8, 70, 26, 14, "GENERATE DATA\n(semantic-first)", fc=GREEN, fs=10)
    box(ax, 40, 70, 26, 14, "TRAIN\nfixed step budget\n(e.g. 1500 steps)", fc=ORANGE, fs=10)
    box(ax, 72, 70, 22, 14, "DEV EVALUATE\n(informs iteration)", fc=PURPLE, fs=10)
    arrow(ax, 34, 77, 40, 77)
    arrow(ax, 66, 77, 72, 77)
    # dev feedback edge: a separate loop above the boxes, back to GENERATE DATA
    arrow(ax, 83, 84, 21, 84, color=PURPLE, lw=1.2)
    arrow(ax, 21, 84, 21, 76, color=PURPLE, lw=1.2)
    ax.text(51, 88, "dev feedback: what we measure (loss / dev score) shapes the next round of data & hyperparams.",
            ha="center", fontsize=10, color=PURPLE, style="italic")

    # --- FINAL AUDIT (bottom, separate lane) ---
    box(ax, 36, 40, 34, 14, "FINAL AUDIT\n(one report on the\nfrozen test records)", fc=BLUE, fs=10)
    arrow(ax, 53, 70, 53, 56, color=BLUE)
    note(ax, 72, 44, "recommended workflow: the final audit runs once\non the frozen records and is NOT fed back to\nchange training. (In our runs the pilot test records\nreused the training prompt strings -- see the novelty\naudit -- so 'frozen' refers to the record list, not to\ngenuinely-seen-new prompts.)", fs=10, color=INK)
    note(ax, 8, 44, "the dev loop that iterates is separate\nfrom the one-time final audit.", fs=10, color=INK, ha="center")

    note(ax, 8, 18, "each dev pass feeds the next: what we measure shapes what we generate;\nbut the headline numbers come from a single frozen audit, not an adaptive one.",
         fs=10, color=INK, ha="center")
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
                txt, tc = v, "#2b8a3e"
            ax.text(x+(cw-0.6)/2, y+rh*0.45, txt, ha="center", va="center", fontsize=10, color=tc)
    note(ax, 3, 4, "Green = measured strong result. Red = measured zero. NT = not tested. " +
          "The high-diversity 1.000 is *coverage* of surfaces in its training family, not transfer to an excluded wording family.",
         fs=10, color=INK)
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
    # labels wrapped to 2 lines so the 10pt text clears the bars (which start at
    # x=30); a single 10pt line for row 2/3 overran into the bar.
    labels = ["1. Sequential\n(measured)",
              "2. Joint (measured)\nA and B interleaved",
              "3. True replay-after-A\n(not run)"]
    for row, (lab, style) in enumerate(zip(labels, ["solid", "solid", "dashed"])):
        y = 78 - row*24
        ax.text(2, y+4, lab, ha="left", fontsize=10, color=INK)
        # timeline bar
        ax.add_patch(FancyBboxPatch((30, y), 62, 6, boxstyle="round,pad=0.02,rounding_size=1",
                                    fc="#eef1f5", ec=INK, lw=1.0, linestyle="--" if style=="dashed" else "-"))
        # A and B segments
        seg = (30, 30, 30)  # x start widths for A, B
        if row == 0:   # sequential: full A then full B
            ax.add_patch(FancyBboxPatch((30, y+1), 31, 4, fc=BLUE, ec=BLUE, lw=0.5))
            ax.add_patch(FancyBboxPatch((61, y+1), 31, 4, fc=GREEN, ec=GREEN, lw=0.5))
            ax.text(45.5, y+3, "A", ha="center", va="center", fontsize=10, color="white")
            ax.text(76.5, y+3, "B", ha="center", va="center", fontsize=10, color="white")
        elif row == 1: # joint: A and B interleaved
            ax.add_patch(FancyBboxPatch((30, y+1), 62, 4, fc=GREY, ec=GREY, lw=0.5))
            ax.text(61, y+3, "A + B (interleaved)", ha="center", va="center", fontsize=10, color=INK)
        else:          # true replay (not run)
            ax.add_patch(FancyBboxPatch((30, y+1), 31, 4, fc=BLUE, ec=BLUE, lw=0.5))
            ax.add_patch(FancyBboxPatch((61, y+1), 31, 4, fc=GREEN, ec=GREEN, lw=0.5))
            ax.text(45.5, y+3, "A", ha="center", va="center", fontsize=10, color="white")
            ax.text(76.5, y+3, "B (+ replay of A)", ha="center", va="center", fontsize=10, color="white")
    note(ax, 2, 6, "The book's 'replay/mixed' condition interleaves A and B from the start --- that is JOINT training (row 2), not replay-after-A-first (row 3). Solid rows were measured; the dashed row is a design we did not run. (Rows are schematic, not to scale.)",
         fs=10, color=INK)
    save(fig, "fig_continual_timelines.png")


def fig_three_meanings():
    """D08 -- ONE TASK, THREE MEANINGS OF 'NEW' (ch2 / ch9 box).

    Three cases that all get loosely called 'a new task' but differ in what is
    actually new to the MODEL INPUT: (1) new task ID, same prompt+program, only the
    hidden tests change; (2) genuinely new prompt, same target program; (3) an unseen
    program structure (composition). Only #2/#3 are new to the model input; #1 is new
    only to the evaluator.
    """
    fig, ax = new_fig(w=9.4, h=5.4)
    ax.text(50, 96, "ONE TASK, THREE MEANINGS OF 'NEW'", ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=INK)
    ax.text(50, 90, "What is actually new to the MODEL INPUT?  (green = new to model; grey = not)",
            ha="center", va="center", fontsize=10, color=INK)
    rows = [
        ("1. New task ID,\nsame prompt + program", "same", "same", "different", "grey",
         "only the evaluator's hidden tests change\n-- NOT a new example for the model"),
        ("2. New prompt,\nsame target program", "different", "same", "same", "green",
         "a new surface, same computation\n-- genuinely a new model input"),
        ("3. Unseen\nprogram structure", "different", "different", "different", "green",
         "composing pieces never combined\n-- new input AND new target structure"),
    ]
    headers = ["case", "prompt", "target program", "hidden tests", "new to model?"]
    cols = ["case", "prompt", "target\nprogram", "hidden\ntests", "new to\nmodel input?"]
    colx = [3, 25, 43, 61, 80]
    for c, h in zip(colx, cols):
        ax.text(c+7, 82, h, ha="center", fontsize=10, fontweight="bold", color=INK)
    for r, (lab, pr, prog, test, kind, cap) in enumerate(rows):
        y = 72 - r*22
        box(ax, 3, y, 18, 12, lab, fc="#eef1f5", fs=10, tc=INK)
        ax.text(31, y+6, pr, ha="center", fontsize=10, color=INK)
        ax.text(49, y+6, prog, ha="center", fontsize=10, color=INK)
        ax.text(67, y+6, test, ha="center", fontsize=10, color=INK)
        fc = "#e0f0e4" if kind == "green" else "#dddddd"
        ax.text(87, y+6, "YES" if kind=="green" else "NO", ha="center", fontsize=10,
                fontweight="bold", color="#2b8a3e" if kind=="green" else "#888888")
        ax.text(50, y-6, cap, ha="center", fontsize=10, color=INK, style="italic")
    note(ax, 3, 4, "A 'new task ID' that only changes the hidden tests is NOT a new model input.\n"
          "Report prompt/program novelty, not just task-ID counts.", fs=10, color=INK)
    save(fig, "fig_three_meanings.png")


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
            ha="center", va="center", fontsize=10, color=INK)
    # left: abs(a + b)
    ax.text(25, 76, "abs(a + b)", ha="center", fontsize=10, fontweight="bold", color=BLUE)
    ax.text(25, 66, "absolute value of the sum", ha="center", fontsize=10, color=INK)
    # tree: sum node -> abs
    box(ax, 19, 46, 12, 8, "a + b", fc=BLUE, fs=10)
    ax.text(9, 38, "a = -3, b = 2\n→ a+b = -1", ha="center", fontsize=10,
            color=INK, va="center")
    box(ax, 19, 26, 12, 8, "abs(-1)", fc=BLUE, fs=10)
    ax.text(25, 18, "= 1", ha="center", fontsize=10, fontweight="bold", color=BLUE)
    arrow(ax, 25, 46, 25, 34)
    arrow(ax, 25, 34, 25, 26)

    # right: abs(a) + abs(b)
    ax.text(75, 76, "abs(a) + abs(b)", ha="center", fontsize=10, fontweight="bold", color=GREEN)
    ax.text(75, 66, "sum of the absolute values  (this is abs_add)", ha="center", fontsize=10, color=INK)
    box(ax, 62, 50, 11, 8, "abs(a)", fc=GREEN, fs=10)
    box(ax, 78, 50, 11, 8, "abs(b)", fc=GREEN, fs=10)
    ax.text(64, 42, "abs(-3) = 3", ha="center", fontsize=10, color=INK)
    ax.text(87, 42, "abs(2) = 2", ha="center", fontsize=10, color=INK)
    box(ax, 70, 30, 12, 8, "3 + 2", fc=GREEN, fs=10)
    ax.text(76, 22, "= 5", ha="center", fontsize=10, fontweight="bold", color=GREEN)
    arrow(ax, 68, 50, 73, 38); arrow(ax, 82, 50, 80, 38)
    arrow(ax, 76, 38, 76, 30)

    note(ax, 50, 8, "These are mathematically different functions (outputs 1 vs 5 for the same input). "
          + "The composite in this book, abs_add, is the right-hand one: abs(a) + abs(b).",
         fs=10, color=INK)
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
    ax.text(23, 86, "what was measured", ha="center", fontsize=10, fontweight="bold", color=INK)
    # family set axis
    ax.add_patch(FancyBboxPatch((6, 30), 34, 6, boxstyle="round,pad=0.02,rounding_size=1",
                                fc="#eef1f5", ec=GREY, lw=0.8))
    ax.text(23, 33, "the training family set", ha="center", fontsize=10, color="#333333", va="center")
    # model trained on all families (illustrative labels only)
    for i, fam in enumerate(["α", "β", "γ"]):
        x = 8 + i*10
        ax.add_patch(FancyBboxPatch((x, 46), 9, 9, boxstyle="round,pad=0.02,rounding_size=1",
                                    fc="#cfe0f5", ec=INK, lw=0.8))
        ax.text(x+4.5, 50.5, fam, ha="center", fontsize=10, color=INK)
    ax.text(21, 41, "high-diversity training: sees all families (illustrative α / β / γ)", ha="center", fontsize=10, color=INK)
    # surface test point (well above the families, not overlapping)
    # box widened (9 -> 15) so the 10pt "surface test" label does not overflow
    ax.add_patch(FancyBboxPatch((21, 66), 15, 8, boxstyle="round,pad=0.02,rounding_size=1",
                                fc="#e0f0e4", ec=GREEN, lw=0.8))
    ax.text(28.5, 70, "surface test", ha="center", fontsize=10, color=INK)
    ax.text(28.5, 60, "test is IN the training family set\n→ 1.000 is coverage", ha="center",
            fontsize=10, color=GREEN)
    ax.text(23, 20, "So the high-diversity 1.000 is COVERAGE of surfaces it was trained on,\nnot generalization to a wording family it never saw.",
            ha="center", fontsize=10, color=INK)

    # proposed holdout panel (right, dashed)
    ax.text(74, 92, "what a true holdout needs  (proposed, not measured)", ha="center",
            fontsize=10, fontweight="bold", color=PURPLE)
    ax.add_patch(FancyBboxPatch((58, 20), 32, 64, boxstyle="round,pad=0.02,rounding_size=2",
                                fc="#fbfaf6", ec=PURPLE, lw=1.0, linestyle="--"))
    for i, fam in enumerate(["α", "β", "γ", "δ"]):
        fc = "#cfe0f5" if i < 3 else "#f6dede"
        x = 60 + i*7.5
        ax.add_patch(FancyBboxPatch((x, 66), 6.5, 9, boxstyle="round,pad=0.02,rounding_size=1",
                                    fc=fc, ec=INK, lw=0.7))
        ax.text(x+3.2, 70.5, fam, ha="center", fontsize=10, color=INK)
    ax.text(74, 60, "train on α/β/γ, hold out δ (illustrative)", ha="center", fontsize=10, color=INK)
    ax.add_patch(FancyBboxPatch((64, 40), 20, 9, boxstyle="round,pad=0.02,rounding_size=1",
                                fc="#f6dede", ec=RED, lw=0.8))
    # wrapped to 2 lines so the 10pt label fits the 20-unit box width
    ax.text(74, 44.5, "test on family δ\n(never seen)", ha="center", va="center",
            fontsize=10, color=RED)
    ax.text(74, 30, "only this tests generalization\nto an EXCLUDED family", ha="center", fontsize=10, color=INK)
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
