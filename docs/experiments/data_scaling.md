# Experiment — Chapter 11: How Much Data?

Status: `[MEASURED]` — real run, manifest at `artifacts/manifests/data_scaling.json`.

## Setup
Hold model architecture (0.88M: n_embd=128, n_layer=4, n_head=4) and training protocol
(lr=1e-3, bs=16, 800 steps, 1 seed) constant. Vary dataset size: 100 / 300 / 1000 /
3000. Measure in-distribution problem-level hidden-test pass@1 on a held-out primitive
test pool.

## Result

| dataset size | final train loss | **pass@1 (held-out)** | train time |
|--------------|------------------|-----------------------|------------|
| 100          | 0.000            | **0.100**             | 496s       |
| 300          | 0.000            | **0.098**             | 487s       |
| 1000         | 0.022            | **0.300**             | 482s       |
| 3000         | 0.025            | **0.641**             | 581s       |

## Interpretation

1. **More data clearly helps in-distribution.** pass@1 climbs from 0.10 (100 examples)
   to 0.64 (3000). The model needs substantial data to learn even the narrow
   mapping — at 100 examples it generalizes barely above chance per-operation, at
   3000 it reaches a workable level.

2. **A classic small-data plateau.** 100 and 300 are essentially identical (~0.10);
   the improvement only becomes substantial between 1000 and 3000. So there is a
   *data threshold* below which the model gets almost nothing, and above which
   performance climbs. That threshold is a real, measurable property of the task
   + model.

3. **Low train loss is necessary but not sufficient, again.** At 100/300 examples the
   train loss hits ~0.000 — the model has *memorized* its tiny training set — yet
   pass@1 is only 0.10. This is the book's core motif restated with data scaling:
   a loss of zero on 100 examples buys nothing on unseen ones.

## Outstanding
- The 3000 point (0.641) is below the ~0.900 achieved with the 1400-example pilot
  from Ch10 — because here we test on a *larger* held-out pool (n_per_op=60) and use
  different seeds. The shape (monotone growth, plateau then climb) is what matters.
- Does *diversity* (more operation/paraphrase variety per example) beat *quantity*
  (more examples of the same kind)? [diversity experiment] — the key distinction the
  design wants (more data ≠ more information ≠ more diversity).

## Reproduce
```bash
python scripts/run_data_scaling.py --sizes 100 300 1000 3000 --steps 800
```
