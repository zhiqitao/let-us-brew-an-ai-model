---
title: "Let us brew an AI Model"
subtitle: "What tiny language models can actually learn when given one job"
author: "Zhiqi Research"
---



\newpage

# 1. Let Us Brew an AI Model

**Working subtitle:** What tiny language models can actually learn when given one job.

---

A tiny model appears to solve a programming problem. It reads a sentence — *"Write a
function that takes two numbers, a and b, and returns their sum."* — and produces
just the right Python:

```python
def solve(a, b):
    return a + b
```

We run the hidden tests. It passes all of them. If this were a demo, we'd celebrate
and move on.

But this book is not a demo. So instead of celebrating, we ask the question that
everything in this book hinges on:

> **Why did it answer correctly?**

Maybe it genuinely learned the mapping from the words "sum" and "a and b" to the
computation `a + b`. Or maybe it memorized the exact sentence from training. Or
maybe it recognized this as a near-duplicate of an example it saw, and copied the
reply. Or maybe a simpler machine — one that does nothing but look up the closest
training example — could have done the same thing. Or maybe the test only looked
hard to pass.

The difficult part is not making the model answer. The difficult part is **knowing
why it answered.**

## The one-job constraint

This book gives a small language model exactly one, narrowly defined, objectively
testable job:

> **natural-language specification → Python program**

A model receives a description of a programming task and generates a solution. The
program is executed against hidden tests. That single choice — *executable output +
hidden tests* — is what makes this an experiment rather than a demo, because it gives
us things an ordinary language-model toy rarely does:

- deterministic inputs
- executable outputs
- objective evaluation
- synthetic data generation
- controlled difficulty
- hidden tests
- compositional splits
- memorization tests
- shortcut audits
- reproducible experiments

## What this book is (and is not)

This is **not** a transformer tutorial, and it is **not** a guide to building a
chatbot, an agent, a coding assistant, or a frontier model. It is a controlled
empirical investigation: *how much structured programming capability can a small
language model actually learn, and how can we tell whether it learned it rather than
memorized it or exploited a shortcut?*

The model is the instrument. The experiment is the subject.

## The difficult part

A natural first reaction is: "building a small model is the hard part." It isn't.
Once the laboratory works, a ~0.9M-parameter model will reliably map a handful of
programming sentences to correct Python in-distribution. That part is almost easy.

The hard part is everything after: proving the model didn't just memorize, testing
whether it generalizes when you change the *wording* but not the *computation*,
testing whether it can *combine* two things it knows into something it never saw, and
auditing the evaluator to make sure the number it reports is trustworthy.

This book builds a laboratory, runs those experiments, and reports exactly what
happened — including the places where the model fell flat and where our own
evaluator turned out to be wrong.

The model was the instrument. The experiment was the subject. Let's brew.


\newpage

# 2. What Does It Mean to Learn?

We are going to use a word a lot in this book: *learned*. Before we do, we have to
be precise about what it means. "The model learned to add" is a sentence many
readers would accept. That acceptance is exactly the problem.

## An operational definition

We will not use "learning" as a philosophical term. For this book, a model
demonstrates learned capability when **all** of the following hold, to the degree
the evidence supports:

1. **Performance improves systematically during training** — the loss goes down, and
   the behavior we care about reliably improves.
2. **Performance transfers to held-out examples** — it works on instances it never
   saw, not just the ones in training.
3. **Performance survives controlled changes to superficial features** — things like
   a different variable name, a different wording, or a harmless distractor, none of
   which should change the underlying computation.
4. **Performance survives appropriately designed structural changes** — it can
   combine known pieces in a new arrangement, not just reproduce arrangements it
   already saw.
5. **Simpler explanations have been tested and rejected.** The alternatives —
   exact memorization, retrieval of a near-duplicate, a template, dataset leakage, or
   an evaluator artifact — must be ruled out to the degree the experiment supports.

This definition is deliberately limited. We do not claim to determine whether the
model "understands" programming in a philosophical sense. We ask narrower,
answerable questions: *does it generalize? to what? and can a simpler mechanism
explain the result?*

## The four-level generalization spectrum

This is the book's central conceptual framework, and we will use it to organize most
of our experiments. It is a spectrum of *how* a result could have been obtained, from
the least to the most demanding.

**Level 1 — Memorization.** The model reproduces or exploits information closely
represented in training: an exact example, an exact constant, a familiar template,
memorized wording, a near-duplicate. Question: *can the result be explained by
remembering?*

**Level 2 — Distributional generalization.** The model succeeds on new examples
drawn from essentially the same distribution. It has seen the operation and the
frontier of *which* words and values, but not these exact instances. Question: *can
it perform on unseen instances of the same task?*

**Level 3 — Surface generalization.** The underlying problem is unchanged, but
superficial properties change: new constants, new variable names, new function
names, paraphrased wording, reordered clauses, harmless distractors. Question: *does
the capability survive changes that should not alter the computation?*

**Level 4 — Structural generalization.** The model must combine known components in
structures that were not present during training. If it was trained on `A`, `B`, and
`C`, can it do `A`-inside-`B`, or `B`-and-`C`, or `A` applied to the result of `C`?
Question: *can it compose learned capabilities, or only reproduce learned
combinations?*

**A rule we will follow strictly:** never collapse these four levels into a single
"generalization" number. A model that scores 90% "in-distribution" and 0% "on new
wording" has not generalized; it has memorized the phrasing. Reporting one number
would hide exactly the thing we most want to know.

## The recurring shortcut audit

Because we refuse to trust a single number, every major experiment in this book asks
the same question:

> **How could the model have gotten this result without learning what we think it
> learned?**

The candidate shortcuts are always the same list: memorized templates, memorized
constants, memorized identifiers, memoriized function names, wording artifacts,
sentence-length artifacts, dataset imbalance, train/test leakage, near-duplicates,
reference-solution artifacts, retrieval, evaluator weaknesses, hardcoded answers,
hidden-test leakage, output-format artifacts.

Every major experimental chapter therefore contains a **shortcut audit** with six
parts: (1) the suspected shortcut, (2) why it could explain the result, (3) the
control experiment, (4) the result of that control, (5) what the control rules out,
and (6) what remains unresolved.

This audit — not the headline accuracy — is the book's signature. It is the
difference between "the model works" and "we know why the model works."


\newpage

# 3. Give the Model One Job

Before we can run any experiment, we have to define the task so precisely that a
machine can execute it and we can objectively score it. This is the discipline that
makes everything after possible. Vague tasks give vague answers; a task with
deterministic inputs, executable outputs, and hidden tests gives crisp, auditable
answers.

## The task

The model receives a **natural-language specification** of a programming task and
must produce a **Python program** that solves it. That program is then executed
against hidden tests.

Concretely, the model sees something like:

> "Write a function that takes two numbers, a and b, and returns their sum."

and must produce:

```python
def solve(a, b):
    return a + b
```

We score it by running that program against a set of hidden test cases (inputs with
expected outputs) and checking whether the program's output matches, semantically,
for every case.

## The task schema

Every task is described by a small, formal schema — the ground truth that drives
everything. The key insight is that **one semantic record generates all three**
things we need: the reference program, the natural-language spec, and the hidden
tests. That way there is no drift between "what the task is" and "how we ask for it"
and "how we test it."

The semantic core captures the operation and its arguments:

```json
{
  "operation": "add",
  "args": [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}],
  "output_type": "int"
}
```

From that single record, the teacher generates:
1. the reference Python (`def solve(a,b): return a+b`),
2. a natural-language specification (in one of several phrasings),
3. a set of hidden tests (ordinary, zero, negative, boundary, large cases).

## The pure-function constraint

For the pilot we constrain the generated programs to be **pure functions**. No side
effects, no file I/O, no randomness. This makes evaluation deterministic and
unambiguous: for a given input, there is one correct output. It is a deliberate
simplification, and it is exactly what makes the task cleanly measurable.

