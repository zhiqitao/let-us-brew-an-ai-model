# Publishing Readiness Review — *Let Us Brew an AI Model*

**Manuscript:** `let-us-brew-an-ai-model-v20261001.pdf`  
**Edition:** v20261001  
**Extent:** 229 PDF pages; 6 × 9 in. trim  
**Review date:** 2026-10-31  
**Verdict:** **NOT READY FOR RELEASE** without scientific-record corrections, reproducibility work, and print-layout repair.

## Reading this report

- All page numbers below are **PDF page numbers** unless qualified as **printed pages**. For numbered body pages, PDF page ≈ printed page + 11.
- **P0 — Release blocker:** Without this correction, the book's traceability, central inference, or usable published artifact is materially impaired.
- **P1 — Major:** Must correct for a technical-quality publication; sometimes fixable by rewriting rather than new experiments.
- **P2 — Minor/editorial:** Important polish, clarity, or pedagogy.
- **Confirmed text/layout defect** means observable in the supplied PDF. **Evidence gap** means the draft itself says the necessary record, control, or verification was not preserved; it is **not** an accusation that the underlying experiment was invalid.
- This review was made on the supplied PDF; **source repository, source data, checkpoints, manifests, and rerun outputs were not provided**, so execution-level scientific reproduction is **not certified**. External sources were used only to check the published PyTorch installation guidance.

## 1. Executive judgment

The core concept is strong: an accessible, honest empirical study of the gap between task fitting, prompt-surface robustness, compositional behavior, and the reliability of the evaluator. The book's methodological disclosures are better than an ordinary technical hobby-book draft: it admits that the pilot reuses 21 prompt strings, the Chapter 13 surface success is coverage rather than excluded-family transfer, the size sweep varies budgets and tokenizers, and the apparent composition wall is often a failure to generate parseable code rather than a diagnosed semantic failure.

Those concessions are scientifically valuable. Yet making caveats in one paragraph does not excuse incompatible or stronger claims elsewhere. Two facts particularly damage confidence in a release candidate: **the 0.900 Stage-4 baseline printed repeatedly in the body is explicitly not backed by the surviving manifest (which says 0.9167)**, and the flagship Stage-3/Stage-4 holdout-membership audit is described as having run on **regenerated** samples rather than the **historically scored** files. The book is admirable for disclosing these gaps, but must either close them or narrow its claims before publication.

The editorial/production problems are not cosmetic: code/CLI listings have line-wrap artifacts, several diagrams use illegibly small embedded text, Appendix C tables are stretched into narrow vertical columns, and two stranded continuation pages are glaring in the print layout.

**Recommended disposition: Major revision, followed by an independent reproduction and final print proof.**

## 2. Release blockers and highest-priority findings

### P0-01 — Publish and verify the companion artifacts, not just the tag
**Locations:** PDF p.4; pp.222–223 (Appendix C.10); Preface pp.6–7.

The copyright/front matter and Appendix C explicitly say the companion repository has no public URL and the errata destination is pending. They also say an external reader cannot fully reproduce the experiments yet. A 40-character Git commit hash and release tag are good provenance labels, but without a reachable repository and binary artifacts a reader cannot validate them. The manuscript moreover states no complete `requirements.txt` or equivalent pinned environment was shipped.

**Required:** publish a **read-only release** with a permanent URL; verify the tag resolves to the recorded commit; include code, original scored train/validation/test files, tokenizers, actual run manifests, results tables, raw generations, inference settings, and checkpoint hashes or a candid explanation for any missing artifacts. Provide an immutable archived snapshot/DOI if practical; add working errata and issue-reporting links; include CPU installation with the proper wheel index and a lockfile. Test checkout + the documented commands from a clean system. If the release cannot be published, explicitly change the book's advertised reproducibility claim, not just its caveat.

### P0-02 — Historical held-out membership not verified for the scored experiments
**Locations:** PDF pp.110–111, 125–126, 217–219 (especially Appendix C.7).

Appendix C confirms the pilot split was checked against its **original** files and all 21 test prompts are also in training. But the Stage-3 surface and Stage-4 composition novelty checks were run on **regenerated smaller samples**, not on the historical files that generated the reported scores. Further, zero *exact-string* overlap does **not** prove exclusion of an entire wording family; the manuscript itself concedes this. As a result, the exact provenance of the critical excluded-family 0.000 and composite 0.000 results is less certain than readers may expect from headings such as “held-out family.”

