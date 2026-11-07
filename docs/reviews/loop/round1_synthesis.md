# Round 1 — 4-model independent review synthesis (V2 prompt)

Round header: HEAD `49831ce4`, PDF sha `41e71d07…`, 301pp, tag `v20261001`→`a45a881`, gate 277/277.
Pass partition (V2): MiMo=execution, DeepSeek=quantitative/statistics, Ornith=visual/geometry, Qwen=provenance/self-consistency.
Total: **22 findings — 7 P1, 6 P2, 9 P3.** All CONFIRMED with EXECUTED-DETERMINISTIC evidence except Ornith's R1P-004/R4G-005 (vision-corroborated inference).

## Findings by model

### MiMo — execution/re-derivation (6)
- **R3-EX-01 P1** — shipped **EPUB** carries superseded numbers (diversity 0.500/1.000, data_scaling 0.100/0.641, 0.88M=0.900); built 2026-09-13, never rebuilt; **unpinned** in release manifest. PDF is clean.
- **R3-EX-02 P1** — producing script ≠ shipped script: per-arm `random.seed(...)` added 2026-11-05, **2 days after** the manifests were committed (2026-11-03); no manifest/ledger/gate records the producing commit.
- **R3-EX-03 P2** — clean-clone re-run at HEAD does **not** reproduce seed-0 data-scaling: size-300 collapses 0.900→0.180 (54/300); controlled A/B isolates the cause to the added `random.seed` line. Contradicts "regenerable from the recorded config and seed."
- **R3-EX-04 P2** — `make reproduce` broken: references `scripts/reproduce.py`, which does not exist in any commit.
- **R3-EX-05 P3** — committed build intermediates (`book/_assembled.md`, `_for_review.md`) carry superseded values (0.383, 0.900) presented as current.
- **R3-EX-06 P3** — canonical issue ledger `docs/reviews/loop/issue_ledger.json` named by V2 §5 does not exist.

### DeepSeek — quantitative/statistics/intervention (5)
- **STAT-01 P1** — continual cells have **no denominators** (n_A=60, n_B=36); "identical B accuracy" is really *within one item* at n=36.
- **STAT-02 P1** — summary chapters (Ch.19/20/21) **drop the "combined intervention" qualifier** and assert *phrasing diversity alone*; Ch.13 correctly says 3-factor bundle. Ch.15 shows identifier-set change alone collapses to 0/600 — live alternative explanation.
- **STAT-03 P1** — **dismissal laundering caught by execution**: RETRIEVAL 0.000 waved off as "baseline-harness artifact"; re-running the shipped code gives 1.000/0.125 at *every* seed, and the stated mechanism (`--out/--tag`) can't affect pure TF-IDF → **BLOCKED-UNVERIFIED**. Same silent 0.000 in `stage1_seed1/2`, `composition_seed1/2`.
- **STAT-04 P2** — "small in-distribution cost": 3-seed CI **[-0.58, +0.17] spans zero**; "small" must not describe that.
- **STAT-05 P3** — Table C.7 "tightly stable across seeds" compares **n_per 60 (seed0) vs 130 (seeds1/2)** — undisclosed second variable.

### Qwen — provenance/artifact-integrity/self-consistency (6)
- **QWEN-R2-01 P1** — documented **clean-clone verification procedure fails**: at `af32fb8b` gate = 109/114 (5 mismatches); at HEAD it **crashes** (`FileNotFoundError: artifacts/tokenizer` — 7 tokenizers/38 checkpoints/5 datasets are **gitignored, absent from every commit**). Pilot path *is* reproducible (sha match) but the procedure omits the generation step.
- **QWEN-R2-02 P1** — **colophon's build-commit claim is false**: PDF contains text added in `49831ce4`, which postdates `af32fb8b`; real build commit = `49831ce4`. Gate only checks constant consistency, never PDF-content-vs-build-commit.
- **QWEN-R4-01 P1** — "the repository ships … the scored dataset files under `artifacts/datasets/`" is **false** (0 files, gitignored) and self-contradicts the quickstart 11 pages later.
- **QWEN-R2-03 P2** — `provenance_ledger.json` stale (30 vs 41 rows, missing all 11 corrected runs) + schema-inconsistent (duplicate `experiment_id`s, mixed `.json` suffix, nulls).
- **QWEN-R4-02 P3** — epistemic-label drift: README declares 6 levels; book applies `[SUPERSEDED]` (not in taxonomy), `[DERIVED]` never applied; glossary misdescribes the map's notation.
- **QWEN-R2-04 P3** — manifest `pdf` object has no page-count field (page count only in commit messages).

