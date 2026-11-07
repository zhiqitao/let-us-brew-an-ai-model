# 21. The Model Wasn't the Point: A Conclusion

We began with a question that sounded technical: *can a small language model learn to
solve programming tasks?* The answer we got was more interesting and less about the
model than we expected.

## Where the journey started

The premise was: building a small model is relatively easy; determining what it actually
learned is the hard part. That premise turned out to be more accurate than we had any
right to expect. The model was built in an afternoon. Understanding what it had — and had
not — learned took the rest of the book.

A decoder-only transformer that maps a handful of programming sentences to Python is an
afternoon's work once the pieces are in place. But *knowing what that model actually did*
— whether it learned, memorized, associated, or cheated — required a world, a teacher, a
judge, rivals, and a battery of controlled experiments. The model was the easy part. The
certainty about what it did was the hard part, and it is the part worth writing about.

## What the experiment established

At the core, the answer to the book's central question is now stated in its most
conservative, audit-proof form — the wording we adopt after the third external review
(2026-11-02) and our own code–claim audit:

> In this restricted task family, a sub-million-parameter decoder-only transformer
> frequently produced executable, correct Python for prompt strings that appeared in
> training, even when the resulting program was tested on new input values. That
> performance alone does not establish generalization to new natural-language requests.
> Separate evaluations found severe failures under altered wording and when asked for
> previously untrained program structures. The corrected data-scaling sweep — balanced
> operation coverage, one fixed tokenizer — is flat at ~0.90 across a 30× range, so
> record count bought nothing in this regime; the corrected surface factorial collapses
> to ~0 on new identifiers, on held-out wording, and on both together, so no tested
> prompt-surface change is survived. The corrected equal-count diversity comparison
> shows the combined phrasing/identifier/uniqueness intervention (which does not
> isolate which factor moves the number) moving a genuinely held-out family from 0.000
> to 0.550 mean, costing 0.11-0.38 in-distribution accuracy across the three seeds
> (mean 0.21; at n=3 the 95% interval is -0.58 to +0.17, so the direction is consistent
> in all three runs but the magnitude is not separable from seed noise) (0.950 to 0.743
> mean). The
> durable methodological lesson is that a high score must be interpreted through the
> precise model-visible novelty, the evaluator, the baseline, and the controls used to
> obtain it.

This wording is deliberately more conservative than the capability map's earlier
summary, and the corrected reruns have since strengthened it rather than loosened it:
the data-scaling lever came back flat and the surface collapse came back crisper. Within
it, the experiments separate into what the model **can** do and what it **cannot**.

**It can learn, and it learns well — within a narrow regime.** On individual operations,
the model reliably maps a natural-language spec to correct Python, reaching **~0.90
pass@1** in-distribution on a 0.88M parameter model (the pilot under its own evaluation
scored 0.897; the stage-4 re-evaluation of the same pilot checkpoint measured 0.9167
(n=60; see Appendix C.5) —
different evaluation sets, both reported). It produces general programs for
*fresh inputs of a prompt it saw in training* — a task-ID probe passes 59/60 and a
held-out pair yields the general program, not a memorized literal. That is genuine,
if narrow: it is **not** transfer to a genuinely new request, because the pilot's test
reuses training prompt strings.

**But it is surface-tied and non-compositional.** The two limits that matter:

1. **It anchors to phrasing, not meaning.** In the corrected 2×2 factorial, change only
   the variable names (`a,b` → `left,right`, wording untouched) and it drops to
   **0.000–0.005** — 0 to 3 of 600; change only the wording (same computation,
   different words, identifiers untouched) and it is **0.000 in every seed** — 0 of 480,
   below both baselines; change both and it is 0.000–0.025. It survives no
   prompt-surface change we applied, against ~0.90 on the familiar phrasing (the earlier
   0.35 identifier reading was mixed-factor inflation, P0-03, now superseded). The
   external reality check confirmed it: a human-written test set scored **0/16** —
   **0/11** on requests built from operations the model had seen (a phrasing/surface
   failure) and **0/5** on genuinely held-out composite requests (a structural failure,
   expected separately) — because the model learned a *template*, not the *task*.