**Required:** hash and audit **each original scored file**, and publish a report by operation, split, prompt string, wording-family ID, identifier set, target program hash, and tokenizer; assert set disjointness under the intended dimension and produce collision counts. Include script and machine-readable report. If originals no longer exist, rerun under an explicitly defined, independently auditable new split, label the values as new runs, and preserve the old numbers only as historical/unverified results. Do not transfer zero-overlap evidence from regenerations to historically scored files.

### P0-03 — Reconcile the 0.900 versus 0.9167 baseline contradiction
**Locations:** PDF pp.97–99 (Fig.12.1); pp.135–137, 161–164, 170–173; especially p.215, Appendix C.5.

The body repeatedly calls the 0.88M Stage-4 baseline **0.900** in-distribution; Figure 12.1 plots **0.900**. Appendix C.5 explicitly states that **0.900 is not backed by a surviving manifest**, whereas the Stage-4 baseline manifest gives **0.9167 (55/60)** on its 60-record re-evaluation of `stage1.pt`. This is a confirmed internal contradiction, not merely rounding (0.900 and 0.9167 are different counts on n=60).

**Required:** make the manifest-backed number the canonical published number (or recover and precisely identify a separate 0.900 measurement). Amend every table, figure, prose claim, and legend that refers to the Stage-4 baseline. Keep the **0.897 pilot score (300 records)** separate; those are two evaluations with different denominators and sampling histories. Expose a generated single-source-of-truth metrics table to prevent recurrence.

### P0-04 — Diagnostic stage accounting is labeled incorrectly
**Locations:** PDF pp.51–52 (judge definition), pp.204–206 (Failure Ledger B.10).

The text says the implementation's `syntax_rate` is the result of **combined parse + AST allowlist validation**, not pure parsing. It also says `executable_rate` means **passed at least one hidden test**, not merely executed. Nonetheless Appendix B.10 writes:

```
parse failures              = N - parsed
post-parse / pre-execution  = parsed - executable
executed but test-failing   = executable - all_tests_pass
```

The labels don't follow from the recorded signals. `N - syntax_ok` includes **syntax and capability rejects**. `syntax_ok - executable_rate` can include a program that ran cleanly but answered **all** cases incorrectly, not only a pre-execution failure. `executable_rate - pass@1` is the count of programs that **passed at least one but not all hidden tests**; that is not the full population of executed-but-wrong programs. The claim on PDF p.206 that the pilot's non-successes were “all at the parsing stage” is likewise unsupported: only **combined validation failure** is established.

**Required:** rename the three saved metrics `validation_pass`, `at_least_one_test_pass`, `all_tests_pass`; revise the algebra and stage descriptions; do not infer a pure parse-failure count absent a pure parse flag. For a real four-stage diagnosis, instrument distinct parse, capability, runtime, semantic verdicts per candidate and re-evaluate the saved raw candidate programs, if available. If outputs were not archived, say so and limit the retroactive diagnostic conclusions.

### P0-05 — Core composition interpretation remains confounded with generation and extraction failures
**Locations:** PDF pp.81–82, 99–103, 132–141, 162–164, 205–206.

The book uses the held-out composite score of **0.000** as its central negative result. But the logged composition-exposure run has **syntax/combined-validation rate 0.000** on the held-out composites: no candidate reached actual semantic evaluation. The reason for malformed or truncated programs was **not identified**. The pilot itself famously had a **NUL-termination extraction defect**, and the generator uses stochastic temperature-0.8 sampling without EOS/PAD early stopping. Thus “0.000 under this generation/evaluation protocol” is a measured fact; “a diagnosed inability to compose known operations” is **not** an isolated mechanism.

**Required for strong scientific framing:** recover raw token streams and stop reasons (EOS/PAD vs max_new, length truncation, NUL split); evaluate validity by operation; show token/length parity with matched familiar controls; test deterministic greedy decode and at least one alternate decoding budget; supply new composite prompts with familiar vocabulary and matched length, and an all-composites-seen positive control. Preserve an expressly **measured negative result** without claiming the internal reason if controls cannot be run. Relabel Figure 12.2 and summary prose accordingly.

### P0-06 — Numerical falsehood in the parameter discussion
**Locations:** PDF pp.67 and 73 (printed pp.56 and 62).

The accurate breakdown is **53,632 embeddings + 830,592 other parameters = 884,224**. Hence embeddings are **6.07%**, not a majority. Chapter 8 correctly says ~6%, but Chapter 9 says the parameter split matters because “most of its parameters live there” (in the embeddings). That is false for the model being described. Rewrite that sentence to say the embedding share is modest here, though worth reporting; remove or re-scope generic claims about embedding-dominated small models that imply they apply to this configuration.

### P1-07 — Claim of a clean “model-size” intervention conflicts with actual design
**Locations:** PDF pp.97–104, 214–215.

