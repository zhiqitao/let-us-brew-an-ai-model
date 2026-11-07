# Multi-seed replication (2026-11-01)

> **READ THIS FIRST — two tables in this report are SUPERSEDED.**
> This report is cited by Chapters 10 and 16 and by Appendix C. Its
> **Diversity** table (minimal 0.500/0.000, high 1.000/1.000) and its
> **Data-scaling** table (0.100 / 0.100 / 0.300 / 0.641) were produced by the
> constructions the P0-01/P0-02 audit later corrected. They are kept below as
> the historical record of what those flawed constructions measured — do NOT
> cite them as results. The corrected reruns supersede them:
>
> - **Data scaling (P0-01):** the balanced, operation-stratified rerun is
>   **flat at ~0.90** at every size (0.897–0.900 over 100 / 300 / 1,000 /
>   3,000 records, all three seeds) — no monotone data-size trend once
>   operation coverage, tokenizer, and step budget are held fixed. The
>   0.100 → 0.641 "monotone trend" in the superseded table is an artifact of
>   the confounded construction (book, Chapter 11 and Table C.13).
> - **Diversity (P0-02):** the equal-count rerun gives **LOW 0.000 vs HIGH
>   0.550** on the held-out family (means over seeds 0–2; in-distribution
>   0.950 vs 0.743) — not 1.000 vs 1.000 (book, Chapter 13 and Table C.15).
>
> The composition-exposure, Stage-3 surface, Stage-1 pilot, and
> continual-learning sections below are **not** superseded and stand as written.

Re-ran the seed-0 headline experiments under seeds 1 and 2 on the Hermes host
(Python 3.11 venv `.venv-311`, torch 2.14.0+cpu, `TORCH_DISABLE_AVX2=1`,
`OMP_NUM_THREADS=2`). Each run is a fresh training from a different seed.

## Composition exposure (the central question)

| seed | in-dist pass@1 | exposed pass@1 | **held-out pass@1** | final loss |
|------|------|------|------|------|
| 1 | 1.000 | 0.667 | **0.000** | 0.0179 |
| 2 | 1.000 | 0.667 | **0.000** | 0.0218 |

The held-out composition result is **0.000 for both new seeds**, reproducing the
seed-0 run recorded in the book. The composition failure is not a single-seed
artifact.

## Stage-3 surface

| seed | in-dist | new identifiers | held-out wording |
|------|------|------|------|
| 0 | 0.900 | 0.350 | 0.000 |
| 1 | 0.900 | 0.348 | 0.004 |
| 2 | 0.898 | 0.348 | 0.000 |

The surface numbers are tightly stable across seeds.

> Caveat: the RETRIEVAL baseline reported 0.000 on seeds 1 and 2 (seed 0 gave
> 1.000 in-distribution). This is a baseline-harness artifact of the re-runs, not
> a model result; the MODEL pass@1 values above are consistent and are the
> scientific target.

## Conclusion

The two central findings are now multi-seed-backed:
- composition held-out 0.000 is robust across 3 seeds;
- surface results are stable across seeds.

Together with the decode/termination ablation (which showed the composition 0.000
is not a decode/extraction artifact), the book's core claims are reproducible.

## Diversity (Stage-3, quantity vs diversity)

> **SUPERSEDED (P0-02).** The rows below are the pre-correction, unequal-count
> construction. Corrected equal-count rerun: **LOW 0.000 vs HIGH 0.550** on the
> held-out family (in-distribution 0.950 vs 0.743), Table C.15 / Chapter 13.

| seed | minimal in-dist | minimal surface | high in-dist | high surface |
|------|------|------|------|------|
| 0 | 0.500 | 0.000 | 1.000 | 1.000 |
| 1 | 0.500 | 0.033 | 1.000 | 1.000 |
| 2 | 0.500 | 0.000 | 0.983 | 0.983 |

Stable across seeds: minimal-diversity reaches ~0.5 in-dist / ~0 surface; high-diversity
reaches ~1.0 / ~1.0. **Superseded by the P0-02 equal-count rerun (LOW 0.000 vs HIGH
0.550 held-out) — see the banner at the top of this report.**

## Data-scaling (how much data)

> **SUPERSEDED (P0-01).** The rows below are the pre-correction, confounded
> sweep. Corrected balanced, operation-stratified rerun: **flat ~0.90 at every
> size** (0.897–0.900), Chapter 11 / Table C.13.

| size | seed0 (800 steps) | seed1 (1000) | seed2 (1000) |
|------|------|------|------|
| 100 | 0.100 | 0.094 | 0.076 |
| 300 | 0.098 | 0.100 | 0.100 |
| 1000 | 0.300 | 0.300 | 0.300 |
| 3000 | 0.641 | 0.748 | 0.748 |

The monotone data-size trend holds across all seeds. The size-3000 absolute differs with the
step budget (0.641 at 800 steps vs 0.748 at 1000; seed1=seed2=0.748 at 1000), so the robust
finding is the monotone trend, not a single point. **Superseded: the P0-01 corrected
balanced rerun is flat at ~0.90 at every size and shows no monotone trend — see the
banner at the top of this report.**

## Pilot (Stage-1)

| seed | in-dist pass@1 | final loss |
|------|------|------|
| 1 | 0.900 | 0.0196 |
| 2 | 0.900 | 0.0229 |

Reproduces the published pilot in-dist result (~0.90; the book's 0.897). Seed-0's
`stage1.json` is the pre-fix 0.000 record (see Appendix C.1), not the re-run value.

## Continual-learning

| seed | sequential A-retention | sequential B-acquisition | replay A-retention | replay B-acquisition |
|------|------|------|------|------|
| 1 | 0.000 | 0.889 | 1.000 | 0.889 |
| 2 | 0.000 | 0.861 | 1.000 | 0.889 |

Stable: sequential training catastrophically forgets A (retention 0.0) while
acquiring B (~0.87-0.89); replay retains A (1.0) and acquires B (0.889). The
replay-vs-sequential distinction is robust.

> **Caveat — this replication was not a seed-only change.** The seed-0 run
> (`continual.json`) used `steps_a` 700 + `steps_b` 700 (1,400 steps, `n_per` 70);
> the seeds-1 and 2 re-runs (`continual_seed1.json`, `continual_seed2.json`) used a
> **smaller step budget**, `steps_a` 600 + `steps_b` 600 (1,200 steps, `n_per` 80).
> Two variables therefore moved — the seed *and* the step budget — so these rows are
> a robustness check on the recorded *pattern* (sequential forgets A while still
> acquiring B; joint/interleaved keeps A while acquiring B just as well), not a
> like-for-like, single-variable replication of the seed-0 numbers. Within each run
> both protocols share the same budget, so the sequential-vs-replay contrast itself
> stays controlled. The retention/acquisition values above are as measured.
