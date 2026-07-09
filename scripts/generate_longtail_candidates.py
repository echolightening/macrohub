#!/usr/bin/env python3
"""
generate_longtail_candidates.py — ONE bounded Haiku call to generate a
candidate list of long-tail dishes for MacroHub Track-2's ethnic/home-cooked
coverage gap.

AGENDA item 28, milestone M8, per Fable verdict required modification 1
(fable-bench:item28-nutrition-research-2026-07-09):
  "Long-tail seeding: operator-pruned seed list, and it is an M8 gate item.
  Haiku may generate the candidate dish list, but ZERO long-tail spend beyond
  list generation occurs until the operator/commissioner prunes it. Cap list
  generation itself at ≤$0.50 of the $10 total budget."

Execution note: no metered Anthropic API key exists in this cluster's secrets
(~/local-ai/.{gemini,openai,xai,runpod}_key — no .anthropic_key). Per the
established item-15 precedent (STATE.md design note there), Claude calls in
these pipelines run as headless `claude -p --model haiku` on the operator's
Max session — $0 marginal, so the ≤$0.50 cap is trivially satisfied by
construction (one bounded call, no loop, no retry-to-exhaustion). This is a
build-time judgment call consistent with precedent, not a re-litigation of
the verdict — flagged here and in STATE.md.

THIS SCRIPT DOES ONLY LIST GENERATION. It does not compose recipes, does not
call USDA ingredient lookups, does not write fooddb records. That is the
explicitly out-of-scope M9 phase, gated on operator pruning of this output.

Output: plain markdown file, human-reviewable, NOT consumed automatically by
any downstream script until an operator has edited it.
"""
import datetime
import os
import subprocess
import sys

OUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "fooddb", "long-tail-candidates.md"
)

PROMPT = """You are helping seed a personal nutrition-tracking database's long-tail coverage list.

The database already has solid coverage from three free bulk sources:
- USDA FoodData Central (raw ingredients, US packaged/branded foods, USDA "foods as eaten" mixed dishes)
- Open Food Facts (worldwide packaged/branded grocery products, label-derived)
- MenuStat (major US chain restaurant menu items, 2018 panel)

What's NOT well covered by those three: home-cooked ethnic/cultural dishes that aren't
sold as a packaged product or chain-restaurant item — the kind of dish someone cooks from
a family recipe or orders at an independent (non-chain) restaurant, where the only way to
estimate macros is to decompose the dish into its component ingredients and sum USDA
per-ingredient nutrition data.

Generate a candidate list of 80-120 such dishes, organized by cuisine/region, that would be
useful additions to a personal macro-tracking database. For each dish give just the name and
a 3-8 word description of its typical composition (e.g. main ingredients) — do NOT estimate
any macro numbers, calories, or nutrition values. This is a NAMING/SCOPING list only.

Format as a markdown list grouped by cuisine heading (## Cuisine name), one dish per line as:
- Dish name — brief composition note

Cover a broad spread of world cuisines (South/Southeast/East Asian, Middle Eastern, African,
Latin American, Caribbean, Eastern European, etc.) and favor dishes that are commonly eaten
but genuinely hard to find on a US chain menu or a packaged-food label. Do not include
disclaimers or preamble — output the list directly."""


def log(msg):
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    print(f"[{ts}] [generate_longtail_candidates] {msg}", flush=True)


def main():
    log("dispatching ONE bounded headless Haiku call for candidate-list generation "
        "(list generation only — no composition/estimation spend past this call, "
        "per Fable verdict modification 1)")
    try:
        res = subprocess.run(
            ["claude", "-p", PROMPT, "--model", "haiku"],
            capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        log("FAILED: headless claude call timed out after 180s")
        sys.exit(1)
    if res.returncode != 0 or not res.stdout.strip():
        log(f"FAILED: headless claude call returned code {res.returncode}: "
            f"{res.stderr.strip()[-500:]}")
        sys.exit(1)

    body = res.stdout.strip()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    header = (
        "<!--\n"
        "Long-tail candidate dish list — MacroHub Track-2, AGENDA item 28 M8.\n"
        f"Generated {now} via ONE headless `claude -p --model haiku` call "
        "(generate_longtail_candidates.py). List generation ONLY — per Fable verdict\n"
        "fable-bench:item28-nutrition-research-2026-07-09 required modification 1, ZERO\n"
        "long-tail composition/estimation spend has occurred past this list.\n\n"
        "BLOCKED ON OPERATOR: review this list, cross out anything not wanted, confirm the\n"
        "remainder before M9 (recipe-composition + fooddb-record spend) proceeds. See\n"
        "STATE.md 'BLOCKED-ON-OPERATOR' item.\n"
        "-->\n\n"
        "# Long-tail candidate dishes (operator review required before M9)\n\n"
    )
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(header + body + "\n")

    n_lines = sum(1 for line in body.splitlines() if line.strip().startswith("- "))
    log(f"DONE: wrote {OUT_PATH} — approx {n_lines} candidate dish lines. "
        "STOPPING HERE per scope — no further spend past this call.")


if __name__ == "__main__":
    main()
