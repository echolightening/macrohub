# LOCKED — settled decisions (do not silently change)

Read next to STATE.md, every session. These are things a runner may not change without a
tripped gate + Fable review (see `~/local-ai/ORCHESTRATION.md` → "Arbiter Gates"). Any plan
that touches one of these, or any diff that touches its backing files, trips Gate A/B —
handle via waiver or escalation, never silently.

## Invariants

1. **API keys never leave the device except direct calls to each provider's own endpoint.**
   Keys live in localStorage only, no backend relay. (Source: `README.md` §Setup/§Architecture,
   "Keys are stored in localStorage on your device only. Never transmitted anywhere except
   directly to each AI's API endpoint.")
2. **Single-file, no-build, no-framework PWA** (`index.html`). (Source: `README.md` §1,
   "No dependencies except EmailJS and pdf.js... No backend, no build step, no framework.")
   Kept as-is for Track-1 feature work (item 28 plan); any change to this posture (e.g. adding
   a build step) is a PROPOSED-worthy decision, not a silent one.
3. **Meal data is local-first (IndexedDB), sync is an adapter, never a dependency.** The app
   must fully function offline. (Source: item 28 Fable-authored plan §1 Q1,
   `~/local-ai/specs/plans/item28-macrohub-plan.md`, ADOPT WITH MODIFICATIONS.)
4. **Cross-device sync data-placement is PROPOSED, not yet ratified** — see PROPOSED section
   below. No sync implementation (plan milestone M7) begins before this is ratified at
   milestone M6 (an explicit operator gate).
5. **Track-2 (nutrition-research job) is a standing, budget-capped, launchd-scheduled job** —
   per-tick ≤30min/≤300 items/≤$1.50 Haiku spend; total-run ≤$10 or 7 daily ticks, whichever
   first, auto-halting. (Source: item 28 plan §2, binding Track-2 caps — mirrors item 15's
   YouTube-pipeline precedent.) Do not run Track-2 unattended past these caps without a fresh
   Fable review.
6. **Provenance labeling is mandatory on food-DB records** (`usda | label | ai-estimated`) —
   AI-estimated records must be visually distinguishable in-app, never silently presented as
   authoritative. (Source: item 28 plan §2 condition 7.)

## Files
<none locked yet — Track-1 storage/schema code doesn't exist until milestone M2. First
candidate once M2 lands: the meal data-model/schema module, given schema_version is the
project's two-way door for future photo-recognition compatibility.>

## Behaviors
<none locked yet — no persistence behavior exists today (see STATE.md's "critical gap").
First candidate once M3 lands: "logged meals are never silently lost/cleared" (the exact
gap this build closes — `newMeal()` currently clears all in-memory state).>

## PROPOSED

1. **Cross-device sync architecture and data-placement.** The Fable-authored plan
   recommends: local-first IndexedDB + a pluggable sync-adapter interface, v1 adapter = a
   **private GitHub repo, SEPARATE from the GitHub-Pages deploy repo**, PAT scoped to the
   data repo only, client-side payload encryption default-ON for health-adjacent data (this
   last point strengthened by the plan's Opus critique pass, §3b — the original "PAT is a
   device-local secret exactly like the four AI keys" framing was found unsafe: a
   write-scoped repo PAT sitting in browser localStorage next to two third-party CDN script
   includes is a real supply-chain/XSS exposure, and a same-repo data+deploy setup would
   both self-expose the deployed app and make personal dietary data publicly readable via
   Pages). **This is a real data-placement change (meal data will leave the device to a
   private GitHub repo) and requires the operator's explicit ratification at plan milestone
   M6 before any implementer builds M7.** Not yet resolved — surfaced to AGENDA.md
   (`macrohub-locked-review-2026-07-09`) per this skill's non-deferral rule.

**Resolution status: operator unavailable this session — 1 PROPOSED item written into
`AGENDA.md`'s Dispatchable-now section as `macrohub-locked-review-2026-07-09`, per this
skill's non-deferral rule. Not resolved here.**
