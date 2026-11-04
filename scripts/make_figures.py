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
  * Fig 13.1 = corrected equal-count diversity comparison (LOW vs HIGH on
    in-distribution and on a genuinely held-out phrasing family; 3-seed means
    with min-max whiskers; both arms 1,200 records, 10/10 ops at 120/op, one
    fixed tokenizer), Fig 11.1 = corrected balanced data-scaling sweep (flat
    ~0.90, 10/10 operations at every size, one fixed tokenizer, 3 seeds, one
    shared 300-task test), Fig 15.1 = corrected 2x2 surface factorial (collapse
    on new identifiers and on held-out wording; "new variable identifiers"
    naming).

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
    # VECTOR copy (production: raster PNGs were only ~167-312 dpi at 6x9 trim).
    # The PDF backend draws text/paths as real vectors, so labels stay crisp at
    # any print size; the manuscript references figures/fig_X.pdf.
    v = os.path.join(FIG, os.path.splitext(name)[0] + ".pdf")
    fig.savefig(v, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p, "|", v)
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
# 2. Surface generalization -- Figure 15.1 (CORRECTED 2x2 factorial, seed 0)
# Values exact to artifacts/manifests/surface_corrected_seed0.json (fixes
#   P0-03 + P0-04; supersedes the mixed-factor stage3_surface rows):
#   model 0.898/0.000/0.000/0.000, template 0.800/0.800/0.875/0.875,
#   retrieval 1.000/1.000/0.125/0.125 over cells of 600/600/480/480 records.
# Raw counts: MODEL 539/600, 0/600, 0/480, 0/480;
#   TEMPLATE 480/600, 480/600, 420/480, 420/480;
#   RETRIEVAL 600/600, 600/600, 60/480, 60/480.
# Held-out cells exclude abs_of + cond_abs_max (single wording family),
#   so they are 8 ops x 60 = 480, not 600 (P0-04).
# Model across seeds: familiar 0.898-0.940; identifiers-only 0.000-0.005;
#   wording-only 0.000 (all seeds); both-changes 0.000-0.025.
# "new IDs" -> "new variable identifiers" (P2-PROD-05 / 15.1 variable naming).
# Grayscale-safe: distinct hatching per series + direct value labels; counts in
#   a note (they would overlap if stacked under the 12 tightly-grouped bars).
# ==========================================================================
fig, ax = plt.subplots(figsize=(5.8, 4.6))
labels = ["familiar\n(letters, kept)", "new variable\nidentifiers\n(words, kept)",
          "new wording\n(letters,\nheld-out)", "both changes\n(words,\nheld-out)"]
model = [0.898, 0.000, 0.000, 0.000]
template = [0.800, 0.800, 0.875, 0.875]
retrieval = [1.000, 1.000, 0.125, 0.125]
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
ax.set_title("Surface generalization (corrected 2x2)\nseed 0; 600 / 600 / 480 / 480 records",
             fontsize=FS_TITLE, fontweight="bold", color=INK, pad=34)
# legend above the axes (outside the plot) so it cannot collide with the tall
# familiar bar's 0.898 value label
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.00), ncol=3,
          frameon=False, fontsize=FS_LEGEND, labelcolor=INK)
ax.grid(axis="y", alpha=0.28)
# raw counts + provenance (fixes P0-03 / P0-04): familiar and identifiers-only
# cells are 600 records each (10 ops x 60); the two held-out-wording cells are
# 480 (8 ops x 60 -- abs_of and cond_abs_max have no held-out family). One fixed
# 600-record train set + one fixed train-only tokenizer underlie every cell.
ax.text(0.5, -0.30,
        "seed-0 counts (cells of 600 / 600 / 480 / 480):\n"
        "MODEL 539/0/0/0  ·  TEMPLATE 480/480/420/420  ·  RETRIEVAL 600/600/60/60\n"
        "model across seeds: familiar 0.898-0.940, new IDs 0.000-0.005,\n"
        "new wording 0.000 (all seeds), both 0.000-0.025; held-out cells exclude\n"
        "abs_of + cond_abs_max (8 ops x 60 = 480); fixes P0-03/P0-04",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=FS_NOTE, color=INK)
