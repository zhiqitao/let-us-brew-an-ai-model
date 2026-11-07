# Publishing-Readiness Review Instructions — V3 (round 2)

Supersedes `REVIEW_INSTRUCTIONS_V2.md`. Derived from the 4-model Phase-3 discussion
(`discussion_round1_{mimo,deepseek,ornith,qwen}.json`) after round 1 produced 22 findings
(7 P1 / 6 P2 / 9 P3) but **skipped the mandatory Phase-B adjudication matrix** — V3 makes
that step non-optional and adds the deterministic gates the discussion converged on.

Round 2 is a **REGRESSION round**: every one of the 22 round-1 IDs must be re-verified with
a stored transcript or marked `CANNOT-RELOCATE`; new findings are capped at class-relevant
ones so the loop converges rather than wanders.

---

## §0 Round header (artifact pinning — void on mismatch)

Before reviewing, record and assert:

- `git rev-parse HEAD`, `git describe --tags`, tag target commit.
- `docs/release_manifest.json`: `tag_target_commit`, `pdf_build_commit`, `pdf.sha256`,
  **`pdf.page_count`** (the field MUST exist; if absent the pin is unenforceable and the
  absence is itself a P1 — round-1 R2-04), `epub.sha256`.
- Built PDF sha256 + page count == manifest. Built EPUB sha256 == manifest.
- `verify_release.py` total (record N/N; must be non-decreasing across rounds).

If any pin mismatches, STOP: the round is void until the header is re-pinned.

## §0.5 Shared release sweep (deterministic; runs BEFORE the partitioned passes)

**Partitioning governs depth, never surface coverage.** Every one of the 4 passes executes
this same ~10-minute deterministic sweep first and consumes its output as a shared baseline:

1. **Gate preflight on a clean clone** — `git clone` to a temp dir at the documented
   commit, run `scripts/verify_release.py`. Record three SEPARATE outcomes (do not fuse
   them, round-1 R2-01 did): (a) fresh clone at the documented commit, (b) at HEAD,
   (c) `git ls-files` census of every path the gate opens. A Python traceback (not a clean
   FAIL) = **P0**.
2. **Build-witness / colophon ground truth** — `git log -1 --format=%H -- book/manuscript
   book/latex` == manifest `pdf_build_commit`; the PDF's metadata witness == manifest;
   `git diff --name-only <witness> HEAD -- book/manuscript` empty. Mismatch = **P1
   false-colophon** even when manifest + colophon + gate all agree on the wrong commit.
3. **Surface parity** — extract text from PDF, EPUB, `README.md`,
   `docs/release_manifest.json`, `docs/reviews/loop/provenance_ledger.json`
   (`book/_assembled.md` and `book/_for_review.md` were deleted in the round-1 fix pass —
   they are regenerable build intermediates, now gitignored; regenerate with
   `python book/assemble.py` if a round needs them, then sweep the regeneration).
   Derive the canonical-number registry from
   `artifacts/manifests/*.json`. Per surface: canonical set equal, and every superseded
   value (`0.641`, `0.500`, `0.143`, `0.350`, `0.900`-class at n=300) appears only within
   ±200 chars of a `SUPERSEDED`/`supersedes`/`historical` token. **The PDF being clean is
   NOT evidence the companion surfaces are** — round-1's stale defects lived entirely
   outside the PDF.
4. **Tracked-inputs census** — every path literal the gate/run scripts open must be
   `git ls-files --error-unmatch` clean at the documented commit, or reported
   `REQUIRED-BUT-UNTRACKED`. Disk existence is NOT enough (gitignored inputs pass
   `os.path.exists` silently).
5. **Ships-claim-vs-git** — every manuscript/README "ships X under `<path>`" /
   "the repository carries X" claim → `git ls-files <path>` non-empty OR the claim is
   explicitly scoped to "regenerable, not shipped". Ships-over-gitignored = auto **P1**.
