# Experiment — Stage 4 Structural / Compositional Generalization

Status: `[MEASURED]` — real run, manifest at `artifacts/manifests/stage4_composition.json`.

## Setup
- **Train** on PRIMITIVE operations only (add, sub, mul, max_of, min_of, abs_of,
  list_sum, list_len, first_element, cond_abs_max) — 1400 train tasks.
- **In-distribution test:** held-out primitive tasks (300).
- **Compositional hold-out:** 240 tasks from SIX COMPOSITE operations that compose
  two known primitives but **never appeared in training**:
  `abs_add` (abs+add), `sub_abs` (sub→abs), `sum_of_abs` (abs over list sum),
  `max_add` (max(add,sub)), `double_first` (index×2), `len_minus_one` (len−1).
- **Model:** 0.88M params (V=291, n_embd=128, n_layer=4, n_head=4), 1500 steps,
  final train loss **0.0194**.
- **Env note:** the tokenizer was trained to *cover* composite vocab (so no OOV),
  but the model never saw composite examples during training.

## Result — problem-level hidden-test pass@1

| Candidate | In-distribution | **Compositional (held-out)** |
|-----------|-----------------|------------------------------|
| **MODEL** | **0.900** | **0.000** |
| TEMPLATE  | 0.800 | 0.000 |
| RETRIEVAL | 1.000 | 0.000 |

## Interpretation

1. **The model learns the primitives well** (in-distribution 0.900, beats the
   hand-written template baseline at 0.800). Milestone-2 capability holds.

2. **The model cannot compose them.** On composites it scores **0.000**. Inspection
   of its generated programs confirms the boundary is real, not an eval artifact:
   it either emits malformed fragments (`def = b): return a - b`) or reverts to a
   single memorized primitive pattern. It did **not** learn "I know abs, and I know
   add, therefore I can do abs_add."

3. **Crucially, even the baselines collapse to 0.000** on the compositional split.
   Retrieval can't solve it (no composite exists in training), and the template
   system has no composite rule. So the 0.000 is *not* a task being unfair — it is
   the honest absence of a way to get the answer without genuinely composing.

## Why this is the book's key early finding

This is the **Level-4 structural-generalization boundary** made concrete at a small
scale, exactly as the design predicted (Stage 4: "Can the model compose learned
structures?"). It is also the *correct* response to the Stage-1 pilot finding
("retrieval dominates"): the composite split is non-retrieval-solvable, and it
reveals a real capability limit rather than a task too easy.

**The measured boundary:** a ~0.9M model learns the individual mappings to ~90%
accuracy but **fails completely (0%)** when asked to combine them in unseen ways.

## Outstanding questions (natural next brews)
- Does more **model capacity** (10M / 30M / 100M) buy composition, or more
  memorization? (Stage 5 scaling.)
- Does **replay/mixed exposure** to a few composites during training help? (One-variable
  change of tokenizer/data, not architecture.)
- Is the failure **surface** (new vocabulary/word order) or **structural** (the
  composition itself)? A surface-control (composites with familiar wording) isolates
  this — next audit.

## Reproduce
```bash
python scripts/run_composition.py --steps 1500 --n-embd 128 --n-layer 4 --n-head 4 --seed 0
```
Saved model: `artifacts/checkpoints/stage4_composition.pt`; manifest:
`artifacts/manifests/stage4_composition.json`.