fig.tight_layout()
save(fig, "fig_surface.png")

# ==========================================================================
# 3. Data scaling -- Figure 11.1 (CORRECTED balanced sweep, fixes P0-01)
# Values exact to artifacts/manifests/data_scaling_corrected_seed{0,1,2}.json:
#   seed 0: 0.897 / 0.900 / 0.893 / 0.897 (269/270/268/269 of 300)
#   seed 1: 0.893 / 0.900 / 0.900 / 0.900 (268/270/270/270 of 300)
#   seed 2: 0.900 / 0.900 / 0.997 / 0.900 (270/270/299/270 of 300)
# Balanced 10/30/100/300 records per operation, 10/10 operations at every
#   size, ONE fixed tokenizer (sha256 ddbbc0ed...c1ae), one shared 300-task
#   test (30/op), 1000 steps, bs16, lr1e-3, arch 128/4L, three seeds.
# Template 0.800 (240/300) and retrieval 0.943-1.000 in every arm.
# FLAT: no data-size benefit once operation coverage is held fixed; the old
#   0.100->0.641 curve is a flawed historical run (P0-01), kept in the ledger.
# Grayscale-safe: distinct markers/linestyles per seed + direct labels.
# ==========================================================================
fig, ax = plt.subplots(figsize=(5.6, 4.3))
sizes = [100, 300, 1000, 3000]
perf_s1 = [0.8933, 0.900, 0.900, 0.900]
perf_s2 = [0.900, 0.900, 0.9967, 0.900]
perf = [0.8967, 0.900, 0.8933, 0.8967]      # seed 0 (labeled)
counts = ["269/300", "270/300", "268/300", "269/300"]
labelsize = {100: "100", 300: "300", 1000: "1,000", 3000: "3,000"}
ax.plot(sizes, perf_s1, "^--", color=GREY, lw=1.6, ms=8, label="seed 1", zorder=2)
ax.plot(sizes, perf_s2, "s:", color=GREEN, lw=1.6, ms=8, label="seed 2", zorder=2)
ax.plot(sizes, perf, "o-", color=BLUE, lw=2.2, ms=9, label="seed 0", zorder=3)
for x, y, c in zip(sizes, perf, counts):
    ax.annotate(f"{y:.3f}", (x, y), textcoords="offset points", xytext=(0, 14),
                ha="center", fontsize=FS_VALUE, color=BLUE, fontweight="bold")
    ax.annotate(c, (x, y), textcoords="offset points", xytext=(0, -24),
                ha="center", fontsize=FS_COUNT, color=INK)
ax.set_xscale("log")
ax.margins(x=0.10)  # first point off the left edge so its count label clears the 0.0 tick
ax.set_xlabel("training examples (log scale)\n"
              "10/30/100/300 per op · 10/10 ops at every size",
              fontsize=FS_LABEL)
ax.set_ylabel("pass@1", fontsize=FS_LABEL)
ax.set_xticks(sizes)
ax.set_xticklabels([labelsize[s] for s in sizes], fontsize=FS_TICK)
ax.set_ylim(-0.14, 1.18)
ax.set_title("Data scaling (corrected): flat\n~0.90 from 10 to 300 examples per op",
             fontsize=FS_TITLE, fontweight="bold", color=INK, pad=8)
ax.grid(alpha=0.28)
ax.legend(loc="lower left", frameon=False, fontsize=FS_LEGEND, labelcolor=INK)
# corrected-scope banner: balanced arms, one fixed tokenizer, three seeds.
ax.text(0.5, 0.99,
        "10/10 operations at every size  ·  one fixed tokenizer  ·  3 seeds",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=FS_NOTE, color=INK, fontweight="bold")
ax.text(0.5, -0.28,
        "labels/counts = seed 0 (successes / 300 shared test, 30/op x 10 ops);\n"
        "template 0.800 and retrieval 0.943-1.000 in all 12 arms; 1,000 steps;\n"
        "the earlier 0.100->0.641 curve is a flawed historical run (P0-01)",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=FS_NOTE, color=INK)
fig.tight_layout()
save(fig, "fig_data_scaling.png")

