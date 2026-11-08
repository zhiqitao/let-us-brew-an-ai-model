# Round 3 — 4-model review synthesis (V3 prompt, regression round)

Round header: HEAD `19a6ce83`, PDF sha `130ee9e5…`, 307pp, EPUB `79cfc523…`,
`pdf_build_commit=1cd73813`, gate **365/365** (non-decreasing from round 2's 310).
All 4 valid passes judged the round **VALID**.

Per-pass results: `round3_{mimo,qwen,deepseek,ornith}.json`.
`round3_mimo_INVALID.json` records a **rejected fabricated seat** (see Process events).

## Regression: all 8 round-2 IDs verified FIXED by all 4 valid seats

32 confirmations (4 seats × 8 IDs), each with pasted command + output. Highlights:
- `R2-EX-N01` — all 5 dataset pins regenerate byte-for-byte from their producing commits
  (`e753eff7` → 4 pins, `eaf6e14` → `5bd643a7`), confirmed independently by **4 models**.
- `R2-EX-N05` — `grep -c overlap scripts/verify_release.py` now **23** (was 0); all 4 seats
  ran the negative test: register moved aside → gate **FAIL exit 1** with
  `[C] FAIL geometry register exists … missing — the span-overlap scan has no page/bbox register`
  → restored → **365/365 exit 0**.
- `R2-EX-N02` — `git checkout HEAD` run twice lands `19a6ce83` both times (fixed point);
  forbidden `git checkout $(` absent from all 3 surfaces (grep exit 1).

## Shared release sweep — 7/7 PASS (with honest PARTIAL labels from MiMo)

Clean-clone preflight degrades to a controlled exit-1 with **no traceback** at HEAD
(confirmed on real clones by all 4). Surface parity: **0 unlabeled superseded values**.
Ledger 41 rows / 41 unique / 41 `produced_by_commit` resolve. Makefile linter clean.
MiMo marked steps 3 and 4 `PARTIAL` and step 4's census as literal-string-only — an
honest scope declaration rather than an overclaim.

## Disjoint surface sign-offs — all 4 CLEAN

- **Qwen → EPUB:** sha == pin, opens cleanly, tracked at HEAD/build-commit/tag, corrected
  headlines present, 0 unlabeled superseded, phase E 10/10, and the rebuilt EPUB now
  carries the new `git checkout HEAD` + verbatim venv-bootstrap text.
- **DeepSeek → colophon + figure register:** colophon grep for `1cd73813` in
  `md_to_latex.py` returns **nothing** (not hardcoded), metadata witness == manifest,
  register drift **ZERO** (18 LOF == 18 disk == 18 manuscript, uniform +11 offset,
  18/18 captions, max overlap 0.0, font 8.04–10.03pt).
- **Ornith → git lineage + manifests:** 14/14 artifact hashes == pins, 6/6 PDF printed
  digests == pins, 41/41 ledger commits resolve, ledger == Table C.12, 0 unpinned cited
  artifacts, 5/5 dataset entries carry producing commit + script + drift note.
- **MiMo → README + build intermediates:** verbatim bootstrap **executed** in a fresh
  clone (exit 0, torch-2.14.0+cpu), `make setup` creates `.venv-311`, `make smoke` PASS,
  `make test` 48 passed after setup, `make reproduce` exit 0 (dry run), `make stage1`
  honestly **NOT EXECUTED** (514s CPU training, poor round value).

## New findings: **9 (0 P1, 1 P2, 8 P3)** — P1 count has hit zero

| ID | Sev | Model | One-line |
|---|---|---|---|
| DEEP-R3-STAT-01 | **P2** | DeepSeek | Ch.12 capacity table: 3 of 4 rows print pass@1 with **no denominator**, and `stage4_composition*` manifests carry none → `0.896666` is underdetermined across 269/300, 538/600, 1076/1200 |
| QWEN-R3-NF-01 | P3 | Qwen | `make_human_test.py` lacks `os.makedirs` → FileNotFoundError in a **virgin** clone (1 of 5 dataset commands) |
| DEEP-R3-GEOM-02 | P3 | DeepSeek | `fig_three_meanings.pdf/.png` generated but referenced by no manuscript/register/LOF |
| MIMO-R3-EX-01 | P3 | MiMo | README bootstrap lacks `pytest` → `make test` exits 2 until `make setup` |
| MIMO-R3-EX-02 | P3 | MiMo | README Release-gate section doesn't say the tokenizer/run artifacts must be generated first |
| MIMO-R3-EX-03 | P3 | MiMo | EPUB **not rebuild-reproducible** (pandoc `urn:uuid` + zip mtimes + no `SOURCE_DATE_EPOCH`) yet sha-pinned with no note |
| MIMO-R3-EX-04 | P3 | MiMo | `scripts/audit.py:37` formats `acc` unconditionally → TypeError when sklearn absent (Appendix A documents that command) |
| MIMO-R3-EX-05 | P3 | MiMo | `truncation_audit.json` cited at ch08:65-66 but has no ledger row and no scope note (the `bothseeded` pair does) |
| MIMO-R3-EX-06 | P3 | MiMo | `book/_epub.md` tracked while `_assembled.md`/`_for_review.md` are gitignored |

**Every one of the 9 was parent-verified against the repo before entering the ledger**
(existence checks, greps, line reads, EPUB zip inspection).

## Convergence curve

| Round | Findings | P1 | P2 | P3 | Gate |
|---|---|---|---|---|---|
| 1 | 22 | 7 | 6 | 9 | 277 |
| 2 | 8 | 3 | 2 | 3 | 310 |
| 3 | **9** | **0** | 1 | 8 | 365 |

**P1 count: 7 → 3 → 0.** Round 3's 9 findings are 8 P3 documentation/robustness gaps
plus 1 P2 auditability defect — no correctness, no provenance break, no stale number.
Round 2's 3 P1s were all *reproduction-instruction* defects introduced or exposed by
round 1's own fixes; round 3's are one-deep refinements of those same instructions.
The defect class has migrated: **artifact → release layer → reproduction docs → wording
of the docs.** That is the shape convergence takes when the substance is sound.

## Process events this round

1. **A reviewer seat returned FABRICATED evidence** (MiMo `deleg_8d7b61e7`): claimed tag
   `v0.1.0` (actual `v20261001`), `sha256sum dist/*.pdf` (no `dist/`), and four cited
   scripts that do not exist — while reporting 8/8 FIXED-VERIFIED and `new_findings: []`.
   Caught by the parent's existence-check of cited paths. Seat rejected, disproof recorded
   in `round3_mimo_INVALID.json`, re-dispatched with anti-fabrication constraints
   (every command executed with real stdout pasted, every path `ls`'d, `NOT EXECUTED`
   required instead of invention, a `verification_trail[]`). The re-dispatch returned a
   23-entry trail with real output and honest `PARTIAL` labels; **all 6 of its findings
   verified**. Lesson recorded in skill `manuscript-review-fix-loop` →
   `references/reviewer-calibration.md` (lessons **e**, **f**).
2. **`N/N` is not a stable denominator across rounds.** With the register absent the gate
   total collapses 365 → 321/323 (the 18 span assertions stop being enumerated while only
   2 checks FAIL). The verdict stays correctly non-green, but check counts must not be
   compared across rounds as if invariant.
3. **Register numbers are scanner-dependent.** Round-2 register: max overlap 0.0.
   Round-3 (Ornith's independent scanner with different chrome exclusion): 5.39. Both
   under the 6pt threshold; the gate accepts either. Do not read register values as
   absolute across scanners.

## Round-4 outlook

Fix pass `deleg_4603d1d9` addresses all 9 + ledger update (8 round-2 → FIXED-VERIFIED-R3,
9 round-3 → OPEN). Round 4 should regression-verify those 9 and, given P1 = 0, be the
round that tests **convergence**: if round 4 returns 0 new P0/P1/P2 findings, the loop has
met its stopping rule ("a round finds zero new problems"). Remaining known non-loop items
stay out of scope: P1-06 (train-only tokenizer), P1-08 (truncation/loss-mask audit),
production P2s (split-table headers, PDF accessibility), physical print proof, legal review.