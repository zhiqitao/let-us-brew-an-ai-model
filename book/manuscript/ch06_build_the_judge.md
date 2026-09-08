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
