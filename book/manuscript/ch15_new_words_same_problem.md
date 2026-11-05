# 15. New Words, Same Problem

Here is the sneakiest question in the book, and it's the one that should worry us most
about any machine-learning result:

> **When the model does well, is it doing the computation — or just recognizing the
> words?**

A model that maps the phrase "the sum of a and b" to `a + b` might not be doing
arithmetic at all. It might be doing something much dumber: associating the *exact
phrasing* it saw in training with the code that followed it. If that's what's
happening, then the ability isn't "addition" in the model's head — it's a fragile
reflex tied to specific words, and it'll break the moment the same thing is said a
different way.

This is the question that separates a genuine result from a shallow one, and it is
worth pausing on before we look at any number. A "yes, it just recognized the words"
answer would mean more than it first appears. It would mean that every high score the
model achieved — every impressive in-distribution number — was evidence of *association*
with the phrasing, not evidence that it can regenerate the intended program. The model
did not write the arithmetic itself — Python executes that when the program runs; what the
model does is *emit source code* that stores the answer, and it learned that a particular
sentence corresponds to `return a + b`. That is a different claim from saying it
understands addition, and it is the one we need to test.

## The design: change what shouldn't matter

To find out, we run the **surface-generalization** test. The logic is simple and
elegant: if we change something that *shouldn't* change the computation — the variable
names, or the wording — and the model fails, then its success is **not robust to that
surface shift**. It is tied to the phrasing it saw. (We are careful about what this
does and does show: it demonstrates a lack of robustness to the chosen shift, not
that no internal semantic representation exists.)

The key is choosing *what* to change. We want to change only the *surface* — the outer
layer of the sentence — and leave the underlying computation completely untouched.
Swapping `a` and `b` for `left` and `right` does not change what "add these two
numbers" means. Rewording "their sum" as "the total" does not change the operation.
If the model truly understood addition, neither change would matter. If it merely
memorized a sentence, either change would break it. That asymmetry is exactly what we
measure — and to measure it cleanly we change each factor *separately*, in a full
2 × 2 design, because our first attempt changed two things at once and had to be
corrected (a code audit showed the original "new identifiers" condition also changed
wording-family coverage, and its denominator was misstated; Appendix B, P0-03 and
P0-04).

## The setup

The corrected experiment trains the model on the ten arithmetic operations with
**letter identifiers** (`a`, `b`) and only the **kept subset** of wording families, then
re-asks the *identical* tasks under controlled surface changes. Everything is held fixed
across the four cells:

- **one fixed training set**: 600 tasks — 60 per operation × 10 operations — letter
  identifiers × kept wording families;
- **one fixed tokenizer**, fit on those training texts only and reused unchanged across
  every cell and every seed (vocabulary 291; SHA-256
  `2c5c800b21e6a9a39d2688aec50cd4e092b3f99ea673b0618ffa6ffc65eb0a2b`);
- **identical task sets per cell**, scored by the MODEL and by both baselines on the
  same records, after the same 1,500-step training budget (batch 16, learning rate
  1e-3), under seeds 0, 1, and 2.

The four cells and their denominators:

| cell | identifiers | wording | records |
|------|-------------|---------|---------|
| familiar | letters | kept families | **600** (10 ops × 60) |
| identifiers only | words (`left`, `right`) | kept families | **600** (10 ops × 60) |
| wording only | letters | held-out family | **480** (8 ops × 60) |
| both changes | words | held-out family | **480** (8 ops × 60) |

The held-out-wording cells have **480** records, not 600, because `abs_of` and
`cond_abs_max` have a single wording family and therefore have no held-out family to
test — they are excluded from those two cells (P0-04). With the factors unmixed and the
denominators recorded in the manifest, any difference between cells is attributable to
the surface change that cell applies.

