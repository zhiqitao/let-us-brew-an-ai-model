# Finding 001 — Pilot NL renderer leaks the operation

Status: `[MEASURED]` (via `scripts/audit.py`)

## Observation
A TF-IDF + logistic-regression classifier predicts the **operation** from the
natural-language specification with **cross-val accuracy = 1.000** (>0.9 warning
threshold). The pilot dataset's wording is strongly correlated with the answer.

## Why this matters
- For **Stage 1** (learn the op->code mapping), this is acceptable — the model is
  *supposed* to map meaning to code.
- For **Stage 3 surface generalization** (new wording/paraphrase), it is a problem:
  a model that succeeds might be exploiting the wording, not the meaning.

## Decision
Keep the current high-correlation renderer for the Stage 1 pilot. Before any Stage 3
surface-generalization experiment, add many more paraphrase families and hold out
*template families* in train vs test so wording cannot leak the operation. Record
this in the experiment manifest for the relevant runs.

## What the control rules out
The audit itself is sound — it correctly detects the leakage. This is a dataset
property, not an evaluator bug.
