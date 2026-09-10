
The design requires that we do not sanitize the journey into a success story. This is
the honest record of everything that went wrong, was surprising, or was a failed
attempt — because each of these taught us something, and several are as valuable as
any success.

Each entry: what happened, what we learned, and what we did about it.

---

## The evaluator reported the model at 0.000 — but the model was fine

**What happened.** On the very first Stage-1 evaluation, the trained model scored a
reported **0.000** (syntax failure on every problem). This looked like a total failure
of the approach.

**What we found.** The model was actually producing correct programs — but our
generation output appended null-byte padding, and Python's parser rejects null bytes.
So the **judge** was scoring valid programs as syntax errors.

**What we learned.** The most important lesson of the book, demonstrated on ourselves:
*never trust a number from a system we have not audited.* Fixing the judge revealed the
model's true 0.897. If we'd taken 0.000 at face value, we'd have wrongly concluded the
approach failed.

**Action.** Fixed `generate_code` to truncate at the first null byte; re-ran; got 0.897.

---

## The pilot wording leaked the answer (100% predictability)

**What happened.** The leakage audit trained a trivial TF-IDF classifier to predict the
operation from the natural-language prompt. It succeeded **100%** of the time.

**What we learned.** Our first renderer's wording was so tied to the operation that a
model "succeeding" might just be exploiting the phrasing, not learning the computation.
This is *why* the surface-generalization tests matter.

**Action.** Recorded as finding-001; noted the pilot is fine for Stage 1 but must add
wording-family holdouts before any surface test.

---

## A bigger model did NOT fix composition

**What happened.** We scaled the model across a ~33× range (0.88M → 29.3M) expecting
the composition boundary to move. It did not: composition stayed at **0.000** at all
four sizes (0.88M, 6.5M, 10.2M, 29.3M).

**What we learned.** At ~1–30M parameters, compositional generalization failure is
**not a capacity ceiling**. It is a structural/learning limit that scaling alone does
not resolve. This is a genuine negative result that redirects the investigation.

**Action.** Recorded in `docs/experiments/scaling_composition.md`.

---

## Sequential training caused catastrophic forgetting (A → 0.000)

**What happened.** Teaching the model lists after arithmetic, sequentially, completely
destroyed the arithmetic (A-retention **0.000**).

**What we learned.** Catastrophic forgetting is real and severe here — but it is a
**procedure** problem, not a fate. Replay (interleaving A and B) retained A perfectly
(1.000) with zero cost to learning B.

**Action.** Recorded; the chapter states this clearly — the protocol, not capacity,
determines the outcome.

---

## The pilot task was "too easy" (retrieval solved it)

**What happened.** The retrieval baseline scored **1.000** on the pilot test set, and
the model scored 0.897. So a non-learning lookup did better than the model.

**What we learned.** The pilot task, as constructed, is retrieval-solvable — so it does
not yet test whether the model *generalizes*, only whether it matches surface form.
This is exactly the "task too easy" outcome the plan anticipated.

**Action.** We did not hide it; we used it to justify harder splits (surface, then
composition), which produced the real findings above.

---

## The human-written test set: 0/16

**What happened.** The trained model solved **0/16** naturally-phrased human prompts —
even simple "add two numbers" phrased as a person would.

**What we learned.** This is the external, real-world corroboration of the surface
finding. The model learned a *template*, not the *task*. The moment a real user phrases
a request differently, it fails.

**Action.** Recorded as an external sanity check; it sharpens the book's honest
conclusion.

---

## The free-model proofread returned degraded output

**What happened.** We dispatched the 85K-char draft to two free models for a proofread.
One leaked its chain-of-thought and broke into noise; the other timed out. No usable
independent review was collected.

**What we learned.** Free endpoints are flaky for long documents, and we should not
fabricate fixes from unusable output. We were honest about this rather than pretend a
review happened.

**Action.** Noted honestly; the book's line-edit stands on its own merit, not a
fabricated review.

---

## Transient SIGILL crashes during training

**What happened.** Long CPU training runs occasionally crashed with signal 11 (SIGILL)
on the AVX-only Ivy Bridge CPU — intermittently, one run succeeds and the next dies.

**What we learned.** Hardware quirks are real and part of the brew. The fix is
`TORCH_DISABLE_AVX2=1` plus a retry loop (and `OMP_NUM_THREADS=1` for larger models).

**Action.** Wrapped all long runs in a retry loop; documented the workaround.

---

## Parameter-math and naming mistakes (caught by testing)

**What happened.** Early writing had a parameter-count mis-derivation (didn't sum to
the true 8.94M/884K) and the human-test evaluator initially referenced a non-existent
key.

**What we learned.** Always verify arithmetic against the real build, and let the
"test the tester" discipline catch even our own book's numbers.

**Action.** Recomputed from the actual build; fixed the evaluator.

---

*The point of this ledger is the opposite of marketing. Every entry above, in its own
way, made the final understanding sharper — and several of them — the broken evaluator,
the wording leak, the task-too-easy result, the 0/16 human test — are among the most
valuable findings in the book precisely because they forced us to be honest.*
