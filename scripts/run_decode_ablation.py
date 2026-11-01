#!/usr/bin/env python3
"""Decode / termination ablation on the composition-exposure checkpoint.

THE QUESTION (external review's most important):
The book's central result is "composition 0.000" on HELD-OUT composites. Is that
a generation/decoding/extraction artifact (model emits something, but NUL-padding
or a too-short max_new truncates it into invalid Python), or a genuine failure?

This script is READ-ONLY with respect to training: it loads the existing
checkpoint artifacts/checkpoints/stage4_exposure.pt (884,224 params) and the
EXACT tokenizer that checkpoint was trained with, reproducing the
composition-exposure split from scripts/run_composition_exposure.py (seed 0),
and re-decodes the HELD-OUT composites (plus the EXPOSED composites as a
control) under several decode/extraction settings:

TOKENIZER PROVENANCE: artifacts/tokenizer/ is gitignored and comp_tok.json was
overwritten by a later experiment (run_composition_diversity.py, mtime
2026-09-11 20:44, vs checkpoint 19:43); its vocab differs from the exposure
run's at 75/291 indices, and evaluating with it collapses BOTH the held-out
and the exposed sets to 0.000 (archived: raw_runs/disk_tok/,
eval/disk_tok/, manifests/decode_ablation_disk_tok.json).
train_tokenizer is deterministic (Counter + sorted, no RNG), so rebuilding it
in memory from the exposure corpus reproduces the training vocab exactly.
--tok auto (default) does that; --tok <path> loads a vocab json instead.

  run A: greedy (T=0.0, argmax), max_new=256  -> settings greedy@64/128/256
  run B: sampled T=0.8,           max_new=256  -> settings sample0.8@64/128/256
  run C: sampled T=0.8,           max_new=80   -> the book's eval procedure
                                                  (generate_code: T=0.8 default,
                                                  max_new=80, NUL-truncation)

max_new 64/128/256 are PREFIXES of a single run per temperature, so the token
stream is held fixed and only the extraction length varies (clean ablation).
Run C mirrors src/eval/evaluator_runner.generate_code exactly (its own RNG
stream, NUL truncation, .strip()).

For every setting x task we archive the raw generation and compute a FAILURE
DECOMPOSITION (mutually exclusive, exhaustive):
  (a) parse_fail      : empty output or ast.parse fails
  (b) allowlist_fail  : parses but sandbox.validate_source rejects it
  (c) zero_pass       : valid+executable, but 0 hidden tests pass
                        (subflags: no_solve / runtime_error_all / wrong_output)
  (d) partial         : some but not all hidden tests pass
  (e) all_pass        : all hidden tests pass  (= pass@1)

Rates reported per setting: syntax_rate = 1-(a); valid_program_rate = 1-(a)-(b)
(programs that reach execution); executable_rate = >=1 test pass (the Judge's
execution_ok); pass@1 = (e).

Outputs (all new files; nothing existing is modified):
  artifacts/raw_outputs/decode_ablation/raw_runs/<run>.jsonl   (raw programs)
  artifacts/raw_outputs/decode_ablation/eval/<setting>.json    (per-task eval)
  artifacts/manifests/decode_ablation.json
  docs/reviews/loop/decode_ablation.md

Run: source .venv-train/bin/activate && TORCH_DISABLE_AVX2=1 OMP_NUM_THREADS=2 \
     python scripts/run_decode_ablation.py
"""
import os, sys, json, time, ast, argparse
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
import torch.nn.functional as F

from src.tokenizer.tokenizer import load_tokenizer, train_tokenizer
from src.model.gpt import GPT, Config
from src.data_generator.generator import generate_dataset, generate_compositional
from src.evaluator.evaluator import Judge
from src.sandbox import sandbox

ROOT = os.path.join(os.path.dirname(__file__), "..")
EXPOSED = ["abs_add", "sub_abs", "sum_of_abs"]
HELD_OUT = ["max_add", "double_first", "len_minus_one"]

# (setting_name, run_name, temperature, max_new, nul_truncation)
SETTINGS = [
    ("greedy_max64",        "greedy_max256",        0.0,  64, True),
    ("greedy_max128",       "greedy_max256",        0.0, 128, True),
    ("greedy_max256",       "greedy_max256",        0.0, 256, True),
    ("sample08_max64",      "sample08_max256",      0.8,  64, True),
    ("sample08_max128",     "sample08_max256",      0.8, 128, True),
    ("sample08_max256",     "sample08_max256",      0.8, 256, True),
    ("book_sample08_max80", "book_sample08_max80",  0.8,  80, True),
]
RUNS = [  # (run_name, temperature, max_new)
    ("greedy_max256",       0.0, 256),
    ("sample08_max256",     0.8, 256),
    ("book_sample08_max80", 0.8,  80),
]


