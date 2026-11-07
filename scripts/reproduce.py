#!/usr/bin/env python3
"""reproduce.py — regenerate ONE recorded experiment manifest end-to-end.

Round-1 R3-EX-04: `make reproduce` referenced this file, which existed in no
commit. It is a deliberately THIN wrapper around the existing run scripts — no
training/eval logic is duplicated here, the runner is invoked verbatim.

Default mode is a DRY RUN: it prints the exact command it would run and the
output manifest path, then exits 0 (so `make reproduce` is cheap and safe — a
full CPU training run takes hours). Pass --run to actually execute.

The runner writes into artifacts/reproduced/ (gitignored), NEVER over
artifacts/manifests/ — the recorded manifests are the archived evidence the
book cites and must not be clobbered by a re-run. Note (Appendix C): a re-run
is a fresh training and is not expected to reproduce the recorded numbers
exactly.

Usage:
    python scripts/reproduce.py --list           # enumerate regenerable manifests
    python scripts/reproduce.py                  # dry-run the default target
    python scripts/reproduce.py --target diversity_corrected_seed1 --run
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Regenerable manifests: id -> (runner script, extra argv, output manifest name).
# Only runs whose committed runner takes an explicit --seed are listed; the
# mapping is data, the execution is the runner's own.
REGISTRY = {}
for _fam in ("data_scaling_corrected", "diversity_corrected", "surface_corrected"):
    for _seed in (0, 1, 2):
        _id = f"{_fam}_seed{_seed}"
        REGISTRY[_id] = (f"scripts/run_{_fam}.py", ["--seed", str(_seed)],
                         f"{_id}.json")
DEFAULT_TARGET = "data_scaling_corrected_seed0"
OUT_DIR = os.path.join("artifacts", "reproduced")


def plan(target):
    """(command argv, repo-relative output manifest path) for a registry id."""
    script, extra, manifest = REGISTRY[target]
    out_dir = OUT_DIR.replace(os.sep, "/")
    argv = [sys.executable, script, *extra, "--manifest-dir", out_dir]
    return argv, f"{out_dir}/{manifest}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true",
                    help="enumerate regenerable manifests and exit")
    ap.add_argument("--target", default=DEFAULT_TARGET,
                    help=f"registry id to regenerate (default: {DEFAULT_TARGET})")
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="print the plan and exit 0 (default)")
    ap.add_argument("--run", action="store_true",
                    help="actually execute the runner (overrides --dry-run)")
    args = ap.parse_args()

    if args.list:
        for tid in sorted(REGISTRY):
            _, out = plan(tid)
            script = REGISTRY[tid][0]
            print(f"{tid:36s} <- {script:42s} -> {out}")
        return 0

    if args.target not in REGISTRY:
        print(f"FAIL  unknown target {args.target!r}; use --list "
              f"({len(REGISTRY)} regenerable manifests)", file=sys.stderr)
        return 2

    argv, out_path = plan(args.target)
    print(f"target:         {args.target}")
    print(f"command:        {' '.join(argv)}")
    print(f"output manifest: {out_path}")
    print("note:           recorded manifests under artifacts/manifests/ are "
          "never overwritten; a re-run may not reproduce the recorded numbers "
          "exactly (Appendix C).")

    if not args.run:
        print("dry run — nothing executed (pass --run to execute).")
        return 0

    tok = os.path.join(ROOT, "artifacts", "tokenizer")
    if not os.path.isdir(tok):
        print("FAIL  artifacts/tokenizer/ is missing (gitignored); run the "
              "quickstart generation step (scripts/generate_data.py + the run "
              "scripts) first.", file=sys.stderr)
        return 1
    os.makedirs(os.path.join(ROOT, OUT_DIR), exist_ok=True)
    print("running...", flush=True)
    return subprocess.call(argv, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())