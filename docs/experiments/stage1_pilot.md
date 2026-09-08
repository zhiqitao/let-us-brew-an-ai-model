# Experiment — Stage 1 Pilot (first brew)

Status: `[MEASURED]` — real run, documented manifest at `artifacts/manifests/stage1.json`.

## Setup
- **Task:** natural-language spec → Python program, 10 pilot operations.
- **Data:** 1400 train / 300 val / 300 test (operation-disjoint splits).
- **Model:** small decoder-only transformer, V=291, n_embd=128, n_layer=4, n_head=4,
  block=128 → **884,224 params** (embedding 53,632 + non-embedding 830,592).
- **Training:** 1500 steps, bs=16, lr=1e-3, ADAMW, next-token objective; final train
  loss **0.0208**; ~514s on CPU.
- **Evaluator:** hidden tests, semantic comparator, mutation-tested.

## Result — problem-level pass@1 (deterministic/greedy) on the test set

| Candidate   | syntax | executable | **pass@1** |
|-------------|--------|-----------|------------|
| **MODEL**   | 0.897  | 0.897     | **0.897**  |
| TEMPLATE    | 1.000  | 0.900     | 0.800      |
| RETRIEVAL   | 1.000  | 1.000     | **1.000**  |

## Interpretation

1. **Milestone 2 passed: the model learned something.** It beats the hand-written
   template/rule baseline (0.897 vs 0.800) and produces executable programs 90% of
   the time. A small model (0.88M params) learns the NL→code mapping on this narrow
   task.

2. **But retrieval dominates (1.000).** Per the pilot go/no-go criteria (§26, option
   C): *retrieval dominates → the task is too easy → force controlled task expansion.*
   The pilot task set has near-duplicate prompts, so a TF-IDF retriever that finds
   the closest training example solves it perfectly. The model's 0.897 is real
   capability, but the *task* doesn't yet force *generalization* — an important,
   interpretable pilot finding.

## Correction during the run (test-the-tester)

The first eval reported the model at **0.000** (syntax=0). Root cause: the generation
loop emitted NUL padding (`\x00`) after a complete program, and `ast.parse` rejects
NUL bytes, so the judge scored the model's valid output as a syntax failure. **The
evaluator was broken, not the model.** Fixed `generate_code` to truncate at the first
NUL byte. This is precisely the book's recurring lesson — *test the tester* — applied
to our own first run.

## Decision / next step

The task is too easy (retrieval-solvable). To force generalization, the next brew
must increase **structural diversity** and introduce **compositional / surface
generalization splits** so retrieval and templates can no longer dominate:
- distinct NL template families in train vs test (target Stage-3 surface gen),
- hold-out operation **combinations** (target Stage-4 composition),
- more paraphrase diversity (reduce wording → operation leakage, see finding-001).

## Reproduce
```bash
make setup
python scripts/generate_data.py --n-per-op 200
python scripts/audit.py
python scripts/train.py --steps 1500 --n-embd 128 --n-layer 4 --n-head 4 --seed 0
```
Saved model: `artifacts/checkpoints/stage1.pt`; manifest: `artifacts/manifests/stage1.json`.
