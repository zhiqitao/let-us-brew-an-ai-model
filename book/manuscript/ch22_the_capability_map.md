# 22. The Capability Map

We have run a small, disciplined set of experiments and measured a coherent boundary.
Rather than a list of results, let us draw the **capability map**: one picture that
says, for each behavior we tested, whether the model acquired it, whether it generalizes,
what it costs, and where it breaks.

Everything below is scoped to **our** setup: a ~0.9M–29.3M decoder-only transformer,
trained on a few thousand generated natural-language-to-Python tasks, evaluated by a
mutation-tested execution-based judge. These are claims about this brew, not universal
laws about all small models. Where we say "here" or "in this regime", it is deliberate —
these are well-controlled measurements in one configuration, not proofs that hold
everywhere.

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

| Question | What it asks | Measured result | Status (in this setup) |
|-------|--------------|-----------------|--------|
| **Q1 Mem** | Could it be explained by remembering? | Held-out 59/60; canary → general program | `[MEASURED]` it generalizes primitives, doesn't parrot |
| **Q2 Dist** | Does it work on new instances of the same task? | In-distribution 0.900 | `[MEASURED]` yes — here |
| **Q3 Surf** | Does it survive superficial change? | *Narrowly-trained model:* new wording → 0.000; new identifiers → 0.350. *Diversity-trained model (same count):* **1.000 / 1.000** — but the strong form ("generalizes to a never-seen family") is not established, since the surface test's family & identifiers were present in the diverse pool | `[MEASURED]` — brittle when trained narrowly; diverse training covers more surfaces (generalization to a truly-held-out family untested) |
| **Q4 Struct** | Can it compose known pieces in unseen ways? | 0.000 (baselines also 0.000) | `[MEASURED]` no — in this regime |

### The evidence, keyed by checkpoint

The table above groups results by *question*. But each number belongs to a specific
**checkpoint** (a saved model) and a specific **evaluation split**, and it is important
not to let one row mix scores from different models. Here is the same evidence laid out
run by run, so every cell traces to the checkpoint the registry names. A dash (`—`)
means that evaluation was **not run for that checkpoint**; `NT` means the evaluation is
not applicable to that run; `0.000` is a measured zero.

**Panel 1 — code-generation evaluations, by checkpoint**

| Checkpoint | params | familiar prompt | new identifiers | excluded wording | covered alternate surface | held-out composite |
|---|---|---|---|---|---|---|
| `stage1.pt` (Stage 1 pilot) | 0.88M | 0.897 | — | — | — | 0.000 |
| `stage3_surface.pt` (Stage 3) | 0.88M | 0.900 | 0.350 | 0.000 | — | — |
| high-diversity (same count) | 0.88M | 1.000 | — | NT | 1.000 | — |
| `stage4_6p5m.pt` | 6.5M | 0.897 | — | — | — | 0.000 |
| `stage4_10m.pt` | 10.2M | 0.773 | — | — | — | 0.000 |
| `stage4_composition.pt` | 29.3M | 0.897 | — | — | — | 0.000 |

Key: the surface-row scores (new identifiers 0.350, excluded wording 0.000) come from the
**Stage-3 checkpoint**, not the Stage-1 pilot. The composition score for `stage1.pt` is a
separate re-evaluation of the pilot on the composition split (which is why the registry
lists a "Stage-4 composition baseline" row that points at `stage1.pt`). The high-diversity
row's 1.000 is **coverage** of surfaces in its training family, not transfer to an
excluded wording family.

**Panel 2 — composition-intervention and continual-learning runs**

These conditions are not "one bigger model"; they test whether *training content* or
*schedule* changes the boundary, so they belong in their own panel.

| Condition | params | in-dist | exposed composites | held-out composite |
|---|---|---|---|---|
| composition-exposure (stage4_exposure) | 0.88M | 1.000 | 0.667 | 0.000 |
| composition-diversity (minimal) | 0.88M | 1.000 | 0.592 | 0.000 |
| composition-diversity (high) | 0.88M | 1.000 | 0.550 | 0.000 |

**Panel 3 — sequential vs. joint training**

| Protocol | final A accuracy | final B accuracy | true replay-after-A |
|---|---|---|---|
| Sequential (A then B) | 0.000 | 0.889 | NT (not run) |
| Joint (A+B from start) | 1.000 | 0.889 | — |

Note the "sequential" A figure is a **final task accuracy**, not "retention relative to a
pre-B checkpoint" — there was no A-only checkpoint to retain against. A true
replay-after-A-first continuation (which *would* measure retention relative to an
A-trained checkpoint) was **not** run.

Read the map vertically and it shows a steady decline in how much we can trust the
model's "understanding" as we move from "did it see this before" (Level 1) to "can it
put things together" (Level 4). The model passes the first two levels cleanly and fails
the last two completely.

## What the model can do

**It can learn individual operations well.** On in-distribution primitives — `add`,
`sub`, `mul`, `max`, `abs`, `list_sum` — the ~0.9M model solves ~90% of held-out
problems under the evaluation's default temperature-0.8 sampled decoding. It beats a hand-written template rule system (0.900
vs 0.800). This is real, measurable capability on a narrow task.

**It generalizes across instances, not just examples.** It passed 59/60 held-out
prompts and, on a *canary* it had never seen, produced the *general* program rather
than a memorized literal. So for a single operation, the model is a learner, not a
parrot. That is Question-2 distributional generalization, achieved.

## What the model cannot do

