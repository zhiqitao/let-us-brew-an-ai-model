# 16. Same Pieces, New Combination

Everything so far warned us. The model knows `abs` and `add` individually. Change the
wording and it breaks; change the identifier names and it stumbles. But the pieces are
there. So the question this chapter asks is the sharpest one of the whole book:

> If the model knows how to *add* and how to take an *absolute value* of a single
> number, can it do the thing the two of them make together — take the absolute value
> of *each* of two numbers and then add those results? (`abs(a) + abs(b)`)

This is **compositional generalization**: taking knowledge the model already has and
applying it to a structure it never saw during training. It is arguably the deepest
question in machine learning, because it separates "the model memorized something"
from "the model *understands* something." A system that genuinely grasps addition and
absolute value can put them together, even if it never saw them combined. A system
that merely memorized the word "sum" mapped to a `+` cannot.

## The setup: design the test to be unfair-but-fair

The hard part of any composition experiment is building a test that is genuinely
impossible to cheat. Here is how we do it.

![Same operators, different programs](figures/fig_same_ops.png)

One clarification before the mechanics. The composite `abs_add` is **`abs(a) + abs(b)`**
(the sum of the absolute values of each input), *not* the absolute value of a sum
(`abs(a + b)`). These are different functions — for `a = -3, b = 2` they give `5` and
`1`. The figure above shows the two, and the book consistently uses the right-hand
one (`abs(a) + abs(b)`) for `abs_add`. This matters because the two would require
different programs and distinguishing tests; calling one by the other's name would
change the oracle.

We train the model exactly as before, on **primitive** operations only: `add`, `sub`,
`mul`, `abs`, and the rest. We never show it a held-out composite operation.

A necessary clarification before we go further, because it affects how strong the claim
can be. We define "primitive" **operationally**: an operation entry in the generator's
tables that the training set treats as an atomic task. By that definition the six
composites (`abs_add` and the rest) were indeed held out of training, so the model never
saw a prompt→composite-program pair as a supervised example.

But one operation in the *primitive* pool — `cond_abs_max`, which returns
`max(abs(a), abs(b))` — is **structurally** a composition of `abs` and `max`, even though
the generator lists it as a primitive. This matters for how we read the result: it means
the training pool was *not purely structurally primitive* — it already contained one
operation that combines two others. So we should **not** say "the model was never shown
*both* abs and max being used together" (it was, via `cond_abs_max`), and we should not
claim a clean structurally-atomic primitive-only training set. What we **can** say is
narrower and specific: the model was never shown any of the **six named
held-out composite operations** (`abs_add`, `sub_abs`, `sum_of_abs`, `max_add`,
`double_first`, `len_minus_one`) as a task, and it failed on all of them. We flag this
as a caveat because "primitive-only" is only true as an operational bookkeeping label,
not as a statement that no training operation combined two behaviors.

Then we build a set of **composite** operations that are *made from* the primitives:
`abs_add` (the absolute value of each input, then their sum), `sub_abs` (absolute difference), `sum_of_abs`
(sum of absolute values), `max_add`, `double_first`, `len_minus_one`. These are not
new primitive functions; they are combinations of the ones the model already knows.
To solve `abs_add`, a model *must* take the absolute value of each input and then add the results
— two pieces it demonstrably knows.

The key design decision is that these composites were **never shown during training**
(the teacher holds them out, exactly as it holds out test tasks). So the test is:
can the model reach into its bag of known primitive behaviors and compose them in a
combination it has never seen? If it cannot, we have found its compositional
boundary. If it can, we have found something remarkable.

To make the test fair, we also show what *both* baselines do. The retrieval baseline
has nothing to compose — it can only find the closest primitive example and copy it.
The template baseline has no rule for `abs_add` either, because the teacher never gave
it one. So if *everything* fails, the failure is at least not unique to the learned
model: the easy shortcuts also cannot do it (without this negative signal, a model-only
failure could just mean the task was inherently beyond any of our methods). This is a
useful cross-check, though it is a measured negative, not a proof that no shortcut
exists.

## What we measured

Here is the result, and it is unambiguous:

| Test | MODEL | TEMPLATE | RETRIEVAL |
|------|-------|----------|-----------|
| In-distribution (primitives) | 0.900 | 0.800 | 1.000 |
| **Compositional (unseen combos)** | **0.000** | **0.000** | **0.000** |

Let us read this carefully, because the meaning is subtle.

