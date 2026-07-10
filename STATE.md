# STATE — MacroHub (READ FIRST)

Canonical current state. Item 28 in the commissioner AGENDA (`~/local-ai/AGENDA.md`),
Trailblazer Mode. Full build plan: `~/local-ai/specs/plans/item28-macrohub-plan.md`.

## What this is
A single-file vanilla-JS PWA (`index.html`, no framework/build step) for daily macro
estimation: paste a meal description and/or upload photos/PDFs, four AI providers (Claude,
GPT-5.5, Gemini, Grok) estimate macros in parallel, cross-AI statistics (5m/5m+) synthesize
a conservative ceiling, a "Nourish" summary is generated, and a full session log emails out.
No backend; API keys live in localStorage on-device only. Deploys via GitHub Pages.
Architecture detail: `README.md` §Architecture; setup: `README.md` §Setup.

## Current status (as of enrollment, 2026-07-09)
HEAD `37acccb` — v1d two-stage EXTRACT→JUDGE pipeline pass (frontier models never see
images directly in that path; Claude stage-1 extract call effort-tuned).

Last Fable review: 2026-07-09 @ eb6aa66 — plan authored and critiqued
(`fable-bench:item28-macrohub-plan-2026-07-09`), not yet a code review.

**Critical gap the item-28 build closes: there is NO meal persistence today.** All state
(`results`, `histories`, `rawResponses`) is in-memory per session; `newMeal()` emails the
log and clears everything. Only API keys + settings persist (localStorage, `mk_*` keys).

## Progress
**Fixes 2026-07-10 (operator-reported live, all pushed):**
- `9e7b1d8` — Encrypt-payloads checkbox was genuinely dead (CSS `-webkit-appearance:none` meant
  for text inputs was also zeroing out the checkbox). Already committed locally by a prior
  session but never pushed; pushed now.
- `e5e990f` — a meal only persisted to IndexedDB on "+ new meal", not when estimated — so syncing
  right after logging a meal correctly (if confusingly) reported "0 meals synced". Now persists
  at the end of `runAll()`/`sendFollowup()` too.
- `033f9b4` — custom scale-factor input (any number, e.g. 1.75x) alongside the existing
  0.5x/1.5x/2x presets, whole-meal and per-item.
- `4001f10` — **sync is now fully automatic**, no button required: debounced (2.5s) on any
  meal add/edit/delete, a 5-min visible-tab safety net, and an immediate pull on page load.
  Found+fixed a real latent bug while wiring this up: the merge logic was purely additive with
  no concept of deletion, so a hard-deleted meal would've been silently resurrected by the very
  next auto-sync. Fixed via tombstones (`deleteHistoryMeal` soft-deletes, `listVisibleMeals()`
  hides them from the UI, `listMeals()` stays raw for the sync merge to see). Verified live with
  a mocked GitHub API across two simulated devices, not just read as a diff.

**M2 DONE 2026-07-09** (`ed01e1f`): meal data model + storage layer (IndexedDB, local-first).
`newMeal()` now persists via `persistCurrentMealIfAny()` before clearing — closes the
"no meal persistence" gap above. Fable checkpoint ADOPT WITH MODIFICATIONS
(`fable-bench:item28-m2-schema-checkpoint-2026-07-09`) — required fix (stable `meal_id`
across retries, prevents duplicate records) applied same commit sequence.
**M3 DONE** (`507dd66`): browse-by-date History panel — date-grouped, searchable, reuse
(pulls a past meal into the input), delete.
**M4 DONE** (`8022c8c`): per-component quantity presets (0.5x/1.5x/2x per item) + whole-meal
scaling (1.5x/2x), both distinct mechanics per the plan. Not yet browser-tested end-to-end
by a human — JS syntax verified, logic reviewed, `index.html` opened locally for a visual
check, but no automated/manual click-through confirmed yet.
**M5 DONE (absorbed into M3):** confirmed 2026-07-09 — M3's History panel already shipped
reuse (`reuseMeal()`, pulls a past meal into the input) and search (`history-search` input +
`_mealMatchesSearch`). No separate M5 commit was needed; STATE.md's M3 note above already
said this, re-verified before starting M6/M7 work.
**M6 DONE 2026-07-09 (operator gate, ratified):** operator explicitly RATIFIED (live
confirmation, commissioner session) the cross-device sync data-placement decision — see
`LOCKED.md` invariant 7. Closes AGENDA's `macrohub-locked-review-2026-07-09` blocker.
**M7 DONE 2026-07-09 (sync implementation, code-complete):** v1 GitHub-repo adapter built —
new private repo `echolightening/macrohub-sync-data` (separate from this deploy repo), Web
Crypto AES-GCM encryption default-ON (PBKDF2-derived key, self-describing salt/IV in the
synced blob), LWW merge by `updated_at` per `meal_id`, single-overwritten-JSON sync file
(no per-write commits). New "Sync (optional)" panel in `index.html` (repo/PAT/passphrase/
encrypt-toggle/sync-now). Crypto round-trip + merge logic verified in isolation (Node
`webcrypto`, same params); `node --check` passes on the full script.
**NOT YET DONE — needs operator action:** GitHub does not support fine-grained PAT creation
via API/CLI (web-UI-only). Operator must generate a PAT scoped to
`echolightening/macrohub-sync-data` only (Contents: Read/write) and paste it into the Sync
panel — instructions are inline in the panel. Until then, live GitHub round-trip and the
plan's multi-device (phone + laptop) verify step are untested. Full detail:
`~/local-ai/reviews/runlogs/macrohub-item28-m6-sync.md`.

