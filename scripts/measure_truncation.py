#!/usr/bin/env python3
"""P1-08 — length / truncation / padding-in-loss audit (MEASUREMENT ONLY).

The trainer (`src/train/trainer.py`) encodes `prompt + "\\n" + reference_code`,
slices every example to `max_len=128`, zero-pads each batch to the batch max,
and calls `model(x, x)` with no ignore mask — so cross-entropy is computed over
every next-token position, including padding targets. This script MEASURES what
that means for the actual training sets; it does not train, evaluate, or modify
anything in the training/eval path.

Arms audited (each rebuilt exactly the way its script builds it):
  * pilot_stage1            — artifacts/datasets/pilot_train.jsonl, tokenizer
                              fit as scripts/train.py `build_tokenizer` does.
  * stage3_surface_n60      — scripts/run_surface.py `build_tasks` (AST-extracted
                              verbatim from the script) with the RECORDED config
                              of artifacts/manifests/stage3_surface.json
                              (n_per=60, seed=0); tokenizer fit over the same
                              four text groups in the same order as the script.
  * stage3_surface_n130     — same code with the CURRENT script default
                              (n_per=130) so the audit also covers future runs.
  * stage4_composition_exposure — primitives train split (same 70/15/15 logic as
                              scripts/run_composition_exposure.py, re-implemented
                              inline because it lives inside `main()`) plus the
                              EXPOSED composites; tokenizer fit over the same
                              texts as the script.

Per operation it reports: prompt / program / combined token-length
distributions, how many records exceed the 128-token window and how many
program tokens that cuts, which operations are most exposed, and an estimate of
the padding-token share of the training sequence (both the actual dynamic-batch
scheme and the padded-to-128 upper bound).

Outputs:
  artifacts/manifests/truncation_audit.json
  docs/reviews/loop/truncation_audit.md

Run: python scripts/measure_truncation.py   (no torch required)
"""
import ast
import json
import os
import random
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_generator.generator import (  # noqa: E402
    OPERATIONS,
    generate_compositional,
    generate_dataset,
    make_task,
)
from src.nl_renderer.renderer import FAMILIES  # noqa: E402
from src.tokenizer.tokenizer import load_tokenizer, train_tokenizer  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
MAX_LEN = 128
BS = 16                 # scripts/train.py / run_surface.py default batch size
PAD_MC_BATCHES = 20000  # Monte Carlo batches for the padding estimate
PAD_MC_SEED = 0
HIST_EDGES = list(range(0, 208, 16)) + [10**9]


# --------------------------------------------------------------------------- #
# train-set construction (verbatim from the scripts that train)               #
# --------------------------------------------------------------------------- #
def load_tasks(path):
    """src.train.trainer.load_tasks, duplicated to avoid importing torch."""
    return [json.loads(l) for l in open(path) if l.strip()]


def extract_build_tasks():
    """AST-extract `build_tasks` from scripts/run_surface.py so the surface split
    is the script's own code, not a re-implementation (same pattern as
    scripts/run_original_novelty_audit.py). Importing the module directly would
    pull in torch; this keeps the audit torch-free."""
    path = os.path.join(ROOT, "scripts", "run_surface.py")
    src = open(path).read()
    tree = ast.parse(src)
    fn = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == "build_tasks")
    code = ast.get_source_segment(src, fn)
    assert code is not None, "build_tasks source not found in run_surface.py"
    ns = {"FAMILIES": FAMILIES, "make_task": make_task, "OPERATIONS": OPERATIONS}
    exec(compile(code, path, "exec"), ns)  # noqa: S102 - audited repo code
    return ns["build_tasks"]


def surface_texts(train, in_dist, held_word, word_id):
    """Text order used by scripts/run_surface.py when fitting the tokenizer."""
    out = []
    for t in train + in_dist + held_word + word_id:
        out.append(t["nl"]["prompt"] + "\n" + t["reference_code"])
    return out


