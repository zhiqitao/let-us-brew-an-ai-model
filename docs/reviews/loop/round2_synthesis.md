# Round 2 — 4-model review synthesis (V3 prompt, regression round)

Round header: HEAD `3960c9f6`, PDF sha `c3700dfd…`, 306pp, EPUB `0529f94d…`,
`pdf_build_commit=2415ab1c`, gate **310/310** (non-decreasing from round 1's 277).
All 4 passes judged the round **VALID** (pins match, not void).

Per-pass results: `round2_{mimo,qwen,deepseek,ornith}.json`.

## Regression: all 22 round-1 IDs accounted

| Pass | IDs re-verified | Result |
|---|---|---|
| MiMo (execution) | R3-EX-01..06 | **6/6 FIXED-VERIFIED** |
| Qwen (provenance) | QWEN-R2-01/02/03/04, R4-01, R4-02 | **6/6 FIXED-VERIFIED** |
| DeepSeek (quant) | STAT-01..05 | **5/5** — but STAT-05 **DISPROVED** |
| Ornith (visual) | R4G-001/002/003/005, R1P-004 | **5/5 FIXED-VERIFIED** |

**21 FIXED + 1 DISPROVED = 22.** STAT-05 was a round-1 **false positive**
(`n_per` *was* disclosed at point of use) — DeepSeek's round-1 self-doubt was right.
Ornith upgraded R4G-005 from vision-only to EXECUTED-DETERMINISTIC (0 collisions > 6pt
+ renders), satisfying the round-1 evidence-tier correction.

## Shared release sweep (§0.5) — all 7 steps PASS on all 4 passes

Independent confirmation of the round-1 release-cluster fixes: clean-clone preflight
degrades to a controlled exit-1 with **no traceback** at both commits (Qwen + MiMo +
Ornith all ran it on real clones); surface parity finds **0 unlabeled superseded values**
across PDF/EPUB/README/manifest/ledger (the EPUB now labels its historical numbers);
ledger 41 rows / 41 unique ids / 41 `produced_by_commit` resolve; Makefile linter clean;
`make reproduce` exits 0 in the main repo **and** a clean clone.

## Disjoint surface sign-offs — all 4 CLEAN

- **MiMo → EPUB:** sha == manifest, corrected numbers present (0.743/0.950/0.9167/0.893),
  0 superseded strings, git-tracked at HEAD and the documented commit, gate phase E 10/10.
- **DeepSeek → README + build intermediates:** taxonomy honest, `archived experiment
  manifests`, 0 hardcoded `af32fb8b`; `_assembled.md`/`_for_review.md` deleted + gitignored,
  regeneration leaves the tree clean.
- **Ornith → colophon + figure register:** colophon derives from `git rev-parse HEAD` at
  build time (not hardcoded), metadata witness == manifest, manuscript diff EMPTY,
  **LOF 18 == on-disk 18 == register, zero drift**.
- **Qwen → git lineage + manifests:** 14/14 artifact hashes == pins, 6/6 PDF printed
  digests == pins, 41/41 ledger commits resolve, ledger == Table C.12, 0 unpinned cited
  artifacts.

## New findings: **8 (3 P1, 2 P2, 3 P3)** — round 2 is NOT converged

| ID | Sev | Class | One-line |
|---|---|---|---|
| R2-EX-N01 | **P1** | execution | Dataset pins **unsatisfiable** from the shipped generator (3/5 mismatch, `output_type` list→int; `human_test` attribution wrong) |
| R2-EX-N02 | **P1** | execution | Documented `git checkout $(…pdf_build_commit)` is **not idempotent** (backward chain, no fixed point) |
| R2-EX-N05 | **P1** | gate | Gate has **no span-overlap check** (`grep -c overlap` = 0) though V3 §7 claims it; `geometry_measurements.json` untracked |
| R2-EX-N03 | P2 | execution | **No documented command creates `.venv-311`** (`source …/activate` rc=1 in a clean clone) |
| R2-EX-N04 | P2 | build-stamp | §0.5 witness path filter includes tracked **build outputs** → spurious mismatch |
| QWEN-R2-NF-01 | P3 | provenance | Same witness-filter defect (independent) |
| R2-EX-N06 | P3 | execution | Release PDF **gitignored while sha-pinned** (EPUB is tracked); clean-clone phase D FAILs |
| ORN-R2-GEOM-01 | P3 | visual | Fig 8.1 callout boxes faint grey-on-cream (cosmetic, vision-observed) |

**Cross-model agreement:** N04 == QWEN-R2-NF-01 — MiMo and Qwen independently found the
same witness-filter defect. That is the loop's independence signal working: two families,
same defect, neither sharing inputs.

**Convergence read:** round 1 found 22 (7 P1) against a book with a broken release
layer; round 2 found 8 (3 P1) against a book whose release layer now passes a 310-check
gate — and **3 of the 8 are defects in the review apparatus itself** (N04/NF-01 = the
V3 check; N05 = a V3 §7 promise the gate never implemented), not in the book. The
book-facing P1s (N01, N02) are both *documentation-of-reproduction* defects introduced or
exposed by round 1's own fixes. Defect count is falling and migrating from the artifact to
the instrumentation — the direction convergence should take.

## Phase-B adjudication matrix (round 2)

| ID | Finding's proposed correction | Adjudicated decision |
|---|---|---|
| R2-EX-N01 | "regenerate the 3 pilot splits and re-pin" | **CORRECTION REJECTED, OBSERVATION UPHELD.** The pins exist to freeze the content the book's numbers were *scored on*; the recorded pilot results were computed on the old-generator splits, so re-pinning to fresh output would make the pin match shipped code but **stop matching the scored-on data** — strictly worse. Fix = keep pins, add per-file `produced_by_commit` + `producing_script`, disclose the drift (`list`→`int`), correct `human_test` → `make_human_test.py`, gate WARN (not FAIL) on drift. |
| R2-EX-N02 | document "checkout \<build commit\> or later" | **UPHELD.** Root cause is chicken-and-egg (`pdf_build_commit` recorded in a commit postdating the build). Fix = document checkout HEAD for verification; forbid the non-idempotent `git checkout $(` form via a gate check. |
| R2-EX-N03 | document the venv bootstrap verbatim | **UPHELD.** `.venv-311` is gitignored and exists only on the author's machine; docs referenced it as if shipped. |
| R2-EX-N04 / NF-01 | scope the witness filter to sources | **UPHELD (2-model agreement).** Check-construction defect, not provenance drift: excluding `book/latex/book.pdf`+`book.tex` yields exactly `2415ab1c`. V3 patched; exact command added to the gate. |
| R2-EX-N05 | add the span-overlap extractor + track the JSON | **UPHELD.** V3 §7 promised a check the gate never had — a *documentation-vs-implementation* gap in our own apparatus. |
| R2-EX-N06 | track the PDF *or* state the pin is verified against the published artifact | **UPHELD.** Prefer tracking (1.5MB) so the pin is clone-verifiable, matching the EPUB policy. |
| ORN-R2-GEOM-01 | darken callout contrast | **UPHELD as P3 cosmetic.** Correctly V3-capped at VISION-OBSERVED / HIGH-CONFIDENCE INFERENCE; no geometry row because contrast is not overlap. |
| DeepSeek residual nit (README "truncation") | — | **REFUTED by parent:** the sentence wraps to the next line; not truncated. |
| DeepSeek STAT-05 (round 1) | — | **DISPROVED** — round-1 false positive; `n_per` was disclosed. |

## Round-3 outlook

Fix pass `deleg_736c16d1` addresses all 8 + ledger update (21 → FIXED-VERIFIED-R2,
STAT-05 → DISPROVED-R2, 8 new → OPEN). Round 3 should be another regression round over
the 8 new IDs, and must specifically re-check: (a) dataset-pin drift disclosure actually
satisfies a clean-clone reader, (b) the documented checkout is idempotent, (c) the new
span-overlap gate check fails when the JSON is removed/untracked (negative test), (d) the
venv bootstrap command works verbatim in a fresh clone.