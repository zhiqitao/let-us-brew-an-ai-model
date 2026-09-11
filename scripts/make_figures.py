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
fig, ax = plt.subplots()
labels = ["0.88M", "6.5M", "10.2M", "29.3M"]
in_dist = [0.900, 0.897, 0.773, 0.897]
comp    = [0.000, 0.000, 0.000, 0.000]
x = np.arange(len(labels)); w = 0.38
ax.bar(x-w/2, in_dist, w, color="#4C72B0", label="in-distribution")
ax.bar(x+w/2, comp,    w, color="#C44E52", label="composition")
for xi, v in zip(x-w/2, in_dist): ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
for xi, v in zip(x+w/2, comp):    ax.text(xi, v+0.02, f"{v:.3f}", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.05); ax.set_ylabel("pass@1")
ax.set_title("Model size: in-distribution vs composition (measured, 4 points)")
ax.legend(); ax.grid(axis="y", alpha=0.3)
save(fig, "fig_model_size.png")

# ---- 2. Surface generalization (measured) ----
fig, ax = plt.subplots()
labels = ["in-dist", "new IDs", "new wording"]
model = [0.900, 0.350, 0.000]; template = [0.800, 0.800, 0.875]; retrieval = [1.000, 0.683, 0.125]
x = np.arange(len(labels)); w = 0.25
ax.bar(x-w, model, w, label="MODEL"); ax.bar(x, template, w, label="TEMPLATE"); ax.bar(x+w, retrieval, w, label="RETRIEVAL")
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.05); ax.set_ylabel("pass@1")
ax.set_title("Surface generalization (measured)"); ax.legend(); ax.grid(axis="y", alpha=0.3)
save(fig, "fig_surface.png")

# ---- 3. Data scaling (measured) ----
fig, ax = plt.subplots()
sizes = [100, 300, 1000, 3000]; perf = [0.100, 0.098, 0.300, 0.641]
ax.plot(sizes, perf, "o-", color="#4C72B0")
ax.set_xscale("log"); ax.set_xlabel("training examples (log)"); ax.set_ylabel("pass@1")
ax.set_ylim(0, 0.8); ax.set_title("Data scaling (measured)"); ax.grid(alpha=0.3)
save(fig, "fig_data_scaling.png")

# ---- 4. Diversity vs quantity (measured) ----
fig, ax = plt.subplots()
labels = ["minimal diversity", "high diversity"]
in_d = [0.500, 1.000]; surf = [0.000, 1.000]
x = np.arange(len(labels)); w = 0.3
ax.bar(x-w/2, in_d, w, label="in-dist"); ax.bar(x+w/2, surf, w, label="surface")
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.05); ax.set_ylabel("pass@1")
ax.set_title("Diversity vs quantity (same example count, measured)"); ax.legend(); ax.grid(axis="y", alpha=0.3)
save(fig, "fig_diversity.png")

# ---- 5. Continual learning (measured) ----
fig, ax = plt.subplots()
labels = ["sequential", "replay"]
a_ret = [0.000, 1.000]; b_acq = [0.889, 0.889]
x = np.arange(len(labels)); w = 0.3
ax.bar(x-w/2, a_ret, w, label="A-retention"); ax.bar(x+w/2, b_acq, w, label="B-acquisition")
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.05); ax.set_ylabel("pass@1")
ax.set_title("Continual learning: sequential forgets A, replay retains (measured)")
ax.legend(); ax.grid(axis="y", alpha=0.3)
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