**M8 DONE 2026-07-09 (nutrition-database bulk ingest, Track-2):** built per
`~/local-ai/specs/plans/item28-nutrition-research-brief.md` and its Fable verdict
`fable-bench:item28-nutrition-research-2026-07-09` (ADOPT WITH MODIFICATIONS, 4 required
mods — see LOCKED.md invariants 8/9/10). $0 model spend for bulk ingest (deterministic ETL
only). Real free bulk data, three sources, **82,204 total records** across 6 shards:

| Source | Shard file(s) | Records | License / provenance |
|---|---|---|---|
| USDA FoodData Central | `data/fooddb/usda/usda_sr_legacy.json` | 7,793 | public domain, `usda` |
| USDA FoodData Central | `data/fooddb/usda/usda_foundation.json` | 135 | public domain, `usda` |
| USDA FoodData Central | `data/fooddb/usda/usda_fndds.json` | 5,431 | public domain, `usda` |
| USDA FoodData Central | `data/fooddb/usda/usda_branded.json` | 19,882 (capped, see below) | public domain, `usda` |
| Open Food Facts | `data/fooddb/openfoodfacts/openfoodfacts.json` | 30,000 (capped) | **ODbL-1.0** — segregated shard, see LOCKED inv. 8 |
| MenuStat | `data/fooddb/menustat/menustat.json` | 18,963 | free/public, `label` |

