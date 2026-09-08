# Experiment — Stage 3 Surface Generalization

Status: `[MEASURED]` — real run, manifest at `artifacts/manifests/stage3_surface.json`.

## Setup
- **Train** on pilot primitives with letter identifiers (a,b) and only some of the
  wording template families (the last family per operation held out).
- **Tests:**
  - in-distribution: same letters + same families,
  - new identifiers: word names (left, right) instead of (a, b),
  - held-out wording: a template family the model never saw during training.
- **Model:** 0.88M params, 1500 steps, final train loss 0.0218.

## Result — problem-level hidden-test pass@1

| Test               | **MODEL** | TEMPLATE | RETRIEVAL |
|--------------------|-----------|----------|-----------|
| In-distribution    | **0.900** | 0.800    | 1.000     |
| New identifiers    | **0.350** | 0.800    | 0.683     |
| **Held-out wording** | **0.000** | 0.875    | 0.125     |

## Interpretation (Level-3 surface generalization boundary)

1. **The model is not grounded in meaning; it is anchored to surface form.**
   In-distribution it scores 0.900, but:
   - changing `a,b` → `left,right` (same computation) drops it to **0.350**;
   - changing the *wording* to a held-out paraphrase family drops it to **0.000**.

2. **It falls BELOW both baselines under surface change.** The rule-based TEMPLATE
   baseline (which recognizes keywords) is *unaffected* by wording (0.875) and
   identifiers (0.800), because it never learned surface-to-op associations. The
   model, by contrast, tied the operation to the exact words/letters it saw.

3. This is Act V in miniature ("Catching the model cheating"): what looked like
   learned capability (0.900) is largely **phrasing memorization**. A trivial
   change that should not alter the computation (different words, different letter
   names) collapses it.

## Companion finding
- **Composition (Stage 4):** 0.000 on composites (can't compose primitives).
- **Surface (Stage 3):** 0.000 on new wording, 0.350 on new identifiers.
- Together these establish that this small model's "capability" is narrow,
   surface-tied, and non-compositional — a clean, honest scientific result.

## Outstanding questions
- Does more **capacity** buy robustness (or just more memorization)?
- Does **more diverse phrasing/identifiers in training** close the surface gap?
- Is the failure the Vocabulary (new words OOV-adjacent) or the exact wording
  pattern? A surface-control could separate these.

## Reproduce
```bash
python scripts/run_surface.py --steps 1500 --n-embd 128 --n-layer 4 --n-head 4 --seed 0 --n-per 60
```
Saved model: `artifacts/checkpoints/stage3_surface.pt`; manifest:
`artifacts/manifests/stage3_surface.json`.
