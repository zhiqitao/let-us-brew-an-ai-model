# Experiment — Level 1: Memorization / learning distinction

Status: `[MEASURED]` — real run, manifest at `artifacts/manifests/memorization.json`.

## Setup
Loaded the Stage-1 pilot model (0.88M, trained on 1400 primitives). For 60 train
prompts, 60 held-out prompts, and 20 canary prompts, we check:
- exact-reference-reproduction on train prompts (memorization signature),
- pass@1 on held-out prompts (generalization),
- whether a canary (never-trained prompt) yields the *general* program.

## Results
- **Train prompts:** exact-reference-reproduction = **60/60**; pass@1 = 60/60.
- **Held-out prompts:** pass@1 = **59/60**.
- **Canary prompts:** the model emits the general program `def solve(a,b): return a+b`
  (not a memorized literal).

## Interpretation

For **simple primitives**, the model behaves like a *learner*, not a parrot:
- It reproduces training examples exactly (expected) — that is not surprising and is
  consistent with learning.
- Critically, on **held-out** prompts it still passes (59/60), so it has not simply
  memorized the 60 training instances.
- On a **canary** prompt it produces the correct *general* program, not a memorized
  constant. So it did not memorize answer literals.

Thus, at the Level-1/2 boundary on individual primitives, the model has genuinely
learned the mapping and generalizes it to new instances of the same operation.

## The sharper picture (combining all stages)

| Stage | Found |
|-------|-------|
| Memorization (L1) | Generalizes primitives to held-out/canary (not literal memorization) |
| Distributional (L2) | In-distribution pass@1 = 0.900 |
| **Surface (L3)** | **0.000** on held-out wording, 0.350 on new identifiers |
| **Structural (L4)** | **0.000** on unseen primitive combinations |

So: the model truly learns simple operations and generalizes them *within a surface
form*, but the knowledge is **tied to surface phrasing/identifiers** and does **not
compose** into novel structures. A clean, honest capability boundary for a ~0.9M
model.

## Reproduce
```bash
python scripts/run_memorization.py --sample 60
```