The four-size sweep uses **different training-step budgets** (1,500/1,000/800/800) and **different tokenizer training corpora/ID mappings**. Appendix C owns this caveat; still, the body uses causally strong phrases (“Thirty-three times the capacity bought exactly zero,” “more capacity made ...”). The only unconfounded assertion is that **all four tested configurations and schedules scored zero** on their reported composite evaluations. Also, the 0.88M baseline has **n=60** while larger-model in-distribution evaluations have **n=300**, making equally precise display misleading.

**Required:** make the figure title and conclusion descriptive; distinguish change in parameter count from change in the full treatment bundle. A genuine scale-only follow-up should freeze tokenizer, data hashes, training steps or token budget, decode settings, prompt/test membership, and independent seeds. The current observation need not be discarded, but the causal claim must be downgraded.

### P1-08 — Chapter 13 has coverage, not proven novel-family transfer
**Locations:** PDF pp.105–112, Figures 13.1 and 13.2.

The 1.000 “surface” score for high diversity can come from wording families and identifier sets already seen in training. The chapter honestly says so; elsewhere terms such as “mastered,” “generality,” “only diversity differed,” and “diversifying ... cannot tie to a surface” risk implying stronger unseen-surface abstraction. The visually dominant 1.000 bar is particularly susceptible to that misreading.

**Required:** label the condition **alternate-surface coverage** in the figure itself, not only surrounding prose. Evaluate a **strictly excluded family**, a held-out identifier set, and crossed held-out family × identifier tests, ideally with multiple seeds and equal operation/token exposure. Report separate operation-level scores.

### P1-09 — The 0/16 human-written set is not a clean quantitative benchmark
**Locations:** PDF pp.129–131.

The book admits the set is small, convenience-written, and mixes **11 seen-operation requests** (including one operationally “primitive” but structurally composite) with **five held-out composites**. It also admits request 11 is ambiguous (different plausible functions). Many requests do not specify the model's output contract (a `solve` function and its parameter names), so the test changes more than wording unless an identical fixed wrapper/schema was supplied. The score is useful as an exploratory stress-test, not an independently precise estimate of real-user success.

**Required:** provide the exact input prefix/wrapper given the model, a complete expected interface for each request, a clarified request 11, operation-level outcomes, raw completions, and a larger blinded prompt set. Separate seen-operation paraphrases from genuinely held-out composites in graphics and claims.

### P1-10 — “Deterministic” requires conditioning on model output and RNG
**Locations:** PDF p.25 (§3.6) versus pp.82–83, 215–216.

The task-justification bullet says “same spec, same program, same tests.” The **Python execution and oracle** are deterministic conditional on program and fixed tests, but the **model's generation** uses stochastic temperature-0.8 sampling and continuing RNG state. Readers could mistake protocol determinism for end-to-end model determinism. Distinguish deterministic *grading* from stochastic *candidate sampling*; record inference RNG state or separate seed and decoupled sample repetitions.

### P1-11 — Single-seed and clustered-test inferences need a consistently descriptive register
**Locations:** PDF pp.79, 82, 91–95, 98–103, 126, 153–156, 215–221.

The book responsibly avoids ungrounded binomial confidence intervals, but many plots still visually invite overconfident trends. Pilot test has **300 records from only 21 model-visible prompt strings**. Data scaling is **one run per size** on a common 540-record generated pool; small sample selection and operation coverage are not isolated. Larger comparisons have single seed and different experimental budgets. The 0/16 human suite is not representative. “Reliably,” “decisive,” and “proves” should be restricted to exactly the observed run/records.

**Required:** display *raw successes/denominators* in every main result table, add operation/prompt-family grouped breakdowns, repeat train and inference seeds where feasible, and mark descriptive results prominently as such. The book's current confidence-interval caution is good and should be retained.

### P1-12 — Code-safety policy is not runtime containment
**Locations:** PDF pp.29–35, 50–54.

AST allowlisting and restricted `__builtins__` constrain syntax but **do not implement execution timeouts, recursion limits, or memory controls**; the book specifically admits these are only proposed/unused. The warning to execute in a disposable unprivileged environment is welcome, but a reader might still run the bundled evaluator directly on host hardware. The program parser/generator is not an adversarial security boundary.

**Required:** if shipping runnable code, put generated Python behind a genuinely resource-limited isolated worker/subprocess and document OS requirements and operational limits. At minimum, make the README and Quick Start display a clear safety warning **before the first evaluation command**. Avoid saying the apparatus makes arbitrary generated code “safe.”

### P1-13 — Gate B claims need a measured input-gate validation
**Locations:** PDF pp.35–40.