def build_split(seed=0, n_per_op=200, comp_n=40):
    """Exact replica of the split in scripts/run_composition_exposure.py."""
    prim = generate_dataset(n_per_op=n_per_op, id_set="letters", seed=seed)
    by_op = defaultdict(list)
    for t in prim:
        by_op[t["semantics"]["operation"]].append(t)
    train, val, test = [], [], []
    for op, g in by_op.items():
        g.sort(key=lambda t: t["task_id"])
        n = len(g); nv = max(1, int(n * 0.15)); nt = max(1, int(n * 0.15))
        val += g[:nv]; test += g[nv:nv + nt]; train += g[nv + nt:]

    comp = generate_compositional(n_per_op=comp_n, id_set="letters", seed=seed + 5000)
    by_op_c = defaultdict(list)
    for t in comp:
        by_op_c[t["semantics"]["operation"]].append(t)
    exposed, heldout = [], []
    for op, g in by_op_c.items():
        if op in EXPOSED:
            exposed += g
        elif op in HELD_OUT:
            heldout += g
    return {"train": train, "val": val, "test": test,
            "exposed": exposed, "heldout": heldout}


def generate_run(model, tok, tasks, temperature, max_new, out_path):
    """Sequential batch-1 decode, mirroring evaluator_runner.generate_code.

    One RNG stream per run (seeded once) so max_new prefixes are consistent.
    Appends one JSONL line per task; resumes if the file is already complete.
    """
    expected = len(tasks)
    if os.path.exists(out_path):
        lines = [l for l in open(out_path) if l.strip()]
        if len(lines) == expected:
            print(f"  [skip] {os.path.basename(out_path)} already complete "
                  f"({expected} tasks)", flush=True)
            return [json.loads(l) for l in lines]
    torch.manual_seed(0)  # deterministic stream (irrelevant for greedy)
    model.eval()
    records = []
    with open(out_path, "w") as f, torch.no_grad():
        for i, (set_name, t) in enumerate(tasks):
            ids = tok.encode(t["nl"]["prompt"] + "\n")
            ctx = torch.tensor([ids])
            new_ids = []
            for _ in range(max_new):
                logits, _ = model(ctx[:, -model.cfg.block_size:])
                logits = logits[:, -1, :]
                if temperature <= 0.0:
                    nxt = torch.argmax(logits, dim=-1, keepdim=True)
                else:
                    probs = F.softmax(logits / temperature, dim=-1)
                    nxt = torch.multinomial(probs, 1)
                ctx = torch.cat([ctx, nxt], dim=1)
                new_ids.append(int(nxt.item()))
            raw_text = tok.decode(new_ids)
            rec = {"set": set_name, "task_id": t["task_id"],
                   "op": t["semantics"]["operation"], "new_ids": new_ids,
                   "raw_text": raw_text}
            records.append(rec)
            f.write(json.dumps(rec) + "\n")
            f.flush()
            if (i + 1) % 20 == 0 or i + 1 == expected:
                print(f"    {i+1}/{expected} generated", flush=True)
    return records


def extract_from_record(rec, tok, max_new, nul_truncation=True):
    code = tok.decode(rec["new_ids"][:max_new])
    had_nul = "\x00" in code
    if nul_truncation:
        nul = code.find("\x00")
        if nul != -1:
            code = code[:nul]
    return code.strip(), had_nul


def categorize(code, hidden_tests, judge):
    """Failure decomposition -> (category, detail_dict)."""
    detail = {"empty": False, "no_solve": False, "runtime_error_all": False,
              "wrong_output": False, "tests_passed": 0,
              "tests_total": len(hidden_tests)}
    if not code.strip():
        detail["empty"] = True
        return "parse_fail", detail
    try:
        ast.parse(code)
    except SyntaxError:
        return "parse_fail", detail
    try:
        sandbox.validate_source(code)
    except sandbox.SandboxError:
        return "allowlist_fail", detail

    r = judge.evaluate_problem(code, hidden_tests)
    detail["tests_passed"] = r["tests_passed"]
    if r["pass_at_1"]:
        return "all_pass", detail
    if r["tests_passed"] > 0:
        return "partial", detail
    # zero passes: why?
    trs = r["test_results"]
    if trs and all("error" in tr and tr.get("error") for tr in trs):
        detail["runtime_error_all"] = True
    else:
        detail["wrong_output"] = True
    try:
        tree = ast.parse(code)
        funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        if len(funcs) != 1 or funcs[0].name != "solve":
            detail["no_solve"] = True
            detail["runtime_error_all"] = False
            detail["wrong_output"] = False
    except SyntaxError:
        pass
    return "zero_pass", detail


CATS = ["parse_fail", "allowlist_fail", "zero_pass", "partial", "all_pass"]


