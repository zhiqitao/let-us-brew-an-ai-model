# 20. The Capability Map

We have run a small, disciplined set of experiments and measured a coherent boundary.
Rather than a list of results, let us draw the **capability map**: one picture that
says, for each behavior we tested, whether the model acquired it, whether it generalizes,
what it costs, and where it breaks.

Everything below is scoped to **our** setup: a ~0.9M–29.3M decoder-only transformer,
trained on a few thousand generated natural-language-to-Python tasks, evaluated by a
mutation-tested execution-based judge. These are claims about this brew, not universal
laws about all small models. Where we say "here" or "in this regime", it is deliberate —
these are measurements in one configuration, not proofs that hold
everywhere. One of the map's original levers — the data-size sweep (Chapter 11) — did not
survive code audit (P0-01) and has since been re-run correctly: the balanced,
operation-stratified sweep is flat, so record count is now a *measured* null rather than
a confound. The equal-count diversity comparison (Chapter 13) still did not survive code
audit (P0-02) and has no corrected rerun, so its cell remains a confounded historical
construction rather than a causal result; the original surface rows (P0-03, P0-04) are
likewise superseded by the corrected 2×2 factorial that Chapter 15 now reports.

**The central conclusion, in its conservative form** (adopted from the third external
review, 2026-11-02, and now strengthened by the corrected reruns):

> In this restricted task family, a sub-million-parameter decoder-only transformer
> frequently produced executable, correct Python for prompt strings that appeared in
> training, even when the resulting program was tested on new input values. That
> performance alone does not establish generalization to new natural-language requests.
> Separate evaluations found severe failures under altered wording and when asked for
> previously untrained program structures. The corrected data-scaling sweep — balanced
> operation coverage, one fixed tokenizer — is flat at ~0.90 across a 30× range, so
> record count bought nothing in this regime; the corrected surface factorial collapses
> to ~0 on new identifiers, on held-out wording, and on both together, so no tested
> prompt-surface change is survived. The diversity comparison still requires a
> corrected control before it can support a causal claim about surface diversity. The
> durable methodological lesson is that a high score must be interpreted through the
> precise model-visible novelty, the evaluator, the baseline, and the controls used to
> obtain it.

## Why a map, and not a single score

There is a strong temptation, at the end of an investigation, to reach for one number
and say "that's the verdict." It would be satisfying and simple. But every experiment
in this book has argued against exactly that. The model is good at some things and
terrible at others, and those are both true at once. A single number would have to
collapse them, and collapsing them would hide the most important thing: the *shape* of
the boundary.

So we draw a map instead. A map does not pretend to be one verdict; it shows
*dimensions*. It answers, for each question we asked, what we found — and, crucially,
what we did *not* find. That honesty about the unknown is what makes the map worth more
than a headline.

## The four-question generalization map

Recall the four questions from Chapter 2. Here is what we measured for each, on the
~0.9M model. (This is a checklist of *questions*, not a ranking — answering Question 2
does not require answering Question 1, and so on.)

**Question 1 — Memory.** *Can it be explained by remembering?* **Measured:** task-ID probe
59/60; held-out pair → general program. **Status:** `[MEASURED]` — not a literal
answer-parrot on familiar prompts; new-prompt transfer untested, and program memorization
is not excluded (see below).

**Question 2 — Distribution.** *Does it work on new instances of the same task?*
**Measured:** in-distribution 0.900. **Status:** `[MEASURED]` — yes, here (new *inputs*,
familiar prompt).

**Question 3 — Surface.** *Does it survive superficial change?* **Measured** (corrected
2×2 factorial, three seeds): familiar 0.898–0.940 (of 600); new identifiers alone
0.000–0.005 (0–3 of 600); held-out wording alone 0.000 (0 of 480, every seed); both
together 0.000–0.025 (0–12 of 480). Diverse pool — 1.000 / 1.000 (42 realized records
vs 1,200). **Status:** `[MEASURED]` for the narrow model — it collapses on *any*
prompt-surface change, single-factor or combined; `[CONFOUNDED]` for the diverse pool —
it covers more surfaces, but its arms were not equal-count and no truly-held-out family
was tested by that arm (P0-02).