## Hidden tests

The hidden tests are the heart of evaluation. Each task carries an independent set of
test cases designed to catch real errors, not just a single happy path. For an
arithmetic task we include ordinary values, zero, negatives, boundary values, and
large-magnitude values. The tests are generated independently of the reference
program's *logic* — computed from the semantics, not copied from the solution — so
that a model that merely memorizes the reference still can't predict the exact test
suite.

## The success criterion

For a single problem, the success criterion is:

> **Problem-level hidden-test pass@1** — did the one program the model produced pass
> *every* hidden test for that problem, under deterministic/greedy decoding?

This is deliberately strict. A program that passes 7 of 8 hidden tests *fails* the
problem. That strictness is what keeps the measurement honest: we are not measuring
"close," we are measuring "correct."

## Why this specific task

Natural-language-to-Python is a good laboratory task precisely because it has
everything a controlled experiment needs:

- **Deterministic.** Same spec, same program, same tests.
- **Executable.** We run real Python and compare real outputs.
- **Objectively scorable.** Pass/fail, no judge-subjectivity.
- **Synthetic.** We can generate as much controlled data as we want.
- **Controllable difficulty.** We can escalate from `a+b` to compounded operations.
- **Compositional splits.** We can train on pieces and test on unseen combinations.
- **Memorization tests.** We can plant canaries and check for exact reproduction.
- **Auditable.** We can inspect the exact generated program and run shortcut audits.

The model could not ask for a clearer job. Now we have to build the tools that let us
run and score it: a controlled world, a teacher, a judge, and rivals.


\newpage

# 4. Build a World We Can Control

The model will produce Python. Before we trust anything it produces, we need a way to
run that Python safely and *deterministically* — and to decide, precisely, what is
allowed. This is the **sandbox**: the "world" in which the model operates.

## The principle: whitelist, not blocklist

The naive way to constrain a program is a blocklist: deny `import`, deny `eval`, deny
`open`. Blocklists are fragile — there is always some construct you forgot. The
robust way is the opposite: **an allowlist**. We parse the program to an abstract
syntax tree, and if any node type is not *explicitly permitted*, we **reject the whole
program.**

This is the key design decision. The sandbox does not try to catch "bad" programs; it
states upfront exactly what is allowed, and everything else is refused. If the model
emits even one disallowed construct — an `import`, a `class`, a `try`, a
comprehension, an `eval` — the program is rejected before it ever runs.

## What's allowed (the capability spec)

For the pilot we whitelist a deliberately small subset of Python:

- literals (integers, floats), variables, assignment, `return`
- arithmetic: `+ - * / // % **`
- comparisons, boolean operators
- `if / elif / else`, `for`, `while`, `break`, `continue`, `pass`
- lists, indexing, slicing
- a small set of built-ins: `abs, min, max, sum, len, range, int, float, round`
- simple `def` functions

Everything else is rejected: imports, file I/O, network, subprocess, `eval`/`exec`,
`class`, `try/except`, arbitrary attribute access, comprehensions, lambdas.

The crucial point is that the model is *only ever* allowed to emit this subset. This
is the controlled world, and the capability spec is versioned so we can track how it
grows across the book.

## Resource and determinism policy

Beyond what's allowed syntactically, we also control *how* the program may run:

- maximum AST depth and program length,
- maximum nesting,
- a hard execution timeout,
- recursion protection,
- float-comparison tolerance,
- **no randomness, no time, no environment access** — the world is deterministic.

A program with the same input must always produce the same output. That is what makes
the experiment clean.

## The pipeline

```
source -> parse -> AST -> whitelist validation -> compile -> restricted execution
        -> semantic comparison
```

Validation happens on the tree *before* execution, so disallowed code never runs.
Execution uses a stripped set of globals that exposes only the allowed built-ins.

## An honest caveat

This sandbox is a **teaching and evaluation** sandbox. It is deliberately strict about
the capability subset, but it is not a claim of production-grade adversarial
isolation. The distinction matters: we are not trying to secure a server against a
hostile attacker; we are trying to run generated code and measure whether it does what
we asked. The book states this limitation clearly rather than overstating what the
sandbox guarantees.

## Why this matters

The sandbox is the foundation of trust in every later result. If the sandbox leaked —
allowed something disallowed, or failed to be deterministic — every score in the book
would be suspect. That is why we test it so thoroughly, and why the very first thing
we verify is that it correctly **rejects** the constructs it must reject: imports,
`eval`, classes, `try`, comprehensions, lambdas. A sandbox that only permits is easy;
a sandbox that also correctly refuses is the real achievement.


\newpage

# 5. Build the Teacher

We need data. But the kind of data we need cannot be scraped from the internet — it
has to be *engineered* so that we can control exactly what the model is and isn't
exposed to, and so we can carve it into generalization tests. That is the role of the
**teacher**, the dataset generator.

## Semantic-first

The most important design decision is the direction of generation. We do **not** start
with "here's a sentence, let me write code for it." We start with the **meaning**, and
generate everything else from it — so that the reference code, the natural-language
spec, and the hidden tests all agree, because they are all the same semantic record
rendered three ways.

```
SEMANTIC INTENT
   -> PROGRAM STRUCTURE
      -> REFERENCE CODE
      -> NATURAL LANGUAGE
      -> HIDDEN TESTS
```

The semantic core is minimal for the pilot:

```json
{"operation": "add", "args": [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}]}
```

From this one record, the teacher produces:
1. the ground-truth Python,
2. a natural-language prompt (in one of several phrasings),
3. a set of hidden tests.

## Maximizing controlled diversity

A good generator does not just produce many examples; it produces *diverse* ones while
keeping the semantics fixed. We deliberately vary:

- **constants** — different values, so the model can't memorize outputs,
- **identifiers** — `a,b` vs `left,right`, so it can't associate the operation with
  particular names,
- **wording** — several template families per operation, so it sees the same
  instruction said many ways.

This diversity is what later lets us run surface-generalization tests: because we
control *how* we vary the surface, we can also *hold it out* and test whether the
model generalizes.

## Avoiding accidental correlation

The danger in any generated dataset is **accidental correlation** — a pattern that
makes the answer trivially predictable from the surface. Classic examples:
every addition uses the word "total"; every maximum uses variable `x`; every loop is
exactly one sentence long. If those correlations exist, a model (or a trivial
classifier) can solve the task without learning the computation.

We deliberately break these correlations and then — crucially — **audit for them**.

## The leakage audit

Before trusting any dataset, we ask: *can a trivial classifier predict the answer from
the surface alone?* We train a TF-IDF + logistic-regression model on the natural-
language specs and see how well it predicts the target operation.

And it *caught* something. On our first pilot renderer, a trivial classifier predicted
the operation from the wording with **100% accuracy**. That is a red flag: it means
the wording leaked the answer, so a model that "succeeded" might just be exploiting
the phrasing.

This is a crucial, early win for the methodology. We did not sweep the leak under the
rug; we recorded it as a findable artifact (finding-001) and noted exactly what it
means for downstream experiments: the pilot wording is too predictable for
*generalization* experiments, so we must add many more paraphrase families and hold
them out before any surface test.

## The lesson

The teacher is not a bulk-data tool; it is a controlled instrument. Its job is to
produce data with *controlled* diversity and *audited* cleanliness, so that when the
model succeeds, we can attribute the success to learning the computation — not to the
data accidentally revealing the answer. And when the data *does* leak, we want to find
out ourselves, before the model does.


\newpage

# 6. Build the Judge

We need a way to decide whether a generated program is correct. This is the **judge**:
an execution-based evaluator. Getting it right is not a detail — the judge is the
instrument whose readings the whole book depends on. If the judge is wrong, every
number is wrong. So we build it carefully, and then we attack it.

## The four-stage pipeline