2. **It cannot compose what it knows.** Train on `abs` and `add` separately, then ask
   for `abs_add` — it scores **0.000**. The baselines also collapse to 0.000, so the
   failure is a *measured negative*: no method we tried — learned, retrieval, or
   template — produced a composite program. (This is a strong negative signal, not a
   proof that no cleverer method could; see the shortcut audit in Chapter 16.)

   **What the zero *is*, is now measured** (the matched-control experiment,
   Table C.16): among the 120 held-out generations per seed there are **0 complete
   programs and 0 wrong-semantics** — the model never emits a complete program,
   correct or wrong — and the zero survives a verbatim seen-surface framing
   (120/120 no-viable-code per seed) and a length-matched new-composite control
   (0 complete programs under both surfaces), while rewording *mastered* primitives
   under unseen wording collapses generation the same way (298/300 in seed 0 and
   300/300 in seed 1 without a complete program, against 300/300 complete and
   passing under the native wording). So the boundary we report is a
   **prompt-OOD generation failure** — no viable code for unseen prompts, unseen
   compositions among them — not a model that composes incorrectly.

**One limit looked moveable — by changing the data, not its quantity — and the
corrected rerun confirms it.** Diversity of
surface phrasing is the one lever in the book that changed the surface outcome. Its
first comparison did not survive code audit: the high-diversity pool realized only
**42 records** against the minimal arm's 1,200 (P0-02; the mechanism is in Chapter 13's
audit note), so the reported **1.000** was coverage of 42 exact mappings — not transfer,
and not an equal-count result. The corrected rerun holds both arms at exactly **1,200
records**, 10/10 operations at 120 per operation, one fixed tokenizer, matched
protocol — and the finding survives in honest form: on a genuinely held-out phrasing
family the narrow arm scores **0.000** (0 of 100, every seed) and the diverse arm
**0.550** mean (0.640 / 0.300 / 0.710), while in-distribution the narrow arm is
sharper (**0.950** vs **0.743** mean). So the picture is more than "small models are
fragile": *content diversity* is a **measured** lever for widening what a small model
handles — partial transfer, still below both baselines on that test, bought with a
little in-distribution sharpness. More *capacity* (0.88M→29.3M) also did not lift the
compositional limit. **More *data* of the same kind is now measured, and it bought
nothing:** the corrected, operation-balanced size sweep is flat at ~0.90 from 10 to 300
examples per operation — a 30× range with no benefit (Chapter 11) — while the original
rising curve (0.100 → 0.641) was the operation-coverage confound (P0-01), preserved only
as a labeled flawed historical run in the failure ledger. Whether more data would help
*composition* is still a question we did not test and do not assert: the corrected sweep
scored in-distribution only.

**The scaling conclusion is our sharpest negative result.** Composition stays at
**0.000** across model sizes from 0.88M to 29.3M, under the training schedules we ran.
Within that tested range, more capacity did not buy composition. We are careful not to
call this a capacity "ceiling": it is a measured boundary in this regime, not proof
that capacity cannot help under other conditions (different training budgets, larger
sizes, or different optimizers).

## What the laboratory produced along the way

The experiments told a clean, coherent, honest story — and the laboratory caught
itself. The first time we evaluated the model, it scored 0.000 — and it wasn't the
model's fault. The evaluator was broken (a NUL-padding artifact in the output made
every program fail to parse). Fixing the *tester* revealed the model's true 0.897. That
moment — discovering our own instrument was wrong before we trusted it — is as much a
part of this book as any model result.

## The deeper achievement

The book's real finding is not "small models are limited." It is:

> **Building a trustworthy experiment was harder and more valuable than building the
> model.**

The model was the instrument. The experiment was the subject. The things that made this
work — the sandbox that rejects anything not explicitly allowed, the judge that executes
code and compares semantics rather than strings, the mutation suite that red-teams the
judge, the leakage audit, the baselines that ask "could a simpler machine do this?", the
four-question taxonomy that refuses to collapse everything into one number — those are the
actual achievements here.

Each of these forms a discipline rather than a checklist. The sandbox's allowlist (not a
blocklist) rejected the disallowed constructs covered by its validator, so a failure could
more often be attributed to the model rather than to an accident of environment — within
the constructs the gate covers. The
judge's execution-based, semantic comparison meant a "correct" answer was judged correct
under the stated acceptance rule (it ran and matched the expected output), rather than
being merely stylistically close. The mutation suite meant we doubted the judge
before we trusted it. The baseline comparisons meant a number only had meaning relative
to a simpler machine. And the four-question taxonomy meant we never overstated a result by
collapsing different kinds of generalization into one score.

## The recurring habit

There is a way of thinking that runs through everything here, and it is worth naming
directly because it is what a careful investigation actually looks like. It is the habit
of distrusting the easy answer — including our own.