**It cannot survive changes to the surface form.** Change the variable names from
`a,b` to `left,right` (identical computation) and performance falls to 0.350. Rephrase
the instruction with a wording family the model never saw (identical computation) and
performance falls to **0.000** — below *both* baselines. This is Question-3 failure: the
model's capability is **anchored to the phrasing**, not grounded in the computation.

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
| Data size | 100 → 3000 examples | helps *in-distribution* (0.10→0.64); **composition not tested** in this run (we did not evaluate the scaled models on the composite split) |
| Training protocol | sequential vs joint | **big** — fixes continual retention (0.000→1.000); a *different* lever, not a composition lever |

The second half of the map is about levers, and it is where the surprising findings
live. We tried three ways to move the boundary — more capacity, more data, and a
different training procedure. More capacity did nothing to composition (0.000 at all
four sizes); more data was only evaluated on the in-distribution task (composition was
not tested in the scaling run); and a different training procedure was the decisive
lever for a *different* problem (continual learning), not for composition. This
asymmetry is worth circling, because it tells us where effort does and does not pay.

## The capacity grid, in full

The sharpest negative result in the whole book is the model-size sweep, and it deserves
its own table because it is the claim a reader would most want to test. We ran the
composition experiment across a ~33× range of capacity. We did **not** hold every
hyperparameter constant — the runs used different step counts (see Appendix C), so this
is a sweep across capacity with some training-budget variation alongside it, not a
strictly-controlled size-only comparison.

| Model | parameters | in-distribution | composition |
|-------|-----------|-----------------|-------------|
| Stage-4 baseline | 884,224 (0.88M) | 0.900 | **0.000** |
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
(0.773–0.900) across all four sizes — capacity neither helped nor hurt the narrow task.
(One 10.2M reading of 0.383 turned out to be a training-run artifact.) Second,
in-distribution performance is **not** a monotonic ladder that predicts the deep
boundary: the models that reached 0.900 in-distribution scored 0.000 on composition,
exactly like the one that reached 0.773. Capacity that helps the shallow score does
nothing for the deep one.

## What's measured vs. what's unknown

**Measured (this setup):**
- The model learns single operations to ~90% in-distribution and generalizes them
  across instances (Q1/Q2).
- The *narrowly-trained* model is surface-tied: new wording → 0.000, new identifiers →
  0.350 (Q3). The *diversity-trained* model (same count) reaches 1.000/1.000 on the
  tested surface — though, as the caveat notes, that is strongest as a coverage
  statement, not proof of generalization to a wholly unseen wording family.
- It cannot compose: unseen combinations → 0.000, and neither ~33× capacity (across
  0.88M→29.3M) nor more data changes this (Q4).
- Continual learning is a procedure problem: sequential forgets (A → 0.000), joint
  retains (A → 1.000) with no acquisition cost.
- The pilot task was retrieval-solvable (retrieval = 1.000), so that split is "too
  easy"; the composition split is not (all baselines 0.000).

**Supported / suggestive / open:**
- The composition failure is now **tested twice, not simply suggestive**: (a) exposure
  to a few composites during training does **not** unlock composition on unseen ones
  (the model memorizes the seen combinations at 0.667 but stays at 0.000 on held-out
  ones); and (b) diversifying the *surface* of the composite exposure (many phrasings ×
  id-sets) also leaves the held-out composite at **0.000**. So it is neither a "just
  show it combinations" fix nor a "diversify the phrasing" fix.
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
- **Test the data.** The diversity-vs-quantity experiment showed the *same* example
  count produces surface-fragility (0.000) with minimal diversity or much broader
  surface coverage (1.000) with high diversity. Diversity — not quantity — is what
  changes how much surface the model covers. (This is coverage of the surfaces in the
  training family; it is not established transfer to a wording family excluded from
  training.)
- **Baselines are first-class.** A trivial TF-IDF retriever dominated the pilot task
  (1.000), proving it was "too easy," and forced us to build harder splits. And the
  moments the model *fell below* a baseline were the most informative results.
- **The protocol, not capacity, determines continual learning.** Sequential training
  destroyed capability A (0.000) when learning B; joint training preserved A perfectly
  (1.000) at no cost to B. This is a *procedure* finding.

## The boundary, in one line

> **A small model learns narrow, individual mappings well and generalizes them across
> instances, but its knowledge is surface-tied and non-compositional — and within the
> tested range, neither more parameters nor more data turns that into robust,
> compositional capability. (We also tested a scheduling change — sequential vs. joint
> training — but that experiment measured retention of *separately learned* task
> groups, not composition, so it does not speak to the composition boundary.)**

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
| 1 | arithmetic | ✅ measured, ~0.90 in-distribution |
| 2–3 | variables, conditionals | ✅ variables measured (~0.90); conditionals appear inside the reference for `max_of`/`min_of`/`abs` but were **not isolated** as a standalone task |
| 4–5 | lists, indexing | partially — `list_sum`/`list_len` measured; indexing appears in `first_element`/`double_first` but was **not isolated** |
| 6 | loops | **not isolated** (no standalone loop operation in the primitives; loops appear only inside `list_sum`'s reference) |
| 7 | **composition** | ❌ **0.000** — the wall |
| 8 | simple functions | not isolated (the task is always "write one `solve` function") |

The honest reading is narrow: we measured individual operations well, and composition
fully; the intermediate rungs (conditionals, indexing, loops as independent skills) were
**not** isolated, so we do not claim about them either way. What we can say is that the
model climbs the rungs we isolated reliably and stops at composition.

The deeper value of the map is what it does to our confidence. Before drawing it, we
knew "the model is limited." After drawing it, we know more precisely which limits we
*moved* with a lever and which we *did not*: composition and surface-tiedness were not
moved by scale or more-of-the-same data (in our runs), while continual forgetting was
both seen and fixed by how we trained. We are careful not to call the unmoved ones
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
