#!/usr/bin/env python3
"""Generate the book's recurring figures from MEASURED data (no invented numbers).
Figures per design section 35 (visual language).

Legibility/production pass (external review P1-PROD-03, P1-08/11/14/15.1):
  * primary labels >= ~10pt at the figure's rendered width (book textwidth =
    325.215pt = 4.507in; titles are wrapped and notes kept short so the
    tight-cropped natural width stays ~= figsize width, keeping
    F * 4.507 / natural_width >= ~10pt for primary type),
  * high contrast (dark ink, no pale-grey-on-color annotations),
  * grayscale-safe encoding (hatching + distinct markers/linestyles, never
    red/green as the ONLY success/failure signal),
  * direct labels and raw counts on the data,
  * Fig 13.1 titled/labeled "covered alternate surfaces" (not unseen-family
    generalization), Fig 11.1 marked one-seed/540-records/coverage-unverified,
    Fig 15.1 uses "new variable identifiers" naming.

Run: python scripts/make_figures.py
"""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIG = os.path.join(ROOT, "book", "figures")
os.makedirs(FIG, exist_ok=True)

# ---- shared high-contrast, grayscale-safe palette ----
INK      = "#1a1a1a"   # near-black text (max contrast on white)
BLUE     = "#2f5f9f"   # darker blue -- series 1
GREEN    = "#2e7d32"   # darker green -- series 2
RED      = "#b02a30"   # darker red   -- series 3 / zero
GREY     = "#5a5a5a"   # mid-dark grey for neutral (never pale)
# font scale: primary 13pt on ~5.4in figures -> >= ~10.8pt at 4.507in render
FS_TICK   = 13
FS_LABEL  = 13
FS_VALUE  = 13
FS_COUNT  = 11
FS_TITLE  = 14.5
FS_NOTE   = 11
FS_LEGEND = 12


def load(path):
    return json.load(open(path))


def save(fig, name):
    p = os.path.join(FIG, name)
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)
    return p


# ==========================================================================
# 1. Model size vs composition -- Figure 12.1 (measured, 4 points)
# 10.2M uses the clean-retrain value (0.773); the original 0.383 was a SIGILL
# training-run artifact (see docs/experiments/scaling_composition.md).
# Values exact to artifacts/manifests/stage4_scaling.json (Appendix C.5):
#   0.88M baseline in-distribution = 0.9167 (55/60), NOT the unbacked 0.900.
# Grayscale-safe: solid+circles vs dashed+squares, direct value labels.
# ==========================================================================
fig, ax = plt.subplots(figsize=(5.4, 4.2))
params = [0.88e6, 6.5e6, 10.2e6, 29.3e6]        # exact parameter counts
in_dist = [0.9167, 0.897, 0.773, 0.897]
in_dist_labels = ["0.9167", "0.897", "0.773", "0.897"]
comp    = [0.000, 0.000, 0.000, 0.000]
ax.plot(params, in_dist, "o-", color=BLUE, lw=2.2, ms=9,
        label="in-distribution pass@1", zorder=3)
ax.plot(params, comp, "s--", color=RED, lw=2.2, ms=9,
        label="held-out composite pass@1", zorder=3)
for xi, v, t in zip(params, in_dist, in_dist_labels):
    ax.annotate(t, (xi, v), textcoords="offset points", xytext=(0, 12),
                ha="center", fontsize=FS_VALUE, color=BLUE, fontweight="bold")
# label only the endpoints of the flat zero line (all four are 0.000; labeling
# every point makes the two middle labels collide on the log axis)
for i in (0, 3):
    ax.annotate("0.000", (params[i], comp[i]), textcoords="offset points",
                xytext=(0, -20), ha="center", fontsize=FS_VALUE, color=RED,
                fontweight="bold")