**Question 4 — Structure.** *Can it compose known pieces in unseen ways?* **Measured:**
0.000 (baselines also 0.000). **Status:** `[MEASURED]` — no, in this regime.

### The evidence, keyed by checkpoint

The table above groups results by *question*. But each number belongs to a specific
**checkpoint** (a saved model) and a specific **evaluation split**, and it is important
not to let one row mix scores from different models. Here is the same evidence laid out
run by run, so every cell traces to the checkpoint the registry names. Notation used
throughout: `—` = **not run for that checkpoint**; `NT` = **not tested** for this run
(the question would be applicable but was not evaluated); `NA` = **not applicable** (the
question cannot apply, by design); `0.000` = a measured zero. A single `—`/`NT`
distinction: we only use `NT` when the evaluation *could* have been run but was not, and
`NA` only when it makes no sense for that run.

**Panel 1 — code-generation evaluations, by checkpoint**

- **`stage1.pt` (Stage 1 pilot)** — familiar prompt 0.897; held-out composite 0.000.
- **`stage3_surface.pt` (Stage 3) — superseded flawed historical run (P0-03, P0-04)** — familiar prompt 0.900; new identifiers 0.350 (mixed factors); excluded wording 0.000 (480 records).
- **`surface_corrected_seed{0,1,2}.pt` (corrected 2×2 factorial; fixes P0-03, P0-04)** — familiar 0.898 / 0.900 / 0.940 (of 600); identifiers-only 0.000 / 0.003 / 0.005 (of 600); wording-only 0.000 (of 480, all seeds); combined 0.000 / 0.025 / 0.000 (of 480).
- **`data_scaling_corrected_seed{0,1,2}_size*.pt` (corrected size sweep; fixes P0-01)** — in-distribution 0.893–0.997, **flat** across 100→3000 (10→300 per op, 10/10 operations) on one shared 300-task test; composition not evaluated.
- **high-diversity pool (42 realized records vs 1,200 — P0-02)** — familiar prompt 1.000; covered alternate surface 1.000; excluded wording NT.
- **`stage4_6p5m.pt`** — familiar prompt 0.897; held-out composite 0.000.
- **`stage4_10m.pt`** — familiar prompt 0.773; held-out composite 0.000.
- **`stage4_composition.pt`** — familiar prompt 0.897; held-out composite 0.000.

Key: the superseded surface-row scores (new identifiers 0.350, excluded wording 0.000)
come from the **Stage-3 checkpoint**, not the Stage-1 pilot, and both carry construction
defects: the new-identifier arm changes identifiers and wording-family coverage together
(P0-03), and the excluded-wording arm has 480 records over 8 operations, not 600 over 10
(P0-04). The corrected factorial rows come from their own checkpoints (one fixed
600-record train set, one fixed train-only tokenizer) and carry their denominators in the
manifest: 600 / 600 / 480 / 480, with `abs_of` and `cond_abs_max` excluded from the
held-out cells. The composition score for `stage1.pt` is a
separate re-evaluation of the pilot on the composition split (which is why the registry
lists a "Stage-4 composition baseline" row that points at `stage1.pt`). The high-diversity
row's 1.000 is **coverage** of surfaces in its training family — a pool of just 42
realized records, not an equal-count arm (P0-02) — not transfer to an
excluded wording family.

**Panel 2 — composition-intervention and continual-learning runs**

These conditions are not "one bigger model"; they test whether *training content* or
*schedule* changes the boundary, so they belong in their own panel.

- **composition-exposure (`stage4_exposure`)** — in-dist 1.000; exposed composites 0.667; held-out composite 0.000.
- **composition-diversity (minimal)** — in-dist 1.000; exposed composites 0.592; held-out composite 0.000.
- **composition-diversity (high)** — in-dist 1.000; exposed composites 0.550; held-out composite 0.000.

**Panel 3 — sequential vs. joint training**

