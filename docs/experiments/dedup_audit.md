# Experiment — Model-visible prompt deduplication audit (R05)

Status: `[MEASURED]` — real run, `artifacts/manifests/dedup_audit.json`.
Script: `scripts/run_dedup_audit.py`.

## The question

Task IDs can change hidden-test inputs without changing the prompt or reference
program. A reported "held-out" example is only meaningful if the *model-visible
prompt string* is new, not merely the task ID. This audit counts, for each split, the
distinct records vs. distinct prompt strings vs. distinct (prompt, program) pairs, and
the prompt overlap between train and held-out.

## Result (surface split)

| Split | records | unique prompts | unique (prompt,program) pairs |
|-------|---------|----------------|-------------------------------|
| train | 110 | 11 | 11 |
| in-distribution | 100 | 10 | 10 |
| held-out wording (last family) | 100 | 10 | 10 |
| **train × held-word prompt overlap** | | | **0** |
| train × held-word pair overlap | | | **0** |

## Result (composition split)

| Split | records | unique prompts | unique (prompt,program) pairs |
|-------|---------|----------------|-------------------------------|
| train (primitives) | 100 | 21 | 21 |
| composite hold-put | 60 | 6 | 6 |
| **train × comp prompt overlap** | | | **0** |

## Interpretation

The held-out wording family in the **surface** split does **not** appear in training
(prompt overlap 0), so the ch15 surface result is a genuine held-out-family
generalization failure, not a coverage artifact. Similarly, the composite prompts do
not overlap with the primitive-training prompts, so the ch16 composition result is
tested on prompts the model never saw during training.

**Important caveat on this audit's size.** This reproduction uses a small per-operation
sample (10 records per family/op) because it is regenerated for the audit, not the full
training set used in the real runs (which used larger per-op counts and the real
dataset files). The *prompt-overlap* finding (0 between train and the relevant
holdout) is robust to that, because the families/operations are disjoint by
construction. The *unique-prompt* and *unique-pair* counts above are for this sample
only and should not be quoted as the real dataset's absolute counts; they are
illustrative of the structure, and the real numbers are in the dataset files under
`artifacts/datasets/`.

## The two different "surface" cases (R02)

This confirms a distinction the book must keep straight:

- **ch15 / Stage-3 surface:** the held-out wording is the *last family per operation*,
  which the model never saw. So its 0.000 is a genuine held-out-family failure.
- **ch13 / diversity:** the high-diversity model trained on *all* families × both
  id-sets, so its 1.000 surface score is *coverage* of surfaces in its training
  family, not transfer to an excluded family.

These are different setups and answer different questions. The book states this
explicitly.

## Reproduce
```bash
TORCH_DISABLE_AVX2=1 python scripts/run_dedup_audit.py
```