ax.set_xscale("log")
ax.margins(x=0.12)  # room so the edge-point value labels are not clipped
ax.set_xticks(params)
ax.set_xticklabels(["0.88M", "6.5M", "10.2M", "29.3M"], fontsize=FS_TICK,
                   rotation=30, ha="right", rotation_mode="anchor")
# x-axis label + scope note merged into ONE text block: as a separate transAxes
# text the rotated tick labels kept pushing the axis label down onto the note.
ax.set_xlabel("tested configuration (params, log scale)\n"
              "one run per config; step budgets\n"
              "(1,500/1,000/800/800) and tokenizers\n"
              "differ -- not a size-only sweep",
              fontsize=FS_LABEL, color=INK)
ax.set_ylim(-0.24, 1.12)
ax.set_ylabel("pass@1", fontsize=FS_LABEL)
ax.set_title("Model size vs composition\n(measured, 4 runs)",
             fontsize=FS_TITLE, fontweight="bold", color=INK, pad=8)
# legend in the empty band between the blue line and the flat zero line so it
# cannot collide with the data
ax.legend(loc="center", bbox_to_anchor=(0.5, 0.38), frameon=False,
          fontsize=FS_LEGEND, labelcolor=INK)
ax.grid(alpha=0.28, which="both")
# scope note is merged into the x-axis label above (a separate transAxes text
# overlapped the axis label once the tick labels were rotated).
fig.tight_layout()
save(fig, "fig_model_size.png")

# ==========================================================================
# 2. Surface generalization -- Figure 15.1 (measured, one seed, n=600/cond)
# Values exact to artifacts/manifests/stage3_surface.json:
#   model 0.900/0.350/0.000, template 0.800/0.800/0.875, retrieval 1.000/0.683/0.125
# Raw counts (of 600 = 10 ops x 60): model 540/210/0, template 480/480/525,
#   retrieval 600/410/75 (410/600=0.683, 525/600=0.875, 75/600=0.125).
# "new IDs" -> "new variable identifiers" (P2-PROD-05 / 15.1 variable naming).
# Grayscale-safe: distinct hatching per series + direct value labels; counts in
#   a note (they would overlap if stacked under the 9 tightly-grouped bars).
# ==========================================================================
fig, ax = plt.subplots(figsize=(5.7, 4.5))
labels = ["in-distribution", "new variable\nidentifiers", "reworded\nwording"]
model = [0.900, 0.350, 0.000]
template = [0.800, 0.800, 0.875]
retrieval = [1.000, 0.683, 0.125]
C_MODEL, C_TEMPLATE, C_RETRIEVAL = BLUE, GREEN, RED
x = np.arange(len(labels)); w = 0.25
ax.bar(x-w, model, w, label="MODEL", color=C_MODEL, edgecolor=INK)
ax.bar(x, template, w, label="TEMPLATE", color=C_TEMPLATE, edgecolor=INK, hatch="//")
ax.bar(x+w, retrieval, w, label="RETRIEVAL", color=C_RETRIEVAL, edgecolor=INK, hatch="xx")
# value labels rotated 90 deg so each stays within its own bar column and
# cannot run into a taller neighbouring bar
for xi, v in zip(x-w, model):
    ax.text(xi, v+0.02, f"{v:.3f}", ha="center", va="bottom", rotation=90,
            fontsize=FS_VALUE, color=INK, fontweight="bold")
for xi, v in zip(x, template):
    ax.text(xi, v+0.02, f"{v:.3f}", ha="center", va="bottom", rotation=90,
            fontsize=FS_VALUE, color=INK, fontweight="bold")
for xi, v in zip(x+w, retrieval):
    ax.text(xi, v+0.02, f"{v:.3f}", ha="center", va="bottom", rotation=90,
            fontsize=FS_VALUE, color=INK, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=FS_TICK)
ax.set_ylim(0, 1.30)  # headroom for the rotated value labels
ax.set_ylabel("pass@1", fontsize=FS_LABEL)
ax.set_title("Surface generalization\n(one seed, n=600 per condition)",
             fontsize=FS_TITLE, fontweight="bold", color=INK, pad=34)