**Scope of the aggregate comparisons.** The wording cells cover the 8 operations that
have a held-out family (480 records); the familiar and identifiers-only cells cover all
10 (600). Any **aggregate** wording-effect comparison in this chapter is restricted to
those 8 operations shared by all four cells — per-operation scores are reported for
every cell, so the restriction is checkable against the manifest — and on that shared
set the comparison is 480/480 (familiar) versus 0/480 (wording only) in every seed, so
the 480-versus-600 aggregate never conflates operation coverage with a wording effect:
`abs_of` and `cond_abs_max` are excluded from *both* sides of the wording contrast, and
their familiar-surface scores remain visible in the per-operation breakdown. One
further scope note: the held-out wording is a **single deterministic family per
operation** — the last family in the fixed family inventory, chosen by rule, not
sampled across families — so each wording cell is one fixed re-rendering per operation,
not an average over possible rephrasings.

## The result

Model pass@1 by seed (successes in parentheses):

| cell (denominator) | seed 0 | seed 1 | seed 2 |
|--------------------|--------|--------|--------|
| familiar (600) | **0.898** (539) | **0.900** (540) | **0.940** (564) |
| identifiers only (600) | **0.000** (0) | **0.003** (2) | **0.005** (3) |
| wording only (480) | **0.000** (0) | **0.000** (0) | **0.000** (0) |
| both changes (480) | **0.000** (0) | **0.025** (12) | **0.000** (0) |

The baselines are identical across all three seeds: TEMPLATE scores 480/600 = 0.800 on
the two kept-wording cells and 420/480 = 0.875 on the two held-out-wording cells;
RETRIEVAL scores 600/600 = 1.000 on the two kept-wording cells and 60/480 = 0.125 on the
two held-out-wording cells.

Look at what happens when we touch only the *surface*, not the math.

- **New identifiers alone.** The model was trained on `a` and `b`. We ask the same
  question with `left` and `right` — identical wording, identical operation.
  Performance collapses from **0.898–0.940 to 0.000–0.005**: 0, 2, and 3 successes out
  of 600. The identifier shift by itself costs the model essentially everything, while
  on the very same records RETRIEVAL stays at 600/600 and TEMPLATE at 480/600.

- **Held-out wording alone.** Identifiers untouched; we say the exact same problem using
  a phrasing family the model never saw during training. Performance is **0.000 in every
  seed** — 0 of 480, three times over.

- **Both at once.** 0.000 / 0.025 / 0.000 — 0 to 12 of 480. Combining the shifts recovers
  nothing: the collapse is already complete on either single factor.

So the model that scores ~0.90 on the familiar phrasing falls to ~0 on *any* change of
surface — new variable names, new wording, or both — even though the computation is
identical in all four cells. The earlier 0.350 "new identifiers" figure came from the
original Stage-3 run, which changed identifiers *and* wording-family coverage together;
with the factors unmixed, the identifier-only cell is ~0, so 0.350 was **mixed-factor
inflation**, not a partial identifier effect. That original run is preserved as a
labeled flawed historical record (P0-03, P0-04) in the failure ledger and as a
superseded row in Appendix C; the corrected factorial above is this chapter's result.

## The damning comparison

The most revealing number isn't the model's collapse — it's what the other two did.
![Surface generalization — corrected 2x2 factorial](figures/fig_surface.pdf)

*Corrected 2×2 factorial (fixes P0-03 and P0-04); all three seeds are shown — seed-0
bars with seeds 1 and 2 as open markers — and each cell's denominator **n** is printed
under that cell. Each pass@1 is over the
cell's own held-out task set, with the MODEL and both baselines scored on identical
records: the familiar and identifiers-only cells have **600** records each (10
operations × 60), the wording-only and both-changes cells have **480** (8 operations ×
60 — `abs_of` and `cond_abs_max` have a single wording family and are excluded from the
held-out cells), so the rates are integer fractions over those denominators: MODEL
539/600, 0/600, 0/480, 0/480; TEMPLATE 480/600, 480/600, 420/480, 420/480; RETRIEVAL
600/600, 600/600, 60/480, 60/480. Across seeds the model's familiar cell is 0.898–0.940,
identifiers-only 0.000–0.005, wording-only 0.000 in all seeds, both-changes 0.000–0.025.
One fixed 600-record training set and one fixed train-only tokenizer underlie every
cell; the superseded mixed-factor Stage-3 rows are the flawed historical run (P0-03,
P0-04). Decoding is temperature-0.8 single-sample.*