### Ornith — visual/print/render-geometry (5) + 18-figure register
- **R4G-001 P2** — Fig 5.1 callout overlaps its glosses (up to 72pt); vision: "effectively illegible."
- **R4G-002 P2** — Fig 13.2 dashed panel: corrected-run annotation collides with "from training families" (~100pt), garbling the key claim.
- **R4G-003 P3** — Table 18.1: "joint/interleaved" overflows column 1 into column 2 (~20pt).
- **R1P-004 P3** — interior figure labels **4.3–7pt** across 12+ figures (captions all 10.9pt, pass) — below 8pt floor.
- **R4G-005 P3** — vision-observed arrow overlaps: Fig 16.1 "3+2" operator obscured; Fig 8.1 arrow pierces parameter block.
- Register: 18 figures from LOF; 0 spans past trim/text-block; all captions ≥8pt; axes-box clipping *refuted* on 12.1/15.1 (not carried as findings).

## Cross-model synthesis

### COMMON — found by 2+ models independently
1. **Release/reproduction claims exceed the artifacts** (3 models): MiMo R3-EX-02/03 (producing-script drift, re-run doesn't reproduce) + Qwen QWEN-R2-01/02/R4-01 (gate crashes, colophon false, "ships datasets" false) + DeepSeek STAT-03 (RETRIEVAL dismissal falsified). **Biggest cross-model agreement — the headline of round 1.**
2. **Stale artifacts outside the PDF** (3 models): MiMo R3-EX-01 (EPUB) + R3-EX-05 (build intermediates) + Qwen QWEN-R2-03 (provenance ledger). Theme: the PDF is clean; *companion surfaces* are not.
3. **Uncaveated strong claims contradicted by own data** (2 models): DeepSeek STAT-02/04 (single-lever "phrasing diversity", "small cost" CI spans zero) + MiMo R3-EX-03 ("regenerable from config and seed").

### UNIQUE — only one model found it
- **MiMo:** EPUB staleness (nobody else opened the EPUB), `make reproduce` broken, build intermediates, missing ledger.
- **DeepSeek:** continual denominators, phrasing-diversity overreach, RETRIEVAL falsification, CI-spans-zero, n_per 60-vs-130.
- **Qwen:** gate crash, false colophon, false "ships datasets", ledger schema, label drift, page-count field.
- **Ornith:** all 5 figure findings (only visual pass — expected under partitioning).

### What each model MISSED that others caught
- MiMo missed: figure overlaps (Ornith), statistics (DeepSeek), colophon/gate-crash (Qwen).
- DeepSeek missed: EPUB staleness, figures, gate crash.
- Qwen missed: figures, statistics, EPUB.
- Ornith missed: everything non-visual (by design).

**Validation:** each model found its assigned defect class and missed the others' — exactly what V2's pass partitioning predicted. Shared-input correlation was reduced by partitioning, not eliminated.

## Round-1 verdict
**NOT CONVERGED.** 7 P1s, all EXECUTED. The numerics re-derive (62/62 MiMo, 68/68 DeepSeek headline cells) and the PDF is geometrically clean — but the **release/reproduction layer** (EPUB, colophon, clean-clone gate, producing-script provenance, dataset-shipping claim) and several **claim-tier overreaches** fail. Round 2 must re-check every one of these after the fix pass.