All records match the M2 schema field-for-field: `fooddb_id`, `name`, `aliases[]`,
`per_100g` (using MacroHub's exact field names `cal/pro/carb/fat/satfat/fiber`), `serving`,
`source`, `provenance`, `confidence`. Build scripts: `scripts/ingest_usda.py`,
`scripts/ingest_off.py`, `scripts/ingest_menustat.py` — all re-runnable, all take a `--cap`
(or `--cap-branded`) flag for a larger future ingest (growth path, see below).

**Deviation from the brief, documented not silent:** MenuStat's cited source
(menustat.org) is a dead/repurposed domain as of this build — it now redirects to an
unrelated third-party site. The dataset's real current home is Harvard Dataverse,
`doi:10.7910/DVN/K4NYTR` ("MenuStat Annual Data", Cleveland 2022) — same NYC-DOH-produced
panel, free, no auth. Used the most recent year available there (2018). See
`scripts/ingest_menustat.py` module docstring for the full note.

**Deliberate caps for this seed run** (per M10 gate text below — not "largest practical
dataset"): USDA Branded capped at 20,000 (of ~2M+ available in the full bulk download,
already extracted locally at `data/fooddb/_raw/usda_extracted/branded_food.csv` — a
re-run with `--cap-branded 0` ingests all of it, no redesign needed). Open Food Facts
capped at 30,000 (of ~4.5M rows in the official "en" export already downloaded at
`data/fooddb/_raw/off_en.csv.gz`; the full multilingual Parquet dump, ~7.6GB, is a further
future option). MenuStat is NOT capped — all 18,963 rows with complete macro fields were
kept (52,181 rows dropped for being "customizable build" placeholders with a text range
instead of a number, e.g. `Calories_text: "340-1175"` — never estimated, per the
drop-don't-guess policy applied uniformly across all three sources).

Raw downloads (~4.4GB: USDA zip+extracted CSVs, OFF csv.gz) are kept at
`data/fooddb/_raw/` for cheap re-runs at a higher cap, but gitignored
(`data/fooddb/.gitignore`) — not committed.

**Long-tail candidate list generated (M8's bounded piece of the M9 gate, per Fable
verdict modification 1):** `scripts/generate_longtail_candidates.py` made exactly ONE
headless `claude -p --model haiku` call (no metered Anthropic API key exists in this
cluster's secrets — `~/local-ai/.{gemini,openai,xai,runpod}_key` only, no
`.anthropic_key` — so per the item-15 precedent this runs $0-marginal on the Max plan,
trivially satisfying the verdict's ≤$0.50 list-generation cap). Output: **158 candidate
dishes across 9 cuisine headings** at `data/fooddb/long-tail-candidates.md` — plain
markdown, names + composition notes only, zero macro numbers (by design — this is a
naming/scoping list, not an estimate).

**BLOCKED-ON-OPERATOR (new, blocks M9):** review `data/fooddb/long-tail-candidates.md`,
cross out anything not wanted, confirm the remainder before M9 (recipe-composition +
any long-tail fooddb-record spend) proceeds. Per LOCKED.md invariant 9 / Fable verdict
modification 1, **zero** long-tail composition/estimation spend has occurred past the
list-generation call above, and none may occur until this gate clears.
`scripts/run_longtail_tick.sh` (the eventual M9 launchd entry point) already checks for
an operator-created marker file (`data/fooddb/.longtail-candidates-approved`) and exits
without doing anything if it's absent — so even an accidental launchd install can't jump
this gate.

**launchd for M9: written, NOT installed** (same pattern as item 15 — the permission
classifier correctly blocks unattended recurring-job installation without live operator
authorization). `launchd/com.tq.localai.macrohub-longtail.plist` +
`scripts/run_longtail_tick.sh` exist and are self-terminating-by-design (unloads at
first of $10 total spend / 7 daily ticks / candidate-list drained, per LOCKED inv. 5 and
the brief's stopping-condition design) but `longtail_composition.py` itself — the actual
M9 recipe-composition logic — has NOT been built; that's explicitly out of scope for
this M8 dispatch and gated on the operator-pruning step above regardless.

**M10 close-out gate text (standing acceptance criterion, written now per Fable verdict
modification 4 — apply this when M9/M10 actually run):** M10 close-out must be judged
against *"a useful personal seed with a documented growth path"* — NOT the operator's
original aspirational "largest practical dataset" framing. The corpus built here
(82,204 free-tier records + a pending, operator-gated long-tail slice) is the correct
shape for that bar: broad authoritative coverage from three free bulk sources, a bounded
Haiku-assisted long-tail extension, and a documented, re-runnable path to ingest more of
any source later (raise/remove the `--cap`/`--cap-branded` flags) without redesigning
the pipeline. Do not fail M10 for not being exhaustive — that was never the target.

Full build log: `~/local-ai/reviews/runlogs/macrohub-item28-m8-nutrition.md`.

## Next steps (item 28 plan)
M1 → M2 → M3 → M4 → M5 (done, see above) → M6 (done) → M7 (code-complete, pending operator
PAT for live verify) → **M8 DONE** (bulk ingest, see above) → **M9 BLOCKED ON OPERATOR**
(review/prune `data/fooddb/long-tail-candidates.md`, create
`data/fooddb/.longtail-candidates-approved` to clear the gate, then build
`scripts/longtail_composition.py` and install the launchd job) → M10 close-out (judge
against the "useful personal seed with documented growth path" gate text above, not
"largest practical dataset"). Full milestone table + Fable checkpoints: the plan file
above.

## Stored-meal schema (planned, not yet built — item 28 plan §1 Q3)
Item fields extend today's `{name, cal, pro, carb, fat, satfat, fiber}` with optional
`fooddb_id`, `provenance` (`ai-estimated | usda | label | user-edited`), `confidence`,
`image_refs[]` (empty for now); top-level `schema_version`, `meal_id`, `logged_at`.
