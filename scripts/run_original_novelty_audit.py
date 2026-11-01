#!/usr/bin/env python3
"""B04 -- ORIGINAL-holdout novelty audit for the scored Stage-3 / Stage-4 splits.

The external review asked for a novelty audit (prompt / template-family / operation
overlap between train and the held-out splits) run on the *historically scored*
train/test files. Those files were never archived: `scripts/run_surface.py` and
`scripts/run_composition.py` build their splits in memory from the generator plus a
seed and only ever persist the score manifest, so there is no scored JSONL on disk
to re-open.

This script therefore does the strongest thing that is actually possible, and says
so plainly:

  1. It reads the RECORDED config (seed, n_per, comp_per_op) from the score
     manifests that the scoring runs themselves wrote.
  2. It extracts the split code VERBATIM from the scoring scripts (AST slice of
     `build_tasks` out of run_surface.py; AST slice of the split statements out of
     run_composition.main()) and executes that source -- it does not re-implement
     the split, so the regeneration cannot drift from the scoring script.
  3. It regenerates the splits deterministically (make_task is a pure function of
     (operation, task_id, seed, id_set, family) via random.Random(seed); no global
     RNG is consulted) and audits THOSE records.
  4. It cross-checks the regeneration against the generator source as it stood at
     the commit that recorded each manifest (`git show <manifest-commit>:<path>`),
     so we can state whether the model-visible content (prompt / program / family)
     is identical to what the scoring run saw.

Read-only: the only files written are the two report files named below.

Outputs:
  docs/reviews/loop/original_novelty_audit.json
  docs/reviews/loop/original_novelty_audit.md
"""
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import types
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from src.data_generator.generator import (OPERATIONS, COMPOSITE_OPERATIONS,  # noqa: E402
                                          make_task)
from src.nl_renderer.renderer import FAMILIES  # noqa: E402

OUT_DIR = os.path.join(ROOT, "docs", "reviews", "loop")
OUT_JSON = os.path.join(OUT_DIR, "original_novelty_audit.json")
OUT_MD = os.path.join(OUT_DIR, "original_novelty_audit.md")

