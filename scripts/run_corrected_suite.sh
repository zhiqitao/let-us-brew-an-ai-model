#!/usr/bin/env bash
# Run BOTH corrected experiments for seeds 0,1,2 with retry-on-SIGILL.
# Sequential on purpose: the host has 2 CPUs and OMP_NUM_THREADS=2.
# The corrected scripts are resume-safe (partial results + checkpoints), so a
# SIGILL retry restarts only the arm/condition that died.
#
# Usage: bash scripts/run_corrected_suite.sh
set -u
cd "$(dirname "$0")/.."
PY=.venv-311/bin/python
export TORCH_DISABLE_AVX2=1 OMP_NUM_THREADS=2

for seed in 0 1 2; do
  echo "=== data_scaling_corrected seed=$seed ==="
  bash scripts/retry_on_sigill.sh "$PY" scripts/run_data_scaling_corrected.py --seed "$seed" || exit 1
done
for seed in 0 1 2; do
  echo "=== surface_corrected seed=$seed ==="
  bash scripts/retry_on_sigill.sh "$PY" scripts/run_surface_corrected.py --seed "$seed" || exit 1
done
echo "ALL CORRECTED RUNS COMPLETE"