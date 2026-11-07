# Review Instructions V2 — 4-Model Self-Verification Loop
# (Let Us Brew an AI Model)
# Versioned + frozen alongside the commit. Derived from: GPT-6.1-Sol Master Review
# Instructions + 4 ChatGPT review rounds, analyzed by MiMo/DeepSeek/Ornith/Qwen, then a
# 4-model discussion. Supersedes review/PUBLICATION_REVIEW_INSTRUCTIONS.md.
# Loop: review -> synthesize -> fix -> re-review, until 20 rounds OR a round finds ZERO new
# defects. Fix autonomously; do not ask. Gate every round with scripts/verify_release.py.

## 0. Round header — pin identity BEFORE reading (void the round on mismatch)
Record and assert at round start; any deviation from the prior round = STOP (different edition):
- built PDF SHA-256 + page count == docs/release_manifest.json
- git tag v20261001 -> target commit; PDF build commit; HEAD
- hash of EVERY artifact the book cites (all 7 tokenizer files, checkpoints, generator.py,
  figure sources) — flag any the release manifest does NOT pin (unpinned = drift risk)
- canonical figure/section set derived from the built PDF's List of Figures / TOC — NEVER a
  hand-typed constant (the register said "18"; the disk has ~19)
- page offset derived per-anchor from embedded printed numbers (the "PDF = printed + 11"
  constant breaks after any unnumbered insert/blank/roman switch)
- verify_release.py version + its 192-check output consumed as the shared baseline

## 1. Two-phase independence (manufactured, not assumed)
- **Phase A — BLIND:** each model gets ONLY the artifact + its defect-class rubric. No digest,
  no prior findings, no ledger. Submissions hashed/committed before Phase B opens. Only
  Phase-A-sealed findings count toward NOVELTY credit.
- **Phase B — ADVERSARIAL:** full ledger opened; regression + cross-falsification.
- Cross-model is NOT automatically independent (shared digest/manuscript = shared-interpretation
  error). Each pass must state its PRIMARY SOURCE (raw PDF / code / manifests / digest).
- **Blind cross-adjudication:** to falsify another model's P0/P1, re-derive from the cited raw
  evidence WITHOUT seeing the original verdict/severity; the AUTHOR recuses from judging their own
  finding. End UPHELD / DOWNGRADED / DISPROVED with a command or counter-quote. Only
  cross-attack can LOWER a severity — that keeps the scale honest.

## 2. Pass partitioning — by DISJOINT defect class (not by chapter, not by model strength)
- **MiMo = execution / re-derivation (R3 + new):** run the experiment scripts; assert
  realized-vs-requested shape (len==1200, ops 10/10, 480 records, 42 unique pairs); re-derive
  every manifest number; reproduce one representative run from a clean checkout.
- **DeepSeek = quantitative integrity / statistics / intervention audit (new class):** every pass@1
  must carry (value, n_test_cases, n_seeds, min-max across seeds, single-seed flag) — a number
  without its denominator is auto-P1 "uninterpretable"; compute cross-seed dispersion/CI; config-
  diff each arm pair and declare "one variable" ONLY when the diff has exactly one entry (this
  catches the Ch.18 continual 700+700 vs 600+600 steps mismatch and data_scaling 800 vs 1000).
- **Ornith = visual / print / render-geometry (R1 print + R4 geometry):** render-geometry is the
  PRIMARY integrity gate (label pt >= 8, spans inside page box, no label overlap); model vision is
  SECONDARY, only for design/pedagogy; figure register derived from the built PDF's LOF; re-locate
  prior findings by text/figure anchor (never page number).
- **Qwen = provenance / artifact integrity / manuscript self-consistency (R2 + R4):** hash every
  cited artifact and flag unpinned ones; resolve git lineage; attempt a clean-clone build at the
  tag (the tag is 210 files behind the shipped build and lacks verify_release.py — a P0 for a
  book claiming reproducibility); stale-fragment + citation-target sweep; epistemic-label and
  terminology audit; claim-tier reconciliation (uncaveated strong claim contradicted by the book's
  own data = P1, e.g. README "deterministic/reproducible" vs final_loss 0.0179/0.0218/0.0229).

