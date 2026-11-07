# Appendix D — Glossary

Short definitions of the terms used in this book. Where a term has a standard
meaning that we follow, we say so; where we use it in a deliberately narrow way, we
flag it.

Three counting units are defined separately below — a **record**, a **unique prompt**,
and a **held-out family**. They are not interchangeable evidence: a pass on one is not a
pass on the others, so wherever a number is a count, the book says which unit it counts.

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
> capability map in Chapter 20 uses a `[MEASURED]` / `[SUPERSEDED]` notation on the rows it
> labels; not every claim in the book carries an explicit tag, so read the scoping in the
> sentence that introduces each number.)

- **AST (Abstract Syntax Tree).** A tree representation of a program's structure,
  stripped of formatting. The sandbox builds an AST of the generated program and
  checks that it uses only allowed constructs.

- **BPE (Byte-Pair Encoding).** A tokenization method that repeatedly merges the most
  common symbol pairs into a single token. It turns text into a fixed-size vocabulary
  of subword pieces. **The tokenizer this book actually uses is *not* BPE:** it is a
  greedy character/whole-word vocabulary tokenizer — 256 character tokens plus frequent
  whole words, encoded by longest match (see Chapter 8). The earlier "compact BPE"
  wording in Chapter 8 was wrong and has been corrected (P1-07).

- **Baseline / rival.** A deliberately simple reference system (here, a keyword
  template-matcher and a TF-IDF retriever) used to interpret the model's score. A
  baseline tells us whether the task was already easy for a simpler machine.

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

- **Held-out.** Kept out of training and used for an evaluation. Which axis is held out
  differs by split — prompt string, wording family, operation ID, or (in the pilot) only
  the hidden-test input values — so the book states the axis wherever "held out" carries
  a claim; see "Train/val/test split" below.

- **Held-out family (held-out template family).** A template family — a phrasing
  skeleton the teacher renders with — kept out of training entirely and used only for
  evaluation. It is the strongest of the three novelty units: every prompt in a held-out
  family is new *and* comes from a skeleton the model never saw, whereas a held-out
  record or a held-out prompt string can still reuse a familiar skeleton. Operations
  with a single family (`abs_of`, `cond_abs_max`) have no held-out family to offer, so
  they are excluded from held-out-wording cells rather than counted in them.

- **Held-out program probe (formerly called a "canary").** Here, a held-out prompt-and-answer *pair*
  (a prompt the model did not see as this exact pair, though its prompt novelty is not
  independently verified — see Appendix C.7) used to check whether the model reproduces a
  stored value or produces a general program. We use the term in the held-out-probe
  sense, not the classic memorization-canary sense.

- **Hidden tests.** Input/expected-output pairs used to grade a generated program. In
  this book they are evaluator-only artifacts: they never enter training.

- **In-distribution.** Tasks drawn from the same distribution as training (here, held
  out in *instances* but the same operation / surface family).

- **Joint / interleaved training (A+B from start).** Training on both task groups'
  examples interleaved from the beginning of training. Earlier drafts of Chapter 18
  labeled this condition "replay"; we renamed it because *replay* properly means
  continuing from an already-A-trained checkpoint with A examples mixed back in — a
  design this book did **not** run (P1-14).

- **Judge.** The execution-based evaluator: it runs the generated program against
  hidden tests and compares outputs (with a semantic comparator and mutation control).

- **Mutation testing.** Generating deliberately-broken programs and checking that the
  hidden-test suite catches them, to measure how discriminating the tests are.

- **New IDs ("new task IDs").** Where the book says *new IDs* — e.g. the pilot's
  held-out test — it means new **task/test/execution IDs**: records whose hidden-test
  *input values* differ while the prompt string and target program stay the same. It does
  **not** mean new *variable identifier names*, which is the separate Stage-3 "new
  identifiers" surface test (`a,b` → `left,right`).

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

- **Record.** One generated task instance: a semantic record rendered into one prompt
  plus its own hidden tests, with its own `task_id` and its own `split`. The record is
  the book's default counting unit — but a record is not a *unique prompt*: many records
  can carry one prompt string, and a record can be new while its prompt is not (the
  pilot's test records are new records under reused prompts). A count of records is
  therefore evidence about records only.

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

- **Unique prompt.** A distinct prompt *string*, counted once however many records carry
  it. The pilot's train/val/test reuse the same 21 prompt strings, so its record count
  and its unique-prompt count are very different numbers; a novelty claim has to say
  which unit it is counting — record, unique prompt, or held-out family — because these
  are separate evidence units with separate strength (see "Held-out family" above).

- **Validator / Gate B.** The software layer that sits in front of the model and
  declines any incoming request that is not in the designed scope, before the model
  sees it.