Gate B is an external shape recognizer built after the main surface/human evaluations. That distinction is correctly explained. But its ability to enforce the declared request grammar is not backed in the text by a measured conformance report showing accepted variants, false acceptances, false rejections, and its exact threat/scoping assumptions. A “two gates close the loop” schematic can imply more than a syntax-scope check.

**Required:** add a small, reproducible Gate B validation suite and report what request shapes it accepts/rejects. Keep semantics, authorization, and hostile-code security explicitly outside its guarantee.

### P1-14 — The four-stage judge figure shows an idealized rather than recorded pipeline
**Locations:** PDF pp.51–52; Figure 6.1.

The figure stacks four stage boxes, while the text says parse + allowlist are **one recorded validation gate** and “execution” is derived from passing at least one test. That discrepancy is acknowledged verbally but pedagogy would be much clearer if the figure showed **two layers**: desired diagnostic stages and actual saved instrumentation.

**Required:** redraw Figure 6.1 with combined validation, actual execution/test loop, the `>=1` and `all` counters, and a clear note that per-candidate failure taxonomy was not collected.

### P1-15 — Mutation score is narrow, though numerically correct
**Locations:** PDF pp.144–148.

35 mutants yielded 29 killed + 6 strict/non-strict tie-equivalent survivors; **29/35=0.829 raw** and **29/(35−6)=1.000 equivalence-adjusted**. These calculations are internally correct *under the stated equivalence case analysis*, not a measured guarantee of full judge correctness. Only a few mutation recipes were actually used, and not all alternative correct programs or important off-by-one/variable errors were tested.

**Required:** retain both denominators; define the exact operator/operation coverage matrix; add distinct wrong-variable, hardcoded, boundary, off-by-one and runtime-failure mutations, plus independent correct alternative programs. Avoid presenting the 1.000 adjusted score without the narrow denominator nearby.

### P1-16 — `canary` is not a conventional planted memorization canary
**Locations:** PDF pp.118–121.

The text itself acknowledges this: the “canary” is a **held-out pair**, not a distinctive example injected into training and later tested for regurgitation. It supports the narrow claim that the generated program is not a memorized **literal answer value** for that one test; it does not rule out memorization of general prompt→program templates. Rename it “held-out program probe” consistently or conduct a genuine planted-canary experiment.

### P1-17 — The learning objective makes the very low training loss less diagnostic
**Locations:** PDF pp.68, 73–75.

The transformer trains on `prompt + newline + program` with **no completion-only loss mask**. It is rewarded for predicting repeated prompt tokens as well as program tokens. This is openly documented, so not a secret methodological defect; however, the dramatic **~0.02 training loss** is an aggregate over both and should not be presented as clean evidence of code-completion fit alone. Add code-token-only training/validation losses and a program-token conditional score, or qualify more strongly.

### P1-18 — Operation taxonomy includes a structurally composite “primitive”
**Locations:** PDF pp.133–137, 208–210.

`cond_abs_max` (max of absolute values) is in the ten-operation “primitive” pool despite composing `abs` and `max`. The book conscientiously admits this; nonetheless “primitive-only” training and “never saw combinations” should not appear unqualified in headings or result glosses. `max_add` also has algebraically equivalent simpler forms; matched tests should establish all claimed operation semantics, not just names.

**Required:** prefer “ten seen operation IDs” versus “six held-out operation IDs,” and separately provide *structural* complexity/primitive taxonomy in the operation dictionary. State the input-domain/precondition requirements for indexing and list semantics.

### P1-19 — Installation and runnable listings require a copy/paste audit
**Locations:** PDF p.23 (JSON schema), pp.80–82, 100–101 (generated code), pp.209–210 (behavioral sketches), pp.222–223 (quick start).

The print line-breaking engine inserts **continuation arrow markers** into code/JSON or breaks command flags over lines. On p.23 the JSON schema visibly has an arrow inserted before `"type"`; on p.223 the CLI flag `--n-embd` is split as a single `-` on one line and `-n-embd` on the next. These are acceptable only if explicitly denoted **non-copyable display**, but are not acceptable for supposedly “verbatim” reproduction commands. Appendix C also shows Python-like behavioral sketches (including comprehensions) that are **not allowed** by the sandbox, which it acknowledges but readers could still copy accidentally.

**Required:** use breakable code-listing environments without in-band glyphs, or short multi-line CLI commands with explicit shell `\\` continuations. Print valid JSON; test every runnable code/command snippet automatically. Distinguish illustrative invalid model samples, behavioral pseudocode, and actual accepted reference source with consistent labels.

### P1-20 — CPU dependency installation needs platform-specific accuracy
**Locations:** PDF pp.222–223.