When we change the *words*, the **template baseline gets *better*, not worse** (0.875,
up from 0.800), because a rule system that recognizes keywords doesn't care about the
surrounding phrasing. The **retrieval baseline** falls to 0.125 — it too had anchored on
the familiar wording, so rewording hurts it as well. On the identifier-only change,
retrieval doesn't move at all (600/600): a retriever matching on content words is
indifferent to what the variables are called. Only the learned model is *catastrophic*
in every changed cell — 0 to 3 of 600 on identifiers, 0 of 480 on wording — below both
baselines under every surface change we applied.

So the model's ~0.90 in-distribution score was **tied to the phrasing it
saw**. It had learned that this kind of sentence maps to that program. Whether it has
learned anything more general about "take two numbers and return their sum" — something
we could say any number of ways and still mean — is exactly what the reworded collapse
tests, and under this shift it did **not** hold. (We do not take the failure as proof of
the absence of any semantic representation; it shows lack of robustness to the phrasing
change we applied.)

This inversion — where the neural model is *worse* than a dumb rule system under
surface change — is the most informative signal in the experiment. It is not a
competitive defeat; it is a diagnostic revelation. The dumb template system is
indifferent to the exact wording because it just matches keywords; it never had to
bind a meaning to the phrasing at all. The neural model, by contrast, appears to have
bound the operation to the *particular words*, so when the words change, the binding
snaps. The model's behavior was more entangled with surface form than a hard-coded
rule's was.

## The brewing experience

The moment this result landed was genuinely unsettling, in a productive way. We had
just celebrated the ~0.90 familiar score — the model, we thought, could "add." Then we
reworded the same problem and the floor fell out. The ~0.90 had been real, and it had
been *narrow*. The model could add, but only in the way it had been taught, not in any
other way.

The corrected factorial made the narrowness narrower still. The first version of this
experiment had offered a consolation prize — a partial 0.350 on new identifiers, as if
the model half-survived a change of variable names. When the factors were unmixed, the
consolation prize disappeared: identifiers alone took the score to 0–3 of 600. There was
no cell, on any seed, where a surface change left the model standing.

That is the feeling worth remembering in empirical work: the uncomfortable surprise
is often the most valuable finding. It would have been easy to stop at "the model
scores ~0.90, success." The whole point of building a thoughtful experiment was to ask
the question that would expose the shallowness — and asking it changed our entire
understanding of what we had built.

## The shortcut audit

1. **Suspected cheat: phrasing memorization.**
   **Why it fits:** the model tied training phrasings to code.
   **Control:** held one whole phrasing style out of training, tested on it.
   **Result:** 0.000 in every seed — 0 of 480, three times.
   **Ruled out:** that this model's success is *robust* to the chosen phrasing shift.
   **Still open:** whether the failure reflects purely surface association or the new
   vocabulary/wording pattern; and note that failure under one rewording does not, by
   itself, establish that there is no internal semantic representation.

2. **Suspected cheat: name memorization.**
   **Why it fits:** trained on `a,b`, maybe it hardwired those labels.
   **Control:** retest on `left,right` with wording held fixed at the kept families
   (the identifiers-only cell).
   **Result:** 0.000 / 0.003 / 0.005 — 0 to 3 of 600. A complete collapse, not a
   partial drop.
   **Ruled out:** that the model survives an identifier change; names alone break it.
   **Superseded:** the earlier 0.350 reading was a mixed-factor shift (P0-03), replaced
   by this cell.

## The honest takeaway

A model that scores ~0.90 on familiar phrasings and 0.000 on a rewording of the same
problem — or on the same problem with different variable names — has not generalized to
the *problem*. It generalized to the *phrasing*. That's the difference between "the
model works" and "the model works when I say it the way I said it in training" — and
it's the most important lesson of the generalization chapters.

The sharpest way to state it, as observed: under this checkpoint, this decoding, and
this extraction, the model produced `a + b` for the familiar phrasing and no passing
program for the reworded one — ~0.90 falling to 0.000 on an identical computation, with
the identifier-only cell falling just as far (0–3 of 600). One reading of that pattern
is a hypothesis about the mechanism, not a measurement: that the model learned the
*word "sum"* rather than addition. When that word appears in the sentence it was trained
on, the model produces `a + b`; when the same meaning arrives in different words, it
produces nothing usable. What the counts establish is the behavior — a severe
surface-robustness failure under *every* surface change we applied, single-factor or
combined — not the cause, and they do not rule out an internal representation of
addition. That is the difference the experiment draws between generalizing and merely
reciting.

