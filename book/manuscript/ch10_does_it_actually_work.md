# 10. Does It Actually Work?

We have a trained model, a judge, and a test set. The natural question is the one
the whole book has been building toward: *does it actually work?*

And the answer, as with almost everything in this book, is **"it depends on what we mean,"** and then **"let's measure it rather than argue."** Because "works" is not a
single number. It is a question about *which* kind of capability, under *which*
conditions, measured in *which* way. The job of this chapter is to take that vague
word and replace it with something we can actually see.

## The setup

We trained a small decoder-only transformer on 1,400 generated tasks: the model reads
a natural-language specification and must produce the reference Python program. The
trained model is tiny — **884,224 parameters** (0.88M), of which 53,632 are the
embedding and 830,592 are the non-embedding weights. It saw 1,500 gradient steps on a
batch of 16, reaching a training loss of **0.0208**.

We then asked it to solve 300 **held-out** test tasks, and scored each generated
program by executing it against that task's hidden tests. The novelty here needs a
precise statement: these test records reuse the **same 21 prompt strings** the model saw
in training, but each carries a **new task ID with fresh hidden-test input values**. So
"held out" here means new *instances* of a seen prompt — the model had to produce, for a
prompt it already knows, a program that passes input values it has never seen. It is not a
test of a brand-new request (for that, see Chapter 15's human-written prompts and the
surface/composition holdouts, whose prompts genuinely never appear in training). This is
the moment of truth for the whole apparatus: everything we built — the world, the
teacher, the judge, the rivals — converges on this measurement.

| Quantity | Training | Validation | Pilot test |
|---|---:|---:|---:|
| Records | 1,400 | 300 | 300 |
| Prompt strings | 21 | 21 | 21 |
| Test prompts also seen | n/a | 21 of 21 | 21 of 21 |
| What changes at test | n/a | task ID, inputs | task ID, inputs |

The dataset is a three-way 1,400 train / 300 validation / 300 test split
(`artifacts/datasets/pilot_manifest.json`). The validation split was recorded but never
used for model selection — `scripts/train.py` loads it and evaluates only on the test
set — so every figure in this chapter is a test-set figure.

A key distinction to keep straight: the numerical inputs go to **Python** (the model's
program is executed on them), while the **language model** receives only the prompt string.
So a new task ID changes what the *judge* feeds the program, not what the *model* sees.

## One task, end to end

The cleanest way to see what the judge does is to follow one task from prompt to
verdict. Here is a real run against the pilot model — record `add_0036` from the
scored pilot evaluation (`artifacts/datasets/pilot_test.jsonl`).

**The request.** "Implement solve so that given a and b it returns their sum."

**The reference program** (the teacher's ground truth):

```
def solve(a, b):
    return a + b
```

**What the model actually produced** (temperature-0.8 sampled decoding, this checkpoint — the same single sample used for the reported score):

```
def solve(a, b):
    return a + b
```

**The hidden tests** (input/expected pairs) that the judge then runs. For this record
(`add_0036`) the task's suite has **eight** cases; here is an **excerpt** of three (a
basic, a zero, and a negative case). The judge runs all eight and this task **passes —
all 8/8**.

| inputs | expected |
|--------|----------|
| (-86, -95) | -181 |
| (0, -28) | -28 |
| (-1, -33) | -34 |

The judge runs the model's program on each pair, compares the output with the
semantic comparator, and reports **pass@1**. This task passes.

Now the informative contrast: a task the model *had not seen*. The teacher's
composite `abs_add` asks for the sum of the absolute values of two numbers
(`abs(a) + abs(b)`). A provenance note before the examples: the scored pilot evaluation
runs only on `artifacts/datasets/pilot_test.jsonl`, which contains the 10 primitive
operations and the 21 training prompt strings — no `abs_add` record and no reworded
prompt. So neither of the two failures below is an output of that scored run; both are
**separately-run demo generations** against the pilot model, outside the evaluation set,
and we label them as such rather than presenting them as pilot-evaluation outputs.

The first comes from the live demo battery (`scripts/demo_live_model.py`, archived in
`docs/experiments/model_sweep_live.md`): the `stage1.pt` checkpoint, which knows both
`abs` and `add` individually, was fed the composite prompt:

> "Write a function that takes two numbers, a and b, takes the absolute value of each,
> and returns their sum."