The stated `torch==2.14.0` is a **real September 2026 release**, so **do not** replace it on the false premise that it does not exist. But the example `pip install torch==2.14.0 scikit-learn matplotlib (CPU wheels)` is prose, not a reproducible command; it lacks exact versions for non-torch dependencies, and on Linux does not show the documented CPU-only index. The official previous-version instructions specify `--index-url https://download.pytorch.org/whl/cpu` for CPU wheels. Provide separate tested OS-specific recipes and/or a lockfile, plus an exact command transcript rather than an example that reads like one. No requirement to upgrade to the latest PyTorch for reproducing a historical run.

## 3. Print production and editorial issues

### P1-PROD-01 — Stranded continuation pages
- **PDF p.20, printed p.9:** almost entirely blank except the final `works.”` completing a sentence from Chapter 2. Reflow chapter or adjust page break/typography so a single word is not stranded.
- **PDF p.115, printed p.104:** a near-empty page carrying the final sentence fragment of the Chapter 14 opening; the next page begins with a long table. Reposition the table or opening content to prevent a nearly blank middle page.
- **PDF p.229, printed p.218:** final glossary page contains only the tail of the glossary (one bullet) and large whitespace. Consolidate with previous page if possible. This is lower impact than the first two but conspicuous in the finished book.
- Section divider pages and the intentionally blank preliminary pages are **not** automatically defects; do not remove them merely to reduce page count.

### P1-PROD-02 — Appendix C registry tables are too tall and too narrow
**Locations:** PDF pp.211–214 (printed pp.200–203).

The five-column registry forces the Key Result into a very narrow width, breaking common words into multiple one- or two-syllable lines (e.g., the Stage-1 and continual-learning rows). It is technically within page margins but no longer easy to scan. **Redesign the registry into per-run panels** or a two-table scheme: compact summary (`run ID`, `question`, `n`, `headline result`, `status`) plus provenance (`configuration`, `data hash`, `tokenizer hash`, `manifest`, `checkpoint`). A machine-readable CSV/JSON registry is ideal; the print page should remain a readable index, not a raw manifest dump.

### P1-PROD-03 — Figures use rasterized small type, pale annotation, and many colors

All **18 figure occurrences** (17 figure-bearing pages; 12.1 and 12.2 share PDF p.99) are embedded raster images, commonly drawn approximately 4.5 inches wide at effective ~189–300 dpi. Resolution is broadly adequate for photographs but **small labels remain physically small in print**, regardless of pixel density. The apparatus figures often use faint light-gray notes and pale text on colored fills; some plots have dense captions and microscopic x-axis labels. Avoid red/green as the only success/failure encoding even when the heatmap also has ✓/×. Recreate with vector SVG/PDF where possible, increase label size and contrast, use direct labels, and proof on grayscale paper at actual 6 × 9 inches (not a zoomed screen).

### P1-PROD-04 — PDF accessibility and print preflight

The PDF's fonts are embedded (positive), and basic text bounding boxes do not extend beyond the physical pages (positive). But the PDF is **not tagged**, and the figures are raster objects with no machine-readable alt text. For accessible ebook/PDF release, produce structure tags, reading order, figures' alternative descriptions, real headings, and labeled tables. Preflight for grayscale legibility, black generation, contrast, trim/bleed where needed, and print-on-demand proof quality.

### P2-PROD-05 — Consistency and copy edit

- Remove or explicitly justify the whimsical inconsistent capital R in chapter/TOC labels (`BRew`, `WoRld`, `TeacheR`, `GenERatoR` etc.). The actual printed style looks unintentional and can harm search/navigation.
- Normalize `pass@1`, `pass@k`, “syntax,” “validation,” “executable,” “new IDs,” “held-out,” and “composite” against one glossary. In particular, avoid “new IDs” alone when **only test IDs** change, as this can be confused with identifier/variable names.
- Break dense, apology-like caveat chains into a compact **Claim / Evidence / Does not establish** box or table per result. Keep the honesty; remove duplication across body, conclusions, failure ledger, and registry.
- Keep printed code and commands monospaced, syntactically faithful, with consistent indentation. Validate all links in Reading Further; the sources are currently listed in Chapter 21 rather than a conventional References section, which is acceptable if deliberately styled.
- Provide a one-page **Experimental Ledger at a Glance** early in Part III: checkpoint ID, model-visible novelty, n, training seed, inference seed, score, controls, unresolved caveats. That one page can cure repeated ambiguity more efficiently than pages of disclaimers.

## 4. Figure-by-figure audit — all 18 figures