6. **Ledger schema** — `provenance_ledger.json`: row count == scored runs in
   `artifacts/manifests/`, no duplicate `experiment_id`, uniform suffix, no unexpected
   nulls, every `produced_by_commit` resolves.
7. **Makefile target linter** — every `scripts/*.py` token in a recipe exists; every
   `.PHONY` target has a recipe; `make -n` parse-clean.

**Disjoint surface sign-off (4-way redundancy on the P1s):** after the shared sweep, each
pass signs off ONE disjoint surface in depth — round 2: MiMo = EPUB, DeepSeek =
`_assembled.md` + README, Ornith = PDF colophon/build-witness + figure register, Qwen =
git lineage + manifests. **Rotate the sign-off surface each round** so no model examines
the same surface twice (fresh eyes without mismatching class skill).

**Surfaces-not-opened declaration:** each pass enumerates the release surfaces it did NOT
open and why. Silence is treated as a coverage claim and scored as a miss.

## §1 Two-phase independence (unchanged from V2, adjudication now enforced)

- **Phase A (blind):** review with NO knowledge of other models' findings.
- **Phase B (adversarial cross-adjudication): MANDATORY — a round is INVALID without the
  adjudication matrix.** One row per P0/P1:
  `{id, challenger (a DIFFERENT model), re-derivation command, verdict:
  UPHELD / DOWNGRADED / DISPROVED, author_recused: true}`. The finding's author recuses
  from its adjudication. Round 1 asserted "All CONFIRMED" with zero adversarial
  re-derivation — that is why this very V3 exists.

## §2 Pass partitioning (4 class primaries kept; depth partitioned, coverage shared)

- **MiMo — execution / reproduction-from-the-artifact.** Re-derive every headline number
  from manifests; assert realized-vs-requested shape by running code; reproduce a
  representative run from a clean clone. **Also:** assert every Makefile target's recipe
  resolves and run `make reproduce`, recording the exit code. For every colophon/README/
  back-matter claim naming a build artifact, commit hash, or reproduction command,
  **execute it verbatim from a clean clone** and record pass/fail with exact output.
- **DeepSeek — quantitative integrity / statistics / intervention audit.** Every headline
  number carries `(value, n_test_cases, n_seeds, min-max)`; **the denominator must appear
  AT THE POINT OF USE**, not reconstructable from an appendix forty pages later. Any
  magnitude adjective (`small`, `tiny`, `negligible`, `tightly stable`, `identical`)
  applied to a measured quantity must print the dispersion/CI supporting it; if the CI
  spans zero OR the compared arms differ in `n_per`/`steps`, the adjective is auto-**P1
  SCOPE OVERREACH**. Intervention audit: diff the full config + data-construction path;
  "one variable" only when the diff has exactly one entry. **Anchor discipline:** cite the
  PRINTED chapter/section number from the built PDF's TOC, never the manuscript filename
  (filenames offset by up to four: `ch21_*.md` = printed 19, `ch22_*.md` = 20,
  `ch25_*.md` = 21; no `ch19`/`ch23`/`ch24` files exist).
- **Ornith — visual / print / render-geometry.** Render-geometry is the primary integrity
  gate and must be **deterministic**: a bbox-overlap extractor (span intersections between
  callout/annotation spans and adjacent gloss/axis/caption spans; flag overlap > 6pt) is a
  primary duty, so overlap defects do not depend on model vision. The 8pt label floor is a
  **READABILITY FLAG, not an integrity gate** — a sub-8pt interior label is P3 unless it
  renders a required value illegible (captions at 10.9pt already pass). Vision is
  secondary, only for design/pedagogy. Derive the figure register from the built PDF's
  List of Figures; rate EVERY figure on 4 axes.
