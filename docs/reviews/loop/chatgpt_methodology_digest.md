# ChatGPT Review Methodology — Digest (synthesized from 4 models)

Source: GPT-6.1-Sol Master Review Instructions (949 lines) + 4 brew-book review rounds
(2026-10-31, 11-01, 11-02, 11-04), analyzed independently by MiMo, DeepSeek,
Ornith-1.5-122B, Qwen3.8-27B. This digest feeds the 4-model review-loop design.

## 1. What ChatGPT does (convergent across all 4 models)

- **Six passes (Instructions §3, A–F):** (A) uninterrupted conceptual read, (B) independent
  quantitative challenge, (C) dedicated visual/print audit, (D) evidence/terminology/
  cross-reference/production, (E) adversarial re-review of one's own acceptances, (F)
  dedup + finite release decision. Each pass targets a different defect class.
- **Dual page anchors:** physical PDF page (1-based) primary + printed page + chapter/section +
  figure/table ID + verbatim quote; page offset (PDF = printed + 11) stated ONCE, not per finding.
- **T/V/Q/R coverage ledger:** per-page status (text read / rendered viewed / quant checked /
  refs examined); a T-only page may NOT be called visually checked; thumbnails don't count as
  figure inspection. Forces honest partial credit over a global "reviewed" claim.
- **Figure register, 4 independent ratings** per figure (technical integrity / print readability /
  visual design / pedagogy) each PASS-MARGINAL-FAIL-NOT VERIFIED + KEEP/POLISH/REDESIGN verdict,
  INCLUDING passing figures — coverage demonstrable by row count (all 18 enumerated every round).
- **Severity ⊕ Confidence, two axes:** severity P0 blocker / P1 must-fix / P2 polish / P3 taste,
  separate from confidence CONFIRMED / HIGH-CONFIDENCE INFERENCE / NEEDS VERIFICATION / NOT
  CHECKED / DISPROVED, plus a non-asserting **VERIFY** class (a question, not a proven defect).
  Guard: "a guess cannot become P0 merely because it sounds alarming."
- **Independent re-derivation shown inline:** inputs + equation + result visible (53,632+830,592 =
  884,224 → 6.07%; 8×60 = 480; 420/480 = 0.875). Reader can re-run the arithmetic.
- **Evidence-boundary statement** in every round: explicit "Not performed" list (no training rerun,
  no manifest-hash verification, no pass@1 reproduction, no physical print proof).
- **Canonical-scenario ledger:** one root-cause issue carries ALL dependent anchors (R1's 0.900/
  0.9167 issue spans 5 page ranges under ONE ID) — dedup, not volume.
- **Epistemic classification** (FACT/MEASURED/DERIVED/ASSUMPTION/ILLUSTRATIVE/UNVERIFIED) checked
  across prose, tables, captions AND figures — attacks label drift (a derived example silently
  acquiring a "measured" tag).
- **Verbatim suggested corrections + executable acceptance tests** per issue (assert
  len(high_train)==1200; assert surface_cell_denominators == [600,600,480,480]).
- **Verdicts bound to explicit gates A–F** (technical / evidence / visual / pedagogy / production /
  coverage), never to reviewer enthusiasm or a decreasing comment count.
- **Decision principle (R2 §1):** distinguish (1) PDF-visible error, (2) inter-passage
  contradiction, (3) a limitation the book ALREADY acknowledges, (4) a proposed new experiment —
  so acknowledged caveats are never reported as discovered defects.

## 2. The R1→R4 defect-class escalation (the key insight)

Each round caught a CLASS invisible to the passes before it:
- **R1 (10-31, PDF-only):** internal arithmetic/consistency inside the PDF + print defects
  (0.900 vs 0.9167; embeddings 6.07% not "most"; stranded pages; 189–300 dpi figures).
- **R2 (11-01, + external web):** PDF vs the OUTSIDE WORLD — live license contradiction, false
  "repo not public", empty rendered page (p.39), duplicate future-work, missing hyperlinks.