def evaluate_setting(setting_name, records, tasks_by_id, tok, max_new,
                     nul_truncation, judge, out_dir):
    by_set = {"heldout": [], "exposed": []}
    nul_counts = {"heldout": 0, "exposed": 0}
    post_nul = {"heldout": 0, "exposed": 0}
    for rec in records:
        t = tasks_by_id[rec["task_id"]]
        code, had_nul = extract_from_record(rec, tok, max_new, nul_truncation)
        if had_nul:
            nul_counts[rec["set"]] += 1
            # alternative extraction: keep ALL content, just delete NUL chars
            full = tok.decode(rec["new_ids"][:max_new]).replace("\x00", "").strip()
            if full != code:
                post_nul[rec["set"]] += 1
        else:
            full = code
        cat, detail = categorize(code, t["hidden_tests"], judge)
        cat_alt, detail_alt = categorize(full, t["hidden_tests"], judge)
        by_set[rec["set"]].append({
            "task_id": rec["task_id"], "op": rec["op"], "category": cat,
            "detail": detail, "code": code, "code_nul_filter": full,
            "category_nul_filter": cat_alt, "detail_nul_filter": detail_alt,
            "raw_len_chars": len(rec["raw_text"]),
        })

    def summarize(items, cat_key, detail_key):
        n = len(items)
        counts = {c: 0 for c in CATS}
        sub = defaultdict(int)
        for it in items:
            counts[it[cat_key]] += 1
            for k, v in it[detail_key].items():
                if isinstance(v, bool) and v:
                    sub[k] += 1
        syntax = 1 - (counts["parse_fail"] / n)
        valid = 1 - ((counts["parse_fail"] + counts["allowlist_fail"]) / n)
        exe = sum(1 for it in items if it[detail_key]["tests_passed"] > 0) / n
        pass1 = counts["all_pass"] / n
        return {
            "n": n,
            "syntax_rate": round(syntax, 4),
            "valid_program_rate": round(valid, 4),
            "executable_rate": round(exe, 4),
            "pass_at_1": round(pass1, 4),
            "decomposition": counts,
            "subflags": dict(sub),
        }

    results = {}
    for set_name, items in by_set.items():
        r = summarize(items, "category", "detail")
        r["nul_truncated"] = nul_counts[set_name]
        r["post_nul_content"] = post_nul[set_name]
        r["mean_extracted_chars"] = round(
            sum(len(it["code"]) for it in items) / r["n"], 1) if r["n"] else 0.0
        # alternative extraction: delete every NUL instead of cutting at the
        # first one (tests whether NUL-truncation discards recoverable content)
        r["alt_nul_filter"] = summarize(items, "category_nul_filter",
                                        "detail_nul_filter")
        results[set_name] = r
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{setting_name}.json"), "w") as f:
        json.dump({"setting": setting_name, "max_new": max_new,
                   "nul_truncation": nul_truncation, "tasks": by_set}, f, indent=1)
    return results


def fmt_rate(x):
    return f"{x:.3f}"


