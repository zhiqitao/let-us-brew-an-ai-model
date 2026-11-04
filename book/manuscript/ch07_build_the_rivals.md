# 7. Build the Rivals

A model that scores 90% sounds impressive — until we ask the hard question: *could a
much simpler machine do the same thing?* This chapter is about building those simpler
machines, our **rivals**, and why they are the most important comparison in the book.

## The principle

![The rivals](figures/fig_rivals.pdf)

The template and the retrieval baseline are *sanity checks*, not a score ceiling. Our
model is drawn next to them for comparison: it has to clear them to be worth anything,
but beating a baseline is never a bad result — it just needs to be interpreted
correctly.

The value of a neural model's success is judged *relative to a baseline*. If a
hand-written rule or a lookup table solves the task as well as the trained model, then
the model isn't demonstrating capability — it's re-deriving something simpler. The
baselines are what turn "the model works" into "the model does more than a simpler
machine could." But a baseline is not a *ceiling* a result must sit below: a strong
model beating a baseline is a good outcome. The baselines tell us *whether the task
was already easy for a simpler machine*, which is the information we need to
interpret the model's score — they do not cap how good a model is allowed to be.

This is a point that deserves to be stated bluntly, because it is easy to overlook: a
number in isolation is almost meaningless. "The model solved 90% of the problems"
sounds like a triumph. But if a ten-line lookup table also solved 90%, the model's
result shows **no demonstrated advantage over that baseline** — it does not prove the
model has no learned capability, but it does mean we cannot credit the score to
learning rather than to the task simply being easy. The baseline is what gives the
number its meaning.

This is the single question the whole book keeps asking:

> **Could a much simpler machine do this?**

And it is remarkable how often the answer is "yes" at first. That is a feature of the
investigation, not a defect. Finding that the task is too easy for a simple machine
tells us exactly how to make it harder, which is how the whole brew progresses.

## Rival 1 — the template / rule system

Our simplest rival is a deterministic pattern-matcher. It recognizes known keywords in
the specification — "sum" → addition, "maximum" → max, "length" → list length — and
emits the corresponding predefined code template. It does no learning whatsoever. It
is, in the most honest sense, *dumb* — a set of hand-written if-then rules.

This rival answers: *how much of the task is solvable WITHOUT learning?* If a keyword
recognizer does fine, then the task's "hard part" is just pattern-matching, and a model
learning it isn't learning much.

Building this rival is almost too easy. It is a few rules that map common words to
common code. But its simplicity is precisely its value. It is a **specific, hand-written
alternative** against which to measure the learned model. Be clear about what this
baseline does and does not establish. It is **not** a lower bound on all possible rule
systems, and it is **not** a limit on what a simpler machine could do — it is one
particular rule table, worth the keyword → code mappings it happens to encode. If our
learned model cannot beat *this* baseline, we learn an important, but narrow, fact: the
task does not require the extra machinery, at least relative to *this* alternative. That
is a statement about the task and this specific baseline (it is easy for this rule table),
not a statement that no learning occurred, and not a statement that no other baseline
exists. The model may well have learned; it is just not learning anything *beyond* what
this particular set of rules gives us.

## Rival 2 — retrieval

Our second rival is even more interesting. A **retrieval** system builds a simple
TF-IDF index over the training prompts. Given a new task, it finds the most similar
training example and *reuses that example's code*.

This rival answers: *can apparent neural competence be explained by retrieval?* If the
test set is close enough to the training set, a lookup that does nothing but find the
nearest example will do perfectly — and a model that also scores high might just be
doing the same thing in a more complicated way.

The retrieval rival is the more insidious of the two, because it is the one that
threatens the model's success most directly. A template system shows whether the task
is trivially pattern-matching. But a retrieval system probes something subtler: whether
a model's score could be explained by *surface similarity to training data*. If a TF-IDF
lookup can find a near-duplicate prompt and reuse its answer, then a neural model
scoring similarly might be doing exactly that — matching surface form, not
understanding. Retrieval is the closest thing we have to a detector for "the model is
just copying."

## Why these two matter

These two rivals are the scientific controls. Together they bound what any result
means:

- If the **template** baseline is high, the task is pattern-recognizable — the model's
  win is shallow.
- If the **retrieval** baseline is high, the task is near-duplicate-solvable — the
  model's win may be memorization or surface similarity.

And the third possibility is the one that matters most: **if the model falls *below*
both baselines under some change, we have found a genuine limit of the model's
learning.** The rivals are a reference point, not a ceiling to beat; they reveal
when the neural model is doing something *no simple machine can do* — and, more
valuably, when the neural model has become *worse* than a simple machine, which is a
powerful signal of surface-tied, non-general learning.

Our experiments produced exactly this signal. On the pilot, retrieval scored **1.000**:
a lookup table solved the whole test set. That told us — correctly — that the task
was too easy to force generalization, and we had to make it harder. The rivals did
their job: they caught that the impressive-sounding model was being tested on a task
that didn't require much learning.

Then, in the surface-generalization chapter, the story inverted. Under a *wording*
change, the model collapsed to **0.000** while the template system, which recognizes
keywords and is indifferent to exact wording, rose to **0.875** (from 0.800
in-distribution). Here the rivals
were not a ceiling — they were a *floor*, and the model fell through it. That was the
most informative result of the experiment: it showed that the model's apparent
capability was tied to exact surface form in a way that even a dumb rule system was
immune to.

## Comparability, stated once and applied everywhere

Whenever a model score is set beside a baseline's, three things are held fixed and
reported alongside the number:

- **Same test membership.** The model and both rivals are scored over the *identical*
  task set — the same records, the same hidden tests, the same judge, the same grading
  path. Our scoring helper evaluates MODEL, TEMPLATE, and RETRIEVAL in one pass over the
  same test tasks, so a difference between the numbers cannot come from a difference in
  what was graded.
- **Same prompt exposure at evaluation.** Each system receives exactly the same test
  prompt and nothing else — no hidden tests, no task ID, no reference program. Each
  system's exposure to *training* prompts is different by construction and is stated
  wherever it matters: the model trained on those prompts, the retriever indexes those
  same prompts, and the template rival carries no prompt store at all.
- **Same generator access.** All three draw their programs from the same generated
  corpus: the template rival calls the teacher's own reference generator, the retriever
  reuses training reference programs, and the model trained on that data. None of them
  gets an outside corpus or a hand-written solution library.

One asymmetry we cannot remove and do not pretend to: **the baselines can be advantaged
by domain knowledge.** The template rival's keyword table ("sum" → addition,
"length" → list length) is knowledge we wrote down by hand — the same knowledge a reader
brings to the task — while the model has to induce that association from data. So a
baseline score is not a neutral floor: it can reflect understanding planted in it by its
author. That cuts in the direction of making the baseline *harder* to beat, not easier,
and it is one more reason we read a baseline as a sanity check on the *task*, never as a
measure of learned capability.

## The lesson

A neural model is not impressive merely because it works. It is impressive only when it
does something a simpler machine cannot. Every result in this book is therefore
interpreted relative to these rivals — and the moments where the model *falls below*
them are some of the most informative results of all.

The deep takeaway is that baselines are not a formality or a box to tick. They are the
reference frame that gives every measurement its meaning. Without them, a score is just
a number. With them, a score becomes a claim we can interrogate. And building rivals
that are *deliberately simple* is what makes them a strong test: the simpler the
machine that can match or beat the model, the more damning (or the more shallow) the
model's achievement turns out to be.