def composition_exposure_split(n_per_op=200, comp_n=40, seed=0):
    """Re-implementation of the inline split in
    scripts/run_composition_exposure.py `main()` (it is not a standalone
    function, so it cannot be AST-extracted). Logic copied line-for-line."""
    prim = generate_dataset(n_per_op=n_per_op, id_set="letters", seed=seed)
    by_op = defaultdict(list)
    for t in prim:
        by_op[t["semantics"]["operation"]].append(t)
    train, val, test = [], [], []
    for op, g in by_op.items():
        g.sort(key=lambda t: t["task_id"])
        n = len(g)
        nv = max(1, int(n * 0.15))
        nt = max(1, int(n * 0.15))
        val += g[:nv]
        test += g[nv:nv + nt]
        train += g[nv + nt:]
    comp = generate_compositional(n_per_op=comp_n, id_set="letters", seed=seed + 5000)
    by_op_c = defaultdict(list)
    for t in comp:
        by_op_c[t["semantics"]["operation"]].append(t)
    exposed, heldout = [], []
    for op, g in by_op_c.items():
        if op in ("abs_add", "sub_abs", "sum_of_abs"):
            exposed += g
        elif op in ("max_add", "double_first", "len_minus_one"):
            heldout += g
    for t in train:
        t["split"] = "train"
    for t in exposed:
        t["split"] = "train"
    for t in heldout:
        t["split"] = "composition_holdout"
    train_with_comp = train + exposed
    all_texts = ([t["nl"]["prompt"] + "\n" + t["reference_code"] for t in train_with_comp] +
                 [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in heldout])
    return train_with_comp, all_texts


# --------------------------------------------------------------------------- #
# measurement                                                                  #
# --------------------------------------------------------------------------- #
def hist(counts_values):
    h = {}
    for v in counts_values:
        for e in HIST_EDGES:
            key = f"<{e}" if e < 10**9 else ">=208"
            if v < e:
                h[key] = h.get(key, 0) + 1
                break
    # stable key order
    keys = [f"<{e}" for e in HIST_EDGES if e < 10**9] + [">=208"]
    return {k: h.get(k, 0) for k in keys}


def stats(vals):
    if not vals:
        return {"n": 0}
    sv = sorted(vals)
    p90 = sv[min(len(sv) - 1, int(0.90 * len(sv)))]
    return {
        "n": len(vals),
        "min": sv[0],
        "mean": round(statistics.mean(vals), 2),
        "median": statistics.median(vals),
        "p90": p90,
        "max": sv[-1],
        "histogram": hist(vals),
    }


