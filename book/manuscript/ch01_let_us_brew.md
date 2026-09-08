# 1. Let Us Brew an AI Model

A tiny model is given one job. It reads a sentence — *"write a function that takes
two numbers, a and b, and returns their sum"* — and it writes back the right Python:

```python
def solve(a, b):
    return a + b
```

We run the hidden tests. It passes. If this were a demo, we'd move on.

But this is not a demo. So before we celebrate, we ask the one question that turns
this whole book into an experiment rather than a party trick:

> **Why did it get it right?**

Maybe it genuinely learned that "sum" and "a and b" mean "add them together." Maybe
it memorized that exact sentence from training. Maybe it noticed this was nearly
identical to an example it saw and copied the answer. Maybe a much dumber machine —
one that does nothing but look up the closest training example — could have done the
same thing. Or maybe our test wasn't as hard as we thought.

Making the model answer is easy. **Knowing why it answered is the whole game.**

## One job, and a way to check it

We give the model exactly one, narrow, checkable job:

> **read a plain-English programming request → produce a working Python program**

Then we *run* that program against hidden tests. That single choice — executable
output plus hidden tests — is what makes this a real experiment instead of a showcase,
because it hands us the things a language-model toy usually lacks:

- inputs we control,
- code we can actually execute,
- an objective pass/fail,
- data we can generate in any quantity,
- difficulty we can dial up or down,
- tests we can keep hidden from the model,
- splits we can design to expose memorization,
- audits we can run to catch shortcuts.

## What this book is (and isn't)

This is not a transformer tutorial. It is not a guide to chatbots, agents, or coding
assistants. It is a careful, honest investigation of a single question:

> **How much structured programming capability can a small language model actually
> learn — and how do we tell whether it *learned* it, rather than memorized it or
> found a cheap shortcut?**

## The part that's actually hard

The natural guess is that *building* a small model is the hard part. It isn't. Once
the laboratory works, a ~0.9 million-parameter model will reliably turn a handful of
programming sentences into correct Python — in-distribution, that is nearly easy.

The hard part is everything after: proving it didn't just copy, checking whether it
still works when you change the *words* but not the *computation*, testing whether it
can *combine* two things it knows into a third thing it's never seen, and auditing our
own evaluator to make sure the number it reports means anything.

This book builds a laboratory, runs those tests, and reports — plainly — what
happened. Including the moments the model fell flat, and the moment we discovered our
own measuring stick was broken, not the model.

**The model was the instrument. The experiment was the subject. Let's brew.**
