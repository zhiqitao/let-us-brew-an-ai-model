# 6. Build the Judge

How do we know a student's answer is right? We check it against the answer key. But
what if the answer key is wrong? Then every student who gets it "right" is actually
wrong, and we'd never know.

That is the risk with our **judge** — the evaluator that decides whether a generated
program is correct. It is the instrument whose readings the whole book depends on. If
the judge is wrong, every number in this book is wrong. So we build it carefully, and
then we attack it.

This is the second pillar of the apparatus, and it is in some ways the most important.
The world (Chapter 4) decides what the model is *allowed* to do. The teacher (Chapter
5) supplies the material to learn from. But the judge is the thing that decides
whether the model *got it right*. A subtle way to frame the whole book: we are not
really studying the model. We are studying the model *through* the judge. So the
judge's integrity sets an upper bound on the trustworthiness of everything that
follows.

## Why an execution-based judge

The naive way to judge a generated program is to compare it, as text, to the expected
answer. This is cheap, and it is almost worthless. Two programs that solve the same
task can look completely different as strings — one uses a loop, another uses `sum()`,
yet both are correct. And two programs that look nearly identical can behave
differently. String comparison measures *how the code is written*, not *whether it
works*. That is not what we care about.

So the judge does the thing that makes this whole task special: it **runs** the
program. It executes the generated code against hidden tests and compares the actual
*output* to the expected output. This is what gives us objective, unambiguous
judgment. There is no opinion about whether the code is elegant or the "right" style —
either it returns the correct result for every test, or it does not.

## The four-stage pipeline

![The judge](figures/fig_judge.png)

The judge is a funnel: a program clears it only by passing every stage, and the
first failure sends it to zero.

We score a candidate program through four stages; a later stage only matters if the
earlier ones pass. Each stage is a filter, and each exists for a specific reason.

1. **Syntax pass** — does the program parse as valid Python?
2. **AST / capability pass** — is every node within the whitelisted subset? If the
   program smuggles in an `import`, it is rejected here.
3. **Execution pass** — did the program produce at least one correct output? In the
   implementation this stage is recorded as *executable* when the program passes at
   least one hidden test (or has no hidden tests), so the recorded quantity is
   "produced at least one correct output," not merely "ran without error": a program
   that executes cleanly but fails every hidden test is recorded as *not* executable.
4. **Semantic pass** — for each hidden test, does the program's output match the
   expected output?

Two honest notes on how this design maps onto the code. **First, stages 1 and 2 are a
single combined validation gate in the implementation:** the evaluator calls
`sandbox.validate_source` once — one call that both parses and checks the whitelist —
and sets `syntax_ok` and `capability_ok` together. So the reported **syntax rate
includes whitelist/capability rejections** (a program rejected for smuggling in an
`import` is counted in the syntax rate), and no separate capability rate is computed.
**Second, stage 3 is coupled to stage 4:** `execution_ok` is derived from the
hidden-test outcomes (`tests_passed > 0`), which is why "executable" means "passed at
least one hidden test," as defined above. The four-stage vocabulary is the design's;
the recorded numbers collapse the first two stages into one gate and tie the third to
the fourth.

The primary metric is **problem-level hidden-test pass@1**: did the one program
produced pass *every* hidden test for that problem?

Why four stages rather than one? Because each stage isolates a *different* kind of
failure, and separating them tells us *why* a program failed. In the design a syntax
error is a very different problem from a capability violation (the model tried to use
something outside its world), which is different again from a runtime error (the code
ran but crashed on a test), which is finally different from a semantic error (the code
ran but produced the wrong answer). If we collapsed all four into one "it failed," we
would lose the ability to diagnose. The judge does not just tell us right or wrong; it
tells us *where* things go wrong, and that diagnostic power is worth keeping. The
honest limit, as noted above: because stages 1 and 2 share one validation call, the
recorded rates separate *failed validation* from *no correct output* from *all tests
passed*, but they do not separate syntax failures from capability violations — the
reported "syntax" rate is really "failed validation."

## Semantic comparison: don't trust string equality

A naive evaluator would compare outputs as strings. That is wrong — the result of a
program is a *value*, so comparing text representations of numbers would reject correct
answers (`0.1 + 0.2` as text is not `0.3`). So the judge compares values with a
**semantic comparator**. Notably, Python's own `==` already recurses into lists and
ignores dictionary insertion order, so the comparator's job is narrower than "fix all
of Python's equality quirks." It adds three real policies on top of Python semantics:

- **floats compared with an explicit tolerance** (Python's `==` on floats is exact;
  `0.1 + 0.2 == 0.3` is `False`). We use an absolute tolerance.
- **booleans treated as booleans, not as 0/1** (so `True` is not equal to `1`),
- **dicts compared order-insensitively**, which Python already does for `==`; the
  comparator re-implements it explicitly for clarity and to recurse into values.

The comparator itself is tested — we don't assume it's right just because it's simple.
And the tolerance matters: floating point arithmetic is not exact, so a judge that
demanded exact equality on floats would reject correct programs. A judge with no
tolerance at all would be as broken as one that accepted anything. Choosing the right
tolerance is a real design decision, and it is the kind of thing that quietly shapes
every number the judge produces.

## Mutation testing: red-teaming the judge

The most important step is treating the judge as something that must be *vetted*. We
**mutate** the reference solution into deliberately-broken versions and ask:
*does the judge catch them?*

We generate mutants such as: `+` → `-`, `>` → `>=`, remove the `return`. The shipped
recipe list is all text substitutions — arithmetic and comparison operator flips,
`and`/`or` swaps, and removing the `return`; swapping arguments, off-by-one loop
boundaries, and wrong-variable edits are design-stage candidates we do not run here.
Then we run each mutant through the hidden tests. A good test suite **rejects** an
obviously-wrong mutant. A weak test suite lets it pass.

The mutation score — the fraction of wrong mutants the tests catch — is a measure of
how much we can trust the judge on *the cases it is designed for*. An obviously-broken
program passing our tests means the tests are too weak for that class of error. Two
honest caveats: (1) passing a finite hidden-test suite means passing *that suite*, not
proving correctness for every allowed input — deterministic scoring is not complete
semantic verification; (2) equivalent mutants (e.g. swapping `+` operands) do not make
a program incorrect, so those should not count against us. We report the mutation
behaviour honestly rather than claim the judge is "proven sound"; it is a well-tested
*heuristic* verifier within the cases we constructed, not a proof.

This is the "test the tester" principle, and it is the reason we do not trust the
judge just because we wrote it. The judge is the instrument of measurement, so we
deliberately give it wrong inputs and check that it rejects them. It is a rare and
valuable discipline: most people build a measuring stick and assume it measures. We
deliberately try to break ours.

## We caught our own judge being wrong

Here is what makes this chapter honest rather than aspirational: the very first time
we evaluated our model, it **scored 0.000** — reported a total syntax failure on
every problem. And the model wasn't wrong. The *judge* was.

The root cause was a generation bug on our side: the model produced a complete, correct
program, but it was followed by padding (null bytes), and `ast.parse` correctly rejects
null bytes — they are not valid source. So the fault was in the *generation/extraction
contract*: those padding bytes were meant as a termination or padding marker that we
needed to strip, not as part of the program. `ast.parse` behaved correctly; our
extraction forgot to truncate the padding before parsing. Once we truncated it, the
model's true score emerged: **0.897**.

That moment is worth more than any passing test. It is the book's core lesson applied
to ourselves: **never trust a number from a system we have not audited.** If we had
taken the first 0.000 at face value, we'd have concluded the approach failed. Instead,
finding the judge's bug told us the truth — the model was actually working.

What is striking is that this bug was not exotic. It was a small, mundane detail — a
sentinel byte used to mark the end of a generated program — colliding with Python's
parser. We would never have found it by reasoning about the model. We found it
because we looked at the judge's *intermediate* output (the syntax scores) rather than
jumping to the headline number, and because we already had the habit of doubting the
measurement. That habit, more than any single fix, is what kept the book honest.

## The honest summary

The judge is not a helper; it is the instrument whose readings we stake the book on.
So we built it strictly (four stages, semantic comparison, tested comparator), then
we red-teamed it (mutation testing), and then — when it gave a suspicious answer — we
attacked it until we found our own bug. Only a judge that survives that scrutiny
deserves to be trusted.

And the deeper lesson is one we will keep relearning: in any measurement, the
instrument is part of the experiment. The model and the judge are both subjects. We
spend almost as much effort verifying the judge as we do training the model — and
that is not waste. That is the only way to trust the numbers at all.