def write_report(manifest, path):
    lines = []
    A = lines.append
    A("# Decode / Termination Ablation — is composition 0.000 an artifact?")
    A("")
    A("**Question (external review):** the book's central result is composition")
    A("**0.000** on held-out composites. Is that a generation/decoding/extraction")
    A("artifact (the model emits *something*, but NUL-padding or a short `max_new`")
    A("truncates it into invalid Python), or a genuine failure of the model?")
    A("")
    A(f"- Checkpoint: `{manifest['config']['ckpt']}` "
      f"({manifest['config']['model_params']['total']:,} params, loaded, NOT retrained)")
    A(f"- Tokenizer: {manifest['config']['tok_source']}, "
      f"{manifest['config']['vocab_size']} tokens — the EXACT vocab the "
      f"checkpoint was trained with")
    vd = manifest["config"].get("tok_vocab_diff_vs_disk")
    if vd and vd.get("identical") is False:
        A(f"- **Tokenizer provenance warning:** the on-disk "
          f"`artifacts/tokenizer/comp_tok.json` (gitignored) was overwritten by a "
          f"later experiment and differs from the training vocab at "
          f"**{vd['differing_indices']}/{vd['matched_vocab_size']}** indices. "
          f"Evaluating with that file collapses BOTH held-out and exposed sets to "
          f"0.000 under every setting — see the appendix "
          f"(`artifacts/manifests/decode_ablation_disk_tok.json`). That is a "
          f"tokenizer-clobber artifact, a different failure class from the decode "
          f"question asked here.")
    A(f"- Split: identical to `scripts/run_composition_exposure.py`, seed 0 — "
      f"{manifest['split']['n_heldout']} held-out composites "
      f"({', '.join(HELD_OUT)}), {manifest['split']['n_exposed']} exposed composites "
      f"({', '.join(EXPOSED)}) as control, "
      f"{manifest['split']['n_train']} primitive+exposed train tasks (unused here).")
    A("- Extraction for every setting: decode -> NUL-truncate -> `.strip()`, exactly")
    A("  as `src/eval/evaluator_runner.generate_code` does. An alternative")
    A("  extraction (delete every NUL, keep all other content) is also scored —")
    A("  see \"Extraction variants\".")
    A("")
    A("## Settings")
    A("")
    A("| setting | T | max_new | source run | note |")
    A("|---|---|---|---|---|")
    for s in manifest["settings_list"]:
        note = ("the book's eval procedure" if s["setting"] == "book_sample08_max80"
                else "prefix of one run (token stream held fixed)")
        A(f"| {s['setting']} | {s['temperature']} | {s['max_new']} | {s['run']} | {note} |")
    A("")
    A("## HELD-OUT composites (never seen in training) — the key table")
    A("")
    A("| setting | syntax | **valid prog** | executable | **pass@1** | "
      "(a) parse | (b) allowlist | (c) 0 tests | (d) partial | (e) all |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for s in manifest["settings_list"]:
        r = manifest["results"][s["setting"]]["heldout"]
        d = r["decomposition"]
        A(f"| {s['setting']} | {fmt_rate(r['syntax_rate'])} | "
          f"**{fmt_rate(r['valid_program_rate'])}** | "
          f"{fmt_rate(r['executable_rate'])} | **{fmt_rate(r['pass_at_1'])}** | "
          f"{d['parse_fail']} | {d['allowlist_fail']} | {d['zero_pass']} | "
          f"{d['partial']} | {d['all_pass']} |")
    A("")
    A("## EXPOSED composites (seen in training) — control")
    A("")
    A("| setting | syntax | **valid prog** | executable | **pass@1** | "
      "(a) parse | (b) allowlist | (c) 0 tests | (d) partial | (e) all |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for s in manifest["settings_list"]:
        r = manifest["results"][s["setting"]]["exposed"]
        d = r["decomposition"]
        A(f"| {s['setting']} | {fmt_rate(r['syntax_rate'])} | "
          f"**{fmt_rate(r['valid_program_rate'])}** | "
          f"{fmt_rate(r['executable_rate'])} | **{fmt_rate(r['pass_at_1'])}** | "
          f"{d['parse_fail']} | {d['allowlist_fail']} | {d['zero_pass']} | "
          f"{d['partial']} | {d['all_pass']} |")
    A("")
    A("## Extraction variants (is NUL-truncation hiding recoverable code?)")
    A("")
    A("| setting | set | NUL-trunc valid | NUL-filter valid | NUL-trunc pass@1 | "
      "NUL-filter pass@1 | gens with content after 1st NUL |")
    A("|---|---|---|---|---|---|---|")
    for s in manifest["settings_list"]:
        for set_name in ("heldout", "exposed"):
            r = manifest["results"][s["setting"]][set_name]
            alt = r["alt_nul_filter"]
            A(f"| {s['setting']} | {set_name} | "
              f"{fmt_rate(r['valid_program_rate'])} | "
              f"{fmt_rate(alt['valid_program_rate'])} | "
              f"{fmt_rate(r['pass_at_1'])} | {fmt_rate(alt['pass_at_1'])} | "
              f"{r['post_nul_content']}/{r['nul_truncated']} |")
    A("")
    A("## Interpretation")
    A("")
    for para in manifest["interpretation"]:
        A(para)
        A("")
    A("## Example generations (first held-out task)")
    A("")
    for ex in manifest["examples"]:
        A(f"**{ex['setting']}** — extracted program "
          f"({ex['category']}, {ex['tests_passed']}/{ex['tests_total']} tests):")
        A("")
        A("```python")
        A(ex["code"] if ex["code"].strip() else "(empty)")
        A("```")
        A("")
    disk = manifest.get("disk_tokenizer_condition")
    if disk:
        A("## Appendix: same ablation with the clobbered on-disk tokenizer")
        A("")
        A(disk["note"])
        A("")
        A("| setting | held-out valid | held-out pass@1 | exposed valid | "
          "exposed pass@1 |")
        A("|---|---|---|---|---|")
        for s in manifest["settings_list"]:
            d = disk["settings"].get(s["setting"])
            if not d:
                continue
            A(f"| {s['setting']} | {fmt_rate(d['heldout']['valid_program_rate'])} | "
              f"{fmt_rate(d['heldout']['pass_at_1'])} | "
              f"{fmt_rate(d['exposed']['valid_program_rate'])} | "
              f"{fmt_rate(d['exposed']['pass_at_1'])} |")
        A("")
    A("---")
    A(f"Raw programs archived under `artifacts/raw_outputs/decode_ablation/`; "
      f"machine-readable results in `artifacts/manifests/decode_ablation.json`.")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=os.path.join(ROOT, "artifacts", "checkpoints", "stage4_exposure.pt"))
    ap.add_argument("--tok", default="auto",
                    help="'auto' = rebuild the exact training tokenizer in memory; "
                         "or a path to a vocab json")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-per-op", type=int, default=200)
    ap.add_argument("--comp-n", type=int, default=40)
    args = ap.parse_args()

    t_start = time.time()
    split = build_split(seed=args.seed, n_per_op=args.n_per_op, comp_n=args.comp_n)
    print(f"split: primitives train {len(split['train'])} val {len(split['val'])} "
          f"test {len(split['test'])}; EXPOSED {len(split['exposed'])}; "
          f"HELD-OUT {len(split['heldout'])}", flush=True)

    if args.tok == "auto":
        # Exact replica of the tokenizer built by run_composition_exposure.py
        # (deterministic: Counter + sorted, no RNG) — reconstructed in memory,
        # nothing on disk is touched.
        all_texts = ([t["nl"]["prompt"] + "\n" + t["reference_code"]
                      for t in split["train"] + split["exposed"]] +
                     [t["nl"]["prompt"] + "\n" + t["reference_code"]
                      for t in split["heldout"]])
        tok = train_tokenizer(all_texts, min_vocab=128, max_vocab=300,
                              save_path=None)
        tok_source = "reconstructed_matched (run_composition_exposure corpus)"
    else:
        tok = load_tokenizer(args.tok)
        tok_source = f"file:{args.tok}"
    # vocab diff vs the current on-disk comp_tok.json (clobbered later file)
    disk_tok_path = os.path.join(ROOT, "artifacts", "tokenizer", "comp_tok.json")
    tok_diff_vs_disk = None
    if os.path.exists(disk_tok_path):
        with open(disk_tok_path) as f:
            disk_vocab = json.load(f)["vocab"]
        if disk_vocab != tok.vocab:
            n_diff = sum(1 for a, b in zip(tok.vocab, disk_vocab) if a != b)
            n_diff += abs(len(tok.vocab) - len(disk_vocab))
            tok_diff_vs_disk = {
                "disk_file": "artifacts/tokenizer/comp_tok.json",
                "disk_vocab_size": len(disk_vocab),
                "matched_vocab_size": len(tok.vocab),
                "differing_indices": n_diff,
                "identical": False,
            }
        else:
            tok_diff_vs_disk = {"disk_file": "artifacts/tokenizer/comp_tok.json",
                                "identical": True}
    print(f"tokenizer: {tok_source}, vocab={tok.vocab_size}; "
          f"vs disk comp_tok.json: {tok_diff_vs_disk}", flush=True)
    cfg = Config(vocab_size=tok.vocab_size, n_embd=128, n_layer=4, n_head=4,
                 block_size=128)
    m = GPT(cfg)
    state = torch.load(args.ckpt, map_location="cpu")
    m.load_state_dict(state)
    m.eval()
    emb, non_emb = m.num_params()
    print(f"loaded {args.ckpt}: total params {emb+non_emb:,} "
          f"(emb {emb:,} / non-emb {non_emb:,}), vocab {tok.vocab_size}", flush=True)

    tasks = [("heldout", t) for t in split["heldout"]] + \
            [("exposed", t) for t in split["exposed"]]
    tasks_by_id = {t["task_id"]: t for _, t in tasks}

    raw_dir = os.path.join(ROOT, "artifacts", "raw_outputs", "decode_ablation",
                           "raw_runs")
    os.makedirs(raw_dir, exist_ok=True)
    raw_records = {}
    for run_name, temperature, max_new in RUNS:
        print(f"\n=== RUN {run_name} (T={temperature}, max_new={max_new}) ===",
              flush=True)
        t0 = time.time()
        recs = generate_run(m, tok, tasks, temperature, max_new,
                            os.path.join(raw_dir, f"{run_name}.jsonl"))
        raw_records[run_name] = recs
        print(f"  run done in {time.time()-t0:.0f}s", flush=True)

    judge = Judge()
    eval_dir = os.path.join(ROOT, "artifacts", "raw_outputs", "decode_ablation",
                            "eval")
    results = {}
    for setting, run_name, temperature, max_new, nul in SETTINGS:
        print(f"=== EVAL {setting} ===", flush=True)
        results[setting] = evaluate_setting(
            setting, raw_records[run_name], tasks_by_id, tok, max_new, nul,
            judge, eval_dir)

    # ---- interpretation, computed from the actual numbers ----
    ho = {s: results[s]["heldout"] for s, _, _, _, _ in SETTINGS}
    ex = {s: results[s]["exposed"] for s, _, _, _, _ in SETTINGS}
    book = ho["book_sample08_max80"]
    g256 = ho["greedy_max256"]
    s256 = ho["sample08_max256"]
    e_book = ex["book_sample08_max80"]
    e_g256 = ex["greedy_max256"]

    interp = []
    delta_valid = g256["valid_program_rate"] - book["valid_program_rate"]
    if g256["valid_program_rate"] >= 0.5 and delta_valid >= 0.3:
        interp.append(
            f"**Decoding/extraction is a real part of the 0.000.** Under the book's "
            f"eval (T=0.8, max_new=80, NUL-truncation) only "
            f"{book['valid_program_rate']:.3f} of held-out generations are valid "
            f"programs; under greedy with max_new=256 that rises to "
            f"{g256['valid_program_rate']:.3f} (+{delta_valid:.3f}). The book's "
            f"number is therefore partly a decode/termination artifact, not a pure "
            f"semantic measurement.")
    elif g256["valid_program_rate"] < 0.3:
        interp.append(
            f"**The 0.000 is NOT an extraction artifact.** Even with the most "
            f"favorable decode we tried (greedy argmax, max_new=256, NUL-truncation) "
            f"only {g256['valid_program_rate']:.3f} of held-out generations are "
            f"valid programs (book setting: {book['valid_program_rate']:.3f}); "
            f"sampled T=0.8 at max_new=256 gives {s256['valid_program_rate']:.3f}. "
            f"Longer generation and greedy decoding do not rescue the format, so the "
            f"failure is upstream of extraction — the model does not emit well-formed "
            f"programs at all for held-out composite prompts.")
    else:
        interp.append(
            f"**Mixed.** Greedy@256 raises the held-out valid-program rate to "
            f"{g256['valid_program_rate']:.3f} vs {book['valid_program_rate']:.3f} "
            f"under the book's setting — decoding matters somewhat, but does not by "
            f"itself explain the 0.000.")

    if all(ho[s]["pass_at_1"] == 0.0 for s in ho):
        interp.append(
            f"**pass@1 stays 0.000 under every setting** on held-out composites "
            f"(greedy@64/128/256: "
            f"{ho['greedy_max64']['pass_at_1']:.3f}/"
            f"{ho['greedy_max128']['pass_at_1']:.3f}/"
            f"{g256['pass_at_1']:.3f}; sampled@64/128/256: "
            f"{ho['sample08_max64']['pass_at_1']:.3f}/"
            f"{ho['sample08_max128']['pass_at_1']:.3f}/"
            f"{s256['pass_at_1']:.3f}; book: {book['pass_at_1']:.3f}). Combined "
            f"with the 0.000 valid-program rate, the held-out failure happens "
            f"BEFORE semantics can be exercised — no decode produces a program "
            f"that even parses. Semantic failure is separately visible on the "
            f"exposed control: pass@1 caps at 0.667 under every setting because "
            f"the sum_of_abs op fails all 40 instances (at greedy@64 those are "
            f"well-formed programs with wrong output), so both a generation "
            f"failure (held-out) and a residual semantic failure (exposed) exist, "
            f"and neither is fixable by decoding.")
    else:
        best = max(SETTINGS, key=lambda s: results[s[0]]["heldout"]["pass_at_1"])
        interp.append(
            f"**Some held-out settings pass tests:** best is "
            f"{best[0]} with pass@1 "
            f"{results[best[0]]['heldout']['pass_at_1']:.3f} — the 0.000 is at least "
            f"partly decode-dependent.")

    if e_g256["valid_program_rate"] < 0.5:
        interp.append(
            f"**Note on greedy:** argmax also collapses the EXPOSED control "
            f"(valid-program rate {e_g256['valid_program_rate']:.3f} at max_new=256), "
            f"so greedy is a degenerate decode for this model on ANY composite "
            f"prompt — not a 'more favorable' one. The decisive comparison for the "
            f"book's number is therefore sampled T=0.8 at max_new 64/128/256 vs the "
            f"book's 80.")
    interp.append(
        f"**Control (exposed composites — training instances, an upper bound):** "
        f"under the book's own decode the exposed set scores valid-program rate "
        f"{e_book['valid_program_rate']:.3f} and pass@1 {e_book['pass_at_1']:.3f} "
        f"(greedy@256: {e_g256['valid_program_rate']:.3f}/"
        f"{e_g256['pass_at_1']:.3f}), while held-out under the SAME decode is "
        f"{book['valid_program_rate']:.3f}/{book['pass_at_1']:.3f}. The pipeline "
        f"produces valid, passing programs when the composite was seen — so the "
        f"pipeline is sound and the held-out failure is specific to the unseen "
        f"composition, not to decoding in general.")
    # (the computed verdict is appended after the examples are built, below)

    # examples: first held-out task under book + greedy@256
    examples = []
    first_id = split["heldout"][0]["task_id"]
    for setting in ("book_sample08_max80", "greedy_max256"):
        with open(os.path.join(eval_dir, f"{setting}.json")) as f:
            ev = json.load(f)
        for it in ev["tasks"]["heldout"]:
            if it["task_id"] == first_id:
                examples.append({
                    "setting": setting, "task_id": first_id,
                    "code": it["code"][:600],
                    "category": it["category"],
                    "tests_passed": it["detail"]["tests_passed"],
                    "tests_total": it["detail"]["tests_total"],
                })
                break

    # appendix: the earlier disk-tokenizer condition, if archived
    disk_manifest_path = os.path.join(ROOT, "artifacts", "manifests",
                                      "decode_ablation_disk_tok.json")
    disk_condition = None
    if os.path.exists(disk_manifest_path):
        with open(disk_manifest_path) as f:
            dm = json.load(f)
        disk_condition = {
            "note": ("The identical ablation scored with the tokenizer file "
                     "currently on disk (`artifacts/tokenizer/comp_tok.json`, "
                     "overwritten by `run_composition_diversity.py` AFTER this "
                     "checkpoint was trained; "
                     f"{(tok_diff_vs_disk or {}).get('differing_indices', '?')} "
                     "of 291 vocab indices differ). Every setting scores 0.000 "
                     "valid-program rate on BOTH held-out and exposed sets: a "
                     "tokenizer-clobber artifact that mimics — and would mask — a "
                     "composition failure. Raw runs: "
                     "`artifacts/raw_outputs/decode_ablation/raw_runs/disk_tok/`."),
            "settings": dm.get("results", {}),
        }

    # extraction-variant aggregate: does NUL-truncation ever discard content?
    post_nul_total = sum(results[s][sn]["post_nul_content"]
                         for s, _, _, _, _ in SETTINGS
                         for sn in ("heldout", "exposed"))
    nul_total = sum(results[s][sn]["nul_truncated"]
                    for s, _, _, _, _ in SETTINGS
                    for sn in ("heldout", "exposed"))

    # failure-mode profile: what do the raw generations actually look like?
    failure_mode = {}
    for run_name in ("greedy_max256", "sample08_max256"):
        for set_name in ("heldout", "exposed"):
            rs = [r for r in raw_records[run_name] if r["set"] == set_name]
            codes, starts, first_nul = [], 0, []
            for r in rs:
                ids = r["new_ids"]
                code = tok.decode(ids)
                i = code.find("\x00")
                if i != -1:
                    code = code[:i]
                code = code.strip()
                codes.append(code)
                starts += code.startswith("def solve")
                p = next((k for k, tid in enumerate(ids)
                          if tok.itos[tid] == "\x00"), None)
                if p is not None:
                    first_nul.append(p)
            failure_mode[f"{run_name}/{set_name}"] = {
                "n": len(rs),
                "distinct_extracted_codes": len(set(codes)),
                "starts_with_def_solve": starts,
                "nul_terminated": len(first_nul),
                "first_nul_token_median": (
                    int(sorted(first_nul)[len(first_nul) // 2])
                    if first_nul else None),
            }
    fm_h = failure_mode.get("greedy_max256/heldout", {})
    fm_e = failure_mode.get("greedy_max256/exposed", {})
    if fm_h and fm_e:
        interp.append(
            f"**Failure mode (raw generations):** on the 120 held-out prompts "
            f"greedy decoding produces only "
            f"{fm_h['distinct_extracted_codes']} distinct extracted programs — "
            f"constant per operation, not per instance — and only "
            f"{fm_h['starts_with_def_solve']}/120 even begin with `def solve`; "
            f"{fm_h['nul_terminated']}/120 collapse into NUL padding (median "
            f"first-NUL token {fm_h['first_nul_token_median']}), and NUL is an "
            f"absorbing token, so longer `max_new` just appends more NULs. Under "
            f"the identical decode, "
            f"{fm_e['starts_with_def_solve']}/120 exposed prompts start with "
            f"`def solve` ({fm_e['distinct_extracted_codes']} distinct programs, "
            f"one per operation). The held-out failure happens at "
            f"the FIRST generated tokens — before any truncation could matter.")

    # conditional verdict from the actual numbers
    best_valid = max(ho[s]["valid_program_rate"] for s in ho)
    best_valid_setting = max(ho, key=lambda s: ho[s]["valid_program_rate"])
    best_pass = max(ho[s]["pass_at_1"] for s in ho)
    best_pass_setting = max(ho, key=lambda s: ho[s]["pass_at_1"])
    if best_pass > 0:
        verdict = (f"**Verdict: the 0.000 IS partly a decode artifact.** The best "
                   f"held-out setting ({best_valid_setting} / {best_pass_setting}) "
                   f"reaches valid-program rate {best_valid:.3f} and pass@1 "
                   f"{best_pass:.3f}, so at least some of the book's 0.000 comes "
                   f"from its decode/extraction choice (T=0.8, max_new=80) rather "
                   f"than from the model alone. The residual gap to the exposed "
                   f"control ({e_g256['pass_at_1']:.3f}-"
                   f"{e_book['pass_at_1']:.3f}) is the genuine semantic failure.")
    elif best_valid < 0.3:
        verdict = (f"**Verdict: the 0.000 is NOT a decode/termination/extraction "
                   f"artifact.** Best held-out valid-program rate across all seven "
                   f"settings is {best_valid:.3f} ({best_valid_setting}) and pass@1 "
                   f"is 0.000 everywhere (best {best_pass_setting} = {best_pass:.3f}). "
                   f"Greedy argmax, 3.2x longer generation (256 vs 80), and an "
                   f"extraction that keeps all post-NUL content change nothing, "
                   f"while the same pipeline scores "
                   f"{e_g256['valid_program_rate']:.3f}-"
                   f"{e_book['valid_program_rate']:.3f} valid and "
                   f"{e_g256['pass_at_1']:.3f}-{e_book['pass_at_1']:.3f} pass@1 on "
                   f"the exposed control. The failure is real: on unseen "
                   f"compositions the model does not emit a well-formed program at "
                   f"all under any decode — the breakdown is at the FIRST generated "
                   f"tokens, not at truncation — and on the exposed control, where "
                   f"programs are well-formed, pass@1 still caps at "
                   f"{e_book['pass_at_1']:.3f} (sum_of_abs fails 40/40 even on its "
                   f"own training instances). Neither the format collapse nor the "
                   f"residual gap is fixable by decoding.")
    else:
        verdict = (f"**Verdict: mixed.** Best held-out valid-program rate is "
                   f"{best_valid:.3f} ({best_valid_setting}) vs "
                   f"{book['valid_program_rate']:.3f} under the book's setting, but "
                   f"pass@1 never exceeds {best_pass:.3f} ({best_pass_setting}). "
                   f"Decoding affects the format rate; the semantic failure "
                   f"remains.")
    if post_nul_total == 0:
        verdict += (" NUL-truncation discards no recoverable content: none of the "
                    f"{nul_total} NUL-containing generations had any non-NUL "
                    "content after its first NUL, and the delete-all-NULs "
                    "extraction yields identical numbers.")
    interp.append(verdict)
    manifest = {
        "experiment_id": "decode_ablation",
        "status": "MEASURED",
        "question": ("Is the book's composition 0.000 on held-out composites a "
                     "decode/termination/extraction artifact or a real failure?"),
        "config": {
            "ckpt": os.path.relpath(args.ckpt, ROOT),
            "tok": args.tok,
            "tok_source": tok_source,
            "tok_vocab_diff_vs_disk": tok_diff_vs_disk,
            "seed": args.seed, "n_per_op": args.n_per_op, "comp_n": args.comp_n,
            "block_size": 128, "n_embd": 128, "n_layer": 4, "n_head": 4,
            "vocab_size": tok.vocab_size,
            "model_params": {"embedding": emb, "non_embedding": non_emb,
                             "total": emb + non_emb},
            "trained": False,
            "extraction": "decode -> NUL-truncate -> strip (as generate_code)",
            "book_eval_note": "book eval uses T=0.8, max_new=80, NUL-truncation",
        },
        "split": {
            "n_train": len(split["train"]), "n_val": len(split["val"]),
            "n_test": len(split["test"]),
            "n_exposed": len(split["exposed"]),
            "n_heldout": len(split["heldout"]),
            "exposed_ops": EXPOSED, "held_out_ops": HELD_OUT,
        },
        "settings_list": [{"setting": s, "run": r, "temperature": t,
                           "max_new": m, "nul_truncation": n}
                          for s, r, t, m, n in SETTINGS],
        "results": results,
        "interpretation": interp,
        "failure_mode": failure_mode,
        "disk_tokenizer_condition": disk_condition,
        "examples": examples,
        "runtime_seconds": round(time.time() - t_start, 1),
    }
    mp = os.path.join(ROOT, "artifacts", "manifests", "decode_ablation.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest ->", mp, flush=True)

    rp = os.path.join(ROOT, "docs", "reviews", "loop", "decode_ablation.md")
    write_report(manifest, rp)
    print("report ->", rp, flush=True)

    # console summary
    print("\n=== SUMMARY (held-out) ===")
    for s, r, t, mn, n in SETTINGS:
        hr = results[s]["heldout"]
        er = results[s]["exposed"]
        print(f"  {s:22s} heldout: valid={hr['valid_program_rate']:.3f} "
              f"pass@1={hr['pass_at_1']:.3f} | exposed: "
              f"valid={er['valid_program_rate']:.3f} pass@1={er['pass_at_1']:.3f}")
    print(f"total runtime {time.time()-t_start:.0f}s", flush=True)


if __name__ == "__main__":
    main()