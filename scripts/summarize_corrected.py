#!/usr/bin/env python3
"""Aggregate the corrected experiment manifests into the final JSON summary.

Reads (without modifying) artifacts/manifests/data_scaling_corrected_seed{0,1,2}.json
and artifacts/manifests/surface_corrected_seed{0,1,2}.json and prints one JSON
object with the corrected tables + realized counts + verification notes.

Usage: .venv-311/bin/python scripts/summarize_corrected.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
MAN = os.path.join(ROOT, "artifacts", "manifests")

SEEDS = [0, 1, 2]


def main():
    ds_rows, sf_rows = [], []
    ds_manifests, sf_manifests = [], []
    tok_shas_ds, tok_shas_sf = set(), set()

    for seed in SEEDS:
        p1 = os.path.join(MAN, f"data_scaling_corrected_seed{seed}.json")
        m1 = json.load(open(p1))
        ds_manifests.append(os.path.relpath(p1, ROOT))
        tok_shas_ds.add(m1["tokenizer"]["sha256"])
        assert m1["seed"] == seed
        for r in m1["rows"]:
            assert r["ops_covered"] == 10, r
            assert r["model_denominator"] == m1["test_set"]["n"]
            assert len(r["per_op_pass_at_1"]) == 10
            ds_rows.append({
                "seed": seed,
                "size": r["size"],
                "n_per_op": r["n_per_op"],
                "per_op_counts": r["per_op_counts"],
                "ops_covered": r["ops_covered"],
                "aggregate_pass_at_1": r["aggregate_pass_at_1"],
                "successes": r["model_successes"],
                "denominator": r["model_denominator"],
                "per_op_pass_at_1": r["per_op_pass_at_1"],
                "template_pass_at_1": r["template_pass_at_1"],
                "retrieval_pass_at_1": r["retrieval_pass_at_1"],
                "final_loss": r["final_loss"],
                "steps": r["steps"],
            })

        p2 = os.path.join(MAN, f"surface_corrected_seed{seed}.json")
        m2 = json.load(open(p2))
        sf_manifests.append(os.path.relpath(p2, ROOT))
        tok_shas_sf.add(m2["tokenizer"]["sha256"])
        assert m2["seed"] == seed
        assert m2["train_set"]["ops_covered"] == 10
        for cell, e in m2["conditions"].items():
            assert e["denominator"] == e["n"]
            for lbl, s in e["systems"].items():
                assert s["denominator"] == e["denominator"], (cell, lbl)
            sf_rows.append({
                "seed": seed,
                "condition": cell,
                "id_set": e["id_set"],
                "wording": e["wording"],
                "ops_covered": e["ops_covered"],
                "excluded_ops": e["excluded_ops"],
                "denominator": e["denominator"],
                "realized_n": e["n"],
                "model_successes": e["systems"]["MODEL"]["successes"],
                "model_pass_at_1": e["systems"]["MODEL"]["pass_at_1"],
                "template_successes": e["systems"]["TEMPLATE"]["successes"],
                "template_pass_at_1": e["systems"]["TEMPLATE"]["pass_at_1"],
                "retrieval_successes": e["systems"]["RETRIEVAL"]["successes"],
                "retrieval_pass_at_1": e["systems"]["RETRIEVAL"]["pass_at_1"],
                "model_per_op_pass_at_1": e["systems"]["MODEL"]["per_op"],
            })

    assert len(tok_shas_ds) == 1, f"B1 tokenizer drifted: {tok_shas_ds}"
    assert len(tok_shas_sf) == 1, f"B3 tokenizer drifted: {tok_shas_sf}"
    assert len(ds_rows) == 12 and len(sf_rows) == 12

    # compact human table for the summary strings
    ds_tbl = ["seed size  n/op  pass@1  succ/denom   loss | per-op pass@1"]
    for r in ds_rows:
        perop = " ".join(f"{op}:{v}" for op, v in sorted(r["per_op_pass_at_1"].items()))
        ds_tbl.append(f"{r['seed']}  {r['size']:5d} {r['n_per_op']:4d}  "
                      f"{r['aggregate_pass_at_1']:.3f}  {r['successes']}/"
                      f"{r['denominator']}  {r['final_loss']:.4f} | {perop}")

    sf_tbl = ["seed condition      ops excluded              denom  model      "
              "template   retrieval"]
    for r in sf_rows:
        sf_tbl.append(
            f"{r['seed']}  {r['condition']:14s} {r['ops_covered']:3d} "
            f"{','.join(r['excluded_ops']) or '-':22s} {r['denominator']:5d}  "
            f"{r['model_successes']:3d}/{r['denominator']}={r['model_pass_at_1']:.3f} "
            f"{r['template_successes']:3d}/{r['denominator']}={r['template_pass_at_1']:.3f} "
            f"{r['retrieval_successes']:3d}/{r['denominator']}={r['retrieval_pass_at_1']:.3f}")

    out = {
        "data_scaling_corrected": json.dumps({
            "experiment": "data_scaling_corrected (fixes P0-01)",
            "design": "balanced operation-stratified train sets (size/10 per op, "
                      "10/10 ops), ONE fixed tokenizer across sizes+seeds, fixed "
                      "arch (128/4L/4H/block128), 1000 steps, bs16, lr1e-3, "
                      "fixed 300-task held-out test (30/op, 10/10 ops)",
            "tokenizer_sha256": sorted(tok_shas_ds)[0],
            "test_denominator_per_arm": 300,
            "rows": ds_rows,
            "table": ds_tbl,
        }, indent=1),
        "surface_corrected": json.dumps({
            "experiment": "surface_corrected (fixes P0-03 + P0-04)",
            "design": "2x2 factorial identifier(letters|words) x "
                      "wording(kept|held-out family); one fixed train set "
                      "(600 tasks, 60/op, 10/10 ops, letters x kept families), "
                      "ONE fixed train-only tokenizer, model+template+retrieval "
                      "scored on identical task sets; 1500 steps, bs16, lr1e-3",
            "tokenizer_sha256": sorted(tok_shas_sf)[0],
            "expected_denominators": {"familiar": 600, "id_only": 600,
                                      "wording_only": 480, "combined": 480},
            "rows": sf_rows,
            "table": sf_tbl,
        }, indent=1),
        "manifests": ds_manifests + sf_manifests,
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()