## 3. Required fields per finding (reject the finding without all seven)
1. defect class; 2. severity (P0-P3) ⊕ confidence (CONFIRMED / HIGH-CONFIDENCE INFERENCE /
NEEDS VERIFICATION / NOT CHECKED / DISPROVED) + non-asserting VERIFY class; 3. canonical anchor
(PDF page + printed page + section + figure ID + verbatim quote + quote hash); 4. minimal repro
COMMAND with observed output; 5. blast radius — every other surface carrying the same claim
(prose, table, caption, figure, README, cited companion doc); 6. verbatim replacement text + an
executable acceptance assertion; 7. explicit not-checked list.
**Evidence tiers:** EXECUTED-DETERMINISTIC / EXECUTED-ESTIMATE (Monte-Carlo or seed-mismatched) /
MECHANICALLY-DERIVED / READ-ONLY. Only EXECUTED-DETERMINISTIC may be marked CONFIRMED; every
CONFIRMED must carry the command + transcript pointer. "I verified" without a command is rejected.

## 4. Mandatory rules
- **Statistics:** a bare point estimate with no n / no cross-seed variance is auto-P1.
- **Baseline dismissal:** a failing control (e.g. retrieval 0.000 on seeds 1-2) must be RE-RUN and
  shown to be a genuine harness bug, or tagged BLOCKED-UNVERIFIED with the failed command.
  "artifact" is never an accepted disposition on assertion alone (dismissal laundering).
- **Acknowledged caveat is NOT a defect** (keep ChatGPT's R2 four-way decision principle) — BUT an
  uncaveated strong claim contradicted by the book's own data IS a P1 (SCOPE OVERREACH).
- **Citation-target sweep:** for every doc the book cites, grep for SUPERSEDED/RETRACTED/"do NOT
  cite" and fail if a citing sentence depends on a table under such a banner (the book cites
  multiseed_replication.md in 4 places; that doc now opens with a SUPERSEDED banner).
- **Stale-fragment sweep FIRST** (deterministic, before any human reading): grep superseded values
  (0.350, 0.143, 0.500, 1.000, "42 versus 1200") + status phrases ("not yet", "still needs",
  "proposed, not measured"); any hit outside a labeled historical window = automatic P1.
- **Report PASSED checks** with counts, not only failures (cheapest credibility mechanism).
- **Coverage matrix** (page x T/V/Q/R) required; a pass that cannot fill it reports DENOMINATOR
  UNKNOWN, never a completeness %.

## 5. Canonical issue ledger (the only ID authority)
docs/reviews/loop/issue_ledger.json — {id, class, severity, confidence, anchors[{pdf_page,
printed_page, section, figure, quote_sha256}], first_seen_round, last_verified_round, status
(OPEN / VERIFIED-CLOSED / CANNOT-RELOCATE / BLOCKED), closure_evidence{command, exit_code,
output_sha256}}. Seed it by aliasing existing namespaces (PE-01, P0-0N, B/H, REV-, R1-R4) into
canonical IDs. No round creates an ID without checking for an existing one first. VERIFIED-CLOSED
requires a stored transcript. Findings that cannot be re-located by quote hash = CANNOT-RELOCATE
(itself an anchor-discipline defect).

## 6. New-class mandate (previously unreached — required coverage each round)
1. **Inferential integrity** — claim strength vs evidence strength (per-seed config-diff exactly
   one variable; report dispersion; downgrade effects inside dispersion to "consistent in 3 runs").
2. **Dismissal laundering** — unexplained control failure taints the run's treatment numbers until
   the cause is named and reproduced.
3. **Citation-into-retracted-evidence** — citing sentence whose support doc is superseded.
4. **Reproduction-from-the-artifact** — clean clone at the tag; follow only what the book states;
   measure where it breaks.
5. **Unpinned-provenance drift** — cited artifact/code the gate does not pin, silently mutated
   (comp_tok.json clobbered 75/291; generator.py at manifest commit != current file).
6. **Measurement-instrument validity** — is the reported quantity even comparable across arms
   (pad-share 0.355 vs 0.383, no ignore-index, no EOS, 128-slice cuts sum_of_abs)?
7. **Release-record / ledger self-consistency** — tag_target != pdf_build_commit; the gate must
   prove released-PDF content == TAGGED source; audit provenance_ledger.json's own schema.
8. **Cross-model consensus blind spots** — inject known seeded defects and measure whether the
   loop catches them (meta-evaluation of recall); compute Jaccard overlap of finding sets to
   distinguish consensus from correlated error.

## 7. Release gate (explicit; never sentiment or declining comment count)
READY only when: zero NEW P0/P1 in a full round AND all prior P0/P1 re-verified with
transcripts AND verify_release.py green AND the round header matched the pinned identity.
A model saying "looks clean" is not a gate. Never reopen resolved material for taste (freeze
list); never lower the bar to converge.