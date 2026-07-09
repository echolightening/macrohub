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
4. **Cross-device sync data-placement — RATIFIED 2026-07-09.** See invariant 7 below for the
   confirmed shape. (Superseded: this line previously read "PROPOSED, not yet ratified";
   resolution recorded in full at invariant 7 and in the former PROPOSED section, kept below
   for audit trail.)
5. **Track-2 (nutrition-research job) is a standing, budget-capped, launchd-scheduled job** —
   per-tick ≤30min/≤300 items/≤$1.50 Haiku spend; total-run ≤$10 or 7 daily ticks, whichever
   first, auto-halting. (Source: item 28 plan §2, binding Track-2 caps — mirrors item 15's
   YouTube-pipeline precedent.) Do not run Track-2 unattended past these caps without a fresh
   Fable review.
6. **Provenance labeling is mandatory on food-DB records** (`usda | label | ai-estimated`) —
   AI-estimated records must be visually distinguishable in-app, never silently presented as
   authoritative. (Source: item 28 plan §2 condition 7.)
7. **Cross-device sync data-placement (RATIFIED 2026-07-09).** Local-first IndexedDB remains
   the source of truth; sync is a pluggable adapter, never a dependency (invariant 3). The v1
   adapter is a **private GitHub repo, SEPARATE from the GitHub-Pages deploy repo**
   (`echolightening/macrohub-sync-data`, created 2026-07-09), reachable only via a **PAT
   scoped to the data repo only** (fine-grained, no access to the deploy repo), and **payload
   encryption is default-ON** (client-side AES-GCM, key derived from an operator-supplied
   passphrase via PBKDF2, salt travels with the ciphertext so any device holding the
   passphrase can decrypt) for health-adjacent data. **Confirmed live by the operator in a
   commissioner session on 2026-07-09** — this is the explicit ratification required at the
   M6 operator-gate in `~/local-ai/specs/plans/item28-macrohub-plan.md`'s milestone table;
   closes AGENDA's `macrohub-locked-review-2026-07-09` blocker and item 28's plan milestone
   M6. The substance is unchanged from the PROPOSED item below (kept for audit trail) — the
   Opus critique's three binding additions (separate repo; data-scoped PAT; default-ON
   encryption) are adopted as written, no amendment. Known accepted limitation, stated per
   the critique rather than hidden: last-write-wins per `meal_id` can silently drop one side
   of a two-device concurrent offline edit — acceptable at personal scale. Sync data is
   stored as a single overwritten JSON blob per the critique's anti-repo-bloat guidance, not
   one commit per write. Implementation is milestone M7 (see STATE.md for build status).

## Files
<none locked yet — Track-1 storage/schema code doesn't exist until milestone M2. First
candidate once M2 lands: the meal data-model/schema module, given schema_version is the
project's two-way door for future photo-recognition compatibility.>

## Behaviors
<none locked yet — no persistence behavior exists today (see STATE.md's "critical gap").
First candidate once M3 lands: "logged meals are never silently lost/cleared" (the exact
gap this build closes — `newMeal()` currently clears all in-memory state).>

## PROPOSED

<none currently open. Former item 1 (cross-device sync architecture and data-placement) was
RATIFIED 2026-07-09 — moved to Invariants item 7 above. Original text kept below for audit
trail only; do not re-read as an open decision.>

1. ~~**Cross-device sync architecture and data-placement.** The Fable-authored plan
   recommends: local-first IndexedDB + a pluggable sync-adapter interface, v1 adapter = a
   **private GitHub repo, SEPARATE from the GitHub-Pages deploy repo**, PAT scoped to the
   data repo only, client-side payload encryption default-ON for health-adjacent data (this
   last point strengthened by the plan's Opus critique pass, §3b — the original "PAT is a
   device-local secret exactly like the four AI keys" framing was found unsafe: a
   write-scoped repo PAT sitting in browser localStorage next to two third-party CDN script
   includes is a real supply-chain/XSS exposure, and a same-repo data+deploy setup would
   both self-expose the deployed app and make personal dietary data publicly readable via
   Pages). This is a real data-placement change (meal data will leave the device to a
   private GitHub repo) and requires the operator's explicit ratification at plan milestone
   M6 before any implementer builds M7.**~~ **RATIFIED 2026-07-09 — see Invariants item 7.**

**Resolution status: RESOLVED 2026-07-09.** Operator ratified live in a commissioner session
(explicit confirmation, per the M6 operator-gate). Closes AGENDA's
`macrohub-locked-review-2026-07-09` blocker. The item that was written into AGENDA.md's
Dispatchable-now section under that name is now closeable by the dispatching commissioner.