On the primitive operations it saw, the model scores **0.900 in aggregate** — that is
the pass@1 averaged over all the primitive operations in the split, not a claim that
every single primitive hits 0.900 individually (we did not publish a per-operation
breakdown, so the aggregate should not be read as per-primitive accuracy). But on the
composite operations, it scores **0.000** with the same aggregate reading. Not 0.1, not
"sometimes," not "close." Zero. The model never produced a correct program for any
composite operation it saw, even though every composite is a combination of primitives
the aggregate shows it largely knows.

And here is the *instructive* baseline check: the baselines fail too. The retrieval
baseline gets 0.000 because there is nothing to retrieve that is a composite — its
memory holds only primitives, and it copies whole programs, not pieces. The template
baseline gets 0.000 because no hand-written rule covers a composite. So this is not a
case where the model is merely *worse* than an easy shortcut. It tells us something
clear: the composition test was *not* already solved by a dumb look-up or a fixed rule.

Two honest qualifications on what this does and does not prove. First, the baselines
failing is a useful *negative* signal, not proof the test is "fair" or that every
possible shortcut is excluded. A copy-only retriever failing does not rule out, for
example, a "retrieve the closest primitive and patch its name" shortcut — that is a
different, smarter baseline we did not build, so we cannot say we have excluded all
shortcut solutions, only the two simple ones we ran. Second, it does not isolate
*composition* as the one cause of failure: the model could also be failing for other
reasons — unfamiliar instruction syntax, unseen vocabulary, generation-length limits,
optimization, or a particular held-out operation. We have narrowed *some* causes (it
knows the primitives, it generalizes instances) but not proven that composition is the
single operating factor. That is why we describe the result as a strong measured
failure under this setup, not a proof that composition is impossible.

## What this really means

This is the cleanest negative result in the book, and it is the book's central
finding. Let us unpack it.

The model scores **0.900 in aggregate** on the primitive operations it saw, and **0.000**
on the composites it never saw. To unpack: on the primitives the aggregate is high, but
we did not publish a per-operation breakdown, so we do not say "it *knows* `abs` at 0.900
and `add` at 0.900" as individual facts — we say the *family* of primitives is largely
solved in aggregate. Yet the composites — which combine those same primitives — score
0.000. It is as if the model has access to two perfectly good operations, but the
compositions that must chain them together go nowhere. It cannot take the output of one
primitive and feed it into another in the simplest combination we asked, even though every
piece of that combination is in the family it largely solved.

This is the deep meaning of "surface-tied" that we began to glimpse in Chapter 15.
It is not merely that the model is sensitive to wording. It is that, in this task and
regime, the model's knowledge behaves as if it is **flat and associative**, not
**structured and compositional**. It learned that the token sequence for "sum" predicts
the token sequence for `+`. It did not behave as if it had learned a general
*operation* that can be an argument to another general operation — at least not in the
way the composition test requires. We say "behaves as if" deliberately: this is an
observation about what the model produces under our evaluations, not a claim about
its internal representation.

This distinction is why we built the four-question generalization taxonomy in the first
place and why we refused to collapse everything into one number. If we had only
reported "the model scores 0.900 on this task," we would have given a genuinely
misleading picture. The model is excellent at what it was shown — and utterly unable
to combine what it was shown into anything new. Both statements are true, and both
must be reported.

## The puzzling asymmetry (and why it's a finding, not a bug)

One thing will strike us: the model scores 0.900 in-distribution but 0.000 on
composition. Why would a model that is "good" fail so completely on something so
similar?

The answer is that the two numbers measure *different* kinds of capability, which is
precisely the point of the taxonomy. The 0.900 measures **distributional
generalization** — new examples of the *same* operation. The 0.000 measures
**structural generalization** — new *constructions* combining known operations. These
are different abilities, and a model can be high on one and zero on the other. That
asymmetry is not a contradiction; it is the shape of the truth we are mapping.

## Why we don't call it a "failure of one thing" without checking the other two

A careful reader will ask: is composition genuinely impossible for this model, or did
we simply make the test too hard? The baselines help here. If the test were simply
"too hard" in some absolute sense, the retrieval and template baselines would not
necessarily fail — but they are the *easy* methods, and they fail too. That does not
prove the test is "fair" in an absolute sense or rule out every shortcut; it is a
useful negative signal that the failure is not merely because an easy method happens to
stumble. It makes the result a measured negative, not a proof that no method could
succeed or that the boundary is structural. What we can say: within this apparatus and
these baselines, no method we tried — learned, retrieval, or template — produced a
composite program, which is the result we report.

## The shortcut audit

Before we trust "0.000," we ask how the model might have *faked* a success.