# ==========================================================================
# 4. Diversity at equal count -- Figure 13.1 (CORRECTED, fixes P0-02)
# Values exact to artifacts/manifests/diversity_corrected_seed{0,1,2}.json:
#   LOW  arm (1,200 records, 20 unique pairs):  in-dist 0.950/0.950/0.950
#        (mean 0.950, range 0.950-0.950); held-out family 0.000 x3 (mean 0.000).
#   HIGH arm (1,200 records, 605 unique pairs): in-dist 0.820/0.570/0.840
#        (mean 0.743, range 0.570-0.840); held-out family 0.640/0.300/0.710
#        (mean 0.550, range 0.300-0.710).
# Both arms: exactly 1,200 records, 10/10 ops at 120/op, one fixed tokenizer
#   (vocab 293), matched 1,000 steps/arch/lr/init; held-out families h01/h02
#   used by NO training arm (0 family/prompt collisions, audited).
# The earlier 0.000-vs-1.000 figure was the flawed 42-record historical run
#   (P0-02), superseded by this corrected comparison.
# Grayscale-safe: solid vs hatched bars + direct value labels; whiskers = the
#   per-seed min-max range around the 3-seed mean.
# ==========================================================================
fig, ax = plt.subplots(figsize=(5.6, 4.4))
labels = ["low diversity\n(1,200 records;\n20 unique pairs)",
          "high diversity\n(1,200 records;\n605 unique pairs)"]
# 3-seed means, with per-seed min-max ranges for the whiskers
in_d_mean  = [0.950, 0.743]
in_d_lo    = [0.950, 0.570]   # seed min: 0.950/0.950/0.950 ; 0.820/0.570/0.840
in_d_hi    = [0.950, 0.840]
fam_mean   = [0.000, 0.550]
fam_lo     = [0.000, 0.300]   # seed min: 0.000/0.000/0.000 ; 0.640/0.300/0.710
fam_hi     = [0.000, 0.710]
x = np.arange(len(labels)); w = 0.3
ax.bar(x-w/2, in_d_mean, w, label="in-distribution", color=BLUE,
       edgecolor=INK, yerr=[np.array(in_d_mean)-np.array(in_d_lo),
                            np.array(in_d_hi)-np.array(in_d_mean)],
       capsize=6, error_kw=dict(ecolor=INK, lw=1.6, capthick=1.6))
ax.bar(x+w/2, fam_mean, w, label="held-out phrasing family\n(never trained)",
       color=GREEN, edgecolor=INK, hatch="//",
       yerr=[np.array(fam_mean)-np.array(fam_lo),
             np.array(fam_hi)-np.array(fam_mean)],
       capsize=6, error_kw=dict(ecolor=INK, lw=1.6, capthick=1.6))
for xi, v, lo, hi in zip(x-w/2, in_d_mean, in_d_lo, in_d_hi):
    rng = f"{lo:.3f}-{hi:.3f}" if hi > lo else f"{v:.3f}"
    ax.text(xi, hi+0.03, f"{v:.3f}\n({rng})", ha="center", fontsize=FS_VALUE,
            color=INK, fontweight="bold")
for xi, v, lo, hi in zip(x+w/2, fam_mean, fam_lo, fam_hi):
    rng = f"{lo:.3f}-{hi:.3f}" if hi > lo else f"{v:.3f}"
    ax.text(xi, hi+0.03, f"{v:.3f}\n({rng})", ha="center", fontsize=FS_VALUE,
            color=INK, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=FS_TICK)
ax.set_ylim(0, 1.28)
ax.set_ylabel("pass@1", fontsize=FS_LABEL)
ax.set_title("Diversity at equal count (corrected):\nunseen-family transfer 0.000 -> 0.550",
             fontsize=FS_TITLE, fontweight="bold", color=INK, pad=8)
ax.text(0.5, -0.30,
        "both arms 1,200 records, 10/10 ops at 120/op, one fixed\n"
        "tokenizer, matched 1,000 steps; bars = 3-seed mean, whiskers =\n"
        "seed range (0/1/2); held-out families used by NO arm (0 collisions);\n"
        "the earlier 0.000-vs-1.000 was the flawed 42-record run (P0-02)",
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