- **Qwen — provenance / artifact integrity / manuscript self-consistency.** Round-header
  pinning; hash every cited artifact and flag unpinned ones; stale-fragment +
  citation-target sweeps; epistemic-label audit; claim-tier reconciliation; ledger schema.
  The clean-clone gate run lives in §0.5 (shared), not here exclusively.

**Cross-class duty (all passes):** even though your partition is P, you MUST still run the
two cheapest checks from every other class and report them as secondary findings — a
defect confirmable in under 5 commands is never out of scope. **Quote one finding from a
different model's class that you independently attempted to reproduce, and state whether
it held.**

## §3 Finding schema (7 required fields + root cause; evidence tiers)

Every finding: `id`, `class`, `severity` (P0–P3), `confidence`, `anchor`
(`pdf_page`/`printed_page`/`section`/`quote`), `repro_command`, `observed`, `blast_radius`,
`correction`, `acceptance_assertion`, `evidence_tier`.

**8th required field — `root_cause`:** for release/reproduction-class findings, name the
root cause (script drift vs dataset non-reproducibility vs gitignored/unpinned artifact),
not just the symptom; state what any A/B held constant.

**Evidence tiers:** `EXECUTED-DETERMINISTIC`, `EXECUTED-ESTIMATE`, `EXECUTED-INSTRUMENT`
(geometry/print: overlap, overflow, label-size claims MUST ship measured coordinates —
bbox, overlap in pt — emitted by a committed script), `MECHANICALLY-DERIVED`,
`READ-ONLY`, `VISION-OBSERVED`. **Model vision may only corroborate. A finding whose only
evidence is vision is at most HIGH-CONFIDENCE INFERENCE; "I saw it" is never CONFIRMED.**

## §4 Sweeps (run FIRST, over ALL release surfaces)

- **Stale-fragment sweep** over every surface listed in §0.5 step 3 (not manuscript-only).
- **Citation-target sweep:** every doc the book cites exists; no citing sentence depends on
  a table under a `SUPERSEDED`/`RETRACTED` banner.
- **Claim-inventory lint:** every manuscript hit of
  `reproduc|regenerab|deterministic|ships|pinned|identical|version-controlled` maps to a
  claim ID with an executable assertion and current status; unmapped hit = P1.
- **Report EXAMINED counts per class** (figures measured, tables audited, claims
  inventoried, surfaces opened). A pass that cannot state its denominator reports
  `DENOMINATOR UNKNOWN` and cannot contribute to READY.

## §5 Canonical issue ledger (the only ID authority)

`docs/reviews/loop/issue_ledger.json` — seeded with round-1's 22 IDs. Each pass returns
JSON validated mechanically (the 8 §3 fields enforced by a validator script); a round with
unvalidated findings is void. Prose-only schema enforcement failed in round 1 (§5 named a
file that did not exist — R3-EX-06).

## §6 New-class mandates (V2's 8 + these)