Every time we got a number, the next step was not to celebrate or to move on. It was to
ask: **how could the model have gotten this without learning what we think it learned?**
Could it have memorized? Retrieved? Exploited a template? Leaked the answer from our own
data? Hit a bug in our evaluator? Each of those is a way a seemingly-impressive result
can be hollow, and each one we then built a control to test. That constant, deliberate
suspicion — aimed at our own apparatus as much as at the model — is the difference
between "we ran an experiment" and "we know what the experiment means."

Beyond the numbers, there is a way of working this book was really about. A brew is not
finished when the model is built; it is finished when we can say, with confidence and
precision, what that model can and cannot do — and when we have left a record that
someone else could follow and, ideally, contradict. It is seldom a straight line from
hypothesis to clean result. It is a loop of building, testing the builder, being
surprised, and revising. The surprise is not a detour from the method; it is the method.
And a book about science should show that loop, not hide it.

## What the reader takes away

If we take one thing from this book, it is a habit, not a fact:

> **Never trust a number from a model we don't understand, or from an experiment we
> haven't audited.**

Before we believe "the model learned to add," we have to be able to answer: remove the
memorization, the retrieval, the templates, the leakage, the evaluator artifacts — what
remains? In our case, for simple primitives, what remained was genuine
learning-within-a-surface-form. It was real, and it was narrow, and it did not compose.

**Build the model. Test the model. Break the evaluator. Break the model. Audit the
data. Challenge the conclusion. Repeat.** Only then say: "This is what the model
learned."

## Where this brew leads

The honest map points at specific next experiments, not vague "more data / bigger model":

1. **Does *structural* diversity of combinations unlock composition?** We tested two
   things and both failed: (a) feeding a few composites during training (held-out still
   0.000), and (b) *identifier-diversified* composite exposure — two identifier sets
   (each composite has a single renderer family, so this varied identifiers, not
   wording-family variety; held-out still 0.000). So the remaining open question is diversity of the
   *inner structure* — exposing the model to many *different* primitive pairings — to
   see whether that teaches a general compose-operator. That is the one lever we have
   not isolated. The experiment to run is a systematic increase in *structural*
   diversity — the number, nesting, and variety of operator pairings — with disjoint
   held-out pairing structures and program length and vocabulary matched between
   training and test, so that structure is the only variable that changes.
   (Both data levers now have their corrected reruns: the operation-stratified size sweep
   of P0-01 came back flat, so record count is settled as a null; the equal-count
   diversity comparison of P0-02 came back decisive for held-out-family transfer —
   0.000 → 0.550 mean — so the combined phrasing/identifier/uniqueness intervention
   (which does not isolate which factor moves the number) is settled as a measured,
   partial lever.)
2. **Does the 10.2M in-distribution plateau replicate across configs?** The clean retrain
   measured 0.773 (a stable plateau, not the earlier 0.383 reading). A proper
   training-duration and config sweep at 10M would confirm the plateau is robust.
3. **Does continuing to scale past 30M shift the boundary?** The grid stops where the
   brew lab's CPU becomes impractical. A larger-scale run (or a GPU) would probe whether
   the composition wall eventually moves.
4. **Human-style training.** The 0/16 human test set shows the model fails on
   naturally-phrased prompts. Training on diverse, human-style prompts is the obvious
   path to real usability.

### A future note on widening the world