| Figure | PDF page | What it is intended to teach | Assessment | Required action | Priority |
|---|---:|---|---|---|---|
| **2.1** Four evaluation questions | 18 | Memorization, distribution, surface, composition as separate probes | Concept valid; four vertically stacked colored bars visually imply a progression/ladder despite text saying they are **not a ladder**; white text can be small in print. | Show as a 2×2 set of independent questions, larger type, contrast-safe palette. | P2 |
| **3.1** One job | 22 | Training vs hidden-test execution path | Useful and broadly correct; tiny annotations under model, lane, and comparator hard to read; too much information for width. | Separate training and evaluation lanes cleanly; enlarge type and make test inputs vs model-visible prompt unmistakable. | P1 |
| **4.1** Whole apparatus | 33 | World + teacher + student + judge | Broadly logical but text in lower boxes is microscopic; visual complexity dilutes lesson. | Simplify nodes, move caveats to caption, enlarge internal labels. | P1 |
| **4.2** Two gates | 35 | Input validator vs AST output filter | Good contrast between input/output, but red captions and fine print weak in grayscale; “scoping guarantee” not security guarantee should be visible. | Add explicit “shape only / no semantic or security guarantee” label and improve readability. | P1 |
| **5.1** Teacher | 42 | One semantic record generates prompt, code, tests | Correct high-level principle; qualifications at bottom tiny, so correlation caveat is easily lost. | Larger primary labels; move nuanced error disclaimer to caption. | P2 |
| **6.1** Judge | 51 | Four-stage evaluation | **Conceptual vs implemented pipeline mismatch**: saved metrics collapse stages. | Redraw to actual combined validation and two nested test-success counters; separate ideal diagnostic taxonomy. | P1 |
| **7.1** Rivals | 58 | Template, retrieval, learned model | Pedagogically useful, but pale baseline boxes and small explanation; could imply a baseline is a score ceiling. | Directly annotate each baseline's mechanism and “sanity checks, not ceilings.” | P2 |
| **8.1** Smallest brain | 65 | Decoder-only model configuration | Dense technical text unreadable in its small figure space; specifications already exist in the table. | Replace with simple token→embedding→4 blocks→logits diagram; keep numbers in table. | P1 |
| **9.1** Brew loop | 73 | Generate, train, evaluate, iterate | Structure works; secondary notes tiny; model/evaluator stages could be clearer. | Enlarge cycle boxes, remove undersized notes, show where manifests/checkpoints saved. | P2 |
| **11.1** Data scaling | 91 | Four measured training-size conditions | Readable, but single-seed, possibly unequal operation coverage is hidden in prose/caption. | Add `one seed`, `540 test records`, `coverage unverified` on plot and raw counts. | P1 |
| **12.1** Model size vs composition | 99 | Four configuration outcomes | Visually clear; smallest baseline **0.900** conflicts with manifest-backed **0.9167**; differing step/tokenizer budgets not clearly visible within plot. | Correct baseline and rename x-axis/legend “tested configurations” or mark non-isolated size sweep. | P0 |
| **12.2** Illustrative prompts | 99 | Single-example behavioral grid | Helpful but heatmap looks statistical while it is one prompt per condition; red/green color blocks dominate. | Add “NOT A SCORE / ONE PROMPT PER CELL” within graphic; use hatching/patterns and full checkpoint names. | P1 |
| **13.1** Diversity vs quantity | 106 | Equal counts, radically different score | Strong picture, but high-diversity `surface=1.000` can easily be misread as excluded-family generalization. | Title/legend must state **covered alternate surfaces**, not genuinely unseen wording families. | P1 |
| **13.2** Coverage vs holdout | 111 | Make data-coverage distinction explicit | Important corrective concept; small detailed labels. | Simplify to two large training/test set diagrams; enlarge warning text. | P2 |
| **15.1** Surface generalization | 126 | In-distribution/new identifiers/new wording across model and baselines | Well suited to comparative bars; mixes “IDs” with possible task IDs; historical excluded-family membership not validated on original scored file. | Use **variable identifier names**, raw n/counts, and qualify historical membership on plot/caption; resolve underlying audit. | P0/P1 |
| **16.1** Same operators, different programs | 133 | `abs(a+b)` vs `abs(a)+abs(b)` | **Mathematically correct** for example `a=-3,b=2` giving 1 vs 5; good central pedagogic diagram, though footnotes tiny. | Retain, enlarge formulas and annotate inputs/output on both branches; strengthen colorless printing. | P2 |
| **18.1** Sequential vs joint accuracy | 153 | A acquired, forgotten after B; joint control | Core comparison correctly separates sequential pre-B from final; many bars and hatching slightly crowded. | Use directly labeled A-pre/A-post/B-post dots or bars; show n and number of runs. | P1 |
| **18.2** Sequential, joint, replay | 155 | Distinguish measured joint control from true replay-after-A, **not run** | Correct and particularly valuable caveat; thin timeline text and bottom micro-note. | Enlarge timeline, clearly mark row 3 “NOT RUN” without relying on dotted border/color alone. | P1 |