# legend above the axes (outside the plot) so it cannot collide with the tall
# reworded-wording bar's 0.875 value label
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.00), ncol=3,
          frameon=False, fontsize=FS_LEGEND, labelcolor=INK)
ax.grid(axis="y", alpha=0.28)
# raw counts (of 600) + provenance caveat (P0-02 / 15.1): historical excluded-
# family membership not re-verified on the original scored file.
ax.text(0.5, -0.26,
        "raw counts of 600 (in-dist / new IDs / reworded):\n"
        "MODEL 540/210/0  ·  TEMPLATE 480/480/525  ·  RETRIEVAL 600/410/75\n"
        "held-out wording-family membership not re-verified on the scored file",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=FS_NOTE, color=INK)
fig.tight_layout()
save(fig, "fig_surface.png")

# ==========================================================================
# 3. Data scaling -- Figure 11.1 (measured, one seed)
# Values exact to artifacts/manifests/data_scaling.json:
#   0.100 / 0.098 / 0.300 / 0.641 over one 540-record pool_test.
# Raw counts (from ch11): 54/540, 53/540, 162/540, 346/540.
# P1-11: mark one seed / 540 test records / coverage unverified on the plot.
# ==========================================================================
fig, ax = plt.subplots(figsize=(5.5, 4.2))
sizes = [100, 300, 1000, 3000]
perf = [0.100, 0.098, 0.300, 0.641]
counts = ["54/540", "53/540", "162/540", "346/540"]
labelsize = {100: "100", 300: "300", 1000: "1,000", 3000: "3,000"}
ax.plot(sizes, perf, "o-", color=BLUE, lw=2.2, ms=9, zorder=3)
for x, y, c in zip(sizes, perf, counts):
    ax.annotate(f"{y:.3f}", (x, y), textcoords="offset points", xytext=(0, 14),
                ha="center", fontsize=FS_VALUE, color=BLUE, fontweight="bold")
    ax.annotate(c, (x, y), textcoords="offset points", xytext=(0, -22),
                ha="center", fontsize=FS_COUNT, color=INK)
ax.set_xscale("log")
ax.margins(x=0.10)  # first point off the left edge so its count label clears the 0.0 tick
ax.set_xlabel("training examples (log scale)", fontsize=FS_LABEL)
ax.set_ylabel("pass@1", fontsize=FS_LABEL)
ax.set_xticks(sizes)
ax.set_xticklabels([labelsize[s] for s in sizes], fontsize=FS_TICK)
ax.set_ylim(-0.14, 1.10)
ax.set_title("Data scaling (measured, one seed)",
             fontsize=FS_TITLE, fontweight="bold", color=INK, pad=8)
ax.grid(alpha=0.28)
# P1-11 scope banner: one seed, 540 test records, coverage unverified.
ax.text(0.5, 0.96,
        "one seed  ·  540 test records  ·  coverage unverified",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=FS_NOTE, color=RED, fontweight="bold")
ax.text(0.5, -0.26,
        "counts = successes / 540 shared pool_test records",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=FS_NOTE, color=INK)
fig.tight_layout()
save(fig, "fig_data_scaling.png")

# ==========================================================================
# 4. Diversity vs quantity -- Figure 13.1 (measured, one seed)
# Values exact to artifacts/manifests/diversity.json:
#   minimal 0.500 in-dist / 0.000 surface ; high 1.000 / 1.000 (n_train=1200, seed 0).
# P1-08/13.1: title + legend must say "covered alternate surfaces", NOT
#   unseen-family generalization. The high-diversity 1.000 is coverage of
#   wording families seen in training.
# Grayscale-safe: solid vs hatched bars + direct value labels.
# ==========================================================================
fig, ax = plt.subplots(figsize=(5.6, 4.4))
labels = ["minimal diversity", "high diversity"]
in_d = [0.500, 1.000]
surf = [0.000, 1.000]
x = np.arange(len(labels)); w = 0.3
ax.bar(x-w/2, in_d, w, label="in-distribution", color=BLUE, edgecolor=INK)
ax.bar(x+w/2, surf, w, label="covered alternate surfaces\n(seen families)",
       color=GREEN, edgecolor=INK, hatch="//")