1. **Suspected shortcut: memorizing a composite example.** Narrowed — no held-out
   composite *task* (a prompt→composite-program supervised pair) was shown during
   training, so there was no exact composite example to memorize for a specific
   composite prompt. (We note one caveat: the composition *tokenizer* was fit on
   composite reference text, so composite tokens appear in preprocessing; and one
   "primitive," `cond_abs_max`, is structurally a composition. Neither means the model
   was trained on held-out composite tasks, but we avoid the blanket claim that
   composite programs "never appeared anywhere.")
2. **Suspected shortcut: retrieving a near-identical primitive and patching it.**
   Narrowed — the *copy-only* retrieval baseline scores 0.000. But that only rules out
   copying a whole primitive; it does **not** rule out a smarter baseline that
   retrieves the closest primitive and edits its name/arguments. We did not build that
   smarter retriever, so this shortcut is not fully excluded.
3. **Suspected shortcut: a rule that "just works" on composites.** Narrowed — the
   *template* baseline (fixed rules over the known operations) scores 0.000. That shows
   the specific hand-written rules we wrote do not cover composites; it does not prove
   no rule could, so this is a measured negative for *our* rule set.
4. **Suspected shortcut: the judge being too strict or too loose.** This is the one
   we genuinely have to hold onto as a question, and it is why the judge is
   mutation-tested (Chapter 17). If the judge were rejecting correct composite
   programs, we might be misreading a real success as a failure.

## The natural follow-up: show it some combinations

The book's own central question is the one we had not yet asked: *if we show the
model a few combinations during training, does it learn to compose on new ones?* This
is the experiment we finally ran, and the answer is decisive.

We split the six composite operations: the model was trained on **three** of them
(`abs_add`, `sub_abs`, `sum_of_abs`) alongside the primitives, and tested on the
**other three** it never saw (`max_add`, `double_first`, `len_minus_one`).

| Split | pass@1 |
|-------|--------|
| In-distribution (held-out primitives) | 1.000 |
| Exposed composites (seen in training) | **0.667** |
| **Held-out composites (never seen)** | **0.000** |

The model learns the *specific* composites it was shown — 0.667 on the exposed ones.
But it still scores a flat **0.000** on the combinations it never saw, even though it
uses primitives it knows perfectly (in-distribution 1.000).

That is the answer: **exposure does not unlock composition.** Seeing *some*
combinations does not teach a general "combine two operations" skill. The model
memorized `abs_add` as if it were *just another primitive*, not as a *composition* of
`abs` and `add`. It learned the instance, not the operation.

This closes off the naive fix ("just add composites to the data"). Composition here is
not a matter of having seen a combination — **under everything we have tested**, it does
not emerge from exposure to a few combinations or from diversifying the phrasing of the
exposed ones. We are careful about the word "structural": this is a strong empirical
finding about *this model, this task, this training regime*. It is not a proof that
tiny models "cannot compose" in general — it is a measurement that, in this setup, the
tested interventions did not produce composition. Whether some other intervention
(different optimization, more diverse *combinations* rather than more diverse phrasings
of the same ones) could unlock it is a separate, open question we have not closed.

One step further: since diversity was the lever that *did* fix surface robustness
(Chapter 13), we tested whether *diversifying* the composite exposure unlocks
composition. We diversified the surface of the exposed combinations (the same five
composite operations rendered across many phrasings and identifier-sets) and held out
one composite operation entirely. The result again was a flat **0.000** on the
held-out operation, whether the exposure was minimally or highly diverse.

So the diversity lever does **not** transfer to composition. Surface diversity
diversifies the *outer form* of a combination; composition needs something else. This
points at the one remaining hypothesis: it may be diversity of the *inner structure* —
not different phrasings of the same five pairings, but many *different* primitive
pairings — that could teach the general compose-operator. That is the open question
now, and it is a genuinely different axis from the one we tested.

## The honest framing

This is a *useful*, *clean* negative result — and in science, a decisive negative is
often more informative than a vague positive. We now know something sharp about this
model in this setup: **at ~1M parameters, in this task and training regime, it does not
compose under the interventions we tried.** It learns reflexes here, not structure
here. This is not a statement about "intelligence" or about "what models will
eventually do." It is a precise, reproducible measurement of where *this* model's
capability stops *here* — and, as we have flagged, the door to a different intervention
(or a different, unmeasured cause such as optimization or generation-length limits)
remains open.

And it sets up the rest of the book in a way that is far more interesting than if the
model had composed successfully. Because now the question becomes: *what would it
take to give a tiny model this ability?* More capacity? More data? Different data
with more structure? That is what the next chapters investigate — and the answer is
one of the most genuinely surprising things the book finds.