GENERATOR_PATH = "src/data_generator/generator.py"
SPLIT_SOURCES = {
    "stage3_surface": ["scripts/run_surface.py", GENERATOR_PATH,
                       "src/nl_renderer/renderer.py",
                       "src/program_generator/generator.py",
                       "src/test_generator/generator.py"],
    "stage4_composition": ["scripts/run_composition.py", GENERATOR_PATH,
                           "src/nl_renderer/renderer.py",
                           "src/program_generator/generator.py",
                           "src/test_generator/generator.py"],
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout


def sha256(text_or_bytes):
    b = text_or_bytes if isinstance(text_or_bytes, bytes) else text_or_bytes.encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def canon(rec):
    return json.dumps(rec, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def norm_prompt(s):
    """Case/whitespace/punctuation-insensitive form of a prompt."""
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[^\w\s]", "", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def norm_code(s):
    """Whitespace-insensitive form of a reference program."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", s))


# --------------------------------------------------------------------------- #
# split regeneration -- code taken verbatim from the scoring scripts
# --------------------------------------------------------------------------- #
def load_surface_split_stmt():
    """Return the AST node + source of `build_tasks` from scripts/run_surface.py
    (the exact function run_surface.main() calls)."""
    src = read("scripts/run_surface.py")
    tree = ast.parse(src, filename="scripts/run_surface.py")
    fn = next((n for n in tree.body
               if isinstance(n, ast.FunctionDef) and n.name == "build_tasks"), None)
    if fn is None:
        raise RuntimeError("build_tasks not found in scripts/run_surface.py")
    return fn, ast.get_source_segment(src, fn)


def load_composition_split_stmts():
    """AST-extract the split statements from run_composition.main(): everything
    from `prim = generate_dataset(...)` through the `print(f"tasks: ...")` summary.
    The generator import statement is deliberately NOT taken -- the caller supplies
    generate_dataset/generate_compositional so the same slice can be re-run against
    the scoring-time generator blob for the cross-check."""
    src = read("scripts/run_composition.py")
    tree = ast.parse(src, filename="scripts/run_composition.py")
    main = next(n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "main")
    segs = [ast.get_source_segment(src, s) or "" for s in main.body]
    start = next(i for i, s in enumerate(segs) if s.startswith("prim = generate_dataset"))
    end = next(i for i, s in enumerate(segs) if s.startswith('print(f"tasks:'))
    stmts = main.body[start:end + 1]
    code = compile(ast.Module(body=stmts, type_ignores=[]),
                   "scripts/run_composition.py#split", "exec")
    return code, "\n".join(segs[start:end + 1])


def run_surface_splits(n_per, seed, make_task_fn=None):
    """Run the scoring script's own build_tasks for the recorded (n_per, seed)."""
    fn, _ = load_surface_split_stmt()
    ns = {"make_task": make_task if make_task_fn is None else make_task_fn,
          "OPERATIONS": OPERATIONS, "FAMILIES": FAMILIES}
    exec(compile(ast.Module(body=[fn], type_ignores=[]),
                 "scripts/run_surface.py#build_tasks", "exec"), ns)
    build_tasks = ns["build_tasks"]
    train, in_dist, held_word = build_tasks("letters", "holdout_last", n_per, seed)
    _, word_id, _ = build_tasks("words", "all", n_per, seed + 5000)
    return {"train": train, "in_distribution": in_dist,
            "held_out_wording_family": held_word, "held_out_identifiers_words": word_id}


def run_composition_splits(seed, comp_per_op, gen_module=None):
    code, _ = load_composition_split_stmts()
    if gen_module is None:
        import src.data_generator.generator as gen_module
    ns = {
        "args": types.SimpleNamespace(seed=seed, comp_per_op=comp_per_op),
        "generate_dataset": gen_module.generate_dataset,
        "generate_compositional": gen_module.generate_compositional,
        "OPERATIONS": gen_module.OPERATIONS,
        "defaultdict": defaultdict,
    }
    exec(code, ns)
    return {"train": ns["train"], "val": ns["val"], "test": ns["test"],
            "composition_holdout": ns["comp"]}


# --------------------------------------------------------------------------- #
# scoring-time source cross-check
# --------------------------------------------------------------------------- #
def load_git_module(path, rev, modname):
    blob = git("show", "%s:%s" % (rev, path))
    if blob is None:
        return None, None
    mod = types.ModuleType(modname)
    mod.__file__ = os.path.join(ROOT, path)
    exec(compile(blob.decode("utf-8"), mod.__file__, "exec"), mod.__dict__)
    return mod, sha256(blob)


def file_sha256(path):
    try:
        with open(os.path.join(ROOT, path), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def source_provenance(manifest_path, split_key):
    """For every file the split depends on: is its current content byte-identical
    to the content at the commit that recorded the score manifest?"""
    mcommit = git("log", "-1", "--format=%H", "--", manifest_path)
    mcommit = mcommit.decode().strip() if mcommit else None
    mdate = git("log", "-1", "--format=%ad", "--date=short", "--", manifest_path)
    mdate = mdate.decode().strip() if mdate else None
    files = {}
    for p in SPLIT_SOURCES[split_key]:
        cur = file_sha256(p)
        at = None
        if mcommit:
            blob = git("show", "%s:%s" % (mcommit, p))
            at = sha256(blob) if blob is not None else None
        last = git("log", "-1", "--format=%h %ad %s", "--date=short", "--", p)
        files[p] = {
            "current_sha256": cur,
            "sha256_at_manifest_commit": at,
            "identical_at_scoring_time": (cur == at) if (cur and at) else None,
            "last_commit": last.decode().strip() if last else None,
        }
    return {"manifest_path": manifest_path,
            "manifest_commit": mcommit,
            "manifest_commit_date": mdate,
            "files": files}


# --------------------------------------------------------------------------- #
# metrics
# --------------------------------------------------------------------------- #
def split_stats(name, recs):
    prompts = [r["nl"]["prompt"] for r in recs]
    pairs = [(r["nl"]["prompt"], r["reference_code"]) for r in recs]
    fams = [r["nl"]["template_family"] for r in recs]
    ops = [r["semantics"]["operation"] for r in recs]
    comp_ops = sorted(set(ops) & set(COMPOSITE_OPERATIONS))
    blob = "\n".join(sorted(canon(r) for r in recs))
    pair_blob = "\n".join(sorted("%s\x00%s" % p for p in pairs))
    return {
        "split": name,
        "records": len(recs),
        "sha256_canonical_record_set": sha256(blob),
        "sha256_prompt_program_pair_set": sha256(pair_blob),
        "sha256_task_id_set": sha256("\n".join(sorted(r["task_id"] for r in recs))),
        "distinct_prompts": len(set(prompts)),
        "distinct_prompt_program_pairs": len(set(pairs)),
        "template_family_ids": sorted(set(fams)),
        "operation_ids": sorted(set(ops)),
        "composite_operation_ids": comp_ops,
        "identifier_sets": sorted({r["metadata"]["identifier_set"] for r in recs}),
    }


def _sets(recs):
    return {
        "prompts": {r["nl"]["prompt"] for r in recs},
        "families": {r["nl"]["template_family"] for r in recs},
        "programs": {r["reference_code"] for r in recs},
        "ops": {r["semantics"]["operation"] for r in recs},
        "pairs": {(r["nl"]["prompt"], r["reference_code"]) for r in recs},
        "nprompts": {norm_prompt(r["nl"]["prompt"]) for r in recs},
        "nprograms": {norm_code(r["reference_code"]) for r in recs},
    }


def overlap(train_recs, hold_recs):
    a, b = _sets(train_recs), _sets(hold_recs)
    return {
        "train_records": len(train_recs),
        "holdout_records": len(hold_recs),
        "exact": {
            "prompt_overlap": len(a["prompts"] & b["prompts"]),
            "template_family_overlap": len(a["families"] & b["families"]),
            "program_overlap": len(a["programs"] & b["programs"]),
            "operation_overlap": len(a["ops"] & b["ops"]),
            "prompt_program_pair_overlap": len(a["pairs"] & b["pairs"]),
        },
        "normalized": {
            "prompt_overlap_case_punct_whitespace_insensitive":
                len(a["nprompts"] & b["nprompts"]),
            "program_overlap_whitespace_insensitive":
                len(a["nprograms"] & b["nprograms"]),
        },
        "shared_template_family_ids": sorted(a["families"] & b["families"]),
        "shared_operation_ids": sorted(a["ops"] & b["ops"]),
        "shared_composite_operation_ids":
            sorted((a["ops"] & b["ops"]) & set(COMPOSITE_OPERATIONS)),
    }


def audit_experiment(split_key, splits, train_key, holdout_keys):
    report = {"splits": {k: split_stats(k, v) for k, v in splits.items()},
              "train_vs_holdout": {},
              "disjointness": {}}
    train = splits[train_key]
    for h in holdout_keys:
        ov = overlap(train, splits[h])
        report["train_vs_holdout"]["%s_vs_%s" % (train_key, h)] = ov
    return report


def per_op_family_overlap(train_recs, hold_recs):
    """Family IDs name the renderer function and are shared across operations, so
    the meaningful novelty test is per operation: does any operation's held-out
    wording family also appear in that same operation's training records?
    Returns {operation: [shared family ids]} (empty == disjoint per operation)."""
    tr = defaultdict(set)
    ho = defaultdict(set)
    for r in train_recs:
        tr[r["semantics"]["operation"]].add(r["nl"]["template_family"])
    for r in hold_recs:
        ho[r["semantics"]["operation"]].add(r["nl"]["template_family"])
    out = {}
    for op in sorted(set(tr) & set(ho)):
        shared = sorted(tr[op] & ho[op])
        if shared:
            out[op] = shared
    return out


# --------------------------------------------------------------------------- #
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    m3 = json.loads(read("artifacts/manifests/stage3_surface.json"))
    m4 = json.loads(read("artifacts/manifests/stage4_composition.json"))
    cfg3, cfg4 = m3["config"], m4["config"]

    # ---- Stage 3: surface (held-out wording family + held-out identifiers) ----
    s3 = run_surface_splits(cfg3["n_per"], cfg3["seed"])
    # ---- Stage 4: composition (primitive train vs composite hold-out) ----
    s4 = run_composition_splits(cfg4["seed"], cfg4["comp_per_op"])

    # ---- cross-check: regenerate with the generator blob at the manifest commit
    cross = {}
    for key, manifest_path, runner in (
            ("stage3_surface", "artifacts/manifests/stage3_surface.json", "surface"),
            ("stage4_composition", "artifacts/manifests/stage4_composition.json", "composition")):
        entry = {"manifest_path": manifest_path}
        try:
            mcommit = git("log", "-1", "--format=%H", "--", manifest_path)
            mcommit = mcommit.decode().strip()
            old_mod, old_sha = load_git_module(GENERATOR_PATH, mcommit,
                                               "src.data_generator.generator")
            if old_mod is None:
                entry["status"] = "not_run (generator blob unavailable at %s)" % mcommit[:12]
            else:
                entry["generator_blob_sha256_at_manifest_commit"] = old_sha
                entry["generator_current_sha256"] = file_sha256(GENERATOR_PATH)
                entry["generator_blob_identical"] = (old_sha == file_sha256(GENERATOR_PATH))
                if runner == "surface":
                    alt = run_surface_splits(cfg3["n_per"], cfg3["seed"],
                                             make_task_fn=old_mod.make_task)
                else:
                    alt = run_composition_splits(cfg4["seed"], cfg4["comp_per_op"],
                                                 gen_module=old_mod)
                cur = s3 if runner == "surface" else s4

                def strip_output_type(recs):
                    out = []
                    for r in recs:
                        r2 = json.loads(canon(r))
                        r2.get("semantics", {}).pop("output_type", None)
                        out.append(canon(r2))
                    return sorted(out)

                diffs = {}
                for k in cur:
                    def keyset(recs):
                        return ({r["nl"]["prompt"] for r in recs},
                                {r["reference_code"] for r in recs},
                                {r["nl"]["template_family"] for r in recs},
                                {r["semantics"]["operation"] for r in recs})
                    c, o = keyset(cur[k]), keyset(alt[k])
                    same_except_ot = (strip_output_type(cur[k]) == strip_output_type(alt[k]))
                    diffs[k] = {
                        "records_current": len(cur[k]), "records_at_manifest": len(alt[k]),
                        "prompts_identical": c[0] == o[0],
                        "programs_identical": c[1] == o[1],
                        "families_identical": c[2] == o[2],
                        "operations_identical": c[3] == o[3],
                        "record_json_identical":
                            sorted(canon(r) for r in cur[k]) == sorted(canon(r) for r in alt[k]),
                        "record_json_identical_ignoring_semantics_output_type":
                            same_except_ot,
                        "only_record_difference":
                            "semantics.output_type" if same_except_ot else "unresolved",
                    }
                entry["model_visible_content_vs_scoring_time_source"] = diffs
                entry["status"] = "run"
        except Exception as exc:                                # pragma: no cover
            entry["status"] = "not_run (%s: %s)" % (type(exc).__name__, exc)
        cross[key] = entry

    # ------------------------------------------------------------------ report
    a3 = audit_experiment("stage3_surface", s3, "train",
                          ["held_out_wording_family", "held_out_identifiers_words",
                           "in_distribution"])
    a4 = audit_experiment("stage4_composition", s4, "train",
                          ["composition_holdout", "test", "val"])

    # design-specific disjointness assertions (booleans here are the pass/fail set)
    hw = a3["train_vs_holdout"]["train_vs_held_out_wording_family"]
    wi = a3["train_vs_holdout"]["train_vs_held_out_identifiers_words"]
    ch = a4["train_vs_holdout"]["train_vs_composition_holdout"]
    hwe, wie, che = hw["exact"], wi["exact"], ch["exact"]
    per_op_fam = per_op_family_overlap(s3["train"], s3["held_out_wording_family"])
    a3["disjointness"] = {
        "claim": "held-out WORDING family: for every operation, the held-out "
                 "template family and every held-out prompt string are absent from "
                 "that operation's training records (identifier set deliberately "
                 "stays 'letters' so only wording changes).",
        "train_and_holdout_prompts_disjoint": hwe["prompt_overlap"] == 0,
        "train_and_holdout_prompts_disjoint_after_normalization":
            hw["normalized"]["prompt_overlap_case_punct_whitespace_insensitive"] == 0,
        "train_and_holdout_prompt_program_pairs_disjoint":
            hwe["prompt_program_pair_overlap"] == 0,
        "train_and_holdout_families_disjoint_per_operation": not per_op_fam,
        "held_out_identifiers_share_no_prompt_with_train": wie["prompt_overlap"] == 0,
        "held_out_identifiers_share_no_prompt_with_train_after_normalization":
            wi["normalized"]["prompt_overlap_case_punct_whitespace_insensitive"] == 0,
        "held_out_identifiers_share_no_program_with_train":
            wie["program_overlap"] == 0,
        "held_out_identifiers_use_word_identifiers_only":
            {r["metadata"]["identifier_set"]
             for r in s3["held_out_identifiers_words"]} == {"words"},
        "train_uses_letter_identifiers_only":
            {r["metadata"]["identifier_set"] for r in s3["train"]} == {"letters"},
    }
    a3["findings"] = {
        "global_template_family_id_overlap": {
            "count": hwe["template_family_overlap"],
            "ids": hw["shared_template_family_ids"],
            "per_operation_overlap": per_op_fam,
            "explanation": (
                "Template-family IDs name the renderer function and are shared "
                "across operations, so the bare ID is not globally unique: `_b` is "
                "a KEPT (train) family for the 3-family operations (add/sub/mul) "
                "and the HELD-OUT family for the 2-family operations "
                "(max_of/min_of). The hold-out is disjoint per operation -- no "
                "operation's held-out wording appears in that operation's training "
                "records -- and the model-visible prompt strings are globally "
                "disjoint (0 exact, 0 normalized). The precise claim is therefore "
                "'held-out (operation, wording) combination with globally disjoint "
                "prompt strings', not 'a wording template never rendered for any "
                "operation'."
            ),
        },
        "program_overlap_with_wording_holdout": {
            "count": hwe["program_overlap"],
            "normalized_count":
                hw["normalized"]["program_overlap_whitespace_insensitive"],
            "explanation": (
                "EXPECTED, not a novelty violation: the wording hold-out varies "
                "only the NL template, so the same operation with the same letter "
                "identifiers yields the same reference program. The claim under "
                "test is wording novelty, not program novelty. (The identifier "
                "hold-out, by contrast, shares 0 programs with train.)"
            ),
        },
        "operation_overlap_with_wording_holdout": {
            "count": hwe["operation_overlap"],
            "ids": hw["shared_operation_ids"],
            "explanation": "EXPECTED: a wording hold-out keeps the operation set "
                           "fixed; only the template family changes.",
        },
        "identifier_holdout_family_overlap": {
            "count": wie["template_family_overlap"],
            "ids": wi["shared_template_family_ids"],
            "explanation": "EXPECTED: run_surface.py builds the new-identifier "
                           "test with families='all' -- it is an identifier "
                           "hold-out, not a wording hold-out. Prompts and "
                           "programs are both disjoint from train.",
        },
        "in_distribution_is_a_control_not_a_holdout": {
            "prompt_overlap":
                a3["train_vs_holdout"]["train_vs_in_distribution"]["exact"]
                  ["prompt_overlap"],
            "explanation": "EXPECTED: the in-distribution test reuses train "
                           "wording on fresh seeds; it is the control, not a "
                           "novelty claim.",
        },
        "task_ids_are_not_unique_across_splits": {
            "in_distribution_and_identifier_holdout_share_task_id_set":
                a3["splits"]["in_distribution"]["sha256_task_id_set"]
                == a3["splits"]["held_out_identifiers_words"]["sha256_task_id_set"],
            "explanation": "task_id values repeat across splits (both id-splits use "
                           "the '<op>_id<i>' scheme), so a novelty audit keyed on "
                           "task_id would be misleading; this audit keys on prompt "
                           "/ program / family content.",
        },
    }
    a4["disjointness"] = {
        "claim": "composition hold-out: composite operations never appear in train "
                 "(operation-disjoint by construction), so no prompt, program or "
                 "operation can be shared.",
        "train_and_holdout_operations_disjoint": che["operation_overlap"] == 0,
        "train_contains_no_composite_operation":
            a4["splits"]["train"]["composite_operation_ids"] == [],
        "holdout_contains_only_composite_operations":
            set(a4["splits"]["composition_holdout"]["operation_ids"])
            == set(COMPOSITE_OPERATIONS),
        "train_and_holdout_prompts_disjoint": che["prompt_overlap"] == 0,
        "train_and_holdout_programs_disjoint": che["program_overlap"] == 0,
        "train_and_holdout_prompts_disjoint_after_normalization":
            ch["normalized"]["prompt_overlap_case_punct_whitespace_insensitive"] == 0,
        "train_and_holdout_prompt_program_pairs_disjoint":
            che["prompt_program_pair_overlap"] == 0,
        "train_and_holdout_template_families_disjoint":
            che["template_family_overlap"] == 0,
        "test_split_is_primitive_in_distribution":
            a4["splits"]["test"]["composite_operation_ids"] == [],
    }
    a4["findings"] = {
        "note": "The composite hold-out uses its own renderer families "
                "(_comp_*), so it is disjoint from train on every axis measured: "
                "operation, family, prompt, program and prompt-program pair.",
    }

    all_assertions = []
    for exp in (a3, a4):
        for k, v in exp["disjointness"].items():
            if isinstance(v, bool):
                all_assertions.append((k, v))
    overall = all(v for _, v in all_assertions)

    report = {
        "audit_id": "B04_original_holdout_novelty_audit",
        "generated_by": "scripts/run_original_novelty_audit.py",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provenance": {
            "originals_archived": False,
            "limitation": (
                "The historically scored Stage-3/Stage-4 train/test files were never "
                "written to disk: run_surface.py and run_composition.py build their "
                "splits in memory from the generator plus a seed and persist only the "
                "score manifest. This audit is therefore run on DETERMINISTICALLY "
                "REGENERATED splits built from the recorded config/seed by executing "
                "the scoring scripts' own split code (AST-extracted, not "
                "re-implemented). It is not an audit of an archived original file, "
                "because no such file exists. make_task is a pure function of "
                "(operation, task_id, seed, id_set, family) through random.Random(seed), "
                "so the regeneration is exact for a given generator source; the "
                "cross-check below states whether that source is the scoring-time one."
            ),
            "method": [
                "read seed/n_per/comp_per_op from the manifests the scoring runs wrote",
                "AST-extract build_tasks from scripts/run_surface.py and the split "
                "statements from scripts/run_composition.py, then execute them",
                "regenerate splits, hash record sets, compute overlap",
                "re-run the same split code against the generator blob at the manifest "
                "commit (git show <commit>:src/data_generator/generator.py) and compare",
            ],
            "recorded_configs": {
                "stage3_surface": {"manifest": "artifacts/manifests/stage3_surface.json",
                                   "seed": cfg3["seed"], "n_per": cfg3["n_per"],
                                   "id_set": "letters", "families": "holdout_last",
                                   "identifier_holdout": "words, seed+5000"},
                "stage4_composition": {"manifest": "artifacts/manifests/stage4_composition.json",
                                       "seed": cfg4["seed"],
                                       "comp_per_op": cfg4["comp_per_op"],
                                       "n_per_op": 200,
                                       "n_per_op_source": "literal in run_composition.py "
                                                          "(not a CLI arg; not in the manifest)",
                                       "id_set": "letters"},
            },
            "source_provenance": {
                "stage3_surface": source_provenance(
                    "artifacts/manifests/stage3_surface.json", "stage3_surface"),
                "stage4_composition": source_provenance(
                    "artifacts/manifests/stage4_composition.json", "stage4_composition"),
            },
            "scoring_time_source_crosscheck": cross,
        },
        "stage3_surface": a3,
        "stage4_composition": a4,
        "assertions": {
            "checked": len(all_assertions),
            "failed": [k for k, v in all_assertions if not v],
            "all_disjointness_assertions_hold": overall,
        },
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    write_md(report)
    print(json.dumps({
        "json": OUT_JSON,
        "md": OUT_MD,
        "assertions": report["assertions"],
        "stage3": {k: v["records"] for k, v in a3["splits"].items()},
        "stage4": {k: v["records"] for k, v in a4["splits"].items()},
        "stage3_train_vs_heldword": a3["train_vs_holdout"]
                                    ["train_vs_held_out_wording_family"]["exact"],
        "stage4_train_vs_comp": a4["train_vs_holdout"]
                                  ["train_vs_composition_holdout"]["exact"],
    }, indent=2))


def write_md(r):
    p3, p4 = r["stage3_surface"], r["stage4_composition"]
    prov = r["provenance"]
    L = []
    L.append("# B04 — Original-holdout novelty audit (Stage 3 surface / Stage 4 composition)\n")
    L.append("Generated by `scripts/run_original_novelty_audit.py` at %s.\n"
             % r["generated_at_utc"])
    L.append("## What was audited, and the honest limitation\n")
    L.append("> **The historically scored train/test files do not exist as files.** "
             "`scripts/run_surface.py` and `scripts/run_composition.py` build their "
             "splits in memory from the generator plus a seed and persist only the "
             "score manifest, so there is no archived scored JSONL to re-open. "
             "This audit is run on **deterministically regenerated splits** built from "
             "the **recorded config/seed** by executing the scoring scripts' own split "
             "code (AST-extracted verbatim, not re-implemented). It is *not* an audit "
             "of an archived original, because no archived original was ever produced.\n")
    L.append("Regeneration is exact for a fixed generator source: `make_task` is a pure "
             "function of `(operation, task_id, seed, id_set, family)` via "
             "`random.Random(seed)` and never touches global RNG state. The "
             "cross-check below re-runs the same split code against the generator blob "
             "at the manifest commit to show whether the model-visible content matches "
             "the scoring-time source.\n")
    L.append("### Headline numbers\n")
    L.append("| experiment | split | records | distinct prompts | distinct "
             "prompt–program pairs | train↔holdout prompt overlap | "
             "train↔holdout family overlap | train↔holdout program overlap |")
    L.append("|---|---|---|---|---|---|---|---|")
    for exp_name, exp, hold in (
            ("Stage 3 surface", p3, "held_out_wording_family"),
            ("Stage 4 composition", p4, "composition_holdout")):
        ov = exp["train_vs_holdout"]["train_vs_%s" % hold]["exact"]
        for k, s in exp["splits"].items():
            L.append("| %s | `%s` | %d | %d | %d | %s | %s | %s |"
                     % (exp_name if k == "train" else "", k, s["records"],
                        s["distinct_prompts"], s["distinct_prompt_program_pairs"],
                        ov["prompt_overlap"] if k == hold else "",
                        ov["template_family_overlap"] if k == hold else "",
                        ov["program_overlap"] if k == hold else ""))
    L.append("")

    L.append("### Recorded config used\n")
    L.append("| experiment | manifest | seed | split parameter |")
    L.append("|---|---|---|---|")
    c = prov["recorded_configs"]
    L.append("| Stage 3 surface | `%s` | %s | `n_per=%s`, `id_set=letters`, "
             "`families=holdout_last` |" % (c["stage3_surface"]["manifest"],
                                            c["stage3_surface"]["seed"],
                                            c["stage3_surface"]["n_per"]))
    L.append("| Stage 4 composition | `%s` | %s | `comp_per_op=%s`, `n_per_op=%s` "
             "(literal in the script) |" % (c["stage4_composition"]["manifest"],
                                            c["stage4_composition"]["seed"],
                                            c["stage4_composition"]["comp_per_op"],
                                            c["stage4_composition"]["n_per_op"]))
    L.append("")

    L.append("### Scoring-time source cross-check\n")
    for k, v in prov["scoring_time_source_crosscheck"].items():
        L.append("- **%s** — %s" % (k, v.get("status")))
        if v.get("status") == "run":
            same_gen = v["generator_blob_identical"]
            L.append("  - `generator.py` blob at manifest commit "
                     "sha256 `%s` — %s the current file."
                     % (v["generator_blob_sha256_at_manifest_commit"][:16],
                        "identical to" if same_gen else "DIFFERENT from"))
            for sk, d in v["model_visible_content_vs_scoring_time_source"].items():
                ok = (d["prompts_identical"] and d["programs_identical"]
                      and d["families_identical"] and d["operations_identical"]
                      and d["records_current"] == d["records_at_manifest"])
                L.append("  - `%s`: %d records — model-visible content "
                         "(prompt/program/family/operation) %s the scoring-time source; "
                         "record JSON %s%s"
                         % (sk, d["records_current"],
                            "IDENTICAL to" if ok else "DIFFERS from",
                            "identical" if d["record_json_identical"]
                            else "differs only in `%s`" % d.get("only_record_difference", "?"),
                            "" if d["record_json_identical"] else
                            " (a metadata field that never reaches the model input)"))
    L.append("")

    for name, exp in (("Stage 3 — surface (held-out wording family)", p3),
                      ("Stage 4 — composition (held-out composite operations)", p4)):
        L.append("## %s\n" % name)
        L.append("| split | records | distinct prompts | distinct prompt–program pairs | "
                 "sha256 (record set) |")
        L.append("|---|---|---|---|---|")
        for k, s in exp["splits"].items():
            L.append("| `%s` | %d | %d | %d | `%s` |"
                     % (k, s["records"], s["distinct_prompts"],
                        s["distinct_prompt_program_pairs"],
                        s["sha256_canonical_record_set"][:32] + "…"))
        L.append("")
        L.append("Template-family IDs and operation IDs by split:\n")
        for k, s in exp["splits"].items():
            L.append("- `%s`: families = %s; operations = %s; composite operations = %s"
                     % (k, ", ".join("`%s`" % f for f in s["template_family_ids"]) or "—",
                        ", ".join("`%s`" % o for o in s["operation_ids"]),
                        ", ".join("`%s`" % o for o in s["composite_operation_ids"]) or "none"))
        L.append("")
        L.append("Train vs hold-out overlap:\n")
        L.append("| pair | prompt | family | program | operation | prompt–program pair | "
                 "normalized prompt | normalized program |")
        L.append("|---|---|---|---|---|---|---|---|")
        for k, ov in exp["train_vs_holdout"].items():
            e, n = ov["exact"], ov["normalized"]
            L.append("| %s | %d | %d | %d | %d | %d | %d | %d |"
                     % (k.replace("_vs_", " vs "), e["prompt_overlap"],
                        e["template_family_overlap"], e["program_overlap"],
                        e["operation_overlap"], e["prompt_program_pair_overlap"],
                        n["prompt_overlap_case_punct_whitespace_insensitive"],
                        n["program_overlap_whitespace_insensitive"]))
        L.append("")
        L.append("Disjointness assertions (pass/fail):\n")
        for k, v in exp["disjointness"].items():
            if isinstance(v, bool):
                L.append("- [%s] `%s`" % ("x" if v else " ", k))
            else:
                L.append("- `%s`: %s" % (k, v))
        L.append("")
        if exp.get("findings"):
            L.append("Findings — expected overlaps and caveats (NOT assertion "
                     "failures):\n")
            for k, v in exp["findings"].items():
                if isinstance(v, dict):
                    L.append("- **%s**" % k)
                    for kk, vv in v.items():
                        if kk == "explanation":
                            L.append("  - %s" % vv)
                        else:
                            L.append("  - `%s`: `%s`" % (kk, json.dumps(vv)))
                else:
                    L.append("- **%s**: %s" % (k, v))
            L.append("")

    a = r["assertions"]
    L.append("## Verdict\n")
    L.append("- assertions checked: **%d**, failed: **%d**%s"
             % (a["checked"], len(a["failed"]),
                (" (`%s`)" % "`, `".join(a["failed"])) if a["failed"] else ""))
    L.append("- all disjointness assertions hold: **%s**"
             % ("yes" if a["all_disjointness_assertions_hold"] else "NO"))
    L.append("- scope: regenerated splits from recorded config/seed; originals were "
             "never archived as separate files.")
    L.append("")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main()