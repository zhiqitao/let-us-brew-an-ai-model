# Appendix B — The Failure Ledger

The design requires that we do not sanitize the journey into a success story. This is
the honest record of everything that went wrong, was surprising, or was a failed
attempt — because each of these taught us something, and several are as valuable as
any success.

Each entry: what happened, what we learned, and what we did about it.

---

## 1. The evaluator reported the model at 0.000 — but the model was fine

**What happened.** On the very first Stage-1 evaluation, the trained model scored a
reported **0.000** (syntax failure on every problem). This looked like a total failure
of the approach.

**What we found.** The model was actually producing programs that were correct up to
the end of the program — but our generation output appended null-byte padding, and
Python's parser *correctly* rejects null bytes (they are not valid source). The fault
was in our **extraction contract**: we handed the parser padded output without
stripping the padding. So the **judge** was scoring what were, after truncation, valid
programs as syntax errors.

**What we learned.** The most important lesson of the book, demonstrated on ourselves:
*never trust a number from a system we have not audited.* Fixing the judge revealed the
model's true 0.897. If we'd taken 0.000 at face value, we'd have wrongly concluded the
approach failed.

**Action.** Fixed `generate_code` to truncate at the first null byte; re-ran; got 0.897.

---

## 2. The pilot wording was so predictive of the answer we had to look again

**What happened.** The leakage audit trained a trivial TF-IDF classifier to predict the
operation from the natural-language prompt. It succeeded **100%** of the time.

**What we learned.** At first we recorded this as "the wording leaks the answer," but on
reflection most of it is **task signal, not leakage**: the request is supposed to name
the operation ("sum", "absolute value"), so a classifier recovering it from the wording
is the request doing its job. What it does tell us is that a model "succeeding" might
just be exploiting that phrasing rather than learning the computation — which is *why*
the surface-generalization tests matter. We therefore treat the 100% score as a flag to
inspect *which* words drive it (operation words vs. an accidental cue), not as proof of
contamination.

**Action.** Recorded as finding-001 (with the interpretation corrected above); noted the
pilot is fine for Stage 1 but must add wording-family holdouts before any surface test.

---

## 3. A bigger model did NOT fix composition

**What happened.** We scaled the model across a ~33× range (0.88M → 29.3M) expecting
the composition boundary to move. It did not: composition stayed at **0.000** at all
four sizes (0.88M, 6.5M, 10.2M, 29.3M).

**What we learned.** At ~1–30M parameters, under the training schedules we ran,
compositional generalization stayed at 0.000 and was **not moved by scaling alone**.
We are careful not to call this a capacity "ceiling" — it is a measured boundary in
this regime, not proof that capacity cannot help under other conditions. It is a
genuine negative result that redirects the investigation.

**Action.** Recorded in `docs/experiments/scaling_composition.md`.

---

## 4. Sequential training caused catastrophic forgetting (A → 0.000)

**What happened.** Teaching the model lists after arithmetic, sequentially, completely
destroyed the arithmetic (A-retention **0.000**).

**What we learned.** Catastrophic forgetting is real and severe here — but it is a
**procedure** problem, not a fate. Joint training (A and B interleaved) retained A perfectly
(1.000) with zero cost to learning B.

**Action.** Recorded; the chapter states this clearly — the protocol, not capacity,
determines the outcome.

---

## 5. The pilot task was "too easy" (retrieval solved it)

**What happened.** The retrieval baseline scored **1.000** on the pilot test set, and
the model scored 0.897. So a non-learning lookup did better than the model.

**What we learned.** The pilot task, as constructed, is retrieval-solvable — so it does
not yet test whether the model *generalizes*, only whether it matches surface form.
This is exactly the "task too easy" outcome the plan anticipated.

**Action.** We did not hide it; we used it to justify harder splits (surface, then
composition), which produced the real findings above.

---

## 6. The human-written test set: 0/16

