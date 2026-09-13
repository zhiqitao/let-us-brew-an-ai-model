#!/usr/bin/env python3
"""Generate the book's recurring figures from MEASURED data (no invented numbers).
Figures per design section 35 (visual language).
Run: python scripts/make_figures.py
"""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIG = os.path.join(ROOT, "book", "figures")
os.makedirs(FIG, exist_ok=True)

def load(path):
    return json.load(open(path))

def save(fig, name):
    p = os.path.join(FIG, name)
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)
    return p

# ---- 1. Model-size vs composition (measured, 4 points) ----
# 10.2M uses the clean-retrain value (0.773); the original 0.383 was a SIGILL
# training-run artifact (see docs/experiments/scaling_composition.md).
# Line form (not grouped bars) because composition is uniformly 0.000: a
# ---- 1. Model size (measured) ----
# Use a TRUE numeric log-parameter axis so the x-spacing is quantitative (not an
# equally-spaced categorical plot that implies a meaningful size-response slope).
fig, ax = plt.subplots()
params = [0.88e6, 6.5e6, 10.2e6, 29.3e6]        # exact parameter counts
in_dist = [0.900, 0.897, 0.773, 0.897]
comp    = [0.000, 0.000, 0.000, 0.000]
ax.plot(params, in_dist, "o-", color="#4C72B0", lw=2, ms=8, label="in-distribution")
ax.plot(params, comp,    "s-", color="#C44E52", lw=2, ms=8, label="composition")
for xi, v in zip(params, in_dist): ax.annotate(f"{v:.3f}", (xi, v), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8, color="#4C72B0")
for xi, v in zip(params, comp):    ax.annotate(f"{v:.3f}", (xi, v), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8, color="#C44E52", fontweight="bold")
ax.set_xscale("log")
ax.set_xticks(params); ax.set_xticklabels(["0.88M", "6.5M", "10.2M", "29.3M"])
ax.set_xlabel("model parameters (log scale)")
ax.set_ylim(-0.10, 1.05); ax.set_ylabel("pass@1")
ax.set_title("Model size: in-distribution vs composition (measured, 4 runs)")
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.02), frameon=False, fontsize=8)
ax.grid(alpha=0.3, which="both")
fig.tight_layout()
save(fig, "fig_model_size.png")

# ---- 2. Surface generalization (measured) ----
# Consistent model/template/retrieval colors across all figures; direct numeric
# labels so an explicit 0.000 is visible (a zero-height bar is invisible).
fig, ax = plt.subplots()
labels = ["in-dist", "new IDs", "new wording"]
model = [0.900, 0.350, 0.000]; template = [0.800, 0.800, 0.875]; retrieval = [1.000, 0.683, 0.125]
C_MODEL, C_TEMPLATE, C_RETRIEVAL = "#4C72B0", "#55A868", "#C44E52"
x = np.arange(len(labels)); w = 0.25
ax.bar(x-w, model, w, label="MODEL", color=C_MODEL)
ax.bar(x, template, w, label="TEMPLATE", color=C_TEMPLATE, hatch="//")
ax.bar(x+w, retrieval, w, label="RETRIEVAL", color=C_RETRIEVAL, hatch="xx")
for xi, v in zip(x-w, model): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=7)
for xi, v in zip(x, template): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=7)
for xi, v in zip(x+w, retrieval): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=7)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.10); ax.set_ylabel("pass@1")
ax.set_title("Surface generalization: MODEL vs baselines (measured, one seed)")
ax.legend(loc="upper right", frameon=False, fontsize=8); ax.grid(axis="y", alpha=0.3)
save(fig, "fig_surface.png")

# ---- 3. Data scaling (measured) ----
fig, ax = plt.subplots()
sizes = [100, 300, 1000, 3000]; perf = [0.100, 0.098, 0.300, 0.641]
labelsize = {100: "100", 300: "300", 1000: "1,000", 3000: "3,000"}
ax.plot(sizes, perf, "o-", color="#4C72B0")
for x, y in zip(sizes, perf):
    ax.annotate(f"{y:.3f}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
ax.set_xscale("log"); ax.set_xlabel("training examples (log scale)"); ax.set_ylabel("pass@1")
ax.set_xticks(sizes); ax.set_xticklabels([labelsize[s] for s in sizes])
ax.set_ylim(0, 1.05); ax.set_title("Data scaling (measured, one seed)"); ax.grid(alpha=0.3)
save(fig, "fig_data_scaling.png")

# ---- 4. Diversity vs quantity (measured) ---- 
# The shared evaluation is the same "alternate surface" test under both conditions.
# For the minimal condition the test shifts identifiers AND family; for the high-diversity
# condition the surface is within the training family (so its 1.000 is coverage of a seen
# surface). Name the evaluation neutrally and annotate the overlap difference per condition.
fig, ax = plt.subplots()
labels = ["minimal diversity", "high diversity"]
in_d = [0.500, 1.000]; surf = [0.000, 1.000]
x = np.arange(len(labels)); w = 0.3
ax.bar(x-w/2, in_d, w, label="in-distribution", color="#4C72B0")
ax.bar(x+w/2, surf, w, label="alternate-surface test", color="#55A868")
for xi, v in zip(x-w/2, in_d): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
for xi, v in zip(x+w/2, surf): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.12); ax.set_ylabel("pass@1")
ax.set_title("Diversity vs quantity")
ax.text(0.5, -0.14, "same example count, same alternate-surface test", transform=ax.transAxes,
        ha="center", va="top", fontsize=8, color="#444444")
