#!/usr/bin/env bash
# Retry-on-SIGILL wrapper for the corrected experiment runs.
#
# The host intermittently kills processes with SIGILL (exit 132 /
# "Illegal instruction"). Retry up to MAX_RETRY (default 10) times with a 4s
# pause. Any other exit code, or a failure log without the SIGILL signature,
# is a real error and stops immediately.
#
# Usage: scripts/retry_on_sigill.sh <cmd> [args...]
set -u
MAX_RETRY=${MAX_RETRY:-10}
LOG_DIR=${LOG_DIR:-artifacts/raw_outputs/corrected_logs}
mkdir -p "$LOG_DIR"

script=$1
name=""
for a in "$@"; do
  case "$a" in
    *.py) name=$(basename "$a" .py); break ;;
  esac
done
[ -n "$name" ] || name=$(basename "$script")
tag="${name}_$(printf '%s' "$*" | md5sum | cut -c1-8)"

for i in $(seq 1 "$MAX_RETRY"); do
  log="$LOG_DIR/${tag}_attempt${i}.log"
  "$@" >"$log" 2>&1
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "[retry] OK: $* (attempt $i/$MAX_RETRY, log $log)"
    exit 0
  fi
  if [ "$rc" -eq 132 ] || grep -q "Illegal instruction" "$log"; then
    echo "[retry] SIGILL (rc=$rc) on attempt $i/$MAX_RETRY: $* -- sleeping 4s"
    tail -3 "$log"
    sleep 4
    continue
  fi
  echo "[retry] REAL ERROR (rc=$rc): $* -- log $log"
  tail -25 "$log"
  exit "$rc"
done
echo "[retry] exhausted $MAX_RETRY attempts: $*"
exit 132