**What happened.** The trained model solved **0/16** naturally-phrased human prompts —
even simple "add two numbers" phrased as a person would. Read by training exposure, that is
**0 of 11** requests for operations the model had seen (phrasing/surface failures) and
**0 of 5** genuinely held-out composite requests (a structural failure from a separate
cause; see Chapter 15).

**What we learned.** The **surface** reading is corroborated by the **0/11**: the model
learned a *template*, not the *task*, and fails when a real user rephrases a request. The
**0/5** composites are a separate, expected outcome (those operations were never shown) and
are not surface evidence; we do not fold them into the surface claim.

**Action.** Recorded as an external sanity check; it sharpens the book's honest
conclusion.

---

## 7. An attempt at an independent line-edit failed

**What happened.** We dispatched the 85K-char draft to two free models for a proofread.
One leaked its chain-of-thought and broke into noise; the other timed out. No usable
independent review was collected.

**What we learned.** On this occasion, relying on two free hosted endpoints for a
long-document proofread did not work. We report this narrowly: it says nothing general
about all free endpoints, only that *these two calls on this long draft* produced no
usable review. The discipline that matters here is that we did **not** fabricate a
review from unusable output — we recorded the failure.

**Action.** Noted honestly as a production detail (see Appendix C's reproducibility note);
the manuscript's line-edit stands on its own merit, not a fabricated review.

---

## 8. Transient SIGILL crashes during training

**What happened.** Long CPU training runs occasionally crashed with signal 4 (SIGILL)
on the AVX-only Ivy Bridge CPU — intermittently, one run succeeds and the next dies.

**What we learned.** Hardware quirks are real and part of the brew. The apparent fix was
`TORCH_DISABLE_AVX2=1` plus a retry loop (and `OMP_NUM_THREADS=1` for larger models).
We report this as a *workaround we used*, not as a confirmed root-cause repair: the
crashes were intermittent, so a successful retry after setting the variable does not by
itself prove the variable is what fixed it, and we did not independently verify that the
installed torch build actually reads this environment variable. All we can claim is
that wrapping runs in a retry loop made them succeed reliably.

**Action.** Wrapped all long runs in a retry loop; documented the workaround.

---

## 9. Parameter-math and naming mistakes (caught by testing)

**What happened.** Early writing had a parameter-count mis-derivation (didn't sum to
the true 884K/884,224) and the human-test evaluator initially referenced a non-existent
key.

**What we learned.** Always verify arithmetic against the real build, and let the
"test the tester" discipline catch even our own book's numbers.

**Action.** Recomputed from the actual build; fixed the evaluator.

---

## 10. A diagnostic schema we propose but did not measure

Many of the failures above are reported as a single "0.000" pass@1 number. That is
honest but blunt: it does not tell a reader *why* a run failed. A candidate program
can fail at several distinct points — it never parses, it parses but is outside the
capability whitelist, it parses and is in-scope but crashes at runtime, or it runs but
returns the wrong output.

The judge has four stages, and they are these (from
`specs/evaluation_protocol_v0_1.md`): **syntax parse** (does it parse as Python?),
**AST / capability validation** (is it within the sandbox whitelist?), **execution**
(does it run without error under the resource policy?), and **semantic comparison**
(does its output match the expected values?). It would be useful to record **per-stage
failure counts** — how many candidates fell over at each of these four points — so a
reader can see whether a 0.000 is a *syntax collapse* (the model emits garbage) or a
*semantic near-miss* (the model emits a coherent, in-scope program that is just wrong).

Here is precisely what we did and did not record. The *aggregate* stage rates **are**
available: the running evaluator (`src/eval/evaluator_runner.py`) accumulates, per run,
`syntax_rate` (the fraction that pass the evaluator's **combined parse + capability
allowlist validation** — in `src/evaluator/evaluator.py` the `syntax_ok` flag is set only
when `sandbox.validate_source` succeeds, and that call checks parsing *and* the AST
allowlist, so it is not a pure parse rate), `executable_rate` (fraction that passed at
least one hidden test — the evaluator's recorded definition, `execution_ok =
tests_passed > 0`; see Chapter 6),
and `pass_at_1`. So for each reported run we do know, in aggregate, how many candidates
passed combined validation and how many passed at least one test — and the pilot table in
Chapter 10 shows these (0.897
pass@1, with the syntax/executable rates alongside). The *NUL* narrative in the failure
ledger is exactly such a case: the intermediate validation score is what exposed the
truncation problem.

What we did **not** record is the **per-candidate first-failure stage** — i.e. for each
individual rejected candidate, we did not log the specific stage at which it stopped
first (its syntax flag may be false *and* its execution flag false, but we did not
capture which stage caused the rejection in a per-example record). So we have aggregate
stage rates but not a per-candidate stage-resolved audit trail.

> We did **not** collect per-candidate stage-resolved counts for the experiments in this
> book — the evaluator recorded aggregate stage rates plus the final verdict per
> candidate, not the first failure stage for each one individually. Adding that is
> straightforward (the four judge stages already exist as functions) and we leave the
> per-candidate stage accounting as proposed work, not as a measured result.

**The aggregate counts do leave a useful trace.** Even without per-candidate records, we
can build a coarse stage breakdown from the cumulative stage rates, because they share the
same denominator (the number of evaluation records). The three recorded signals are named
here by what they actually measure; in the saved manifests they appear under their
historical keys `syntax_rate`, `executable_rate`, and `pass_at_1`:

```
combined-validation failures     = N − validation_pass
validated, but no test passed   = validation_pass − at_least_one_test_pass
partial passes (≥1 but not all) = at_least_one_test_pass − all_tests_pass
successes                       = all_tests_pass
```

(`validation_pass` = passed combined parse + capability validation = the manifest's
`syntax_rate`; `at_least_one_test_pass` = the manifest's `executable_rate`;
`all_tests_pass` = `pass_at_1`.) Note the second category combines *runtime* failures
with programs that ran cleanly but answered **every** case incorrectly, unless those were
saved separately, so we do **not** split it; the third category is programs that passed
at least one but not all hidden tests, which is narrower than "executed but wrong."
Applying this to the pilot's `stage1` run: the MODEL's validation, at-least-one-test,
and all-tests rates were all 0.897 (over the 300-record test). Since
`validation_pass = at_least_one_test_pass = all_tests_pass`, all **31/300** of the
pilot's non-passing candidates failed the evaluator's **combined syntax-and-capability
validation** — and because pure parsing was not logged separately from allowlist
rejection, these aggregate rates do **not** isolate invalid Python syntax from a
capability reject. We therefore do not say the failures were "all at the parsing stage";
the supported statement is the combined-validation one. It is consistent with the
fragment evidence in Chapter 10, and it is precisely why we insist on the aggregate
stage rates being reported alongside pass@1.

We recommend the same check for the composite runs before attributing their 0.000 to a
*semantic* failure. We applied it: for the `composition_exposure` run's held-out
composites, the MODEL's **syntax_rate = 0.0**, executable_rate = 0.0, and pass@1 = 0.0.
So the composite 0.000 is **not** a record of programs that parsed, ran, and were then
rejected by the semantic comparator — it is a record of candidates that **never passed
the combined parse + capability validation gate** (and, since pure parsing was not logged
separately, we cannot say how many of those were invalid Python versus allowlist
rejects). The dominant recorded failure is at *generation/validation*, before execution,
not at the semantic comparison. This is a substantive qualification of any "semantic
failure" reading of the composition result: what we measured is an aggregate zero, and
its recorded failures
were all pre-execution. (We do not claim the *only* cause is generation or validation —
the cause of the validation-rejecting output is not resolved — only that the recorded
stage rate puts the failure
before the semantic comparison, so "the model understood the pieces but could not combine
them" is **not** supported by these aggregate counts alone.)

---

*The point of this ledger is the opposite of marketing. Every entry above, in its own
way, made the final understanding sharper — and several of them — the broken evaluator,
the wording leak, the task-too-easy result, the 0/16 human test — are among the most
valuable findings in the book precisely because they forced us to be honest.*
