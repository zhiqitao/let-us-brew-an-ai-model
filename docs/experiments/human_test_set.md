# Experiment — Human-Written Test Set (external sanity check)

Status: `[MEASURED]` — real run, `scripts/eval_human_test.py` on `stage1.pt`.

## Setup
A small independent set of 16 natural-language programming requests, phrased the way
a *person* would say them (informally, varied, no templates), covering both pilot
primitives and composites. Kept strictly separate from the synthetic training
distribution. The goal: an external reality check — does behavior learned in the
controlled synthetic world transfer to specs a human actually writes?

## Result

**0 / 16 human-written prompts solved.**

Even the simplest ones failed:

- "Take two numbers and give me back their total." → generated malformed code
- "Tell me which of these two is the bigger one." → `def solve(a): return a a a + a - b`
- "Which is smaller…" → `def is. in a: nb + total`
- "Give me the absolute value of this number." → `return a < b`

Every generated program was syntactically or semantically wrong.

## Interpretation — the sanity check CORROBORATES the thesis

This is not a setback; it is exactly the external confirmation the book needed. The
pilot model achieves **0.897 in-distribution** on template-phrased prompts and **0.000
on human-phrased** versions of the same operations. That is the surface-generalization
finding (Chapter 15) reproduced on *hand-written, out-of-distribution* phrasing.

The model did not learn "addition" as an idea. It learned a set of template
associations ("implement solve so that given a and b it returns their sum." →
`solve(a,b): return a+b`). The moment a human phrases the request differently — which
a real user always will — the model fails. This is the most honest, real-world-relevant
statement of the book's central lesson:

> A model that only works when the prompt matches its training templates has not
> learned the task. It has learned a template. The human test set is the proof.

## Honest caveats
- The model was also never trained on composite ops (they're held out), so those
  failing is expected and separate.
- One could improve on human-phrasing by training on diverse/diverse human-style
  prompts (see the diversity experiment, which showed high-diversity training
  reaches 1.000 surface robustness on synthetic variants) — a clear, actionable path.

## Reproduce
```bash
python scripts/make_human_test.py         # writes artifacts/datasets/human_test.jsonl
python scripts/eval_human_test.py --ckpt artifacts/checkpoints/stage1.pt
```
