# Publication-Readiness Audit Instructions — Let Us Brew an AI Model

**Controlling standard.** This document adapts the *From Token to Fleet*
publication-readiness audit (`review/loop/loop8_master_instructions_v2.md`, and
`review/complete-manuscript-review-prompt.md`) to this book. Where this document is
silent, the fleet master instructions and its 16 intellectual-quality principles,
review passes A–F, and the 13-section report shape apply unchanged.

**Target book:** *Let Us Brew an AI Model* — a controlled empirical investigation
into what a small language model can learn when given **one job**
(natural-language specification → Python program, executed against hidden tests).

**Review standard:** TAOCP-grade rigor of method, without imitating TAOCP's style,
scope, or organization. Deliver one consolidated Markdown report per pass, honest
about coverage, usable to drive a finite correction-and-reverification cycle.

---

## 1. Book-specific facts a reviewer must use

- **Trim:** 6 in × 9 in trade paperback (KDP standard). Text block geometry is in
  `book/latex/book.sty` (`paperwidth=6in, paperheight=9in`). Not US Letter.
- **Current structure (7 parts, 21 chapters, 4 appendices):**
  - Part I The Question: 1 Let Us Brew, 2 What Does It Mean to Learn?, 3 Give the Model One Job
  - Part II Build the Laboratory: 4 Build a World, 5 Build the Teacher, 6 Build the Judge, 7 Build the Rivals
  - Part III The First Brew: 8 Smallest Brain, 9 First Brew, 10 Does It Actually Work?
  - Part IV How Capability Scales: 11 How Much Data?, 12 How Much Brain?, 13 Same Data, More Diverse Data
  - Part V Catching the Model Cheating: 14 The Model That Memorized, 15 New Words Same Problem, 16 Same Pieces New Combination, 17 Red-Team the Judge
  - Part VI Break It: 18 Teaching It Something New, 19 The Cost of Capability
  - Part VII What Did We Learn?: 20 The Capability Map, 21 The Model Wasn't the Point
  - Appendix A Annotated Tour of the Generator, B The Failure Ledger, C The Experiment Registry, D Glossary
- **Evidence taxonomy (the book's own, normalize within it):** `[MEASURED]`,
  `[DERIVED]`, `[DESIGN]`, `[HYPOTHESIS]`, `[INTERPRETATION]`, `[UNKNOWN]`.
  Experiment status: `[PLANNED]` `[RUNNING]` `[MEASURED]` `[FAILED]` `[REJECTED]`
  `[SUPERSEDED]`.
- **The four-level generalization taxonomy (central framework, must never be
  collapsed into one number):** Memorization, Distributional generalization,
  Surface generalization, Structural generalization.
- **The canonical scenario:** the NL→Python one-job task; the canonical
  instrument is the lab (THE WORLD / THE TEACHER / THE JUDGE / THE STUDENT).
  The canonical small-student baselines and the composition baseline
  (the 0.88M number) are canonical values — trace them across chapters.
- **Source files:** `book/manuscript/*.md` (authoritative); rendered book
  `book/let-us-brew-an-ai-model-v20261001.pdf`; build `book/build_book.py`
  (md_to_latex → xelatex → pdfunite cover); experiment records in
  `docs/experiments/` and `docs/decisions/`; evidence of failed runs in
  `docs/failures/failure_ledger.md`.

## 2. Nonnegotiable principles (from the controlling standard)

Independent derivation; visible assumptions; dimensional/population integrity;
causal mechanism (why a rule arises and when it stops); real-measured vs
modeled vs vendor vs illustrative; internal consistency (one canonical
definition or an explicit controlled change); engineering honesty (bounded /
estimated / demonstrated / unknown); pedagogical transfer; section value;
visuals as reasoning; print finish; evidence traceability; proportionality;
reproducibility; convergence without cosmetic churn.

## 3. The review passes (A–F)

Run **Pass A** conceptual read, **Pass B** technical/quantitative challenge,
**Pass C** dedicated visual/print audit, **Pass D** evidence/terminology/
cross-reference/production audit, **Pass E** adversarial re-review, **Pass F**
deduplication and finite release decision. Reuse stable issue IDs.

## 4. The recurring omission to test for (this book's known risk class)

The design (`design/BOOK_DESIGN.md`) §9 originally specified **eight acts and
23–24 chapters**, including an Act "Give It More Python" (capability expansion /
ability ladder stages 5–6: increased Python expressivity, length & complexity)
and extra Act-VIII chapters. The published book was **structurally compressed**
to the 7-part / 21-chapter shape above, and the ability ladder's later stages
were **folded into future work** because **no experiments measured them**.
A reviewer must therefore verify, **honestly**, that the book:

1. Never claims measured capability that no experiment produced (anti-fabrication
   is the bedrock — see `docs/failures/failure_ledger.md` and Appendix C
   "What is NOT tested").
2. **Scopes itself**: the tested Python-capability surface and the untested
   surface (expressivity beyond the tested ops, longer programs / greater
   complexity, other generalization axes) are stated explicitly, not implied
   complete.
3. Does not present the compressed structure as if it matched the original
   eight-act design, or leave a stale/contradictory architecture/design doc that
   promises content that is absent.

A finding that "a design-promised chapter is missing" must be disposed as:
(a) **confirmed content defect** only if the book claims the capability and
cannot support it; (b) **honest scoping** (book already states the boundary) →
no change; or (c) a **design/repo documentation reconciliation** (update
`design/BOOK_DESIGN.md` to the implemented structure) rather than inventing
experiments to fill it. Never manufacture experiment results to satisfy a
missing chapter.

## 5. Severity & confidence

- **P0** release blocker; **P1** must fix; **P2** important polish; **P3** taste.
- `CONFIRMED` / `HIGH-CONFIDENCE INFERENCE` / `NEEDS VERIFICATION` /
  `NOT CHECKED` / `DISPROVED`.

## 6. Required report at the end of each pass

One consolidated Markdown report. Sections, in order:
1. Audit identity & scope (PDF hash, counts, trim, coverage %, limitations)
2. Executive decision & scorecard (10 axes PASS/FAIL/NOT VERIFIED) + verdict
3. P0/P1 priority queue
4. Detailed issue register (ID / severity / confidence / location / observed /
   evidence / why / root cause / required correction / acceptance test / status)
5. Canonical-scenario & cross-chapter consistency register
6. Quantitative & evidence validation appendix (include passed derivations)
7. Complete figure-by-figure verdict register (technical integrity / print
   legibility / visual composition / pedagogical contribution; verdict
   KEEP/POLISH/MAJOR REVISION/REDESIGN/REMOVE-MERGE)
8. Tables, equations, typography, page-level production findings
9. Storyline, pedagogy, editorial value (per part/chapter)
10. Full physical-page coverage ledger (T/V/Q/R per page)
11. Prior-issue regression & closure ledger
12. Ordered correction plan & release gates
13. Final certification boundary (what was / was not verified)

**Release gates A–F** (technical integrity; evidence integrity; visual
communication; pedagogy/editorial; production/distribution; coverage & honesty)
must all pass before "ready to publish."

## 7. Model behavior

Use real tools, compute rather than intuit, look at actual pixels, reject fake
certainty, inspect adverse cases, don't conflate comment count with thoroughness,
don't rush to favorable verdict, don't add optional whimsy after gates pass, and
never claim an independent third-party check without one.