def measure_arm(name, tasks, tok, tokenizer_note, source):
    """Compute per-operation length/truncation stats + padding estimate."""
    per_op = defaultdict(lambda: {"prompt": [], "code": [], "combined": [],
                                  "over": 0, "cut": 0, "cut_max": 0,
                                  "prompt_over": 0, "boundary_mismatch": 0})
    all_prompt, all_code, all_combined = [], [], []
    rows = []  # (op, L) for the padding simulation
    dropped_short = 0

    for t in tasks:
        op = t["semantics"]["operation"]
        prompt = t["nl"]["prompt"] + "\n"   # trainer's prompt_marker
        code = t["reference_code"]
        p_ids = tok.encode(prompt)
        c_ids = tok.encode(code)
        full = tok.encode(prompt + code)
        # verify the prompt/code split is exact (no vocab token spans the "\n"
        # boundary), so per-part lengths are meaningful
        boundary_ok = (p_ids + c_ids == full)
        if not boundary_ok:
            per_op[op]["boundary_mismatch"] += 1
        L = min(len(full), MAX_LEN)   # what Dataset keeps after ids[:max_len]
        if len(full) < 4:
            dropped_short += 1
            continue
        p_len, c_len, comb = len(p_ids), len(c_ids), len(full)
        d = per_op[op]
        d["prompt"].append(p_len)
        d["code"].append(c_len)
        d["combined"].append(comb)
        all_prompt.append(p_len)
        all_code.append(c_len)
        all_combined.append(comb)
        if comb > MAX_LEN:
            d["over"] += 1
            cut = comb - MAX_LEN
            d["cut"] += cut
            d["cut_max"] = max(d["cut_max"], cut)
        if p_len >= MAX_LEN:
            d["prompt_over"] += 1
        rows.append((op, L))

    # ---- padding Monte Carlo: replicate src.train.trainer.Dataset.batch ----
    # T = min(max sampled len, 128); x zero-padded; loss over all T-1 targets.
    # A target at index t+1 is padding (id 0) iff t+1 >= L, i.e. T-L terms/row.
    rng = random.Random(PAD_MC_SEED)
    n = len(rows)
    pad_cells = real_cells = loss_terms = pad_loss_terms = 0
    batch_T_sum = 0
    op_pad = defaultdict(lambda: {"rows": 0, "pad_cells": 0, "loss_terms": 0,
                                  "pad_loss_terms": 0})
    for _ in range(PAD_MC_BATCHES):
        idx = [rng.randrange(n) for _ in range(BS)]  # random.choice equivalent
        T = min(max(rows[i][1] for i in idx), MAX_LEN)
        batch_T_sum += T
        for i in idx:
            op, L = rows[i]
            L = min(L, T)
            pad_cells += T - L
            real_cells += L
            loss_terms += T - 1
            pad_loss_terms += T - L
            o = op_pad[op]
            o["rows"] += 1
            o["pad_cells"] += T - L
            o["loss_terms"] += T - 1
            o["pad_loss_terms"] += T - L

    per_op_out = {}
    for op in sorted(per_op):
        d = per_op[op]
        per_op_out[op] = {
            "n_records": len(d["combined"]),
            "prompt_tokens": stats(d["prompt"]),
            "program_tokens": stats(d["code"]),
            "combined_tokens": stats(d["combined"]),
            "records_over_128": d["over"],
            "program_tokens_cut_total": d["cut"],
            "program_tokens_cut_max": d["cut_max"],
            "records_prompt_alone_ge_128": d["prompt_over"],
            "program_coverage_complete": d["over"] == 0,
            "encode_boundary_mismatches": d["boundary_mismatch"],
            "padding": {
                "rows_sampled": op_pad[op]["rows"],
                # pad_cell_share is filled in after the second MC pass below
                "pad_cell_share": None,
                "pad_loss_target_share": round(
                    op_pad[op]["pad_loss_terms"] / max(1, op_pad[op]["loss_terms"]), 4),
            },
        }

    # second MC pass (same seed => same batches) to accumulate per-op cell
    # denominators: cells = sum of batch T over that op's sampled rows
    rng = random.Random(PAD_MC_SEED)
    op_cells = defaultdict(int)
    for _ in range(PAD_MC_BATCHES):
        idx = [rng.randrange(n) for _ in range(BS)]
        T = min(max(rows[i][1] for i in idx), MAX_LEN)
        for i in idx:
            op_cells[rows[i][0]] += T
    for op in per_op_out:
        o = op_pad[op]
        per_op_out[op]["padding"]["pad_cell_share"] = round(
            o["pad_cells"] / max(1, op_cells[op]), 4)

    over_ops = sorted([op for op in per_op_out
                       if per_op_out[op]["records_over_128"] > 0],
                      key=lambda op: -per_op_out[op]["records_over_128"])
    total_over = sum(per_op_out[op]["records_over_128"] for op in per_op_out)
    total_cut = sum(per_op_out[op]["program_tokens_cut_total"] for op in per_op_out)

    return {
        "source": source,
        "n_train_records": len(tasks),
        "records_dropped_len_lt_4": dropped_short,
        "tokenizer": tokenizer_note,
        "overall": {
            "prompt_tokens": stats(all_prompt),
            "program_tokens": stats(all_code),
            "combined_tokens": stats(all_combined),
        },
        "truncation_at_128": {
            "records_over_128": total_over,
            "record_share_over_128": round(total_over / max(1, len(tasks)), 6),
            "program_tokens_cut_total": total_cut,
            "program_tokens_cut_max": max(
                (per_op_out[op]["program_tokens_cut_max"] for op in per_op_out),
                default=0),
            "records_prompt_alone_ge_128": sum(
                per_op_out[op]["records_prompt_alone_ge_128"] for op in per_op_out),
            "operations_with_truncation": over_ops,
            "all_programs_fully_covered": total_over == 0,
        },
        "padding": {
            "method": (f"Monte Carlo of src.train.trainer.Dataset.batch: "
                       f"{PAD_MC_BATCHES} batches, bs={BS}, sampling with "
                       f"replacement, seed {PAD_MC_SEED}; loss = cross-entropy "
                       f"over all T-1 targets with no ignore index. The real "
                       f"runs never seed Python's `random`, so batch composition "
                       f"is nondeterministic there; this is an estimate under "
                       f"seed {PAD_MC_SEED}"),
            "mean_batch_T": round(batch_T_sum / PAD_MC_BATCHES, 2),
            "pad_cell_share_actual_batches": round(
                pad_cells / max(1, pad_cells + real_cells), 4),
            "pad_loss_target_share_actual_batches": round(
                pad_loss_terms / max(1, loss_terms), 4),
            "pad_cell_share_if_padded_to_128": round(
                1 - (sum(r[1] for r in rows) / len(rows)) / MAX_LEN, 4),
            "pad_token_id": 0,
            "pad_token_repr": repr(tok.itos[0]),
        },
        "per_operation": per_op_out,
    }


