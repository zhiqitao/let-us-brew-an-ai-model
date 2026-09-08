# Consolidated experimental findings (capability map)

Status: `[MEASURED]` unless noted. Every number from a real run; manifests in
`artifacts/manifests/`, write-ups in `docs/experiments/`.

## The four-level generalization spectrum, measured on the ~0.9M student

| Level | What we tested | Result (pass@1) | Finding |
|-------|----------------|-----------------|---------|
| **L1 Memorization** | train-prefix reproduction; held-out; canary | exact-repro 60/60; held-out 59/60; canary→*general* program | learns, doesn't parrot, for primitives |
| **L2 Distributional** | held-out primitives, same distribution | MODEL 0.900 | in-distribution capability solid |
| **L3 Surface** | new identifiers (a,b → left,right); held-out wording | 0.350; **0.000** | surface/`phrasing`-tied, collapses below baselines |
| **L4 Structural** | unseen composition of two known primitives | **0.000** | cannot compose |

## Baseline comparisons (always: is the model beating a simpler machine?)

| Test | MODEL | TEMPLATE | RETRIEVAL |
|------|-------|----------|-----------|
| Stage-1 in-dist (primitives) | 0.897 | 0.800 | 1.000 |
| Stage-3 in-dist | 0.900 | 0.800 | 1.000 |
| Stage-3 new identifiers | 0.350 | 0.800 | 0.683 |
| Stage-3 held-out wording | 0.000 | 0.875 | 0.125 |
| Stage-4 in-dist | 0.900 | 0.800 | 1.000 |
| Stage-4 composition | 0.000 | 0.000 | 0.000 |

## The headline boundary (as of the ~0.9M / pilot scale)

> A ~0.9M model **genuinely learns** simple NL→code mappings and generalizes them
> within a surface form (in-distribution ~0.9, canary emits the general program),
> but the knowledge is **anchored to surface wording/identifiers** (new wording →
> 0.000) and **does not compose** (unseen combinations → 0.000). It beats a
> hand-written template rule system in-distribution, but a trivial TF-IDF retriever
> dominates whenever the split is retrieval-solvable.

This is a clean, falsifiable, honest result: the model's "capability" is real but
narrow, surface-tied, and non-compositional.

## Key process lessons (the book's methodology arc)

1. **Test the tester** — first Stage-1 eval reported the model at 0.000 (syntax),
   but the *evaluator* was broken (NUL padding in generation), not the model. Fixed →
   0.897.
2. **Test the teacher** — leakage audit caught a 100%-predictable operation from the
   pilot NL renderer (finding-001). Must add wording-family holdouts before L3 tests.
3. **Baselines are first-class** — retrieval dominates whenever solvable; the model
   only "wins" where retrieval can't reach (and even then only in-distribution).

## Open / next
- Scaling: does capacity (6.5M) buy composition? [RUNNING]
- Data scaling: when does more data stop helping? [prepared]
- Continual learning: does learning B destroy A? [prepared]