for xi, v in zip(x-w/2, in_d):
    ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=FS_VALUE, color=INK, fontweight="bold")
for xi, v in zip(x+w/2, surf):
    ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=FS_VALUE, color=INK, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=FS_TICK)
ax.set_ylim(0, 1.18)
ax.set_ylabel("pass@1", fontsize=FS_LABEL)
ax.set_title("Diversity vs quantity:\ncovered alternate surfaces",
             fontsize=FS_TITLE, fontweight="bold", color=INK, pad=8)
ax.text(0.5, -0.22,
        "same 1,200-record count, same test, one seed --\n"
        "the high-diversity 1.000 is COVERAGE of trained\n"
        "wording families, not unseen-family generalization",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=FS_NOTE, color=INK)
ax.legend(loc="upper left", frameon=False, fontsize=FS_LEGEND, labelcolor=INK)
ax.grid(axis="y", alpha=0.28)
fig.tight_layout()
save(fig, "fig_diversity.png")

# ==========================================================================
# 5. Continual learning -- Figure 18.1 (measured)
# Rename to sequential vs JOINT training (the review's R08/D05 point); label the
# joint condition as final task accuracy, not "retention".
# Values exact to artifacts/manifests/continual{,_preB}.json:
#   sequential A-after-A 1.000, final A 0.000, final B 0.889; joint A 1.000, B 0.889.
# Grayscale-safe: distinct hatching + direct labels; legend outside the axes.
# ==========================================================================
fig, ax = plt.subplots(figsize=(5.9, 4.6))
labels = ["sequential\n(A then B)", "joint\n(A+B)"]
a_final = [0.000, 1.000]
a_afterA = [1.000, 0.0]   # sequential only: A measured right after phase A
b_acq = [0.889, 0.889]
x = np.arange(len(labels)); w = 0.28
ax.bar(x-w, a_afterA, w, label="A right after phase A (sequential, before B)",
       color="#9db8dd", edgecolor=INK, hatch="..")
ax.bar(x, a_final, w, label="final A-task accuracy", color=BLUE, edgecolor=INK, hatch="////")
ax.bar(x+w, b_acq, w, label="final B-task accuracy", color=GREEN, edgecolor=INK, hatch="xx")
for xi, v in zip(x-w, a_afterA):
    if v and v > 0.001:
        ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=FS_VALUE, color=INK, fontweight="bold")
for xi, v in zip(x, a_final):
    ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=FS_VALUE, color=INK, fontweight="bold")
for xi, v in zip(x+w, b_acq):
    ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=FS_VALUE, color=INK, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=FS_TICK)
ax.set_ylim(0, 1.18)
ax.set_ylabel("pass@1", fontsize=FS_LABEL)
ax.set_title("Task accuracy: sequential\nvs joint training (measured)",
             fontsize=FS_TITLE, fontweight="bold", color=INK, pad=26)
# Legend outside the axes (below) so it cannot overlap the data/labels; hatch
# as well as color so the chart survives grayscale printing.
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=1,
          frameon=False, fontsize=FS_LEGEND, labelcolor=INK)
ax.grid(axis="y", alpha=0.28)
# note above the axes (outside the plot) so it cannot collide with the joint
# group's 1.000 value label
ax.text(0.5, 1.03, "one run per condition (seed 0)", transform=ax.transAxes,
        ha="center", va="bottom", fontsize=FS_NOTE, color=INK, style="italic")