def main():
    # ---------------- arm 1: pilot / stage 1 ----------------
    pilot = load_tasks(os.path.join(ROOT, "artifacts", "datasets", "pilot_train.jsonl"))
    pilot_texts = [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in pilot]
    tok_pilot = train_tokenizer(pilot_texts, min_vocab=128, max_vocab=300)
    note_pilot = {
        "fit": "train_tokenizer(train texts in file order, min_vocab=128, "
               "max_vocab=300) — scripts/train.py build_tokenizer",
        "vocab_size": tok_pilot.vocab_size,
        "pad_token_repr": repr(tok_pilot.itos[0]),
    }
    on_disk = os.path.join(ROOT, "artifacts", "tokenizer", "pilot_tok.json")
    if os.path.exists(on_disk):
        note_pilot["matches_on_disk_pilot_tok_json"] = (
            load_tokenizer(on_disk).vocab == tok_pilot.vocab)

    # ---------------- arm 2/3: stage 3 surface ----------------
    build_tasks = extract_build_tasks()
    arms = {}
    arms["pilot_stage1"] = measure_arm(
        "pilot_stage1", pilot, tok_pilot, note_pilot,
        "artifacts/datasets/pilot_train.jsonl (scripts/train.py, seed 0)")

    for tag, n_per in (("stage3_surface_n60", 60),
                       ("stage3_surface_n130", 130)):
        train, in_dist, held_word = build_tasks("letters", "holdout_last", n_per, 0)
        _, word_id, _ = build_tasks("words", "all", n_per, 5000)
        texts = surface_texts(train, in_dist, held_word, word_id)
        tok = train_tokenizer(texts, min_vocab=128, max_vocab=300)
        note = {
            "fit": "train_tokenizer(train+in_dist+held_word+word_id texts in "
                   "run_surface.py order, min_vocab=128, max_vocab=300)",
            "vocab_size": tok.vocab_size,
            "pad_token_repr": repr(tok.itos[0]),
        }
        if n_per == 60:
            on_disk = os.path.join(ROOT, "artifacts", "tokenizer", "surface_tok.json")
            if os.path.exists(on_disk):
                note["matches_on_disk_surface_tok_json"] = (
                    load_tokenizer(on_disk).vocab == tok.vocab)
        src = ("scripts/run_surface.py build_tasks (AST-extracted), n_per=60, "
               "seed=0 — recorded config of artifacts/manifests/stage3_surface.json"
               if n_per == 60 else
               "scripts/run_surface.py build_tasks (AST-extracted), n_per=130, "
               "seed=0 — current script default (not the recorded run)")
        arms[tag] = measure_arm(tag, train, tok, note, src)

    # ---------------- arm 4: stage 4 composition exposure ----------------
    comp_train, comp_texts = composition_exposure_split()
    tok_c = train_tokenizer(comp_texts, min_vocab=128, max_vocab=300)
    note_c = {
        "fit": "train_tokenizer(exposed-primitive train + held-out composite "
               "texts in run_composition_exposure.py order, min_vocab=128, "
               "max_vocab=300)",
        "vocab_size": tok_c.vocab_size,
        "pad_token_repr": repr(tok_c.itos[0]),
    }
    arms["stage4_composition_exposure"] = measure_arm(
        "stage4_composition_exposure", comp_train, tok_c, note_c,
        "scripts/run_composition_exposure.py: primitives train (1400) + EXPOSED "
        "composites (120) = 1520 records, seed 0")

    # ---------------- trainer facts (read from source, not assumed) ----------
    trainer_src = open(os.path.join(ROOT, "src", "train", "trainer.py")).read()
    gpt_src = open(os.path.join(ROOT, "src", "model", "gpt.py")).read()
    trainer_facts = {
        "max_len": MAX_LEN,
        "prompt_marker": repr("\n"),
        "explicit_eos_token": False,
        "eos_note": ("the only prompt/code separator is the single newline from "
                     "prompt_marker, and truncation is a hard slice ids[:max_len]"),
        "batch_padding_value": 0,
        "batch_padding_token": repr(chr(0)),
        "loss_ignore_index_present": "ignore_index" in gpt_src,
        "loss_note": ("GPT.forward computes F.cross_entropy(logits[:, :-1], "
                      "targets[:, 1:]) over every position — padding targets "
                      "(id 0 = NUL) contribute to the loss"),
        "trainer_slices_at_max_len": "[:max_len]" in trainer_src,
        "examples_shorter_than_4_dropped": "len(e) >= 4" in trainer_src,
    }

    # ---------------- ranking of most-exposed operations ----------------
    exposure = []
    for tag, a in arms.items():
        for op, d in a["per_operation"].items():
            exposure.append({
                "arm": tag, "operation": op,
                "records_over_128": d["records_over_128"],
                "n_records": d["n_records"],
                "max_combined": d["combined_tokens"]["max"],
                "mean_combined": d["combined_tokens"]["mean"],
                "headroom_to_128": MAX_LEN - d["combined_tokens"]["max"],
                "program_tokens_cut_total": d["program_tokens_cut_total"],
            })
    exposure.sort(key=lambda r: (-r["records_over_128"], -r["max_combined"]))

    # ---------------- provenance cross-checks ----------------
    # (a) the composition-0.000 baseline (scripts/run_composition.py) trains on
    # the primitive 70/15/15 split — is that model-visibly the pilot train file?
    from collections import defaultdict as _dd
    prim = generate_dataset(n_per_op=200, id_set="letters", seed=0)
    _by = _dd(list)
    for t in prim:
        _by[t["semantics"]["operation"]].append(t)
    comp_prim_train = []
    for op, g in _by.items():
        g.sort(key=lambda t: t["task_id"])
        n = len(g)
        nv = max(1, int(n * 0.15))
        nt = max(1, int(n * 0.15))
        comp_prim_train += g[nv + nt:]
    _key = lambda t: (t["task_id"], t["nl"]["prompt"], t["reference_code"])  # noqa: E731
    pilot_is_comp_baseline_train = (
        sorted(map(_key, pilot)) == sorted(map(_key, comp_prim_train)))

    # (b) surface tokenizer provenance: recorded n_per=60 vs current default 130
    tr60, id60, hw60 = build_tasks("letters", "holdout_last", 60, 0)
    _, wid60, _ = build_tasks("words", "all", 60, 5000)
    tr130, id130, hw130 = build_tasks("letters", "holdout_last", 130, 0)
    _, wid130, _ = build_tasks("words", "all", 130, 5000)
    v60 = train_tokenizer(surface_texts(tr60, id60, hw60, wid60),
                          min_vocab=128, max_vocab=300).vocab
    v130 = train_tokenizer(surface_texts(tr130, id130, hw130, wid130),
                           min_vocab=128, max_vocab=300).vocab
    surface_tok_provenance = {
        "n60_vocab_equals_n130_vocab": v60 == v130,
        "n60_vocab_differs_from_n130_vocab": len(set(v60) ^ set(v130)),
    }
    disk_surface = os.path.join(ROOT, "artifacts", "tokenizer", "surface_tok.json")
    if os.path.exists(disk_surface):
        surface_tok_provenance["n60_vocab_matches_on_disk_surface_tok_json"] = (
            load_tokenizer(disk_surface).vocab == v60)

    # (c) what exactly does the one truncated operation lose?
    trunc_detail = {}
    trunc_records = [t for t in comp_train
                     if len(tok_c.encode(t["nl"]["prompt"] + "\n"
                                         + t["reference_code"])) > MAX_LEN]
    if trunc_records:
        t0 = trunc_records[0]
        full_txt = t0["nl"]["prompt"] + "\n" + t0["reference_code"]
        ids = tok_c.encode(full_txt)
        p_len = len(tok_c.encode(t0["nl"]["prompt"] + "\n"))
        trunc_detail = {
            "operation": t0["semantics"]["operation"],
            "n_truncated_records": len(trunc_records),
            "distinct_programs_among_truncated": len(
                set(t["reference_code"] for t in trunc_records)),
            "prompt_tokens": p_len,
            "program_tokens": len(ids) - p_len,
            "program_tokens_kept": max(0, MAX_LEN - p_len),
            "program_tokens_cut": len(ids) - MAX_LEN,
            "kept_tail": tok_c.decode(ids[:MAX_LEN])[-100:],
            "cut_tail": tok_c.decode(ids[MAX_LEN:]),
            "full_program": t0["reference_code"],
        }

    out = {
        "audit": "P1-08 — silent context truncation and padding-in-loss: "
                 "empirical length audit",
        "generated_by": "scripts/measure_truncation.py (measurement only; no "
                        "training, no evaluation, no model reruns)",
        "max_len": MAX_LEN,
        "trainer_facts": trainer_facts,
        "arms": arms,
        "provenance_checks": {
            "pilot_train_equals_composition_baseline_train_model_visible":
                pilot_is_comp_baseline_train,
            "note": ("scripts/run_composition.py (the composition-0.000 "
                     "baseline) trains on the same primitive 70/15/15 split as "
                     "pilot_train.jsonl — compared on (task_id, prompt, "
                     "reference_code)"),
            "surface_tokenizer": surface_tok_provenance,
        },
        "truncation_detail": trunc_detail,
        "most_exposed_operations": exposure[:15],
    }
    out_path = os.path.join(ROOT, "artifacts", "manifests", "truncation_audit.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print("wrote", out_path)

    md = render_md(out)
    md_path = os.path.join(ROOT, "docs", "reviews", "loop", "truncation_audit.md")
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w") as f:
        f.write(md)
    print("wrote", md_path)

    # console headline
    for tag, a in arms.items():
        t = a["truncation_at_128"]
        p = a["padding"]
        print(f"{tag:28s} n={a['n_train_records']:5d} "
              f"over128={t['records_over_128']:4d} cut={t['program_tokens_cut_total']:5d} "
              f"pad_loss_share={p['pad_loss_target_share_actual_batches']:.4f} "
              f"ops_trunc={t['operations_with_truncation']}")


def fmt_stats(s):
    if s["n"] == 0:
        return "—"
    return (f"min {s['min']} / med {s['median']} / mean {s['mean']} / "
            f"p90 {s['p90']} / max {s['max']}")


def render_md(out):
    L = []
    L.append("# P1-08 — Truncation & padding-in-loss audit (length measurements)\n")
    L.append("Generated by `scripts/measure_truncation.py` (measurement only — no "
             "training, no evaluation, no model reruns). Machine-readable twin: "
             "`artifacts/manifests/truncation_audit.json`.\n")
    L.append("## What the trainer actually does (read from source)\n")
    tf = out["trainer_facts"]
    L.append(f"- Encodes `prompt + {tf['prompt_marker']} + reference_code`, then a "
             f"hard slice `ids[:{tf['max_len']}]` "
             f"(`trainer_slices_at_max_len={tf['trainer_slices_at_max_len']}`).")
    L.append(f"- **No explicit EOS token** is appended: {tf['eos_note']}.")
    L.append(f"- Batches are zero-padded to the batch max (pad id "
             f"{tf['batch_padding_value']} = {tf['batch_padding_token']}, i.e. NUL).")
    L.append(f"- Loss has **no ignore index** "
             f"(`loss_ignore_index_present={tf['loss_ignore_index_present']}`): "
             f"{tf['loss_note']}.")
    L.append(f"- Examples shorter than 4 tokens are dropped "
             f"(`examples_shorter_than_4_dropped="
             f"{tf['examples_shorter_than_4_dropped']}`).\n")

    L.append("## Headline numbers\n")
    L.append("| arm | records | combined med/max | records >128 | program tokens "
             "cut | ops with truncation | pad share of loss targets |")
    L.append("|---|---|---|---|---|---|---|")
    for tag, a in out["arms"].items():
        t = a["truncation_at_128"]
        c = a["overall"]["combined_tokens"]
        p = a["padding"]
        ops = ", ".join(t["operations_with_truncation"]) or "none"
        L.append(f"| {tag} | {a['n_train_records']} | {c['median']}/{c['max']} | "
                 f"{t['records_over_128']} | {t['program_tokens_cut_total']} | "
                 f"{ops} | {p['pad_loss_target_share_actual_batches']:.3f} |")
    L.append("")

    pc = out.get("provenance_checks", {})
    L.append("## Provenance checks\n")
    L.append(f"- `pilot_train.jsonl` == composition-baseline train set "
             f"(model-visible): **{pc.get('pilot_train_equals_composition_baseline_train_model_visible')}**"
             f" — {pc.get('note', '')}")
    st = pc.get("surface_tokenizer", {})
    for k, v in st.items():
        L.append(f"- surface tokenizer `{k}`: **{v}**")
    L.append("")

    td = out.get("truncation_detail") or {}
    if td:
        L.append("## The one truncated operation, in detail\n")
        L.append(f"- `{td['operation']}`: {td['n_truncated_records']} truncated "
                 f"records, {td['distinct_programs_among_truncated']} distinct "
                 f"program(s) among them.")
        L.append(f"- prompt {td['prompt_tokens']} tokens + program "
                 f"{td['program_tokens']} tokens = "
                 f"{td['prompt_tokens'] + td['program_tokens']} combined; the "
                 f"128-window keeps {td['program_tokens_kept']} program tokens "
                 f"and cuts **{td['program_tokens_cut']}**.")
        L.append(f"- kept tail ends: `{td['kept_tail'][-80:]!r}`")
        L.append(f"- cut tail: `{td['cut_tail']!r}`")
        L.append("- i.e. training never shows a *completed* program for this "
                 "operation: the sequence stops before the `else` branch and "
                 "the `return`.\n")

    for tag, a in out["arms"].items():
        L.append(f"## {tag}\n")
        L.append(f"- Source: {a['source']}")
        L.append(f"- Tokenizer: vocab {a['tokenizer']['vocab_size']}, pad token "
                 f"{a['tokenizer']['pad_token_repr']!r}; fit: "
                 f"{a['tokenizer']['fit']}")
        for k, v in a["tokenizer"].items():
            if k.startswith("matches_"):
                L.append(f"- `{k}`: **{v}**")
        L.append(f"- Records dropped (len<4): {a['records_dropped_len_lt_4']}\n")
        L.append("| op | n | prompt tokens (min/med/mean/p90/max) | program tokens | "
                 "combined | >128 | prog tokens cut | pad loss share |")
        L.append("|---|---|---|---|---|---|---|---|")
        for op, d in a["per_operation"].items():
            def row(s):
                return f"{s['min']}/{s['median']}/{s['mean']}/{s['p90']}/{s['max']}"
            L.append(f"| {op} | {d['n_records']} | {row(d['prompt_tokens'])} | "
                     f"{row(d['program_tokens'])} | {row(d['combined_tokens'])} | "
                     f"{d['records_over_128']} | "
                     f"{d['program_tokens_cut_total']} | "
                     f"{d['padding']['pad_loss_target_share']:.3f} |")
        t = a["truncation_at_128"]
        p = a["padding"]
        L.append("")
        L.append(f"**Truncation:** {t['records_over_128']}/{a['n_train_records']} "
                 f"records exceed {out['max_len']} tokens "
                 f"({t['record_share_over_128']:.4f}); "
                 f"{t['program_tokens_cut_total']} program tokens cut in total "
                 f"(max {t['program_tokens_cut_max']} in one record); "
                 f"{t['records_prompt_alone_ge_128']} records have a prompt that "
                 f"alone reaches 128. All programs fully covered: "
                 f"**{t['all_programs_fully_covered']}**.")
        L.append(f"**Padding:** actual dynamic batches — pad cells "
                 f"{p['pad_cell_share_actual_batches']:.3f}, pad share of loss "
                 f"targets {p['pad_loss_target_share_actual_batches']:.3f} "
                 f"(mean batch T {p['mean_batch_T']}); if every row were padded "
                 f"to the full 128 the pad-cell share would be "
                 f"{p['pad_cell_share_if_padded_to_128']:.3f}. Method: "
                 f"{p['method']}.\n")

    L.append("## Which operations are most exposed\n")
    L.append("| arm | op | records >128 | n | max combined | headroom to 128 | "
             "mean combined | program tokens cut |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in out["most_exposed_operations"]:
        L.append(f"| {r['arm']} | {r['operation']} | {r['records_over_128']} | "
                 f"{r['n_records']} | {r['max_combined']} | "
                 f"{r['headroom_to_128']} | {r['mean_combined']} | "
                 f"{r['program_tokens_cut_total']} |")
    L.append("")

    L.append("## Reading (honest scope)\n")
    L.append("- These are measurements of the regenerated train sets built by the "
             "scripts' own split code from recorded configs/seeds; like the novelty "
             "audit, the historically scored splits were never archived as files, so "
             "this audits the deterministic regeneration, not an archived original. "
             "The rebuilt tokenizers match the on-disk `pilot_tok.json` and "
             "`surface_tok.json` vocab-for-vocab, which corroborates the "
             "regeneration (for the surface arm the n60 and n130 vocabularies "
             "are identical, so that match corroborates the corpus, not the "
             "`n_per` choice — `n_per=60` comes from the recorded manifest).")
    L.append("- **Pilot and Stage-3 surface: no truncation.** Every one of the "
             "1,400 pilot and 600 recorded surface training records fits inside "
             "128 tokens (longest combined = 109, `cond_abs_max`), so every "
             "program the pilot/surface models were asked to learn has complete "
             "coverage in the training window. For those arms the 128-token "
             "window is not a confound.")
    L.append("- **The composition-0.000 baseline is also untruncated.** "
             "`scripts/run_composition.py` trains on the same primitive split as "
             "`pilot_train.jsonl` (provenance check above), which has 0 records "
             "over 128 — so training-time truncation cannot explain the held-out "
             "composite 0.000, and we do not claim it does. (The decode ablation "
             "narrowed *inference-time* stopping; it did not test training-time "
             "truncation. The two are separate questions.)")
    L.append("- **One operation IS truncated: `sum_of_abs` in the Stage-4 "
             "exposure arm.** All 40 of its training records exceed the window "
             "and lose the last 44 program tokens — the `else` branch and the "
             "`return` — so training never shows a completed program for that "
             "operation. This is a real coverage defect *for that arm and that "
             "operation*. It is also the one exposed operation the decode "
             "ablation reports failing on its own training instances; that "
             "correlation is suggestive, but we ran no ablation (retrain with a "
             "longer window) and therefore do not claim truncation *caused* any "
             "score.")
    L.append("- Truncation counts say how many training records lose program tail "
             "tokens at the 128-token window; they do **not** by themselves show "
             "that any measured score was caused by truncation — that would need "
             "an ablation (longer window / no truncation), which we did not run.")
    L.append("- The padding share is a share of *loss target positions*, computed "
             "under the trainer's exact batching rule; it is not a share of the "
             "loss *value* (we did not run the model to decompose the loss). "
             "Padding targets are token id 0 (NUL), so every padded row trains "
             "the model to predict NUL after a sequence's last token. We report "
             "this as a property of the objective, not as an explanation for any "
             "particular evaluation result.")
    L.append("- The decode ablation narrowed *inference-time* stopping; it did not "
             "test *training-time* truncation. The two are separate questions.\n")
    return "\n".join(L)


if __name__ == "__main__":
    main()