## The human-written test set: the hardest rewording of all

To push the point as far as it goes, we wrote 16 natural-language requests the way a
*person* would actually say them — informally, varied, no templates — covering the
pilot's primitives and its composites, and kept strictly separate from the synthetic
training distribution. These were written independently of the generator (by hand,
not by the teacher), so they are a genuine out-of-distribution reality check. We label
each by whether it asks for a **primitive** operation (1–10) or a **composite** one
(11–16). The full set:

**Primitive requests (1–10):**

1. "Take two numbers and give me back their total."
2. "Add these two values together."
3. "Return the result of subtracting the second number from the first."
4. "What's the product of these two numbers?"
5. "Tell me which of these two is the bigger one."
6. "Which is smaller, the first or the second number?"
7. "Give me the absolute value of this number."
8. "Sum up every number in this list."
9. "How many items are in this list?"
10. "What's the first element of this list?"

**Composite requests (11–16):**

11. "Return the larger of the two, but as a positive number."
12. "Add the absolute values of both numbers."
13. "Give me the distance between these two numbers."
14. "Sum the absolute values of everything in the list."
15. "Double the first item in the list."
16. "Return one less than the length of the list."

**A note on the 11–16 label, because it is not uniform.** Only requests 12–16 map to
**five genuinely held-out composite operations**, and note that `max_add` is *not*
represented among them — there is no `max_add` request in this set. Requests 12–16 cover
`abs_add`, `sub_abs`, `sum_of_abs`, `double_first`, and `len_minus_one`. Request 11
("larger of the two, but as a positive number") maps to `cond_abs_max` — an operation that
*is in the named* generator training pool (the pilot's primitive set) even though it is
structurally composite. So request 11 is a case of a **familiar operation in new
phrasing**, not held-out composite behavior. We therefore keep the "composite" label as
shorthand but read requests 11–16 as a mixture: 11 tests new phrasing of a seen (but
composite) op, and 12–16 test genuinely held-out composite tasks. Likewise, requests 1–10
do not cover ten distinct primitives: two of them ("total" and "add these") both ask for
addition, so they cover **nine** distinct operation IDs. The outcome (0/16) is the same
either way, but the interpretation of *why* differs.

Against the pilot checkpoint, the model solved **0 of 16**. Read by training exposure,
that is **0 of 11 requests asking for seen operations** (requests 1–10, which cover nine
distinct primitive operation IDs with addition counted twice, plus request 11, which
rephrases the seen `cond_abs_max`) and **0 of 5 genuinely held-out composite requests**
(requests 12–16). Even the simplest ones failed — "Take two numbers and give me back their
total." produced malformed code; "Tell me which of these two is the bigger one." produced
`def solve(a): return a a a + a - b`. None produced a valid program.

One of these needs an explicit caveat because it is genuinely **ambiguous** on its own.
Request 11, "Return the larger of the two, but as a positive number," could mean
`abs(max(a,b))` (the larger value, made positive) **or** `max(abs(a),abs(b))` (which is
the larger of the two absolute values). For inputs `-5` and `2`, the first gives `2` and
the second gives `5` — a real difference. We intended request 11 to mean
`max(abs(a),abs(b))` (i.e. `cond_abs_max`, the operation it maps to), and we scored it
that way, but a reader could legitimately read it either way. So we flag it rather than
treat request 11 as a crisp test. (For the record, the ambiguity does not change the
outcome — the model produced nothing valid — but it matters for interpreting *why*, and
it is exactly the kind of wording an external evaluator would trip on.)

This is the surface-tiedness finding (the reworded 0.000 above) reproduced on
*hand-written, out-of-distribution* phrasing. A caveat worth stating: 16 convenience
prompts is a useful sanity check, not a statistically representative estimate of
real-world performance. We also note that hand-writing a prompt independently of the
generator is **not** the same as having an *independent external evaluator* who also
scores it — so the human set is a sanity check on phrasing, not a second, independent
implementation of the judge. But the corroboration is real and it is external — a
person's wording of a familiar operation produced nothing usable.