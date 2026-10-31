# 9. The First Brew

Everything's built. Now the moment of truth: we train the model for the first time and
watch what happens.

This chapter is deliberately unheroic. The goal isn't a triumphant result — it's to
confirm the loop works and to see the model's honest behavior as it learns. It is
the first time a recipe we have been assembling is finally run: we are not
hoping for a masterpiece, we are checking that the oven works and nothing explodes.
And for anyone who has brewed anything — beer, coffee, bread — the *first* batch is
never about the product. It is about learning our equipment, our ingredients, and our
own impatience. This chapter is that first batch.

## The data

1400 training tasks: a natural-language specification paired with its reference
Python program. The model's job is to read the spec and produce the code. Each task is
a single semantic record — one idea — rendered three ways (a program, an English
instruction, a set of hidden tests), so the data is internally consistent by
construction. We do **not** need to worry as much that a prompt says "sum" but its answer
subtracts, because both came from the same seed. That said, "same seed" is not a
guarantee: a wrong semantic record would be wrong in all three renderings at once, so
the consistency reduces (but does not eliminate) the risk of a prompt/answer mismatch.

The dataset is a three-way split — **1,400 train / 300 validation / 300 test** records,
the counts recorded in `artifacts/datasets/pilot_manifest.json`. The validation split
was generated but never used for model selection: `scripts/train.py` loads it and
evaluates only on the test set, so every number this stage reports is a test-set number.

We hold out a separate 300-record test set. Because the teacher uses a task-ID seed to
change only the hidden-test *inputs* while the prompt string and reference program stay
the same, those 300 test records **reuse the same 21 prompt strings** as training (see the
novelty audit in Appendix C); what is new at test time is the task ID and the
execution-test values, not the prompt. We state this plainly, because it shapes exactly
what the pilot's 0.897 does and does not establish: familiar-prompt program generation
on fresh execution inputs, not generalization to a new request.

## The model

The student is a small, deliberately plain decoder-only transformer: 4 layers, hidden
dimension 128, 4 attention heads, a compact 291-token vocabulary, and 128-token
context. Total **884,224 parameters** — but we report the split honestly, because it
matters more than the round number: **53,632** are the embeddings (the token and
positional tables, which store the vocabulary and position), and **830,592** are the
non-embedding weights. The embeddings are trainable representations, not a static lookup —
but a tiny model's parameter count is often dominated by them, and we never want a "0.9M
parameter model" claim to hide that most of its parameters live there.

## The training process, step by step

![The brew loop](figures/fig_brew.png)

Every experiment is one pass around this loop: generate, train, measure, and let
what we measured shape what we generate next.

Training a small transformer is not a single action; it is a loop repeated 1,500
times. At each step:

1. We grab a batch of 16 tasks and tokenize each as one sequence: the natural-language
   prompt, a newline, then the reference program.
2. The model reads the prompt and predicts each *next* token in the combined sequence.
   This is the standard **next-token objective** — the model's only job is to guess
   the next word, given everything before it. It is a deceptively simple task, and it
   is the entire basis of how these models learn to write.
3. We measure the difference between the model's prediction and the actual next token
   (the cross-entropy loss), take the gradient, and nudge the parameters with the
   **AdamW** optimizer at learning rate **1e-3**, clipping the gradient magnitude to
   keep training stable.
4. Repeat.

We print the loss every 200 steps so we can watch it behave. Here is what it actually
did:

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

That is a large, clean drop — from 5.84 to about 0.02 in 1500 steps. (The per-step log
above reads 0.019 at the last step; the recorded final training loss in the experiment
manifest is 0.0208 — the same quantity reported at slightly different rounding or on a
different averaging window, both meaning the loss has collapsed to a low floor.) A
provenance note: only that final value, **0.0208**, is machine-recorded in the manifest
(`artifacts/manifests/stage1.json`) — the intermediate values in the log above are
illustrative, transcribed from the printed training log, and should be read
accordingly, as a picture of the curve rather than as manifest-verified figures. Two
things about this curve are worth sitting with, because they reveal more than the final
number.

**First, the shape tells us the *training loop is working*, nothing more.** The
loss falls steeply in the first 200 steps (5.84 → 0.029), then flattens out near a
floor. This is the curve we expect from a functioning loop that is fitting the data:
rapid improvement at first, then diminishing returns. If instead the loss had wobbled
or stayed high, we would have had a debugging problem on our hands, not a training
result. But a *converging* loss by itself does not distinguish learning from
memorization — both produce a falling loss. That distinction is exactly what the
upcoming evaluations, not the loss curve, have to settle.

**Second, the *final* value is not the interesting number.** A loss of 0.019 means the
model can predict the next token of the *training* sequence almost perfectly. That
tells us it fits the training data — and nothing more. This is the book's recurring
motif, and it is worth saying loudly: **a falling training loss, and even a very low
one, is not evidence of learning.** It is evidence of fitting. The distinction is the
entire point of the experiment.

## What the training process felt like (the brewing experience)

Anyone who has trained a model knows the peculiar rhythm of it. We set a batch of
runs going and we wait, checking the loss every few minutes with a combination of hope
and suspicion. The first steps are the most honest — a fresh, random model has loss
near the log of the vocabulary size, because its best guess is uniform. That initial
5.84 is exactly what a model that knows nothing looks like.

Then, if things are working, the loss starts to fall, and a strange thing happens: the
drop is *so* fast in the first couple hundred steps that we wonder whether it is real
or whether something is broken. In this case the model reached near-floor loss within
200 steps. The rest of the training is just the model quietly polishing the last
fraction of a point.

There is also a genuine practical question that arises during training: **how do we
know it hasn't crashed mid-run?** We use periodic **training checkpoints** that record
the state at regular intervals *during* the run, so that a crash at step 1200 loses at
most the steps since the last save. A single save only at the end of training — say,
just before evaluation — does **not** protect against a mid-run crash; it only protects
the completed run. So we keep intermediate checkpoints, not just a final one. This is
a small discipline, but it has saved us more than once — a training run on this
hardware takes real time, and we do not want to lose it to an unplanned stop.

## The honest caveat

A falling training loss — and even a very low one — is *not* evidence of learning. We
saw this in the pilot and it is the book's recurring motif. The training loss tells us
the model fits the training data. It does not tell us it can *generalize* to unseen
problems, or that it learned the computation rather than the surface form.

So after training, the only losses that matter are the *held-out* ones: how well does
the model do on problems it never saw? That is Chapter 10's question, and the answer
there is the real measurement of this brew.

## Why the details of the training process matter

It is tempting to skip the mechanics and jump to results. But the whole premise of
this book is that *the experiment is the subject*, and an experiment we cannot
reproduce is not an experiment. The exact vocabulary size, the number of layers, the
batch size, the learning rate, the number of steps — these are not trivia. They are
the conditions under which every later claim is true. If we change one and the result
changes, that tells us something; if we change two and the result changes, we can no
longer say which one caused it. This is the **one-variable discipline** that governs
every experiment in the book, and it is why we record the configuration so carefully
in a manifest alongside every result. A reader should be able to take our numbers and run
the same configuration — and reproduce the *procedure*, not necessarily the identical
sampled scores (a fresh stochastic rerun under temperature-0.8 sampling may differ slightly,
and the repository is not yet public; see Appendix C.10). The recording is what makes the
procedure reproducible, even before scores are confirmed on an independent run.

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
