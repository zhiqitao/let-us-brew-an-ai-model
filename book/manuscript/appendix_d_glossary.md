# Appendix D — Glossary

Short definitions of the terms used in this book. Where a term has a standard
meaning that we follow, we say so; where we use it in a deliberately narrow way, we
flag it.

- **AST (Abstract Syntax Tree).** A tree representation of a program's structure,
  stripped of formatting. The sandbox builds an AST of the generated program and
  checks that it uses only allowed constructs.

- **BPE (Byte-Pair Encoding).** A tokenization method that repeatedly merges the most
  common symbol pairs into a single token. It turns text into a fixed-size vocabulary
  of subword pieces.

- **Baseline / rival.** A deliberately simple reference system (here, a keyword
  template-matcher and a TF-IDF retriever) used to interpret the model's score. A
  baseline tells us whether the task was already easy for a simpler machine.

- **Canary (held-out probe).** Here, a never-seen prompt used to check whether the
  model reproduces a stored value or produces a fresh general program. We use the term
  in the held-out-probe sense, not the classic memorization-canary sense.

- **Checkpoint.** A saved copy of the model's weights at a point in training.

- **Composite operation.** An operation that is a combination of two primitives the
  model already knows (e.g. `abs_add = abs(a) + abs(b)`).

- **Continual learning.** Learning a new capability after an old one, and whether the
  old one is retained.

- **Distribution shift.** When the test inputs come from a different distribution than
  the training inputs. Surface change (new wording) is a mild case.

- **Greedy decoding.** Choosing, at each step, the single most likely next token, with
  no sampling. The book reports greedy pass@1.

- **Hidden tests.** Input/expected-output pairs used to grade a generated program. In
  this book they are evaluator-only artifacts: they never enter training.

- **In-distribution.** Tasks drawn from the same distribution as training (here, held
  out in *instances* but the same operation / surface family).

- **Judge.** The execution-based evaluator: it runs the generated program against
  hidden tests and compares outputs (with a semantic comparator and mutation control).

- **Mutation testing.** Generating deliberately-broken programs and checking that the
  hidden-test suite catches them, to measure how discriminating the tests are.

- **pass@1.** The fraction of evaluation prompts for which the model's (greedily
  decoded) program passes all hidden tests.

- **Primitive.** A single, non-composite operation (e.g. `add`, `abs_of`, `list_sum`).

- **Sandbox / Gate A.** The software layer that runs generated programs and rejects any
  that use a construct outside an allowlist (e.g. `import`, `eval`), before they run.

- **Semantic comparator.** The rule that decides whether an output equals an expected
  value. Beyond Python's `==`, it adds float tolerance and strict bool/int handling.

- **Surface / surface form.** The exact wording and identifier names of a request, as
  opposed to its underlying meaning.

- **Train/val/test split.** The division of a dataset into the examples used to train,
  to monitor training, and to evaluate (held out). In this book the splits are
  semantically disjoint by operation or wording family.

- **Validator / Gate B.** The software layer that sits in front of the model and
  declines any incoming request that is not in the designed scope, before the model
  sees it.
