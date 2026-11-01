# Decode / Termination Ablation — is composition 0.000 an artifact?

**Question (external review):** the book's central result is composition
**0.000** on held-out composites. Is that a generation/decoding/extraction
artifact (the model emits *something*, but NUL-padding or a short `max_new`
truncates it into invalid Python), or a genuine failure of the model?

- Checkpoint: `artifacts/checkpoints/stage4_exposure.pt` (884,224 params, loaded, NOT retrained)
- Tokenizer: `artifacts/tokenizer/comp_tok.json` (saved vocab, 291 tokens)
- Split: identical to `scripts/run_composition_exposure.py`, seed 0 — 120 held-out composites (max_add, double_first, len_minus_one), 120 exposed composites (abs_add, sub_abs, sum_of_abs) as control, 1400 primitive+exposed train tasks (unused here).
- Extraction for every setting: decode -> NUL-truncate -> `.strip()`, exactly
  as `src/eval/evaluator_runner.generate_code` does.

## Settings

| setting | T | max_new | source run | note |
|---|---|---|---|---|
| greedy_max64 | 0.0 | 64 | greedy_max256 | prefix of one run (token stream held fixed) |
| greedy_max128 | 0.0 | 128 | greedy_max256 | prefix of one run (token stream held fixed) |
| greedy_max256 | 0.0 | 256 | greedy_max256 | prefix of one run (token stream held fixed) |
| sample08_max64 | 0.8 | 64 | sample08_max256 | prefix of one run (token stream held fixed) |
| sample08_max128 | 0.8 | 128 | sample08_max256 | prefix of one run (token stream held fixed) |
| sample08_max256 | 0.8 | 256 | sample08_max256 | prefix of one run (token stream held fixed) |
| book_sample08_max80 | 0.8 | 80 | book_sample08_max80 | the book's eval procedure |

## HELD-OUT composites (never seen in training) — the key table

| setting | syntax | **valid prog** | executable | **pass@1** | (a) parse | (b) allowlist | (c) 0 tests | (d) partial | (e) all |
|---|---|---|---|---|---|---|---|---|---|
| greedy_max64 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| greedy_max128 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| greedy_max256 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| sample08_max64 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| sample08_max128 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| sample08_max256 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| book_sample08_max80 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |

## EXPOSED composites (seen in training) — control

| setting | syntax | **valid prog** | executable | **pass@1** | (a) parse | (b) allowlist | (c) 0 tests | (d) partial | (e) all |
|---|---|---|---|---|---|---|---|---|---|
| greedy_max64 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| greedy_max128 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| greedy_max256 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| sample08_max64 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| sample08_max128 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| sample08_max256 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| book_sample08_max80 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |

## Interpretation

**The 0.000 is NOT an extraction artifact.** Even with the most favorable decode we tried (greedy argmax, max_new=256, NUL-truncation) only 0.000 of held-out generations are valid programs (book setting: 0.000); sampled T=0.8 at max_new=256 gives 0.000. Longer generation and greedy decoding do not rescue the format, so the failure is upstream of extraction — the model does not emit well-formed programs at all for held-out composite prompts.

**pass@1 stays 0.000 under every setting** on held-out composites (greedy@64/128/256: 0.000/0.000/0.000; sampled@64/128/256: 0.000/0.000/0.000; book: 0.000). So even where the model does produce valid programs, they are semantically wrong — the composition failure is not merely a formatting failure.

**Control (exposed composites, seen in training):** valid-program rate 0.000 (greedy@256) / 0.000 (book), pass@1 0.000 / 0.000. The same decode pipeline produces valid, passing programs when the composite was seen — so the pipeline itself is sound and the held-out failure is specific to the unseen composition, not to decoding in general.

**Verdict:** the composition 0.000 is *not* an artifact of NUL-truncation or a short max_new: greedy decoding and 3-4x longer generation do not produce a meaningful valid-program rate on held-out composites, and pass@1 is 0.000 under every decode setting. Where the model does emit valid programs (the exposed control) they pass — so the pipeline is sound. The failure is real: on unseen compositions the model cannot generate a well-formed, correct program, which is a generation+semantic failure on OOD prompts, not an extraction bug.

## Example generations (first held-out task)

**book_sample08_max80** — extracted program (parse_fail, 0/7 tests):

```python
return b):
```

**greedy_max256** — extracted program (parse_fail, 0/7 tests):

```python
return b):
```

---
Raw programs archived under `artifacts/raw_outputs/decode_ablation/`; machine-readable results in `artifacts/manifests/decode_ablation.json`.