- **Sequential (A then B)** — final A 0.000, final B 0.889, true replay-after-A NT.
- **Joint (A+B from start)** — final A 1.000, final B 0.889, true replay-after-A —.

Note the "sequential" A figure: the **final** A accuracy (0.000) is measured after phase B.
We also measured A **right after phase A** (before B) on the same run — it was **1.000**
(Appendix C.8), so the sequential drop is a same-run before/after forgetting result, not a
case of A never being acquired. A true replay-after-A-first continuation (which *would*
start from an A-trained checkpoint and continue with B plus A replay) was **not** run.

Read the map column by column and it shows a clear boundary rather than an ordered
ladder: the four questions are **separate evaluations**, not steps of a single ascending
scale. So do not read "Level 1 → Level 4" as a measured decline in "understanding." The
honest reading is that these are four distinct, non-nested probes, and the model passes
the first two (familiar-prompt generation, new-instance distribution) and fails the last
two (surface change, composition) under this setup.

## What the model can do

**It can learn individual operations well.** On in-distribution primitives — `add`,
`sub`, `mul`, `max`, `abs`, `list_sum` — the ~0.9M model solves ~90% of held-out
problems under the evaluation's default temperature-0.8 sampled decoding. It beats a hand-written template rule system (0.900
vs 0.800). This is real, measurable capability on a narrow task — for prompt strings
that appeared in training (the pilot's test reuses them), on fresh execution values.

**It produces general programs for fresh inputs of a prompt it saw in training.** On the
task-ID probe it passed 59/60, and on a held-out pair it produced the *general* program
rather than a memorized literal. So for a single operation, the model is not a literal
answer-parrot on familiar prompts. That is distributional generalization across *instances*
of a seen prompt — it is **not** transfer to a genuinely new request, which the pilot did
not test (its test reuses training prompt strings).

## What the model cannot do

**It cannot survive changes to the surface form.** In the corrected 2×2 factorial, change
only the variable names from `a,b` to `left,right` (identical wording, identical
computation) and performance falls to **0.000–0.005** — 0 to 3 of 600 — while RETRIEVAL
stays at 600/600 on the same records. Rephrase the instruction with a wording family the
model never saw (identical computation) and performance is **0.000 in every seed** — 0 of
480, below *both* baselines — over records covering 8 of the 10 operations (`abs_of` and
`cond_abs_max` have no held-out family). Change both at once and it is 0.000–0.025. This
is Question-3 failure in its crispest form: the model's capability is **anchored to the
phrasing it saw** and does not survive *any* prompt-surface change we applied, single or
combined. (The earlier 0.350 identifier reading was a mixed-factor shift, P0-03, and is
superseded; and this is about *robustness to the shifts we tested* — it does not by
itself prove there is no internal semantic representation.)

**It cannot compose what it knows.** Train on `add`, `sub`, `abs`, `max`, `list_sum`
as separate primitives; test on `abs_add` (sum of two absolute values) and `sum_of_abs` — operations that combine two things it knows. The model scores **0.000**. It
did not learn "I know abs and I know add, therefore I can do abs+abs." This is a
Question-4 failure under these schedules. The baseline systems (which we designed to be
easy) *also* scored 0.000 — a useful cross-check that the failure is not unique to the
learned model, though it is a measured negative, not a proof that no method or shortcut
could ever solve it.

## The two axes of the boundary

Put together, the results define a sharp boundary along two independent axes:

**Axis 1 — Surface form.** The model's knowledge is tied to the exact wording and
identifier names it saw. It does not generalize "sum of two numbers" as an abstract
concept; it generalizes "this sentence shape → this code." Change the surface, and the
capability evaporates.

**Axis 2 — Composition.** Even within a surface form it knows, the model did not
combine two learned pieces into a novel structure in our tests. It behaved as if it
lacked a compositional engine here.

## The scaling map (what changes it)

| Lever | Tested | Effect on composition |
|-------|--------|-----------------------|
| Model size | 0.88M → 29.3M (~33×) | **none** — still 0.000 at all four sizes |
| Data size | 100 → 3000 examples (**corrected**: balanced 10/10 operations at every size, one fixed tokenizer — fixes P0-01) | **none** — in-distribution is flat (0.893–0.997) across the 30× range; composition **not tested** in this run (we did not evaluate the scaled models on the composite split) |
| Training protocol | sequential vs joint | **big** — fixes continual retention (0.000→1.000); a *different* lever, not a composition lever |

The second half of the map is about levers, and it is where the surprising findings
live. We tried three ways to move the boundary — more capacity, more data, and a
different training procedure. More capacity did nothing to composition (0.000 at all
four sizes); more data was first the **confounded** sweep of Chapter 11 (P0-01) and then
the corrected balanced sweep, which measured the data lever properly and found it
**flat** — 0.893–0.997 from 100 to 3,000 records — so record count moves neither the
in-distribution score nor anything else we can see (composition was still not evaluated
in the scaling run, so "more data does not fix composition" remains untested); and a
different training procedure was the decisive lever for a *different* problem (continual
learning), not for composition. This asymmetry is worth circling, because it tells us
where effort does and does not pay — and the data lever, now properly measured, is one
where it does not.

## The capacity grid, in full

The sharpest negative result in the whole book is the model-size sweep, and it deserves
its own table because it is the claim a reader would most want to test. We ran the
composition experiment across a ~33× range of capacity. We did **not** hold every
hyperparameter constant — the runs used different step counts (see Appendix C; the
model-size-budget row of the evidence table, Chapter 11), so this
is a sweep across capacity with some training-budget variation alongside it, not a
strictly-controlled size-only comparison.

| Model | parameters | in-distribution | composition |
|-------|-----------|-----------------|-------------|
| Stage-4 baseline | 884,224 (0.88M) | 0.9167 (n=60; see Appendix C.5) | **0.000** |
| Scaling | 6,500,352 (6.5M) | 0.897 | **0.000** |
| 10M point | 10,195,776 (10.2M) | 0.773 | **0.000** |
| 30M point | 29,290,240 (29.3M) | 0.897 | **0.000** |

Four sizes. Composition is **0.000 at all four** under the schedules we ran. That is
the same number repeated across a 33× change in the one resource we might otherwise
blame. We would be careful not to over-read it: because the step counts differed, this
is evidence that capacity alone, under these runs, did not produce composition — it is
not a proof that capacity *cannot* (there may be a threshold, or different training
budgets, we did not reach).

Two honest notes on the grid. First, in-distribution scores sit in a healthy plateau
(0.773–0.9167) across all four sizes — capacity neither helped nor hurt the narrow task.
(We suspect the earlier 10.2M run that read 0.383 was incomplete or anomalous — the original checkpoint is unavailable for forensic confirmation, so the cause was not confirmed.) Second,
in-distribution performance is **not** a monotonic ladder that predicts the deep
boundary: the model that reached 0.9167 in-distribution scored 0.000 on composition,
exactly like the ones that reached 0.897 and 0.773. Capacity that helps the shallow score does
nothing for the deep one.

## What's measured vs. what's unknown

**Measured (this setup):**
- The model learns single operations to ~90% in-distribution and generalizes them
  across instances (Q1/Q2) — for prompt strings seen in training, on fresh execution
  values; that is not generalization to new requests.
- The *narrowly-trained* model is surface-tied under **every** tested change (corrected
  2×2, three seeds): new wording → 0.000 (0 of 480, all seeds), new identifiers →
  0.000–0.005 (0–3 of 600), both → 0.000–0.025, against 0.898–0.940 familiar (Q3). The
  *diversity*-pool model reaches 1.000/1.000 on the tested surface — but its arm realized
  only **42 records against 1,200** (P0-02), so
  this is a coverage statement on an unequal-count construction, not proof of
  generalization to a wholly unseen wording family and not an equal-count causal result.
- It cannot compose: unseen combinations → 0.000 across 0.88M→29.3M capacity (the
  model-size sweep tested composition at each size). **Caveat:** the corrected
  *data-size* sweep (Chapter 11) is flat on in-distribution accuracy (0.893–0.997 across
  100→3000) but tested composition not at all, so we do **not**
  claim that more data likewise fails to help composition — that specific
  "more data doesn't fix composition" claim was **not** tested and is not made here
  (Q4); what *is* measured is that record count buys no in-distribution gain either.
- Continual learning is a procedure problem: sequential forgets (A → 0.000), joint
  retains (A → 1.000) with no acquisition cost.
- The pilot task was retrieval-solvable (retrieval = 1.000), so that split is "too
  easy"; the composition split is not (all baselines 0.000).

**Supported / suggestive / open:**
- The composition failure is now **tested twice, not simply suggestive**: (a) exposure
  to a few composites during training does **not** unlock composition on unseen ones
  (the model memorizes the seen combinations at 0.667 but stays at 0.000 on held-out
  ones); and (b) *identifier-diversified* composite exposure (two identifier sets — each
  composite has a single renderer family, so this varied identifiers, not wording-family
  variety) also leaves the held-out composite at **0.000**. So it is neither a "just
  show it combinations" fix nor an identifier-variety fix — and true wording-family
  diversity for composites was never implemented (P1-05). Two caveats: the
  held-out composite candidates all **failed parsing** before semantic evaluation, so
  the *cause* of that zero is unresolved (it is a recorded negative, not a demonstrated
  mechanism), and even the corrected data-scaling sweep did not evaluate composition at
  all, so the data lever speaks only to in-distribution accuracy (where it is flat).
- The one lever we have **not** isolated is diversity of the *inner structure* — many
  *different* primitive pairings rather than different phrasings of the same few. That
  is the remaining open experiment.
- Whether the composition wall is truly structural or simply sits above our ~30M
  ceiling is **untested** — we stop where the CPU lab becomes impractical.

**Unknown (did not test):**
- Whether behavior on 3+ capabilities or post-continual composition holds.
- Whether a fundamentally different inductive bias (not scale) helps.

## The methodology findings

Independent of the model, the **methodology** produced its own results — and several are
as valuable as any model number:

- **Test the tester.** Our own evaluator reported the model at 0.000 on its first run.
  It was the *judge* that was broken (a null-byte artifact), not the model. Fixing it
  revealed the true 0.897. Never trust a number from a system we have not audited.
- **Test the teacher.** The leakage audit caught a 100%-predictable operation from the
  pilot wording — which, on reflection, is mostly task signal (the request must name
  the operation), not a leak. This is why surface splits need held-out template
  families.
- **Test the construction.** The first data-scaling sweep's rising curve (0.100 → 0.641)
  was an artifact of a `pool[:size]` prefix over an operation-ordered pool (P0-01); the
  corrected balanced rerun came back flat. An innocent slice can manufacture a result
  that even replicates across seeds — only reading the arm-building code against the
  claim catches it.
- **Test the data.** The diversity-vs-quantity experiment showed the *same* example
  count produces surface-fragility (0.000) with minimal diversity or much broader
  surface coverage (1.000) with high diversity — but code audit then showed the arms
  were **not** the same count (42 realized records vs 1,200 — P0-02), so what survives
  is a coverage observation, not an equal-count causal result: diversity — not quantity — remains the
  *suspected* driver of how much surface the model covers, pending a corrected rerun.
  (Coverage of the training family's surfaces, not transfer — evidence table,
  Chapter 11.)
- **Baselines are first-class.** A trivial TF-IDF retriever dominated the pilot task
  (1.000), proving it was "too easy," and forced us to build harder splits. And the
  moments the model *fell below* a baseline were the most informative results.
- **The protocol, not capacity, determines continual learning.** Sequential training
  destroyed capability A (0.000) when learning B; joint training preserved A perfectly
  (1.000) at no cost to B. This is a *procedure* finding.

## The boundary, in one line

> **A small model learns narrow, individual mappings well — frequently producing
> executable, correct Python for prompt strings that appeared in training, even on new
> input values — but that does not establish generalization to new natural-language
> requests, and its knowledge is surface-tied: the corrected factorial shows it collapse
> to ~0 on new identifiers, on held-out wording, and on both together. Under the recorded
> training and decoding settings, the tested checkpoints produced no successful held-out
> composite completions; the exposure run's held-out candidates all failed parsing, so
> the cause remains unresolved. The corrected data-count sweep is flat (0.893–0.997
> across a 30× range), so record count establishes no benefit; the diversity comparison
> realized 42 records against 1,200 and establishes no equal-count causal effect.
> Broader surface training improved coverage, not demonstrated transfer to excluded
> wording families.**
>
> (Size and data scaling are two separate levers, and neither was shown to turn surface
> coverage into compositional capability: the size sweep changed training budgets and
> tokenizer, so it is not a size-only intervention, and the corrected data-count sweep —
> balanced operation coverage, one fixed tokenizer — moved the in-distribution score not
> at all while never evaluating composition (evidence table, Chapter 11). We also tested
> a scheduling change — sequential vs. joint training — but that measured retention of
> *separately learned* task groups, not composition, so it likewise does not speak to the
> composition boundary. The diversity study still requires a corrected control before it
> can support a causal claim about surface diversity.)

## Why the map is the deliverable

This map is the book's real output. It is not a single headline accuracy that would
mislead; it is a precise, honest picture of where capability exists, where it collapses,
and what (and what doesn't) shift the boundary. It is the answer to the central
question — and it is falsifiable, built from real measured runs, and honest about what
remains unknown.

### A syntax/capability inventory (kept distinct)

The four questions above are about *generalization*. Separately, the task family can be
viewed as a ladder of Python syntax/capability (from arithmetic to composition), and it is
worth recording which rungs we actually *isolated* versus which we did not. This is a
*syntax* inventory, distinct from the four generalization questions, and we keep it
separate so it is not read as another trust ladder:

| Rung | Capability | Was it isolated? |
|------|-----------|------------------|
| 1 | arithmetic | yes — measured, ~0.90 in-distribution |
| 2–3 | variables, conditionals | yes — variables measured (~0.90); conditionals appear inside the reference for `max_of`/`min_of`/`abs` but were **not isolated** as a standalone task |
| 4–5 | lists, indexing | partially — `list_sum`/`list_len` measured; indexing appears in `first_element`/`double_first` but was **not isolated** |
| 6 | loops | **not isolated** (no standalone loop operation in the primitives; loops appear only inside `list_sum`'s reference) |
| 7 | **composition** | no — **0.000** — the wall |
| 8 | simple functions | not isolated (the task is always "write one `solve` function") |

The honest reading is narrow: we measured individual operations well, and composition
fully; the intermediate rungs (conditionals, indexing, loops as independent skills) were
**not** isolated, so we do not claim about them either way. What we can say is that the
model climbs the rungs we isolated reliably and stops at composition.

The deeper value of the map is what it does to our confidence. Before drawing it, we
knew "the model is limited." After drawing it, we know more precisely which limits we
*moved* with a lever and which we *did not*: composition was not moved by scale, and
surface-tiedness was not moved by scale or by more-of-the-same data — the corrected size
sweep is flat and the corrected surface factorial still collapses — while continual
forgetting was both seen and fixed by how we trained. We are careful not to call the
unmoved ones
"structural" as if we had proven their cause — we observed that the tested levers did
not reach them.

That distinction — which limits we could move and which we could not — is the kind of
knowledge that changes what a practitioner would try next. It is not the same as saying
"small models are weak"; it is saying "here is where the weakness lived under our tests,
and here is what did and did not reach it." A map with a blank region is more useful
than a map painted over with speculation, because the blank marks where the next
investigation should go.

This is also **not** evidence that the model is "stupid" or that the approach "doesn't
work." The model is good at exactly what it was trained to do — map a narrow phrasing to
a narrow computation — and bad at the two things that separate "reflex" from
"capability": robustness to surface change, and composition. The value of measuring it
precisely is that it tells us *where* to look next.