and produced:

```
def solve(a, ab
```

— a truncated, unusable fragment. The generation stopped early. We did not preserve the
raw token sequence, so we cannot state the precise stop reason from the record (it could
be the `max_new` limit, the NUL-byte extraction boundary, or an unlucky sampled end).
What is clear is that it is an **incomplete extracted candidate whose
termination/extraction cause was not preserved** — a partial Python identifier/source
fragment, not a complete program. Because a termination/extraction defect already changed
the pilot score once, we flag these as an *incomplete extracted candidate*, and do **not**
assert a specific internal cause (we cannot, from the record, tell it apart from a genuine
capability limit). The second is likewise a separately-run demo generation, not a scored
pilot record: on a genuinely
reworded surface ("Return the value obtained by adding together two numbers, denoted
p and q.") — a prompt that is not among the 21 pilot prompt strings — it produced:

```
def  a solve(a, b
```

again truncated. These two demo generations carry the book's whole point: on a familiar
surface the model writes correct code, and on an unseen surface or a new combination
it collapses to a fragment. Nothing about the failure required the hidden tests to be
"unfair" — the invalid fragments were **rejected at parsing** by the judge, before any
execution or comparison, because they do not parse as complete Python programs.

## What we measured: pass@1

Here is the headline result, reported as **problem-level hidden-test pass@1 under the
evaluation's default temperature-0.8 sampling** — that is, for each evaluation record, did
the *single sample* the model produced pass *every* hidden test? (This is sample pass@1,
one sample per record, not a distribution over many samples.) Two sampling details matter
for interpreting it: (1) the evaluator calls the model **once per evaluation record**
(`for t in tasks: candidate(t)` → a fresh `model.generate`), so records that happen to
share a prompt string still get **independent** draws — no output is cached or reused
across records; and (2) the fixed score is a property of the checkpoint, the sampled
outputs, the record weights, the tests, and the decoding settings (temperature, `max_new`,
NUL truncation), not just of the dataset. A single sample per record does not
give within-run sampling error, but the repeated records do act as within-prompt
replicates for the purposes of a familiar-prompt aggregate. The training seed is recorded
per run; generation does not reset the RNG to a separate value, so it uses the continuing
RNG state during evaluation unless explicitly reset (Appendix C.6), which is why sampling
is stochastic rather than exactly seed-reproducible record-for-record. There is no stop
policy: `generate` in `src/model/gpt.py` always draws exactly `max_new` tokens (it never
stops early on EOS or PAD), and extraction truncates at the first NUL byte; the `max_new`
and extraction rules live in `src/eval/evaluator_runner.py`.

| Candidate | syntax | executable (≥1 hidden test passed) | **pass@1** |
|-----------|--------|-----------|------------|
| **MODEL** | 0.897 | 0.897 | **0.897** |
| TEMPLATE | 1.000 | 0.900 | 0.800 |
| RETRIEVAL | 1.000 | 1.000 | **1.000** |

*Reading the columns:* `syntax` is the fraction that passed the judge's combined
parse-and-whitelist validation (Chapter 6 — whitelist/capability rejections are
counted here too), and `executable` is the fraction that **produced at least one
correct output** — passed at least one hidden test — not merely the fraction that ran
without error.

Three things stand out.

**First, the model learns to produce a program for a prompt it has seen many times.**
0.897 means that ~90% of the time, given a *familiar* prompt string, the model produced a
program that passed all the *fresh input values* the judge supplied. That is not a toy
result: the model emits valid, correct Python for a request it has been trained on. But
note exactly what is and is not being claimed. Because every one of the 300 test records
reuses a prompt string the model saw in training, this figure is **familiar-prompt program
generation on new execution inputs** — not generalization to a new request. And it still
**beats the hand-written rule baseline** (0.800) on that same set. A hard-coded
pattern-matching system that recognizes keywords like "sum" and emits a template gets 80%;
our learned model gets ~90%. So on this task, the learned model does *more* than a fixed
rule system.

**Second — but retrieval does even better.** A trivial TF-IDF retriever that does
nothing but find the closest training example and reuse its program scores **1.000**.

That second fact is not a failure; it is the pivotal thing this pilot taught us. It
tells us the task, as currently constructed, is **too easy to force
generalization**. When a non-learning lookup solves 100% of the test set, then the
test set is solvable by retrieval, and a model scoring 90% is not yet being tested on
whether it can generalize — only on whether it can match the surface form of a
training example.

This is exactly the "task too easy" outcome the experimental plan anticipated, and it
is scientifically useful: it tells us *how to make the next task harder.*

## The moment that broke us (and the evaluator, not the model)

There is a story behind these numbers that is more instructive than the numbers
themselves, and it is worth telling plainly. When we ran the evaluation for the very
first time, the model scored **0.000**. Not 0.897 — zero. Every single generated
program failed the syntax check.

Our first instinct, naturally, was that the model was useless. We had spent hours
building a careful apparatus and the tiny model could not even produce a parseable
program. It would have been easy to conclude "the model doesn't work" and write the
whole thing off.

But the book's own discipline — *test the tester* — demanded we ask whether the
*judge* was the problem, not the model. So we looked at what the judge actually
saw. And there it was: the generated programs were valid Python up to the end of the
program, except they had a run of **NUL bytes** (`\x00`) appended after it. The
model had learned to pad its output with a byte that means "nothing." Python's parser
correctly rejects NUL bytes — they are not valid source. The fault was in the
*extraction contract*, not the parser: we had failed to strip the padding before
handing the output to `ast.parse`. So `ast.parse` threw a syntax error on what was,
after truncation, good code, and the judge scored the model's program as a *syntax
failure*.

The fix was a single line: truncate the generated program at the first NUL byte. A
trivial change, and suddenly the model's score leapt from 0.000 to 0.897.

This is the pivotal lesson of this chapter, and it is not about the model at all.
**The evaluator was broken, not the model.** We had designed every
experiment to detect shortcuts and outright cheating in the *model*, and we nearly
missed the one case where the measuring stick itself was faulty. The "test the
tester" principle — that we must verify the tool measures what we think it measures
before trusting a single number it produces — was not a formality. It just saved the
entire project from a false negative.

The reason we caught it is worth pausing on. We did not catch it because we are
clever. We caught it because we had *already* built a method for testing testers
(the mutation suite in Chapter 6), and we had written the pilot's results to a
manifest and looked at the intermediate numbers, not just the headline. Had we
grabbed the final pass@1 and moved on, we would have shipped a book claiming a tiny
model cannot write Python — a conclusion that was wrong.

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
   *computation* or in the *surface form*. To answer that, we need the Question-3
   (surface-change) and Question-4 (composition) experiments, which we run next.

2. **Suspected shortcut: exact memorization.**
   **Why it could explain it:** the model saw 1,400 examples; maybe it memorized the
   prompt→program pairs.
   **Control (Ch14):** a probe of 60 pilot records plus a held-out program probe: **60/60 on the
   training-record probe** (it reproduced every reference program exactly) and
   **59/60 on the held-out/task-ID probe** (a passing general program for a fresh task
   ID), while on the held-out program probe it emitted the *general* program rather than a
   memorized literal. **Caveat:** the pilot test
   reuses training prompt strings, so this does **not** establish unseen-prompt
   generalization — it shows the model produces a *general* program (not a memorized
   constant literal) for these records.
   **What it rules out:** the narrow claim that the model merely emits memorized
   *constant* outputs.
   **What remains:** the deeper question — is the *general program* it produces
   genuinely tied to the computation, or to the particular wording?

## The honest summary

The pilot succeeded in exactly the way a pilot should: the laboratory works, the
model **reliably produces a correct program for a prompt it was trained on**, and —
perhaps most valuably — the experiment told us something *uncomfortable but true*. The
task is retrieval-solvable, a model that beats a template rule system yet sits below a
lookup table, and — crucially — the test reuses the model's known prompt strings, so the
pilot **did not actually test generalization to a new request**. It tested reliable
familiar-prompt generation and shows that the *apparatus* can produce meaningful,
checkable measurements. Whether the model can generalize is the question the remaining
chapters actually probe, using prompts and composition that genuinely were not in
training.

And we were reminded, in the most direct way possible, that the measuring stick is as
much a subject of the experiment as the model. The instrument and the thing measured
both needed to be honest, and only one of them initially was.

That is the baseline from which every later experiment is measured. From here, we
stop making the task easier and start making it *probe* generalization.