One planned direction is **widening the capability spec** — and the wording matters,
because the sandbox already allows more than the experiments ever measured. The
allowlist in Chapter 4 already admits `for`/`while` loops, lists, indexing, and
slicing, so "more Python" does not mean adding those; what is untested is **larger and
more complex programs built from the existing constructs** — longer programs, deeper
nesting, more of the allowed vocabulary. **Genuinely new constructs** are a separate
step again: additional syntax, richer types, and recursion, each admitted under a
controlled policy and then measured. The distinction to keep straight is
*sandbox-allowed* (a static property of the validator) versus *experimentally measured*
(only a narrow set of rungs was ever evaluated — see the syntax inventory in Chapter
20). We did **not** run a full sweep of "add more Python and re-measure" in this book;
nor did we test **program length and complexity** (no evaluation on longer or more
structurally complex programs — an untested axis, not a measured 0) or **expressivity
beyond the tested operations** (Python features, built-ins, or idioms outside the fixed
operation set), both listed under Appendix C's "What is NOT tested." What we did measure is that the
composition failure is not explained by a simple missing-token deficit: the model wrote
valid programs for the primitive operations, whose tokens it clearly knew. But that does
**not** prove the model has full *nested* syntax competence — the observed failures were
malformed fragments, and knowing the tokens for `def`/`return` is not the same as
producing correctly nested compound expressions. So we treat "not a syntax problem" as a
plausible-but-unestablished reading. The matched-control experiment (Table C.16)
has since pinned the *failure mode* of the composition zero — no-viable-code
generation on out-of-distribution prompts, where syntax can even be present but no
complete `solve` program appears (seed 0's length-matched `abs_mul` reaches syntax
0.925 yet defines 0/40 complete programs) — while *why* generation collapses on an
out-of-distribution prompt remains open. The versioned,
step-by-step widening framework (the capability spec's `v0_1`, `v0_2`, …) is how we would
test new capability, and we state it as a proposal for the future rather than a completed
result.

## The honest ending

The model was the instrument. The experiment was the subject. We did not build a general
programmer, and we will not pretend otherwise. What we *did* build is the means to ask,
precisely and honestly, what a small model can and cannot learn — and we got an answer
worth having:

> The small model in this brew — 0.88M→29.3M decoder-only transformers on our
> NL-to-Python task — frequently produced executable, correct Python for prompt strings
> that appeared in training, even on new input values; that does not establish
> generalization to new natural-language requests. In our tests its knowledge was
> surface-tied and non-compositional: the corrected surface factorial collapses to ~0 on
> new identifiers, on held-out wording, and on both together, and more capacity
> (0.88M→29.3M) did not change the compositional limit — a limit the matched controls
> show to be a no-viable-code generation failure on unseen prompts (0 complete
> programs, 0 wrong-semantics on held-out composites), not incorrect composition. The corrected data-scaling sweep
> is flat at ~0.90 across a 30× range, so record count bought nothing; the corrected
> equal-count diversity comparison shows the combined phrasing/identifier/uniqueness
> intervention (which does not isolate which factor moves the number) moving a held-out
> family from 0.000 to 0.550 mean, costing 0.11-0.38 in-distribution accuracy across the
> three seeds (mean 0.21; at n=3 the 95% interval is -0.58 to +0.17, so the direction is
> consistent in all three runs but the magnitude is not separable from seed noise)
> (0.950 → 0.743), while the
> original 42-vs-1,200 run is superseded history.

And the habits we learned — test the tester, test the teacher, compare against baselines,
audit shortcuts, preserve failures — are the durable part. That is the method worth
keeping, and it is the reason the book's real subject was never the model. The brew was
never only about the model; it was about learning to ask a question carefully enough that
the answer could be trusted.

## Where this sits: related work

None of the ideas here is new in isolation, and we want to say so plainly rather than
imply novelty. This book's contribution is not inventing a technique; it is assembling a
small, fully-controlled laboratory and being unusually honest about what the results do
and do not establish. The underlying disciplines have long histories, and a reader who
wants to go deeper should look there:

- **Compositional generalization.** The question of whether a model can combine known
  pieces in novel ways is a longstanding benchmark problem (e.g. the SCAN and COGS
  datasets). Our finding — that a tiny model does not compose under our tests — is a
  narrow case of a much-studied puzzle.
- **Execution-based code evaluation.** Running generated code against hidden tests is
  the standard for code-generation evaluation (the pass@k / HumanEval tradition). We
  borrowed that idea and applied it at a miniature scale, and our mutation-control work
  echoes the broader practice of testing the evaluator itself.
- **Shortcut learning.** "The model found an easier signal than the one we intended" is
  a well-documented phenomenon; our shortcut audit is a small, disciplined instance.
- **Catastrophic forgetting and rehearsal.** The effect we measured is a classic
  finding; the observation that keeping old data in the mix helps is also
  long-established.
- **Mutation testing.** Originating in software engineering, it is the source of our
  judge red-team.

We cite these traditions to place the book in context, not to claim we advanced them. We
did not benchmark against these in this book (the task and scale are far smaller), so we
make no claim of competing with them.

## Reading further

These are the published works the book's questions relate to, cited with stable
identifiers (DOI or ACL Anthology / arXiv record) so a reader can verify each. One line
each on why it matters for the questions here. We have not benchmarked against any of
them — the task and scale here are far smaller — so we make no claim of competing with
them; the citations place the book's questions in context.

- **Compositional generalization.** Lake & Baroni, *Generalization without Systematicity:
  On the Compositional Skills of Sequence-to-Sequence Recurrent Networks*, ICML 2018 —
  arXiv:1711.00350, https://arxiv.org/abs/1711.00350. Introduced the **SCAN** benchmark,
  which probes exactly the "new combination of known pieces" question (the book's
  Question 4) and found seq2seq models largely fail it.
- Kim & Linzen, *COGS: A Compositional Generalization Challenge based on Semantic
  Interpretation*, EMNLP 2020, pp. 9087-9105 — https://aclanthology.org/2020.emnlp-main.731/
  . COGS is a **semantic-parsing / compositional-generalization** dataset (fragments
  grounded in a small world language), not a question-answering benchmark. It showed
  seq2seq models achieving much lower accuracy on novel combinations than on
  in-distribution examples — the same in-distribution vs. compositional gap the book
  measures.
- **Execution-based code evaluation.** Chen, Tworek, Jun, Yuan, et al., *Evaluating Large
  Language Models Trained on Code*, arXiv:2107.03374, 2021 (HumanEval / Codex). The
  pass@k formulation the book adapts to problem-level pass@1, and the insight that
  *executing* a program against tests is a sharper evaluation than comparing text.
- **Shortcut learning and spurious correlation.** Geirhos, Jacobsen, Michaelis, Zemel,
  Brendel, Bethge, & Wichmann, *Shortcut Learning in Deep Neural Networks*, Nature
  Machine Intelligence 2(11):665-673, 2020 — DOI 10.1038/s42256-020-00257-z,
  https://doi.org/10.1038/s42256-020-00257-z. The conceptual framework for asking "did
  the model learn the task, or a shortcut to it?" — the question the book's surface test
  (Question 3) and lexical diagnostic address directly.
- **Continual learning and catastrophic forgetting.** McCloskey & Cohen, *Catastrophic
  Interference in Connectionist Networks: The Sequential Learning Problem*, in *Psychology
  of Learning and Motivation*, pp. 109-165, 1989 — https://doi.org/10.1016/S0079-7421(08)60536-8
  . (The original
  forgetting result); and Kirkpatrick et al., *Overcoming Catastrophic Forgetting in
  Neural Networks*, PNAS 114(13):3521-3526, 2017 — DOI 10.1073/pnas.1611835114,
  https://doi.org/10.1073/pnas.1611835114 (elastic weight consolidation, a
  rehearsal-free alternative). These frame the book's sequential vs. joint training
  result.
