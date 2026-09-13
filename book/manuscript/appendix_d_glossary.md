# Appendix D — Glossary

Short definitions of the terms used in this book. Where a term has a standard
meaning that we follow, we say so; where we use it in a deliberately narrow way, we
flag it.

> **A note on the word "learned."** The book uses "the model learned X" in more than one
> sense, and we want to be explicit about which each claim uses. Sometimes it means the
> model's *optimization fitted the training data* (its loss fell). Sometimes it means *a
> new prompt mapped to a correct program* (an evaluation success). Sometimes it means *an
> abstract arithmetic fact is represented internally* (a mechanism claim). Sometimes it
> means *a novel program structure was generated* (a compositional claim). So when the
> book says "learned," the honest question is always: measured which behavior? We
> therefore do **not** treat "learner vs. parrot" as a binary — a model can be a genuine
> learner of the narrow surface task (its in-distribution score is real) and still not be
> a compositional reasoner. Each claim in the book is scoped to the specific measured
> behavior, not to a general "the model is intelligent" assertion. (The four-question
> capability map in Chapter 22 uses a `[MEASURED]` / `[DERIVED]` notation on the rows it
> labels; not every claim in the book carries an explicit tag, so read the scoping in the
> sentence that introduces each number.)

- **AST (Abstract Syntax Tree).** A tree representation of a program's structure,
  stripped of formatting. The sandbox builds an AST of the generated program and
  checks that it uses only allowed constructs.

- **BPE (Byte-Pair Encoding).** A tokenization method that repeatedly merges the most
  common symbol pairs into a single token. It turns text into a fixed-size vocabulary
  of subword pieces.

- **Baseline / rival.** A deliberately simple reference system (here, a keyword
  template-matcher and a TF-IDF retriever) used to interpret the model's score. A
  baseline tells us whether the task was already easy for a simpler machine.

- **Canary (held-out task-record/pair probe).** Here, a held-out prompt-and-answer *pair*
  (a prompt the model did not see as this exact pair, though its prompt novelty is not
  independently verified — see Appendix C.7) used to check whether the model reproduces a
  stored value or produces a general program. We use the term in the held-out-probe
  sense, not the classic memorization-canary sense.

- **Checkpoint.** A saved copy of the model's weights at a point in training.

- **Composite operation.** An operation that is a combination of two primitives the
  model already knows (e.g. `abs_add = abs(a) + abs(b)`).

- **Continual learning.** Learning a new capability after an old one, and whether the
  old one is retained.

- **Distribution shift.** When the test inputs come from a different distribution than
  the training inputs. Surface change (new wording) is a mild case.

- **Greedy decoding.** Choosing, at each step, the single most likely next token, with
  no sampling.

- **Sampled decoding (what the book's numbers use).** The evaluation calls
  `model.generate` with no temperature override, so it uses the model's default
  **temperature-0.8 multinomial sampling** — a single stochastic sample per record,
  not greedy/argmax. Because it is one draw per record, a single record gives no
  within-*record* estimate of sampling variability, and the repeated records across a run
  are not a perfect distribution over all possible draws. We therefore report it as
  **single-sample execution accuracy / sampled pass@1**. The worked examples are the same
  single-sample output.

- **Hidden tests.** Input/expected-output pairs used to grade a generated program. In
  this book they are evaluator-only artifacts: they never enter training.

- **In-distribution.** Tasks drawn from the same distribution as training (here, held
  out in *instances* but the same operation / surface family).

- **Judge.** The execution-based evaluator: it runs the generated program against
  hidden tests and compares outputs (with a semantic comparator and mutation control).

- **Mutation testing.** Generating deliberately-broken programs and checking that the
  hidden-test suite catches them, to measure how discriminating the tests are.

- **pass@1.** The fraction of evaluation records for which the model's **single
  temperature-0.8 sampled** program passes all of that record's hidden tests (see
  "Sampled decoding" above). One fresh sample is drawn per evaluation record; the fixed
  observed score is a property of the checkpoint, the sampled outputs, the record
  weights, the tests, and the decoding settings — not just of the dataset.

- **Primitive.** A single atom in the *generator's* operation set — e.g. `add`, `abs_of`,
  `list_sum`, `max_of`. It is an **atomic generator entry**, not a structurally
  indivisible program: a "primitive" operation's reference program may itself contain
  sub-expressions (for example the pilot's `cond_abs_max` computes a max of absolute
  values and is genuinely composite). When we say the model trained on "primitives only,"
  we mean it trained on the *named generator operations* as atomic teacher tasks, not
  that each reference program was syntactically indivisible. See the operation dictionary
  in Appendix C (the experiment registry) for which entries are composite.

- **Sandbox / Gate A.** The software layer that runs generated programs and rejects any
  that use a construct outside an allowlist (e.g. `import`, `eval`), before they run.

- **Semantic comparator.** The rule that decides whether an output equals an expected
  value. Beyond Python's `==`, it adds float tolerance and strict bool/int handling.

- **Surface / surface form.** The exact wording and identifier names of a request, as
  opposed to its underlying meaning.

- **Train/val/test split.** The division of a dataset into the examples used to train,
  to monitor training, and to evaluate (held out). In this book the definition of
  "held out" varies by split: the **pilot** split reuses the same 21 prompt strings in
  train/val/test (the test records differ only in hidden-test *input values*), while the
  **surface** and **composition** splits keep a genuinely new prompt wording or
  operation family out of training (train × holdout exact prompt-string overlap is
  reported as 0, per the novelty audit in Appendix C — an audit run on *regenerated*
  samples and checking exact strings, not wording-family membership). So "held out" in
  this book is not a single thing: each split's novelty axis (new prompt vs. new input
  values vs. new operation) is stated explicitly where it matters.

- **Validator / Gate B.** The software layer that sits in front of the model and
  declines any incoming request that is not in the designed scope, before the model
  sees it.