- **R3 (11-02, + release-tagged source):** manuscript vs the CODE that produced the data —
  `pool[:size]` op-coverage confound (1/1/3/8 of 10 ops), 42-vs-1200, mixed factors,
  480-not-600 denominator, non-BPE tokenizer, truncation/padding-in-loss.
- **R4 (11-04, regression of the revised ed.):** manuscript vs ITSELF after revision — stale
  0.350/0.143 fragments, Ch.11 "has not been run", Fig 15.1 caption 000/420, commit
  a45a881-vs-ae1ec01, C.8→C.9 drift, hash 4.17pt past page edge, sub-6.5pt microtype.

## 3. ChatGPT's blind spots (convergent)

- **Never executed anything:** no training/eval rerun, no manifest-hash verification, no pass@1
  reproduction — every number is a *reported* result.
- **Could not resolve git refs:** R4 found the a45a881-vs-ae1ec01 mismatch but left the actual
  tag target unresolved (never ran `git show-ref`).
- **Static deductions never executed:** R3's 42-record pool and op-coverage tables were READ from
  code, not produced by running the generator — realized-vs-requested stays inferred.
- **Its own proposed gates stayed aspirational:** R4 writes `assert(...)`/`verify_release.py`
  pseudocode but never runs it; its closing line: "free-form review without machine-checked
  invariants is not an adequate release gate."
- **Same-model Pass E is not independent validation** (instructions admit this); the 4 rounds
  re-discovered the same figure-legibility issues under NEW IDs — no stable cross-round ledger.
- **Edition/extent drift:** same v20261001 reported as 229/228/231/294 pages — artifact identity
  was only a filename, weakening cross-round comparability.
- No physical print proof, no pixel-diff vs SVG, no exhaustive code/citation/security audit.

## 4. What OUR 4-model loop should adopt (convergent + distinctive)

We CAN do what ChatGPT could not (run code, verify manifests, resolve git). Adopt:
1. **Dynamic-execution pass:** run the experiment scripts; assert realized-vs-requested shape
   (len==1200, ops 10/10, 480 records, 42 unique pairs) — convert R3's static deductions
   into executed failing assertions.
2. **`verify_release.py` re-derives every number** from manifests and fails the build on mismatch
   (WE HAVE THIS — 192 checks + render-geometry).
3. **Real provenance:** `git rev-parse vTAG^{commit}` + SHA-256 of every artifact + the PDF
   (WE HAVE THIS — release manifest).
4. **Automated PDF-span geometry gates:** label pt ≥ 8, spans inside page box, no label overlap
   (WE ADDED the render-geometry check after DeepSeek's P1 clipping catch).
5. **Stable cross-round issue ledger:** IDs survive editions; each round re-verifies prior P0/P1
   and marks VERIFIED-CLOSED only with observed evidence + the command/transcript.
6. **Assign a distinct pass to each of the 4 models + cross-adjudication:** MiMo/DeepSeek/
   Ornith/Qwen each own a pass (conceptual / quantitative / visual-vision / provenance+code),
   then a round where each model must try to FALSIFY the others' P0s (real Pass E/F, which a
   same-model loop cannot honestly claim).
7. **Stale-fragment sweep after every fix batch:** grep superseded values + status phrases
   ("not yet", "still needs", "proposed, not measured") — the R4 class, and the class a
   4-model concurrent edit will also create.
8. **Report PASSED checks, not only failures** (cheapest credibility mechanism).
9. **Pin artifact identity** (file SHA-256 + page count) at the start of every round.
10. **"reported vs verified-by-execution" label:** upgrade CONFIRMED only via our own execution +
    state the command/transcript.
11. **Distinctive adds:** DeepSeek — automate the *intervention audit* (config-diff → "one
    variable" only when the diff has exactly one entry) and *bind claims to code mechanically*
    (claim → script → function → manifest key). Ornith — *prior-review regression testing* (re-
    locate each old finding by text/figure, not page number) and cross-anchor evidence labels to
    the taxonomy across all 4 surfaces. Qwen — the *8-step calculation protocol*, *terminology-
    trap list*, and *6 mechanical publication gates*. MiMo — *execute every runnable listing in
    the book* and the edition-identity pin.