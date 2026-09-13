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
worth pausing on before we look at any number. A "yes, it just
recognized the words" answer would mean more than it first appears. It would mean that every high score the model
achieved — every impressive in-distribution number — was not evidence of learning at
all. It was evidence of association. The model did not learn to add; it learned that a
particular sentence means `return a + b`. That is a completely different claim, and it
is the one we need to test.

## The design: change what shouldn't matter

To find out, we run the **surface-generalization** test. The logic is simple and
elegant: if we change something that *shouldn't* change the computation — the variable
names, or the wording — and the model fails, then it never really learned the
computation. It learned the phrasing.

The key is choosing *what* to change. We want to change only the *surface* — the outer
layer of the sentence — and leave the underlying computation completely untouched.
Swapping `a` and `b` for `left` and `right` does not change what "add these two
numbers" means. Rewording "their sum" as "the total" does not change the operation.
If the model truly understood addition, neither change would matter. If it merely
memorized a sentence, either change would break it. That asymmetry is exactly what we
measure.

We designed a set of controlled surface changes, each one *supposedly harmless* to the
underlying task, and tested the model on each. This is the crux of the book's approach
to generalization: we do not just ask "does it work?" We ask "does it survive the
changes that a genuinely-general system should shrug off?"

## The setup

We trained the model on arithmetic primitives, but only with **letter names** (`a`, `b`)
and only a **subset of the wording** used to describe each operation. Then we re-asked
the *identical* task three different ways and watched whether the model's ability
survived.

## The result

| Test | **MODEL** | TEMPLATE | RETRIEVAL |
|------|-----------|----------|-----------|
| Same as training | **0.900** | 0.800 | 1.000 |
| Same computation, `a,b` → `left,right` | **0.350** | 0.800 | 0.683 |
| **Same computation, reworded** | **0.000** | 0.875 | 0.125 |

Look at what happens when we touch only the *surface*, not the math.

- **New variable names.** The model was trained on `a` and `b`. We ask the same
  question with `left` and `right` — the *identical* operation. Performance collapses
  from **0.900 to 0.350**.

- **Reworded instruction.** We say the exact same problem using a phrasing the model
  never saw during training. Performance drops to **0.000**.

So the model that scored 0.900 on the familiar phrasing falls to 0.350 when the
variable names change, and to 0.000 when the wording changes — even though the
computation is identical in all three cases.

## The damning comparison

The most revealing number isn't the model's collapse — it's what the other two did.
![Surface generalization](figures/fig_surface.png)

*Each pass@1 is over 100 held-out problems per condition; the "new wording" column is
the Stage-3 genuine held-out wording family (train × holdout prompt overlap = 0, see
the novelty audit in Appendix C), and decoding is temperature-0.8 single-sample.*

When we change the *words*, the **template baseline gets *better*, not worse** (0.875,
up from 0.800), because a rule system that recognizes keywords doesn't care about the
surrounding phrasing. The **retrieval baseline** also falls (0.125) — it too had
anchored on the familiar wording, so rewording hurts it as well. Only the learned model
is *catastrophic* here (0.000). This is the cleaner reading: identifier changes
(`a,b` -> `left,right`) left retrieval strong (0.683), but rewording broke both the
learned model and the retriever.

So the model's 0.900 in-distribution score was largely **phrasing memorization**. It
had learned "this exact kind of sentence maps to that program." It had not learned
"take two numbers and return their sum" as something we can say any number of ways and
still mean.

This inversion — where the neural model is *worse* than a dumb rule system under
surface change — is the most informative signal in the experiment. It is not a
competitive defeat; it is a diagnostic revelation. The dumb template system is
indifferent to exact wording because it never learned to associate wording with
meaning in the first place; it just recognizes keywords. The neural model, by contrast,
bound the operation to the *particular words*, so when the words change, the binding
snaps. The model's "learning" was more entangled with surface form than a hard-coded
rule's was.

## The brewing experience

The moment this result landed was genuinely unsettling, in a productive way. We had
just celebrated the 0.900 in-distribution score — the model, we thought, could "add."
Then we reworded the same problem and the floor fell out. The 0.900 had been real, and
it had been *narrow*. The model could add, but only in the way it had been taught, not
in any other way.

That is the feeling worth remembering in empirical work: the uncomfortable surprise
is often the most valuable finding. It would have been easy to stop at "the model
scores 0.900, success." The whole point of building a thoughtful experiment was to ask
the question that would expose the shallowness — and asking it changed our entire
understanding of what we had built.

## The shortcut audit

1. **Suspected cheat: phrasing memorization.**
   **Why it fits:** the model tied training phrasings to code.
   **Control:** held one whole phrasing style out of training, tested on it.
   **Result:** 0.000.
   **Ruled out:** that the model is grounded in the computation.
   **Still open:** is it the wording pattern or the new vocabulary? Need a
   surface-control to separate them.

2. **Suspected cheat: name memorization.**
   **Why it fits:** trained on `a,b`, maybe it hardwired those labels.
   **Control:** retest on `left,right`.
   **Result:** 0.350 — a big but partial drop.
   **Ruled out:** pure name-memorization (it still fails partly, but names aren't the
   whole story).

## The honest takeaway

A model that scores 0.900 on familiar phrasings and 0.000 on a rewording of the same
problem has not generalized to the *problem*. It generalized to the *phrasing*. That's
the difference between "the model works" and "the model works when I say it the way I
said it in training" — and it's the most important lesson of the generalization
chapters.

The sharpest way to state it: the model did not learn *addition*. It learned the
*word "sum"*. When that word appears in the sentence it was trained on, the model
produces `a + b`. When the same meaning arrives in different words, the model has no
idea what to do. And that is the difference between a system that understands and one
that merely recites.

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

Against the pilot checkpoint, the model solved **0 of 16**. Breaking it out, it solved
**0 of 10 primitive** requests and **0 of 6 composite** requests. Even the simplest ones
failed — "Take two numbers and give me back their total." produced malformed code;
"Tell me which of these two is the bigger one." produced `def solve(a): return a a a
+ a - b`. None produced a valid program.

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