**Per-figure outcome:** No obvious arithmetic reversal was identified in Figure 16.1; Figures 12.1, 6.1, 13.1, 15.1 carry substantive interpretation/provenance risks. The remaining figures primarily need legibility and direct labeling. This is a visual inspection of the rendered PDF, **not a pixel-diff against original SVG source**, which was not supplied.

## 5. Chapter-level editorial disposition

| Chapter(s) | Disposition | Main issue/fix |
|---|---|---|
| **1–3** | Good narrative; revise | Define “deterministic scoring” precisely; fix malformed JSON; avoid implying pilot test prompts are unseen. |
| **4** | Major technical caveat | Show runtime isolation limits, unimplemented timeouts, Gate B scoping suite. |
| **5–6** | Rework diagnostics | Distinguish independent implementation paths from a common semantic oracle; align judge text/diagram/metrics. |
| **7** | Strong | Keep two baseline comparisons, but avoid treating them as exhaustive possible shortcuts. |
| **8–9** | Fix factual contradiction | Correct embeddings majority statement, distinguish full-sequence loss from completion loss, preserve log provenance. |
| **10** | Strong caution needed | Pilot is **21 seen prompt strings**, 300 fresh execution-input records; fix terminology around generated sample and seed reproducibility. |
| **11** | Descriptive only | Four single-seed data-size points with unknown small-set coverage and repeated prompt→program pairs; avoid plateau/threshold inference. |
| **12** | Major re-analysis/rewording | Size, tokenizers, steps, sample sizes not cleanly matched; 0.900 conflict and generator-validity confounds. |
| **13** | Good corrective self-audit | Main finding is **coverage of trained wording families**, not unseen-family abstraction. |
| **14** | Rename probe | `canary` not a planted memorization canary; distinguish value memorization from program-template memorization. |
| **15** | Essential but not closed | Audit historical scored held-out file; clarify human benchmark interface/ambiguities; moderate all-or-nothing language (“did not learn addition”). |
| **16** | Central scientific revision | Composite 0 must not be assigned a mechanism while failure stage is syntax and generation stop behavior is unverified. |
| **17** | Good narrow calculation | 0.829 raw and 1.000 adjusted valid for selected 35 mutants, not general judge completeness. |
| **18** | Generally sound | Joint training != genuine replay; retained A measured before/after on re-run, one-seed scope; clarify protocol. |
| **19–21** | Shorten and harmonize | Central conclusions should repeat exact scope and not overclaim mechanism; generate claim/evidence table from registry. |
| **App. A** | Clarify | Verify data/schema snippets against executable source and describe exactly how lexical audit fits TF-IDF. |
| **App. B** | Rework B.10 | Correct stage algebra and first-failure-stage language. Preserve authentic failed attempts. |
| **App. C** | **Highest priority** | Publish artifacts, rectify 0.900/0.9167, audit original scored splits, redesign tables and quickstart. |
| **App. D** | Editorial | Align “pass@1,” “held-out,” “new instance,” “validation,” “executable,” and “primitive” with consistent usage; eliminate stranded last page. |

## 6. Minimal additional experiments and audits to justify the book's core contribution

These are ordered by scientific value and feasibility. They are not all required if the book is deliberately retitled as a record of exploratory results; the first four are necessary for defensible strong publication claims.

1. **Original-artifact novelty audit (mandatory).** Verify IDs, family membership, strings, exact target programs, tokenizers, and hashes on the *scored* train/test split for Stage 3 and Stage 4. Publish exact paths, counts, and emitted report.
2. **Quantitative table reconciliation (mandatory).** Script generation of every body result from stored manifests. In particular, settle Stage-4 55/60 = 0.9167 vs unbacked 0.900; state seed, n, exact dataset per row.
3. **Generation-failure taxonomy (mandatory).** Re-evaluate raw candidates to distinguish `ast.parse` failure, allowlist violation, timeout/runtime exception, zero tests passed, some tests passed, all tests passed. Archive raw completions **before** extraction and after extraction plus stop reason/token budget.
4. **Composition matched-control battery (strongly recommended).** Compare seen primitive, trained composite, excluded composite, and length-/vocabulary-matched noncomposite candidates; run with fixed tokenizer and several decodes. This is the shortest way to distinguish a composition problem from an output-format/syntax-decoder problem.
5. **True held-out-language diversity experiment.** Control 1,200-record count, operation balance, unique prompt targets and token exposure; test a wholly excluded family and crossed identifiers, with at least several train/inference seeds.
6. **Size-isolated matched training sweep.** Same data splits, tokenizer, decoding, and equal token/step budget at every parameter point, multiple seeds; report no unwarranted confidence intervals.
7. **True replay-after-A-first continuation.** Clone the **same** trained A checkpoint for B-only and B+replay continuations, compare to joint-from-start control. This answers the continual-learning intervention the current book explicitly leaves open.
8. **Judge and gate correctness battery.** Alternative correct code structures, mutation classes beyond operator flips, malformed/hostile candidates under OS-enforced resource limits, and Gate B adversarial shape negatives/positives.