We score a candidate program through four stages; a later stage only matters if the
earlier ones pass.

1. **Syntax pass** — does the program parse as valid Python?
2. **AST / capability pass** — is every node within the whitelisted subset? If the
   program smuggles in an `import`, it is rejected here.
3. **Execution pass** — does it compile and run without error under the restricted
   environment?
4. **Semantic pass** — for each hidden test, does the program's output match the
   expected output?

The primary metric is **problem-level hidden-test pass@1**: did the one program
produced pass *every* hidden test for that problem?

## Semantic comparison: don't trust string equality

A naive evaluator would check `output == expected`. That fails in subtle ways. Two
programs can produce the "same" result that isn't string-equal: floats with rounding,
a dict with keys in a different order, nested structures. So the judge uses a proper
**semantic comparator**:

- integers compared exactly,
- floats compared with an explicit tolerance,
- booleans compared as booleans (not as 0/1),
- lists compared element-by-element, recursively,
- dictionaries compared key-insensitively (order doesn't matter),
- nested structures compared recursively.

The comparator itself is tested — we don't assume it's right just because it's simple.

## Mutation testing: red-teaming the judge

The most important step is treating the judge as something that must be *proven*
sound. We **mutate** the reference solution into deliberately-broken versions and ask:
*does the judge catch them?*

We generate mutants such as: `+` → `-`, `>` → `>=`, remove the `return`, swap the
arguments, off-by-one a loop boundary, use the wrong variable. Then we run each mutant
through the hidden tests. A good test suite **rejects** an obviously-wrong mutant. A
weak test suite lets it pass.

The mutation score — the fraction of wrong mutants the tests catch — is a measure of
how much we can trust the judge. If an obviously-broken program passes our tests, the
tests are too weak, and we add more until they discriminate.

## We caught our own judge being wrong

Here is what makes this chapter honest rather than aspirational: the very first time
we evaluated our model, it **scored 0.000** — reported a total syntax failure on
every problem. And the model wasn't wrong. The *judge* was.

The root cause was a generation bug on our side: the model produced a complete, correct
program, but it was followed by padding (null bytes), and `ast.parse` rejects null
bytes. So the judge scored a perfectly valid program as a syntax failure. Once we
truncated the padding, the model's true score emerged: **0.897**.

That moment is worth more than any passing test. It is the book's core lesson applied
to ourselves: **never trust a number from a system you haven't audited.** If we had
taken the first 0.000 at face value, we'd have concluded the approach failed. Instead,
finding the judge's bug told us the truth — the model was actually working.

## The honest summary

The judge is not a helper; it is the instrument whose readings we stake the book on.
So we built it strictly (four stages, semantic comparison, tested comparator), then
we red-teamed it (mutation testing), and then — when it gave a suspicious answer — we
attacked it until we found our own bug. Only a judge that survives that scrutiny
deserves to be trusted.


\newpage

# 7. Build the Rivals

A model that scores 90% sounds impressive — until you ask the hard question: *could a
much simpler machine do the same thing?* This chapter is about building those simpler
machines, our **rivals**, and why they are the most important comparison in the book.

## The principle

The value of a neural model's success is judged *relative to a baseline*. If a
hand-written rule or a lookup table solves the task as well as the trained model, then
the model isn't demonstrating capability — it's re-deriving something simpler. The
baselines are what turn "the model works" into "the model does more than a simpler
machine could."

This is the single question the whole book keeps asking:

> **Could a much simpler machine do this?**

## Rival 1 — the template / rule system

Our simplest rival is a deterministic pattern-matcher. It recognizes known keywords in
the specification — "sum" → addition, "maximum" → max, "length" → list length — and
emits the corresponding predefined code template. It does no learning whatsoever.

This rival answers: *how much of the task is solvable WITHOUT learning?* If a keyword
recognizer does fine, then the task's "hard part" is just pattern-matching, and a model
learning it isn't learning much.

## Rival 2 — retrieval

Our second rival is even more interesting. A **retrieval** system builds a simple
TF-IDF index over the training prompts. Given a new task, it finds the most similar
training example and *reuses that example's code*.

This rival answers: *can apparent neural competence be explained by retrieval?* If the
test set is close enough to the training set, a lookup that does nothing but find the
nearest example will do perfectly — and a model that also scores high might just be
doing the same thing in a more complicated way.

## Why these two matter

These two rivals are the scientific controls. Together they bound what any result
means:

- If the **template** baseline is high, the task is pattern-recognizable — the model's
  win is shallow.
- If the **retrieval** baseline is high, the task is near-duplicate-solvable — the
  model's win may be memorization or surface similarity.

Our experiments produced exactly this signal. On the pilot, retrieval scored **1.000**:
a lookup table solved the whole test set. That told us — correctly — that the task
was too easy to force generalization, and we had to make it harder. The rivals did
their job: they caught that the impressive-sounding model was being tested on a task
that didn't require much learning.

## The lesson

A neural model is not impressive merely because it works. It is impressive only when it
does something a simpler machine cannot. Every result in this book is therefore
interpreted relative to these rivals — and the moments where the model *falls below*
them (as in the surface-generalization chapter) are some of the most informative
results of all.


\newpage

# 8. The Smallest Brain

Now we get to the student. Everything so far — the world, the teacher, the judge, the
rivals — exists to ask one question about this thing. So let us meet it.

## What it is

The student is a deliberately simple, transparent **decoder-only transformer**. The
goal is not novelty; the goal is that we can understand exactly what it is doing. A
20-layer exotic architecture would be a black box; a clean, standard transformer is
one we can reason about.

For the pilot, the configuration is small and honest:

- vocabulary: ~291 tokens (a compact BPE trained on the task corpus),
- hidden dimension: 128,
- layers: 4,
- attention heads: 4,
- context length: 128,
- GELU activation, Pre-LayerNorm, AdamW optimizer.

## The honest parameter count

A common mistake is to quote just a round "10M parameters." We refuse to hide the
important part. The model has **884,224** parameters, of which only **830,592** are
the actual computation. The other **53,632** are the **embedding** — and the
embedding is often the silent dominant term in a tiny model. If you don't separate
them, "0.9M parameters" can mislead: a big fraction might just be storing the
vocabulary, not doing any computation.

So we always report the split: embedding vs. non-embedding.

## The architecture smoke test

Before we train it for real, we run an **architecture smoke test** — a tiny, fast check
that the model's forward and backward passes work, that the parameter count is what we
expect, and that the initial loss is sensible (roughly the log of the vocabulary, since
a fresh random model's best guess is uniform).

This is the same discipline as the very first smoke test, but one level up: we are not
checking "does the loop run?" anymore, we are checking "does *this model* construct and
train correctly?" A 20-second check here prevents discovering a shape bug hours into a
real run.

## Why it's small

The book deliberately keeps the pilot model tiny. This is not modesty; it is method. A
small model is fast to train (so we can iterate on the *experiment*, not wait for the
model), transparent (so a failure is a learning-system problem, not an architecture
mystery), and it makes the *boundary* more visible — a small model that fails to
compose tells us something cleaner than a large model that does something

partly and noisily. We scale it up later precisely to test whether capacity matters,
but the baseline has to be small and legible.

## The configuration is a starting point, not a fact

Crucially, none of these numbers are immutable. The exact architecture is an
experimental variable. Every architectural choice requires a reason, and the question
is never "what architectures can we try?" — it is "what scientific decision does this
comparison enable?" For the pilot, the answer is: this size is fast enough and small
enough to be legible, which is what Stage 0–1 needs.


\newpage

# 9. The First Brew

Everything is built. Now we train the model for the first time, and watch what
happens. This chapter is deliberately underlined and unheroic: the goal is not a
triumphant result, but to establish that the experimental loop works and to see the
model's honest behavior as it learns.

## The data

1400 generated tasks: a natural-language specification paired with its reference
Python program. The model's job is to read the spec and produce the code.

## Training

We train with a standard next-token objective: the model sees the prompt and the
reference program as one sequence, and learns to predict each token given the ones
before it. We use AdamW, batch size 16, learning rate 1e-3, for 1500 steps.

The training loss descends smoothly:

```
step    0   loss 5.84
step  200   loss 0.029
step  400   loss 0.022
step  600   loss 0.023
step  800   loss 0.020
step 1000   loss 0.021
step 1200   loss 0.019
step 1499   loss 0.019
```

That is a large, clean drop — from 5.84 to 0.019 in 1500 steps. A loss that low means
the model can predict the next token of this (prompt, program) sequence almost
perfectly on the training set.

## The honest caveat

A falling training loss — and even a very low one — is *not* evidence of learning. We
saw this in the pilot and it is the book's recurring motif. The training loss tells us
the model fits the training data. It does not tell us it can *generalize* to unseen
problems, or that it learned the computation rather than the surface form.

So after training, the only losses that matter are the *held-out* ones: how well does
the model do on problems it never saw? That is Chapter 10's question, and the answer
there is the real measurement of this brew.

## What this chapter establishes

This first brew is not a result; it is a proof of the loop. We have:

- trained a real model on real data,
- watched its loss descend smoothly,
- saved a checkpoint,
- confirmed that we can take the trained model and produce code for a new prompt,
  run it through the sandbox, and score it with the judge.

That loop — generate data, train, generate code, execute, score — is the laboratory
working end-to-end. It is the foundation everything else stands on. The model is
built. Now we have to find out what it actually learned.


\newpage

# 10. Does It Actually Work?

We have a trained model, a judge, and a test set. The natural question is the one
the whole book has been building toward: *does it actually work?*

And the answer, as with almost everything in this book, is **"it depends on what you
mean,"** and then **"let's measure it rather than argue."**

## The setup

We trained a small decoder-only transformer on 1,400 generated tasks: the model reads
a natural-language specification and must produce the reference Python program. The
trained model is tiny — **884,224 parameters** (0.88M), of which 53,632 are the
embedding and 830,592 are the actual computation. It saw 1,500 gradient steps on a
batch of 16, reaching a training loss of **0.0208**.

We then asked it to solve 300 **held-out** test tasks it never saw, and scored each
generated program by executing it against that task's hidden tests.

## What we measured: pass@1

Here is the headline result, reported as **problem-level hidden-test pass@1 under
greedy decoding** — that is, for each problem, did the single program the model
produced pass *every* hidden test?

| Candidate | syntax | executable | **pass@1** |
|-----------|--------|-----------|------------|
| **MODEL** | 0.897 | 0.897 | **0.897** |
| TEMPLATE | 1.000 | 0.900 | 0.800 |
| RETRIEVAL | 1.000 | 1.000 | **1.000** |

Three things stand out.

**First, the model genuinely learned something.** 0.897 means that ~90% of the time,
an unseen problem's natural-language spec produced a program that passed all its
hidden tests. That is not a toy result. And crucially, it **beats the hand-written
template/rule baseline** (0.800). A hard-coded pattern-matching system that
recognizes keywords like "sum" and emits a template gets 80%; our learned model gets
~90%. So the model is doing *more* than a fixed rule system can do on this task.

**Second — but retrieval does even better.** A trivial TF-IDF retriever that does
nothing but find the closest training example and reuse its program scores **1.000**.

That second fact is not a failure; it is the single most important thing this pilot
taught us. It tells us the task, as currently constructed, is **too easy to force
generalization**. When a non-learning lookup solves 100% of the test set, then the
test set is solvable by retrieval, and a model scoring 90% is not yet being tested on
whether it can generalize — only on whether it can match the surface form of a
training example.

This is exactly the "task too easy" outcome the experimental plan anticipated, and it
is scientifically useful: it tells us *how to make the next task harder.*

## The shortcut audit

Before we trust the "0.897" number, we have to ask how the model might have gotten
there without learning.

1. **Suspected shortcut: retrieval of a near-duplicate prompt.**
   **Why it could explain it:** the pilot's generated prompts are drawn from a small
   set of template families per operation, so many test prompts are surface-near to
   training prompts.
   **Control:** we ran the retrieval baseline — 1.000. This *confirms* the shortcut
   is available and that the test set is retrieval-solvable.
   **What it rules out:** nothing yet, because the model's 0.897 is *below* the
   retrieval ceiling. It does not rule out the model partially relying on surface
   similarity.
   **What remains unresolved:** whether the model's own success is grounded in the
   *computation* or in the *surface form*. To answer that, we need the Level-3
   (surface-change) and Level-4 (composition) experiments, which we run next.

2. **Suspected shortcut: exact memorization.**
   **Why it could explain it:** the model saw 1,400 examples; maybe it memorized them.
   **Control (Ch14):** on held-out prompts it still passed 59/60, and on a *canary*
   prompt it produced the *general* program rather than a memorized literal.
   **What it rules out:** pure example-memorization.
   **What remains:** the deeper question — is the *general program* it produces
   genuinely tied to the computation, or to the particular wording?

## The honest summary

The pilot succeeded in exactly the way a pilot should: the laboratory works, the
model learns, and — perhaps most valuably — the experiment told us something
*uncomfortable but true*. The task is retrieval-solvable, and a model that beats a
template rule system yet sits below a lookup table has not yet been tested on the
thing we care about most: whether it generalizes.

That is the baseline from which every later experiment is measured. From here, we
stop making the task easier and start making it *probe* generalization.


\newpage

# 12. How Much Brain?

The most instinctive answer to "the model failed to compose" is: **make it bigger.**
More parameters, more capacity, more "brain." If a ~0.9M model can't combine what it
knows, surely a larger one can.

This chapter tests that instinct directly, and the answer is one of the cleanest
negative results in the book.

## The setup

We hold everything constant except model size. Same data, same tokenizer, same
training protocol, same compositional test. We train **two** models on the same
primitive-only training set and test both on (a) in-distribution held-out primitives
and (b) the held-out composite operations.

| Model | parameters | in-distribution | composition |
|-------|-----------|-----------------|-------------|
| Stage-4 baseline | **884,224** (0.88M) | 0.900 | **0.000** |
| Scaling | **6,500,352** (6.5M) | 0.900 | **0.000** |

That is a **7.4×** increase in parameters. Almost nothing changed.

## The result

Going from ~0.9M to 6.5M parameters:

- **In-distribution stays at 0.900.** The bigger model reproduces the primitives
  exactly as well as the small one. Capacity didn't hurt; it just didn't add anything
  here.
- **Composition stays at 0.000.** The bigger model is *just as* unable to combine two
  learned primitives as the small one. Seven and a half times the capacity bought
  exactly zero compositional generalization.

## What this means

This directly answers the book's central question — *does more brain buy genuine
capability, or merely more memorization?* — with a decisive answer at this scale:

> **It buys neither. At ~1–7M parameters, the compositional failure is invariant to
> model size.**

The boundary we found in Chapter 16 is **not a capacity ceiling**. It is a
structural/learning limit that scaling alone does not resolve. A bigger model at this
scale just does the same narrow thing slightly more efficiently; it does not develop
the ability to compose.

## The audit: is this a fair comparison?

We must be careful: a single size point doesn't prove there's no capacity curve. But
the shape of the result is telling. If capacity were the binding constraint, we'd
expect a *move* — even a small one — between 0.88M and 6.5M. We see none: composition
is 0.000 at both. And crucially, both models are already at ceiling (0.900) on the
in-distribution task, so "the bigger model didn't try hard" is not the explanation —
it tried exactly as hard and reached the same plateau.

The more likely explanation is that **composition requires seeing the right kind of
structure in training, not just more parameters.** A model that only ever sees
`add` and `abs` as separate problems has no reason to build a "compose" operator; a
7× bigger network just represents the same two reflexes more richly. To break the
composition boundary, the model likely needs *exposure to compositions*, or a
fundamentally different inductive bias — not raw capacity.

## The honest framing

This is a *useful* negative result. It tells us where not to look (raw scaling in the
1–7M regime) and points at where to look instead (structural data / inductive bias).
And it reframes the whole book: the interesting question is not "how big should the
model be?" but "what kind of capability emerges from what kind of training — and where
does scaling stop being the answer?"

The model was the instrument. The experiment — and the boundary it revealed — was the
subject.


\newpage

# 13. Same Data, More Diverse Data

Chapter 11 asked *how much* data. There is a subtler question that often matters
more: what *kind* of data. In particular, is it better to have many examples of the
same thing, or fewer examples spread across more variety?

The temptation is to treat "more data" as one lever. It isn't. There are at least two
distinct things you can add, and they behave differently:

- **more examples** — more instances of the same templates and variation, and
- **more diversity** — more distinct *kinds* of structure and wording.

The distinction matters enough that the book states it as a rule:

> **More data ≠ more information ≠ more diversity.**

## What our experiments hinted

The data-scaling curve (Chapter 11) showed that simply adding *examples* of the same
sort climbs in-distribution performance — 0.10 at 100, 0.64 at 3000. So more examples
clearly helped the model fit the pilot task better.

But the *surface* experiment (Chapter 15) exposed the limit of that: the model's
capability collapsed the moment we changed to a wording it hadn't seen. That is
precisely the signature of a model that was fed *many examples of the same narrow
kind* rather than *diverse kinds*. It learned the particular phrasings well because it
saw many of them, and it learned nothing general because the diversity was low.

In other words, the very quantity that produced the impressive in-distribution score
is what made it surface-fragile. The model was well-fed but narrow.

## The lesson

This reframes what "more data" buys. To make a capability *robust*, you need not just
more examples of a phrasing, but more *diverse* phrasings, identifiers, and structures
— enough that the model cannot tie the operation to any particular surface form. Our
experiments show the model's weakness is not a lack of data *quantity*, but a lack of
data *diversity* (or, deeper, a lack of the structural kind of data needed for
composition — see Chapter 16).

## A caution on the distinction

We have not fully separated "more examples" from "more diversity" in a single
controlled experiment — that factor is worth isolating. But the *indirect* evidence is
strong and consistent: quantity alone drove up the surface-fragile in-distribution
score, while the failures that matter (new wording, new identifiers, composition) all
point to a diversity and structure gap, not a quantity gap.

The honest conclusion is that these are different levers, we have strong evidence that
quantity helps the narrow score, and we have reason to believe diversity — not quantity
— is what robustness requires. Isolating that directly is a natural next experiment.


\newpage

# 14. The Model That Memorized Everything

We spend a lot of this book trying to catch the model cheating. So far we have found
that it is *surface-tied* and *non-compositional*. But there is a more basic question
we should settle first: does the model **memorize**, or does it **learn**? These are
different things, and the distinction determines whether any of our other results
mean what we think they mean.

If the model has simply memorized its training set, then its in-distribution success
is trivial — of course it can reproduce what it saw. If it has *learned*, then it can
apply the mapping to things it never saw. Our Stage-1 result said the model gets
~90% on *held-out* problems, which is a strong hint it learned. But "held-out" can be
a weak guarantee if the held-out problems are surface-near to training ones. So we
test memorization explicitly.

## Three tests

We use three complementary probes on the trained pilot model.

**Test 1 — train-prompt prefix reproduction.** Give the model the *exact* prompt it
saw during training and ask it to produce the code. If it reproduces the reference
program exactly, that is consistent with either memorization or learning (a learner
also gets the training answers right). So this alone proves nothing — but it grounds
the other two.

**Test 2 — held-out generalization.** Give the model a *fresh* prompt for the same
operation, one it never saw, and ask for the program. If it passes, it has not merely
memorized the 60-prompt sample.

**Test 3 — the canary.** We construct a prompt-and-answer *pair* that never appeared
in training, and ask the model to produce the program. If the model outputs the
general program (e.g. `return a + b`), it is doing the computation. If it outputs some
fixed literal or garbage, it might be memorizing something else.

## The result

On a 60-example sample:

- **Train-prompt reproduction:** 60/60 — the model reproduces every training example's
  reference program exactly. (Expected for a well-fit learner.)
- **Held-out generalization:** 59/60 — it also solves essentially every *unseen*
  prompt of the same operation.
- **Canary:** the model emits the **general program** (`def solve(a,b): return a+b`),
  not a memorized constant.

## What this tells us — a nuanced answer

For **simple primitives**, the model behaves like a **learner, not a parrot**:

- It reproduces training examples (expected — a learner does that too).
- It **generalizes** to held-out prompts (59/60), so it did not simply memorize the
  60 instances.
- On a **canary** it emits the general program, not a memorized literal — so it did
  not memorize answer values.

## The shortcut audit, and the honest boundary

This is the subtle part. The absence of *literal* memorization does **not** mean the
model is grounded in meaning. Exactly the opposite mechanism is at work. Our Stage-3
experiment showed that if you change the *surface form* — the variable names or the
wording — the model's performance collapses to 0.000. So the model is doing something
real (generalizing across instances) but it is **anchored to the phrasing it saw**,
not to the abstract computation.

So the refined picture is:

| | What the model does |
|---|---|
| Memorize exact training instances? | **No** — generalizes to held-out + canary |
| Ground the computation independent of wording? | **No** — collapses on new wording |

The model is neither a parrot nor a mathematician. It has learned a *robust association
within a surface form* — it is not memorizing specific examples, but it is also not
representing "addition" in a way that survives being said differently.

## The lesson

Detecting "memorization" is not a simple yes/no. The useful question is not *"did it
memorize?"* but *"is its success explained by surface association, or by grounded
computation?"* Our probes show a clear answer for this model: it escapes example-
memorization but is caught by surface-memorization. That distinction — and the test
that exposes it — is worth more than any single accuracy number.


\newpage

# 15. New Words, Same Problem

The pilot told us the task was too easy; the composition experiment told us the
model cannot combine what it knows. But there is a more subtle question in between,
and it is arguably the one that matters most for whether we can trust any of this.

**When the model does well, is it doing the computation, or just recognizing the
wording?**

A model that maps the *words* "sum" and "a and b" to `a + b` is not necessarily doing
arithmetic. It might be doing a far dumber thing: associating the *exact phrasing* it
saw in training with the code that followed it. If that is what is happening, then
the capability is not in the model's head as "addition" — it is a fragile surface
reflex that will break the moment the phrasing changes.

To find out, we run the **surface-generalization** experiment (Level 3). The insight
is that if you change something that *should not* change the computation — the
variable names, or the words used to express the same instruction — and the model
fails, then the model never learned the computation. It learned the phrasing.

## The setup

We trained the model on pilot arithmetic primitives, but with a twist: we gave it only
**letter identifiers** (`a`, `b`) and only **some** of the wording template families.
Then we re-expressed the *identical* task three different ways and tested whether the
model's capability survived.

## The result

| Test | **MODEL** | TEMPLATE | RETRIEVAL |
|------|-----------|----------|-----------|
| In-distribution | **0.900** | 0.800 | 1.000 |
| New identifiers (`a,b` → `left,right`) | **0.350** | 0.800 | 0.683 |
| **Held-out wording** (a paraphrase family never seen) | **0.000** | 0.875 | 0.125 |

Watch what happens as we change only the *surface*, not the computation.

- **Same computation, different variable names.** The model was trained with `a` and
  `b`. We ask it the same question but with `left` and `right` — the *identical*
  operation. Performance drops from **0.900 to 0.350**.

- **Same computation, different wording.** We rephrase the instruction using a
  template family the model never saw during training. It is the exact same problem,
  just said differently. Performance drops to **0.000**.

## What this means

This is the moment the model's "capability" is revealed to be shallow. The model is
not grounded in the meaning — it is **anchored to the surface form.**

The most damning detail is the comparison against the baselines. When we change the
*words*, the **template baseline gets *better*, not worse** (0.875, up from 0.800),
because a rule system that recognizes keywords doesn't care about the surrounding
wording. The **retrieval baseline** also holds up better (0.683). Only the **learned
model** collapses — because the model learned the *specific phrasing*, not the
*concept*.

So the model's in-distribution success (0.900) was largely **phrasing memorization**.
It had learned that *this exact kind of sentence maps to that program*. It had not
learned "take two numbers and return their sum" as an abstract operation that
survives being said any number of ways.

## The shortcut audit

1. **Suspected shortcut: wording / phrasing memorization.**
   **Why it could explain it:** the model associated training phrasing with code.
   **Control:** held out a whole template family from training; tested on it.
   **Result:** 0.000.
   **What it rules out:** the claim that the model is grounded in the computation.
   **What remains:** whether the failure is *specifically* the wording pattern, or the
   new vocabulary/identifiers (a surface-control experiment separates these).

2. **Suspected shortcut: identifier memorization.**
   **Why it could explain it:** trained on `a,b`, maybe it hardwired those names.
   **Control:** retest with `left,right`.
   **Result:** 0.350 — a big but partial drop.
   **What it rules out:** pure identifier-memorization (still fails partly, so it's
   tied to the letters too, but not the whole story).

## The honest takeaway

A model that scores 0.900 in-distribution and 0.000 on a rephrasing of the same
problem has not generalized to the problem. It has generalized to the phrasing. This
is the difference between "the model works" and "the model works when I say it the
way I said it in training" — and it is the single most important lesson of the
generalization chapters.


\newpage

# 16. Same Pieces, New Combination

This is the experiment this book was always heading toward.

Everything so far measured whether the model learned a *single* operation. It did —
in-distribution, reliably, ~90% of the time. But learning one operation is not the
same as being able to **combine** operations you know into something you have never
seen. That combination is the heart of programming, and arguably of "capability"
itself. A model that can add and can take absolute values but cannot return the sum
of the absolute values of two numbers does not yet have compositional capability —
it has two separate, unrelated reflexes.

So we constructed the experiment that isolates that exact ability.

## The compositional split

We trained the model on **primitives only** — `add`, `sub`, `mul`, `max_of`,
`min_of`, `abs_of`, `list_sum`, `list_len`, `first_element`, and one composite —
1,400 tasks in total. The model saw no composite operation of any kind.

Then we built a **hold-out set of composite operations**, each of which composes two
of those primitives but never appeared during training:

| composite | primitives it composes |
|-----------|------------------------|
| `abs_add` | `abs` then `add` |
| `sub_abs` | `sub` then `abs` |
| `sum_of_abs` | `abs` over a list sum |
| `max_add` | `max(add, sub)` |
| `double_first` | index then `mul` |
| `len_minus_one` | `len` then `sub` |

Crucially, the model *knew every primitive involved* — it scored ~90% on each of
them. The only new thing was the **combination**.

## The result

| Candidate | In-distribution | **Compositional (held-out)** |
|-----------|-----------------|------------------------------|
| **MODEL** | **0.900** | **0.000** |
| TEMPLATE | 0.800 | 0.000 |
| RETRIEVAL | 1.000 | 0.000 |

The model scored **0.000** on compositional generalization. Not "partly" — zero.

And it is not a fluke of the evaluator. We inspected what the model actually
generated for a composite prompt. For `abs_add` — "take the absolute value of each
and return their sum" — it produced:

```
def solve(a, b):
    return a - b
```

which is not even the right primitives. For others it emitted malformed fragments or
reverted to a single memorized primitive pattern. It did not say "I know abs, I know
add, therefore I can do abs_add." It had no such compositional ability at all.

## The audit: is this a fair test?

We must rule out the possibility that this 0.000 is an evaluator artifact or an
unfair split. The evidence that it is *fair* is decisive: **the baseline systems also
scored 0.000.** Retrieval got 0.000 because no composite exists in the training set —
there is literally nothing to retrieve. The template rule system got 0.000 because it
has no composite rule. So the 0.000 is not a sign the task is impossible or wrongly
scored; it is a sign that the *only* way to get a composite answer is to genuinely
compose it — and the model cannot.

## What this teaches

This is as clean a measurement as this book produced, and it is the answer to our
central question at this scale:

> **A ~0.9M-parameter model can learn individual primitives to ~90% accuracy, but it
> cannot compose them into structures it never saw during training. Compositional
> generalization fails completely — even when every component is well learned.**

That is a real capability boundary, and it is *not* the same as "the model is bad."
The model is genuinely good at the single operations. The boundary is specifically
about **combination**.

The natural next question — and we answer it in Chapter 12 — is whether this is a
capacity problem (would a bigger model fix it?) or a structural/data problem (does
the model need to see *combinations* of the right kind during training?). That
distinction is the difference between "we need a bigger machine" and "we need a
different kind of data." As we'll see, at this scale it is not capacity.


\newpage

# 17. Red-Team the Judge

We built a judge and I argued it is the instrument we stake the book on. Chapter 6
showed how we test it (mutation testing) and that it caught a bug. This chapter is the
aggressive version: we stop politely checking the judge and start deliberately
attacking it, the way a determined adversary (or a suspicious reader) would.

The question is the one that hangs over the whole book:

> **How much confidence should we place in a number produced by our judge?**

## The attack surface

A judge that executes generated code is attacked through the code it is given. We
enumerate the ways a candidate could slip through:

- **hardcoded outputs** — a program that ignores the input and returns a fixed answer
  that happens to match one test,
- **mutation variants** — operator flips, wrong variables, off-by-one, missing
  edge-cases (the mutation suite from Chapter 6),
- **weak test cases** — if the hidden tests are too few or too narrow, a wrong program
  can pass,
- **boundary failures** — behavior at zero, negatives, or large values that the tests
  don't probe,
- **resource abuse** — programs that loop forever or consume too much,
- **unsupported syntax** — smuggling in a construct the sandbox should reject,
- **ambiguous specifications** — a prompt the model could reasonably read two ways,
- **evaluator inconsistencies** — the same program scored differently in two runs.

## What we found

The mutation suite is the sharpest tool here. By generating deliberately-broken
variants of the reference solution and checking that the hidden tests catch them, we
measured how discriminating the tests really are. If an obviously-wrong mutant — say
`+` changed to `-` — passes our tests, the tests are too weak and must be strengthened
until important mutant classes are reliably detected.

And the judge's honesty was validated the hard way: it reported the model at 0.000 on
our very first evaluation, and that was a *judge bug*, not a model failure. Once we
fixed the judge, the model's true 0.897 emerged. A judge that can be wrong — and we
proved ours was — must be red-teamed before its numbers are trusted.

## The honest framing

Red-teaming the judge is not a formality; it is the difference between "we ran a
number" and "we know the number means something." The specific lessons:

- **Strengthen tests until wrong programs fail.** The mutation score is the measure.
- **Trust the judge less than the tests.** The judge is a pipeline; the *hidden tests*
  are what actually catch errors, so they must be numerous and edge-case-complete.
- **Attack your own instrument deliberately.** The adversarial habit — "how could this
  number be wrong?" — is what keeps the whole experiment honest.

A judge that has been red-teamed is one we can believe. A judge we've only used is
one we cannot.


\newpage

# 20. What Happens When We Teach It Something New?

Every chapter so far has asked how a small model behaves on one task. But real
capability is not acquired in one shot — it is *grown* by adding new things over time.
Which raises the question at the heart of continual learning: when you teach a model
something new, does the new capability survive, and does the model **keep** the old
ones?

There is a well-known failure mode here, and it goes by the alarmist name
**catastrophic forgetting** — the tendency for a model, after training on task B, to
lose what it learned on task A. The question is whether that happens to our small
model, and crucially, whether the *way* we train determines it.

## The setup

We split the operations into two capabilities:

- **Capability A — arithmetic:** `add`, `sub`, `mul`, `max_of`, `min_of`.
- **Capability B — lists:** `list_sum`, `list_len`, `first_element`.

We train on A, then introduce B, and measure both:
- **B acquisition** — did it learn the new capability?
- **A retention** — did it keep the old one, or did learning B destroy it?

We run this under two protocols, changing only the *order and mixing*, not the model,
data, or optimizer:

- **sequential:** learn A fully, then learn B with no A exposure.
- **replay / mixed:** interleave A and B examples throughout.

## The result

| Protocol | **A-retention** | **B-acquisition** |
|----------|-----------------|-------------------|
| **sequential** | **0.000** | 0.889 |
| **replay**     | **1.000** | 0.889 |

This is as clean a result as this book produced.

**Sequential training causes catastrophic forgetting.** After learning arithmetic and
then lists in sequence, the model's A-retention is **0.000** — it completely forgot
the first capability. That is not "degraded"; it is gone. Learning the lists overwrote
the arithmetic.

**Replay prevents it, with zero cost.** When A and B are interleaved throughout, the
model's A-retention is a perfect **1.000**, and B-acquisition is **0.889** — identical
to sequential. So replay bought complete retention of the old capability with **no
trade-off whatsoever** in learning the new one.

## What this teaches

This is the clearest case in the book where the **training protocol, not the model or
the data, determines the outcome.** Same model. Same data. Same optimizer. The only
difference is whether the first capability stays "in the mix" while the second is
learned. Sequential forgets; replay retains.

The lesson generalizes directly: when you add a new capability to a model, *how* you
do it matters more than any property of the model itself. If you let the new task
dominate the gradient signal and remove the old data, the old capability collapses.
If you keep old and new interleaved, the model can hold both.

And it reframes a common assumption. People often reach for "a bigger model" when
confronted with a model that forgets. This experiment shows the forgetting was never
a capacity problem — a ~0.9M model holds both capabilities perfectly under replay. It
was a *training procedure* problem.

The pattern here echoes a deeper truth we've seen all book: the headline number
("did it learn the new thing?") hides the interesting failure ("what did it lose to
get there?"). Measuring B acquisition alone would have made sequential training look
like a success — 0.889, great. Measuring A retention reveals the cost. The lesson is
to always measure *both* the new and the old.

## The shortcut audit

1. **Suspected shortcut: the 0.000 A-retention is an artifact of how we score A.**
   **Why it could explain it:** maybe the A test is too hard, or the model just needs
   more steps.
   **Control:** replay mode, identical A test — A-retention 1.000.
   **What it rules out:** a broken A test. The same test that scores 0.000 in
   sequential scores 1.000 in replay.
   **What remains:** whether this holds for three or more capabilities, and whether
   replay-adds support *composition* of A and B after the fact.

## The honest summary

Acquiring a new capability can destroy an old one — and it is entirely up to how you
train. Sequential training forgets; replay retains with no cost. This is a controlled,
reproducible demonstration that catastrophic forgetting is a procedure problem, and
it is one of the most practically useful results in the book.


\newpage

# Chapter 20/21 — The Cost of Capability

This chapter answers: *what does each additional capability actually cost?* Using the
measured experiments, we build a cost matrix that makes the trade-offs explicit —
and reveals something important about what "capability" is costing us.

## The cost matrix

Each row is a capability or behavior from our experiments; the columns are the
measurable costs — data, parameters, training steps, and — decisively — the
*generalization* cost.

| Capability | data (examples) | parameters | steps | in-dist pass@1 | surface generalizes? | composes? |
|------------|-----------------|------------|-------|----------------|----------------------|-----------|
| Single primitive (add, sub, …) | 1400 | 0.88M | 1500 | 0.900 | ✗ (new wording → 0.000) | ✗ |
| New identifier robustness | 1400 | 0.88M | 1500 | 0.900 | ✗ (0.350 on new IDs) | — |
| Composition (abs_add, sum_of_abs) | ∞-needed | 0.9M–6.5M | — | — | — | ✗ (0.000) |
| Continual: A then B (sequential) | 1400+1400 | 0.88M | 1400 | B: 0.889 | — | ✗ (A forgotten) |
| Continual: A+B (replay) | 2800 interleaved | 0.88M | 1400 | A: 1.000, B: 0.889 | — | ✗ |

## What the costs tell us

**Capability is cheap; robustness is not.** Learning a single primitive costs ~1400
examples and a few minutes on a 0.88M model, and it "works" (0.900). So the *apparent*
cost of a capability is low. But that number is misleading: it measures only
in-distribution correctness.

**The real cost appears when you ask for generalization.** To make a single primitive
robust to *surface* change (new identifiers, new wording), the experiments suggest
you'd need to change the data substantially — diverse identifiers and wording — not
just add capacity. And composition is not purchasable at this scale at all: it stayed
0.000 at both 0.88M and 6.5M.

**The cost matrix makes a dangerous pricing error visible.** If you only look at the
"in-dist pass@1" column, you'd conclude capability is nearly free and scale up naively.
The generalization and composition columns reveal that the cheap number hides a much
more expensive requirement — robust, compositional capability — which we did not
achieve by scaling data or capacity within our tested range.

## The honest framing

The most honest "cost" we measured is the cost of **mistaking surface association for
grounded capability**. That cost is high: it makes a model that scores 90%
in-distribution *look* capable while it collapses to 0.000 on any change to the
surface. In a deployed system, that is precisely the failure that appears late and
costs the most.

So the real answer to "what does each capability cost?" is: the easy-to-see cost
(data, parameters, steps) is small and scales predictably; the hard-to-see cost —
making the capability actually generalize and compose — is where the true expense
lies, and at this scale it is simply not purchasable with more of the same resource.


\newpage

# 22. The Capability Map

We have run a handful of tightly-controlled experiments. Rather than a list of
results, let us draw the **capability map**: one picture that says, for each behavior
we tested, whether the model acquired it, whether it generalizes, what it costs, and
where it breaks.

We record each finding with an honest epistemic label — what is *proven* (measured),
what is *supported*, what is *suggestive*, and what is *unknown*.

## The four-level generalization map

Recall the four levels from Chapter 2. Here is what we measured at each, on the ~0.9M
model:

| Level | The question | Measured result | Status |
|-------|--------------|-----------------|--------|
| **L1 Mem** | Can it be explained by remembering? | Held-out 59/60; canary → general program | `[PROVEN]` it generalizes primitives, doesn't parrot |
| **L2 Dist** | Does it work on new instances of the same task? | In-distribution 0.900 | `[PROVEN]` yes |
| **L3 Surf** | Does it survive superficial change? | New wording → 0.000; new identifiers → 0.350 | `[PROVEN]` no — surface-tied |
| **L4 Struct** | Can it compose known pieces in unseen ways? | 0.000 (baselines also 0.000) | `[PROVEN]` no |

## The scaling map (what changes it)

| Lever | Tested | Effect on composition |
|-------|--------|-----------------------|
| Model size | 0.88M → 6.5M (7.4×) | **none** — still 0.000 |
| Data size | 100 → 3000 examples | helps *in-distribution* (0.10→0.64), not composition |
| Training protocol | sequential vs replay | **big** — fixes continual retention (0.000→1.000) |

## What's proven vs. what's unknown

**Proven (measured, this setup):**
- The model learns single operations to ~90% in-distribution and generalizes them
  across instances (L1/L2).
- It is surface-tied: new wording → 0.000, new identifiers → 0.350 (L3).
- It cannot compose: unseen combinations → 0.000, and neither 7.4× capacity nor
  more data changes this (L4).
- Continual learning is a procedure problem: sequential forgets (A → 0.000), replay
  retains (A → 1.000) with no acquisition cost.
- The pilot task was retrieval-solvable (retrieval = 1.000), so that split is "too
  easy"; the composition split is not (all baselines 0.000).

**Supported / suggestive:**
- The composition failure is likely *structural-data* (exposure to combinations),
  not capacity — but we did not test feeding the model compositions directly, so this
  is suggestive.

**Unknown (did not test):**
- Whether feeding composites during training unlocks composition.
- Whether behavior on 3+ capabilities or post-continual composition holds.
- Human-written task transfer (recommended external sanity check, not yet run).
- Whether a fundamentally different inductive bias (not scale) helps.

## The boundary, in one line

> **A small model learns narrow, individual mappings well and generalizes them across
> instances, but its knowledge is surface-tied and non-compositional — and within the
> tested range, neither more parameters nor more data nor a different training order
> turns that into robust, compositional capability.**

## Why the map is the deliverable

This map is the book's real output. It is not a single headline accuracy that would
mislead; it is a precise, honest picture of where capability exists, where it
collapses, and what (and what doesn't) shift the boundary. It is the answer to the
central question — and it is falsifiable, built from real measured runs, and honest
about what remains unknown.


\newpage

# 23. What Small Models Can Actually Learn

We have run a small, disciplined set of experiments and measured a coherent boundary.
Let us now state, carefully and honestly, what the experiments showed — the
synthesis the whole book has been assembling.

Everything below is scoped to **our** setup: a ~0.9M–6.5M decoder-only transformer,
trained on a few thousand generated natural-language-to-Python tasks, evaluated by a
mutation-tested execution-based judge. These are claims about this brew, not
universal laws about all small models.

## What the model can do

**It can learn individual operations well.** On in-distribution primitives — `add`,
`sub`, `mul`, `max`, `abs`, `list_sum` — the ~0.9M model solves ~90% of held-out
problems under greedy decoding. It beats a hand-written template rule system (0.900
vs 0.800). This is real, measurable capability on a narrow task.

**It generalizes across instances, not just examples.** It passed 59/60 held-out
prompts and, on a *canary* it had never seen, produced the *general* program rather
than a memorized literal. So for a single operation, the model is a learner, not a
parrot. That is Level-2 distributional generalization, achieved.

## What the model cannot do

**It cannot survive changes to the surface form.** Change the variable names from
`a,b` to `left,right` (identical computation) and performance falls to 0.350.
Rephrase the instruction with a wording family the model never saw (identical
computation) and performance falls to **0.000** — below *both* baselines. This is
Level-3 failure: the model's capability is **anchored to the phrasing**, not grounded
in the computation.

**It cannot compose what it knows.** Train on `add`, `sub`, `abs`, `max`, `list_sum`
as separate primitives; test on `abs_add` (abs then add) and `sum_of_abs` (abs over a
list sum) — operations that combine two things it knows perfectly. The model scores
**0.000**. It did not learn "I know abs and I know add, therefore I can do
abs+abs." This is Level-4 structural failure. And crucially, the baseline systems
*also* scored 0.000 — so the test is fair, and the only way to solve it would be
genuine composition, which the model lacks.

## The two axes of the boundary

Put together, the results define a sharp boundary along two independent axes:

**Axis 1 — Surface form.** The model's knowledge is tied to the exact wording and
identifier names it saw. It does not generalize "sum of two numbers" as an abstract
concept; it generalizes "this sentence shape → this code." Change the surface, and
the capability evaporates.

**Axis 2 — Composition.** Even within a surface form it knows, the model cannot
combine two learned pieces into a novel structure. It has reflexes, not a
compositional engine.

**The honest conclusion in one sentence:**

> A ~0.9M model genuinely learns individual mappings and generalizes them across
> *instances*, but the knowledge is surface-tied (new wording → 0.000) and
> non-compositional (unseen combinations → 0.000) — and neither more capacity
> (6.5M) nor more data (within what we tested) is close to fixing it.

## What it's NOT, and why that matters

This is **not** evidence that the model is "stupid" or that the approach "doesn't
work." It is evidence about *what kind of capability small models acquire from this
kind of data*. The model is good at exactly what it was trained to do — map a narrow
phrasing to a narrow computation — and bad at the two things that separate "reflex"
from "capability": robustness to surface change, and composition.

The value of measuring this precisely is that it tells us *where* to look next. It is
not a shrug and a "small models are limited." It is a specific, falsifiable map: the
boundary is on surface-robustness and composition, not on in-distribution learning.

## Preferring "what these experiments showed"

Throughout, we deliberately avoid claiming things about "all small models." We can
only say what *this* model, on *this* task, with *this* data, did. And what it did is
both genuinely interesting (it learns!) and sharply bounded (it doesn't generalize
or compose).

That boundary — precise, measured, and honest — is the book's real deliverable.


\newpage

# 24. The Model Wasn't the Point

We began with a question that sounded technical: *can a small language model learn
to solve programming tasks?* The answer we got was more interesting and less about
the model than we expected.

## Where the journey started

The premise was: building a small model is relatively easy; determining what it
actually learned is the hard part. That premise turned out to be more accurate than
we had any right to expect. The model was built in an afternoon. Understanding what it
had — and had not — learned took the rest of the book.

We built a laboratory, not just a model. Four artifacts: a **controlled world** (an
AST-whitelisted Python sandbox), a **teacher** (a semantic dataset generator), a
**judge** (an execution-based, mutation-tested evaluator), and the **student** (the
model itself). The model was only one component. The experiment was the subject.

## What the laboratory produced

The experiments told a clean, coherent, honest story:

- **The model learns.** On individual operations it reliably maps natural language to
  correct Python, beating a hand-written template rule system and reaching ~90%
  in-distribution.
- **But it is surface-tied.** Change the variable names, and it drops to 0.35. Change
  the wording while keeping the computation identical, and it falls to **0.000** —
  below both baselines.
- **And it cannot compose.** Even though it knows every primitive, it scores **0.000**
  on operations that combine two things it knows.
- **Neither capacity nor data fixes it at this scale.** A 7.4× larger model and many
  more examples leave the composition boundary at 0.000.

Along the way, the laboratory caught itself. The first time we evaluated the model, it
scored 0.000 — and it wasn't the model's fault. The evaluator was broken (a NUL-
padding artifact in the output made every program fail to parse). Fixing the *
tester* revealed the model's true 0.897. That moment — discovering our own instrument
was wrong before we trusted it — is as much a part of this book as any model result.

## The deeper achievement

The book's real finding is not "small models are limited." It is:

> **Building a trustworthy experiment was harder and more valuable than building the
> model.**

The model was the instrument. The experiment was the subject. The things that made
this work — the sandbox that rejects anything not explicitly allowed, the judge that
executes code and compares semantics rather than strings, the mutation suite that
red-teams the judge, the leakage audit that caught our own dataset leaking the answer,
the baselines that ask "could a simpler machine do this?", the four-level taxonomy
that refuses to collapse everything into one number — those are the actual
achievements here.

## What the reader takes away

If you take one thing from this book, it is a habit, not a fact:

> **Never trust a number from a model you don't understand, or from an experiment you
> haven't audited.**

Before you believe "the model learned to add," you have to be able to answer: remove
the memorization, the retrieval, the templates, the leakage, the evaluator artifacts —
what remains? In our case, for simple primitives, what remained was genuine
learning-within-a-surface-form. It was real, and it was narrow, and it did not
compose.

That is the honest, complete answer. We did not build a general programmer. We built
the means to ask, precisely and honestly, what a small model can and cannot learn —
and we got an answer worth having.

**Build the model. Test the model. Break the evaluator. Break the model. Audit the
data. Challenge the conclusion. Repeat.** Only then say: "This is what the model
learned."

The model was not the point. The experiment was.