1. Inferential integrity (steps/budget held fixed claims).
2. Dismissal laundering (a control failure waved off).
3. Citation-into-superseded-evidence.
4. Reproduction-from-the-artifact (execute, don't deduce).
5. Unpinned-provenance drift (producing script ≠ shipped script).
6. Quantitative integrity / statistics (n, CI, dispersion).
7. Measurement-instrument validity (per-arm `n_per`/padding differences).
8. Ledger / release-record self-consistency.
9. **Build-stamp integrity (NEW):** the build records the actual build commit (witness in
   PDF metadata + `docs/release_manifest.json`); the gate asserts colophon ==
   `pdf_build_commit` == witness, and the PDF content matches the build commit's source. A
   colophon naming a commit that is not the actual build commit is a **P1 false-provenance**.
10. **Seeded-defect recall (NEW):** before each round the synthesizer plants 3 defects —
    one superseded number in a NON-PDF surface (EPUB), one false provenance sentence, one
    geometry overlap ≥ 20pt — and measures recall. Fewer than 3/3 caught invalidates that
    round's "clean" verdict for the planted classes.

## §7 Release gate (READY requires all)

`scripts/verify_release.py` green, including: phase A/B/D as before, **phase C render
geometry** (digest completeness + text-block containment + span-overlap), **phase D′
release-record** (page_count, EPUB stale sweep, colophon/PDF-content-vs-build-commit,
ledger schema + `produced_by_commit` resolve, ships-claim-vs-git, dataset pins), and the
**clean-clone preflight** (no traceback). Companion-surface sweeps run IN-GATE, not as
out-of-band manual greps.

## Round-2 anti-regression checks (must stay green)

1. `verify_release.py` exits 0 at HEAD; printed total non-decreasing (N ≥ round-1's N).
2. Surface parity green: canonical-number fingerprint identical across PDF/EPUB/
   `_assembled.md`; zero superseded values outside a ±200-char window.
3. Build witness green: one `BUILD_COMMIT=<40-hex>` per surface == manifest
   `pdf_build_commit`; `git diff --name-only <witness> HEAD -- book/manuscript` empty.
4. `make reproduce` exits 0 (or target deleted + README updated); `git ls-files
   scripts/reproduce.py` non-empty whenever the target exists.
5. Claim-inventory lint: unmapped count == 0.
6. Repo hygiene: `git status --porcelain` empty; `git ls-files book/*.epub` non-empty;
   EPUB sha256 in manifest; no `[0-9a-f]{40}` in manuscript text other than the two
   sanctioned commits (tag target + build witness).
7. Geometry findings carry machine evidence: `geometry_measurements.json` with ≥ 18 rows
   `{figure_id, page, bbox, overlap_pt, font_pt}` — no visual P0–P2 without a row.

## Round-1 adjudication decisions carried into round 2 (Phase-B matrix, applied)

| ID | Original | Adjudication | Basis |
|---|---|---|---|
| R1P-004 | P3 | **DOWNGRADED → readability polish** (fixed anyway) | 8pt floor is V2's own rubric, not a design standard; 4.3pt may be pre-transform size (DeepSeek + Ornith self-doubt) |
| R4G-005 | P3 | **Evidence tier corrected → vision + post-fix bbox** | vision-only; §3 forbids CONFIRMED without measurement (DeepSeek + Ornith self-doubt) |
| QWEN-R2-01 | P1 | **UPHELD, re-anchored** | support = 5 mismatches at `af32fb8b` + gitignore census, NOT the HEAD crash (DeepSeek: two defects fused) |
| QWEN-R2-04 | P3 | **RECLASSIFIED → gate-addition** (field added anyway) | absence, not a false claim (Qwen self-doubt + Ornith dispute) |
| QWEN-R4-02 | P3 | **UPHELD-P3** (fixed; trivial) | Ornith disputes as taxonomy purity; harm near-zero but fix is one line |
| R3-EX-02 | P1 | **DOWNGRADED → P2** | double-counts R3-EX-03; direction of change is toward reproducibility (Ornith) |
| R3-EX-03 | P2 | **UPHELD, blast radius expanded** (`ch09:172` too) | worse reading open: shipped 0.900 may be from an unseeded run (DeepSeek) |
| STAT-01 | P1 | **UPHELD-P1** | V2 §4 auto-P1: denominator must be at point of use |
| STAT-02 | P1 | **UPHELD at printed Ch.19; Ch.20 sub-claim UNVERIFIED** | DeepSeek could not locate the missing qualifier in `ch20_*.md` |
| STAT-03 | P1 | **UPHELD + root cause extended → dataset regeneration** | Qwen: TF-IDF index over regenerated content; dataset now sha-pinned |
| STAT-04 | P2 | **UPHELD** | DeepSeek defends hardest; severity call, not a discovery |
| STAT-05 | P3 | **DOWNGRADED → wording nit** (fixed anyway) | `n_per` 60-vs-130 IS disclosed in Appendix C (DeepSeek self-doubt) |