## 7. Specific wording replacements

**Instead of (Chapter 9, PDF p.73):** “... most of its parameters live [in embeddings].”  
**Use:** “Of this model's 884,224 parameters, 53,632 (6.1%) are in token and positional embedding tables and 830,592 (93.9%) are elsewhere. Reporting both figures prevents confusion about where parameters are allocated.”

**Instead of (Chapter 12):** “Thirty-three times the capacity bought exactly zero compositional generalization.”  
**Use:** “Across four configurations spanning 0.88M to 29.3M parameters, the sampled held-out-composite pass@1 was 0.000 under each run's recorded training and decoding conditions. Because the runs used different step budgets and tokenizer mappings, this observation is not a controlled estimate of the causal effect of parameter count alone.”

**Instead of (Chapter 15):** “The model did not learn addition. It learned the word ‘sum’.”  
**Use:** “The model generated reliable code for familiar addition prompts but failed under the particular held-out rephrasings tested. The evidence establishes a severe surface-robustness failure, not the absence of any internal representation of addition.”

**Instead of (Appendix B.10):** “The recorded pilot failures were all at the parsing stage.”  
**Use:** “The pilot's 31/300 non-passing candidates also failed the evaluator's **combined syntax-and-capability validation** metric. Because pure parsing was not logged separately, these aggregate rates do not isolate invalid Python syntax from allowlist rejection.”

**Instead of (main-composition conclusion):** “The model could not compose the learned primitives.”  
**Use:** “Under the tested prompts, checkpoint, stochastic decoding, extraction, and judge, no held-out composite candidate passed its full test suite. In the analyzed exposure run, none passed the validation gate; therefore we cannot distinguish a compositional semantic limitation from a failure of generation or extraction using these measurements alone.”

## 8. Final publication acceptance gates

- [ ] Every headline number matches its original scored manifest and dataset; full denominator and model/checkpoint identified; `0.900`/`0.9167` discrepancy resolved.
- [ ] The original Stage-3 and Stage-4 scored holdouts have passed a recorded family/target/tokenizer novelty audit, or claims are accurately downgraded.
- [ ] Judge's metric definitions, algebra, appendix prose, and Figure 6.1 agree with actual logged instrumentation.
- [ ] The central “composition” conclusion is stated as an observed outcome, without asserting an unmeasured internal cause. Ideally, the diagnostic matched-control battery is completed.
- [ ] Embedding parameter share corrected; all number-bearing figures generated from one registry.
- [ ] Companion repository and stable reproducible release publicly accessible; independent clean-clone run succeeds, or inability to reproduce is prominent in the published promise.
- [ ] Every runnable code/JSON/CLI listing parses or executes exactly as printed; no in-band line-break arrows or split flags.
- [ ] Appendix C tables redesigned; orphan pages p.20 and p.115 fixed; p.229 glossary tail consolidated; figures proofed at actual trim size in color and grayscale.
- [ ] Safe execution warning and real runtime resource limiting (or safe isolated execution instructions) accompany shipped commands.
- [ ] Final copyedit, PDF preflight, external technical sign-off, and an actual proof print completed.

## 9. Closing judgment

This is **not** a manuscript that needs its negative results concealed or spun into successes. Those failures, including the NUL extraction error and the lack of transfer to reworded requests, are its best material. The principal revision is to make the **scientific evidence graph auditable**: what original artifact produced each number, which variable was truly held constant, what was actually new to the model, and which failure mechanism is established versus hypothesized.

The current draft is stronger as a thoughtful, candid *laboratory notebook* than as a fully independently reproducible technical study. With the registry contradiction repaired, historically scored holdouts audited, evaluator accounting corrected, claims synchronized to the actual controls, and print figures reworked, it can become a credible publishable case study without pretending to be a general law of tiny language models.
