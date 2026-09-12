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
ax.bar(x, template, w, label="TEMPLATE", color=C_TEMPLATE)
ax.bar(x+w, retrieval, w, label="RETRIEVAL", color=C_RETRIEVAL)
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
# Rename the dual legend precisely; annotate that high-diversity = COVERAGE (the
# review's D02 point), and show the 0.000 explicitly.
fig, ax = plt.subplots()
labels = ["minimal diversity", "high diversity"]
in_d = [0.500, 1.000]; surf = [0.000, 1.000]
x = np.arange(len(labels)); w = 0.3
ax.bar(x-w/2, in_d, w, label="in-distribution", color="#4C72B0")
ax.bar(x+w/2, surf, w, label="surface (coverage)", color="#55A868")
for xi, v in zip(x-w/2, in_d): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
for xi, v in zip(x+w/2, surf): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.12); ax.set_ylabel("pass@1")
ax.set_title("Diversity vs quantity (same example count; surface = coverage)")
ax.legend(loc="upper left", frameon=False, fontsize=8); ax.grid(axis="y", alpha=0.3)
save(fig, "fig_diversity.png")

# ---- 5. Continual learning (measured) ----
# Rename to sequential vs JOINT training (the review's R08/D05 point); label the
# joint condition as final task accuracy, not "retention".
fig, ax = plt.subplots()
labels = ["sequential", "joint (A+B)"]
a_ret = [0.000, 1.000]; b_acq = [0.889, 0.889]
x = np.arange(len(labels)); w = 0.3
ax.bar(x-w/2, a_ret, w, label="final A-task accuracy", color="#4C72B0")
ax.bar(x+w/2, b_acq, w, label="final B-task accuracy", color="#55A868")
for xi, v in zip(x-w/2, a_ret): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
for xi, v in zip(x+w/2, b_acq): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.10); ax.set_ylabel("pass@1")
ax.set_title("Final task accuracy: sequential vs joint training (measured)")
ax.legend(loc="upper left", frameon=False, fontsize=8); ax.grid(axis="y", alpha=0.3)
save(fig, "fig_continual.png")

# ---- 6. Live behavior sweep: pass/fail across all 5 trained models ----
# From scripts/sweep_models.py (measured): every model solves both in-distribution
# cases and fails reword / compose / out-of-scope. Green=PASS, red=FAIL.
fig, ax = plt.subplots(figsize=(8.2, 4.6))
models = ["0.88M\npilot", "0.88M\nsurface", "6.5M", "10.2M", "29.3M\n(30M)"]
cases = ["in-dist\nsum", "in-dist\nproduct", "reworded", "compose", "out-of-scope"]
# PASS=1 FAIL=0, from the measured sweep (identical pattern across all sizes)
data = np.array([
    [1, 1, 0, 0, 0],
    [1, 1, 0, 0, 0],
    [1, 1, 0, 0, 0],
    [1, 1, 0, 0, 0],
    [1, 1, 0, 0, 0],
])
cmap = matplotlib.colors.ListedColormap(["#C44E52", "#55A868"])
bounds = [-0.5, 0.5, 1.5]
norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
im = ax.imshow(data, cmap=cmap, norm=norm, aspect="auto")
ax.set_xticks(np.arange(len(cases))); ax.set_xticklabels(cases, fontsize=8)
ax.set_yticks(np.arange(len(models))); ax.set_yticklabels(models, fontsize=8)
for i in range(len(models)):
    for j in range(len(cases)):
        out = " \u2713" if data[i, j] else " \u2717"
        fc = "white" if data[i, j] else "white"
        ax.text(j, i, out, ha="center", va="center", color="white", fontsize=11, fontweight="bold")
ax.set_title("Live behavior: every trained model solves the task, and none survives\na reword, a new combination, or an out-of-scope request (measured, all 5)")
ax.set_ylabel("model (params)")
# legend
import matplotlib.patches as mpatches
ax.legend(handles=[mpatches.Patch(color="#55A868", label="pass (correct program)"),
                   mpatches.Patch(color="#C44E52", label="fail (no valid program)")],
          loc="lower center", bbox_to_anchor=(0.5, -0.34), ncol=2, fontsize=8)
fig.tight_layout()
save(fig, "fig_live_sweep.png")

print("\nall figures written to", FIG)
