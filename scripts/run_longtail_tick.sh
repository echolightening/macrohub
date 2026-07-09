#!/bin/bash
# run_longtail_tick.sh — launchd entry point for the M9 long-tail composition
# tick (NOT YET RUNNABLE — the operator-pruning gate blocks this, see below).
#
# AGENDA item 28 M9. This wraps the (not-yet-written) longtail_composition.py,
# which will decompose operator-approved dishes from
# data/fooddb/long-tail-candidates.md into USDA-ingredient-summed macro
# records (provenance: computed), falling back to low-confidence
# ai-estimated only when no ingredient mapping is possible (capped at <=10%
# of long-tail records, per Fable verdict modification 3).
#
# Self-terminating design (brief §"launchd vs one-shot", item 5): this tick
# unloads its own launchd job at the FIRST of:
#   (a) cumulative Haiku spend >= $10 total (list-generation's ~$0 + this
#       phase's spend, tracked in data/fooddb/.spend.json)
#   (b) 7 daily ticks elapsed
#   (c) the candidate work-list is drained (processed-set == pruned candidate
#       set from long-tail-candidates.md)
# Per-tick guards: <=30 min wall-clock, <=300 items, <=$1.50 Haiku spend
# (LOCKED.md invariant 5).
#
# BLOCKED ON OPERATOR (see STATE.md): this script and longtail_composition.py
# must NOT run unattended until the operator has reviewed and pruned
# data/fooddb/long-tail-candidates.md. This wrapper exists (per dispatch
# instructions, mirroring item-15's written-not-installed plist) so the
# plist below is installable the moment that gate clears — it is not wired
# to run anything destructive today.
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$PROJECT_DIR/logs/longtail_tick.log"
PRUNE_MARKER="$PROJECT_DIR/data/fooddb/.longtail-candidates-approved"
mkdir -p "$PROJECT_DIR/logs"

echo "=== macrohub longtail tick: $(date) ===" >> "$LOG"

if [ ! -f "$PRUNE_MARKER" ]; then
  echo "BLOCKED: $PRUNE_MARKER not found. Operator has not yet reviewed/pruned " \
       "data/fooddb/long-tail-candidates.md and confirmed the remainder. " \
       "Per Fable verdict modification 1, no long-tail spend may occur past " \
       "list generation until this gate clears. Exiting without doing anything." >> "$LOG"
  exit 0
fi

export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
# longtail_composition.py does not exist yet — M9 build work, out of scope
# for this M8 dispatch. This line is the intended wiring once it's built.
/usr/bin/python3 "$PROJECT_DIR/scripts/longtail_composition.py" >> "$LOG" 2>&1