ax.legend(loc="upper left", frameon=False, fontsize=8); ax.grid(axis="y", alpha=0.3)
save(fig, "fig_diversity.png")

# ---- 5. Continual learning (measured) ----
# Rename to sequential vs JOINT training (the review's R08/D05 point); label the
# joint condition as final task accuracy, not "retention".
# Add the sequential A-after-phase-A measurement (1.000) so the before/after drop is
# visible in one chart (Appendix C.8).
fig, ax = plt.subplots()
labels = ["sequential\n(A then B)", "joint\n(A+B)"]
# group 1 = A-task accuracy (final), split into before-B and after-B for sequential
a_final = [0.000, 1.000]
a_afterA = [1.000, None]   # sequential only: A measured right after phase A
b_acq = [0.889, 0.889]
x = np.arange(len(labels)); w = 0.28
# A accuracy before B (sequential only), drawn as a lighter bar beside the final bar
ax.bar(x-w, a_afterA if a_afterA[0] is not None else [0,0], w, label="A right after phase A\n(sequential, before B)",
       color="#9dc1e6")
ax.bar(x, a_final, w, label="final A-task accuracy", color="#4C72B0")
ax.bar(x+w, b_acq, w, label="final B-task accuracy", color="#55A868")
for xi, v in zip(x-w, a_afterA):
    if v is not None: ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
for xi, v in zip(x, a_final): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
for xi, v in zip(x+w, b_acq): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.15); ax.set_ylabel("pass@1")
ax.set_title("Task accuracy: sequential vs joint training (measured)")
ax.legend(loc="upper left", frameon=False, fontsize=7); ax.grid(axis="y", alpha=0.3)
save(fig, "fig_continual.png")

# ---- 6. Live behavior sweep: illustrative prompts on selected checkpoints ----
# From scripts/sweep_models.py. Cells are one illustrative prompt per case.
# NOTE: 'out-of-scope' is NOT a task failure -- it is a request Gate B would
# decline; the model (without Gate B in front) emits noise, so we label it
# distinctly rather than score it as a failed task.
fig, ax = plt.subplots(figsize=(8.2, 4.6))
models = ["0.88M\npilot", "0.88M\nsurface", "6.5M", "10.2M", "29.3M\n(30M)"]
cases = ["familiar\nsum", "familiar\nproduct", "reworded", "new\ncombination", "out-of-scope"]
# 1=correct program, 0=no valid program; the out-of-scope column is NOT a task the
# model was expected to solve, so it gets its own category (grey) not a red 'fail'.
# 2 marks "out of scope / not a task".
data = np.array([
    [1, 1, 0, 0, 2],
    [1, 1, 0, 0, 2],
    [1, 1, 0, 0, 2],
    [1, 1, 0, 0, 2],
    [1, 1, 0, 0, 2],
])
cmap = matplotlib.colors.ListedColormap(["#C44E52", "#55A868", "#bbbbbb"])
bounds = [-0.5, 0.5, 1.5, 2.5]
norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
im = ax.imshow(data, cmap=cmap, norm=norm, aspect="auto")
ax.set_xticks(np.arange(len(cases))); ax.set_xticklabels(cases, fontsize=8)
ax.set_yticks(np.arange(len(models))); ax.set_yticklabels(models, fontsize=8)
for i in range(len(models)):
    for j in range(len(cases)):
        v = data[i, j]
        if v == 1:
            mark, col = "\u2713", "white"
        elif v == 0:
            mark, col = "\u2717", "white"
        else:  # out-of-scope: NOT scored, use a neutral dash (not an X that implies failure)
            mark, col = "\u2013", "#666666"
        ax.text(j, i, mark, ha="center", va="center", color=col, fontsize=11, fontweight="bold")
ax.set_title("Illustrative prompts on five selected checkpoints\n(one prompt per case; green=correct, red=no valid program, \u2013=out of scope, unscored)")
ax.set_ylabel("checkpoint (params)")
import matplotlib.patches as mpatches
ax.legend(handles=[mpatches.Patch(color="#55A868", label="correct program"),
                   mpatches.Patch(color="#C44E52", label="no valid program"),
                   mpatches.Patch(color="#bbbbbb", label="out of scope (unscored, not a task)")],
          loc="lower center", bbox_to_anchor=(0.5, -0.34), ncol=3, fontsize=8)
fig.tight_layout()
save(fig, "fig_live_sweep.png")