- **Mutation testing of test suites.** Jia & Harman, *An Analysis and Survey of the
  Development of Mutation Testing*, IEEE Transactions on Software Engineering
  37(5):649-678, 2011 — DOI 10.1109/TSE.2010.62, https://doi.org/10.1109/TSE.2010.62. The
  practice of seeding faults to measure a test suite's ability to catch them — the basis
  of the book's judge red-teaming in Chapter 17.

## Three short exercises

If you want to check that you have the book's discipline, try these. Answers are in the
back of this chapter.

**1. Coverage or generalization?** You train a model on three wording families and
evaluate it on a fourth that it has never seen. It scores 0.900. Is that a coverage
result or a generalization result? What if instead you evaluated it on a *rephrasing
within one of the three families it saw* — is *that* same interpretation?

**2. Distinguish two programs.** For the two functions `abs(a + b)` and `abs(a) + abs(b)`,
find one input where they give the same answer and one where they differ. Why does a
single passing test not distinguish them, and what kind of test does?

**3. What does a zero establish?** A model scores 0.000 on a held-out composition split.
Write down what this does and does *not* establish — name at least two other causes of a
zero that the result does not rule out, and one thing you could run to distinguish them.

## Answers to Exercises

**1.** The first is generalization to an excluded family; the second is
coverage of a surface within the training family. Only the first speaks to a
never-seen family. Note that a genuinely new prompt within a familiar family is still a
real form of in-distribution generalization (a new surface, same computation) —
"excluded-family transfer" is a stronger and different shift, not the only form of
generalization the book measures.

**2.** For `a = 2, b = 3` both give `5`; for `a = -3, b = 2`
they give `1` and `5`. One test can be satisfied by both programs, so a distinguishing
test must use a signed input where the two differ.

**3.** The zero shows that, under this
decoding/evaluation procedure, no program passed every hidden test. It does not
identify the cause (instruction interpretation, syntax generation, length handling,
coverage, optimization, or a particular held-out operation), is not proof of a general
capacity limit, and is not proof that the model "cannot compose" — a per-stage failure
report or an all-composites control would narrow which cause holds.

In this book we later ran exactly the kind of control the exercise asks for — the
matched-control experiment (Table C.16). It showed the composition zero is a
no-viable-code generation failure (0 complete programs, 0 wrong-semantics on
held-out composites, both seeds) that survives seen-surface and length-matched
controls, so the cause we now report is prompt-OOD generation collapse, not
incorrect composition.
