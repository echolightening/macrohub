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

## Next steps (item 28 plan)
M1 (this enrollment) → M2 meal data model + storage (schema below) → M3 persist +
browse-by-date → M4 per-component/whole-meal editing → M5 reuse/re-log + search → M6
**operator gate**: ratify the cross-device sync architecture (local-first IndexedDB +
pluggable adapter, v1 recommendation = private GitHub-repo adapter, separate from the
Pages deploy repo per the plan's critique-fold-in — see plan §3b) → M7 sync implementation
→ M8 Track-2 (nutrition-research job) design + dry run → M9 supervised pilot → M10 week
run + close-out. Full milestone table + Fable checkpoints: the plan file above.

## Stored-meal schema (planned, not yet built — item 28 plan §1 Q3)
Item fields extend today's `{name, cal, pro, carb, fat, satfat, fiber}` with optional
`fooddb_id`, `provenance` (`ai-estimated | usda | label | user-edited`), `confidence`,
`image_refs[]` (empty for now); top-level `schema_version`, `meal_id`, `logged_at`.