fig.tight_layout()
save(fig, "fig_continual.png")

# ==========================================================================
# 6. Live behavior sweep -- Figure 12.2 (illustrative prompts, NOT a score)
# From scripts/sweep_models.py. Cells are one illustrative prompt per case.
# P1-12.2: add "NOT A SCORE / ONE PROMPT PER CELL" in the graphic, use
#   hatching/patterns (not red/green alone) and full checkpoint names.
# 'out-of-scope' is NOT a task failure -- it is a request Gate B would decline.
# ==========================================================================
fig, ax = plt.subplots(figsize=(5.7, 4.4))
models = ["0.88M pilot", "0.88M surface", "6.5M", "10.2M", "29.3M (30M)"]
cases = ["familiar\nsum", "familiar\nproduct", "reworded", "new\ncombination",
         "out-of-\nscope"]  # col5 wrapped: on one line it ran into col4's "new"
# 1=correct program, 0=no valid program, 2=out-of-scope (unscored, not a task)
data = np.array([
    [1, 1, 0, 0, 2],
    [1, 1, 0, 0, 2],
    [1, 1, 0, 0, 2],
    [1, 1, 0, 0, 2],
    [1, 1, 0, 0, 2],
])
nrow, ncol = data.shape
# grayscale-safe cell fills + hatching (never color alone): correct = light
# green + check; no-valid-program = light red + '//' hatch + cross; out-of-
# scope = grey + 'xx' hatch + en-dash (neutral, unscored).
face = {1: "#cfe8d2", 0: "#f4cccc", 2: "#d9d9d9"}
hatch = {1: "", 0: "//", 2: "xx"}
edge = {1: GREEN, 0: RED, 2: GREY}
mark = {1: "\u2713", 0: "\u2717", 2: "\u2013"}
mcol = {1: "#145a24", 0: "#7a1a1e", 2: "#333333"}
for i in range(nrow):
    for j in range(ncol):
        v = data[i, j]
        ax.add_patch(mpatches.Rectangle((j - 0.5, nrow - 1 - i - 0.5), 1, 1,
                                        facecolor=face[v], edgecolor=edge[v],
                                        hatch=hatch[v], lw=1.6))
        ax.text(j, nrow - 1 - i, mark[v], ha="center", va="center",
                color=mcol[v], fontsize=16, fontweight="bold")
ax.set_xlim(-0.5, ncol - 0.5)
ax.set_ylim(-0.5, nrow - 0.5)
ax.set_xticks(np.arange(ncol))
ax.set_xticklabels(cases, fontsize=11)  # 13pt made adjacent 8-char headers touch
ax.set_yticks(np.arange(nrow))
ax.set_yticklabels(models, fontsize=FS_TICK)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title("Illustrative prompts on five\nselected checkpoints",
             fontsize=FS_TITLE, fontweight="bold", color=INK, pad=30)
# in-graphic banner so the grid cannot be read as a statistical score (P1-12.2)
ax.text(0.5, 1.04, "NOT A SCORE  \u00b7  ONE PROMPT PER CELL",
        transform=ax.transAxes, ha="center", va="bottom",
        fontsize=FS_NOTE, color=RED, fontweight="bold")
ax.set_ylabel("checkpoint (params)", fontsize=FS_LABEL)
ax.legend(handles=[
            mpatches.Patch(facecolor="#cfe8d2", edgecolor=GREEN, hatch="",
                           label="\u2713 correct program"),
            mpatches.Patch(facecolor="#f4cccc", edgecolor=RED, hatch="//",
                           label="\u2717 no valid program"),
            mpatches.Patch(facecolor="#d9d9d9", edgecolor=GREY, hatch="xx",
                           label="\u2013 out of scope (unscored, not a task)")],
          loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=1,
          frameon=False, fontsize=FS_LEGEND, labelcolor=INK)
fig.tight_layout()
save(fig, "fig_live_sweep.png")