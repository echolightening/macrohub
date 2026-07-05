# MacroHub — Project Briefing

_Versioned in-repo as of the `macrohub-modelpass-v1` run (2026-07-04). Keep this file in
sync with `index.html` going forward — update it in the same commit as any feature change._

## What this is
A single-file PWA (`index.html`) the operator uses for daily macro tracking. Paste a meal
description and/or attach photos or PDFs, hit one button, and it calls Claude, GPT-5.5,
Gemini, and Grok simultaneously — returning itemized macro tables from each. It calculates
statistics across all results, supports multi-turn follow-up corrections, generates a
Nourish-ready diary entry, and emails a full session log.

Hosted on GitHub Pages at `echolightening.github.io/macrohub`. Installed on iPhone home
screen via Safari "Add to Home Screen."

**Local clone:** `~/Projects/macrohub` — this is the permanent local home for the repo
going forward (not a scratch clone). Commits are made locally and pushed after review;
GitHub Pages auto-deploys from `main` within ~60 seconds of a push.

---

## Stack
- Single HTML file, no framework, no build step
- Vanilla JS, system fonts (ui-monospace / ui-serif)
- Dark theme, mobile-first, iOS safe area aware
- CDN dependencies (both loaded as plain `<script src>` tags in `<head>`, no bundler):
  - EmailJS — for the email-log feature
  - pdf.js (`pdfjs-dist@3.11.174`) — for PDF ingestion; pinned to the last version that
    ships the classic global-`pdfjsLib` UMD build (4.x+ went ESM-only, which would need
    `type="module"` and breaks the plain-script-tag pattern this app uses everywhere else)
- API keys and settings stored in localStorage, never sent anywhere except directly to
  each AI's API

---

## APIs called

| ID | Label | Endpoint | Pipeline (two-stage mode) |
|---|---|---|---|
| `claude` | Claude | `api.anthropic.com/v1/messages` | EXTRACT `claude-sonnet-5` → JUDGE `claude-fable-5` (judge falls back server-side to `claude-opus-4-8` on a safety-classifier refusal) |
| `openai` | GPT-5.5 | `api.openai.com/v1/chat/completions` | EXTRACT `gpt-4o` → JUDGE `gpt-5.5` |
| `gemini` | Gemini | `generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent` | `gemini-3.5-flash` (single call) |
| `grok` | Grok | `api.x.ai/v1/chat/completions` | `grok-4.3` (single call) |

Nourish summary generator: `claude-sonnet-5` direct (formatting, not judgment — no
judge, no fallback).

Model refresh sources (verified 2026-07-04): OpenAI model page
`developers.openai.com/api/docs/models/gpt-5.5` (model ID, vision support, 128K max
output) + community/GitHub reports confirming the GPT-5.x family rejects `max_tokens`
with a 400 and requires `max_completion_tokens`; Google's
`ai.google.dev/gemini-api/docs/generate-content/whats-new-gemini-3.5` (model path,
`v1beta` still current, `generateContent` request shape unchanged).

### The two-stage EXTRACT → JUDGE pipeline (v1d) and why

**Economics (the reason this exists — Fable billing is real, $9 posted in week 1):**
photos are the expensive part of a vision request, and they were being re-sent to
frontier-priced models on every turn. In two-stage mode, **photos bill only to the
cheap extractors** (Sonnet 5 / gpt-4o); the frontier models (Fable 5 / GPT-5.5) are
text-only judges that see ≤~2k tokens per meal (meal description + draft JSON + prose
note). Per-meal Claude-lane cost drops roughly 3–5×, and frontier cost **stops scaling
with photo count entirely** — a 20-photo meal costs the same at the judge stage as a
text-only one.

**Shape:** stage-1 EXTRACT does everything the old single call did — vision, full
prompts, per-AI conversation history (histories[] holds stage-1 turns only). Stage-2
JUDGE is stateless per meal-state: input = meal description + stage-1's final merged
JSON (+ stage-1's prose note on follow-ups), **never images, never history**; system
prompt = verify plausibility/portions/math, correct if needed, return the same JSON
shape only. The card displays the judged table; `results[id]`, 5m/5m+, email, and
Nourish all consume the judged numbers. Both stages are stored in `rawResponses`
tagged `stage: 'extract'` / `'judge'`, so the raw ↕ toggle shows the full pipeline.
Batched photo runs are judged ONCE on the final merged table, not per batch.

**Judge failure is graceful:** if stage-2 fails for any reason (network, refusal,
malformed JSON), the card shows stage-1's result with a small amber "unjudged" marker
instead of erroring — a degraded answer beats no answer for a daily logging tool.

**The door:** `PIPELINE_MODE` const at the top of the script. `'two-stage'` (current)
or `'direct'`, which reverts both premium lanes to their pre-v1d single-call behavior
(Fable 5 + Opus fallback / GPT-5.5) — both code paths are kept reachable, so the
revert is a one-word edit. Model labels derive from the same door via `AI_CONFIGS`
(`sonnet-5→fable-5`, `gpt-4o→gpt-5.5` in two-stage; `fable-5`, `gpt-5.5` in direct).

### Claude judge — headers and body (stage-2 only)

```
anthropic-dangerous-direct-browser-access: true
anthropic-beta: server-side-fallback-2026-06-01   ← judge + direct door only, NOT stage-1
anthropic-version: 2023-06-01
```
```json
{
  "model": "claude-fable-5",
  "max_tokens": 1200,
  "fallbacks": [{"model": "claude-opus-4-8"}],
  "output_config": {"effort": "low"}
}
```
**The fallback pattern:** Fable 5's safety classifiers can decline a request
(`stop_reason: "refusal"`, HTTP 200). With the `fallbacks` param + beta header, the API
transparently re-serves a declined request on Opus 4.8 inside the same call — no client
retry logic needed. Response content blocks may include non-`text` types (`thinking` with
empty text, `fallback` markers), so text extraction filters `content` for
`block.type === 'text'` rather than assuming `content[0]` is text — this filtering also
applies to the Sonnet 5 extractor and Nourish calls, since Sonnet 5 runs adaptive
thinking by default and emits thinking blocks in `content`. If the whole fallback chain
still ends in refusal, the judge throws → the lane falls back to the unjudged stage-1
result (see above); in `'direct'` mode the card shows "Claude declined this request".

### GPT-5.5 — token parameter and reasoning budget

GPT-5.5 is in the reasoning-model family and rejects the legacy `max_tokens` parameter
with a 400 ("Unsupported parameter"); use `max_completion_tokens` instead. In two-stage
mode GPT-5.5 is the text-only judge; the gpt-4o extractor is a classic non-reasoning
model and keeps plain `max_tokens: 1500`.

**Reasoning-budget gotcha (bit us in v1):** hidden reasoning tokens count *inside*
`max_completion_tokens`. With a small cap (1500), the model spends the whole budget on
reasoning and returns `finish_reason: "length"` with an **empty content string** — which
surfaced as "no JSON found in response". The fix (v1b): `max_completion_tokens: 16000`
(only tokens actually used are billed) plus `reasoning_effort: 'low'` (this is table
extraction, not a reasoning task; default is `medium`). `'none'` is the literal minimum
for GPT-5.5 but had a documented bug when combined with `max_completion_tokens` on this
model family, so `'low'` is the lowest clean setting. `callOpenAI()` also now throws a
descriptive error (including `finish_reason`) if `message.content` comes back
empty/whitespace, instead of letting `parseResponse()` mislabel it.

### Gemini — endpoint

Same `v1beta` API version and `generateContent` request shape as before (`contents`,
`systemInstruction`, `generationConfig`, `inline_data` for images) — only the model path
segment changed. `toGeminiContents()` semantics are untouched.

All 4 called simultaneously via `Promise.allSettled`. Results render as each completes.

---

## Prompts

**Initial (text only):** JSON-only response, itemized macro breakdown
**Initial (image or PDF):** Vision prompt, JSON-only response
**Initial (both):** Vision + text description, JSON-only response
**Follow-up:** Two-part response — plain-English explanation of changes (2-4 sentences) + full updated JSON

JSON shape:
```json
{
  "items": [{"name":"...","cal":0,"pro":0,"carb":0,"fat":0,"satfat":0,"fiber":0}],
  "total": {"cal":0,"pro":0,"carb":0,"fat":0,"satfat":0,"fiber":0}
}
```

---

## Macro fields
`cal` (calories), `pro` (protein g), `carb` (carbs g), `fat` (total fat g), `satfat` (sat fat g), `fiber` (fiber g)

---

## Features

### Input
- Text field (optional) + photo/PDF grid (optional) — at least one required
- Up to 20 photo-equivalent items, auto-resized to 1500px max dimension client-side
- Photos auto-batched into chunks of 10 per API call (app-defined batch size, not a
  hard provider limit)
- Follow-up input: text + photos/PDFs, same optional/required logic

### PDF ingestion (uniform path — no per-API branches)
- Both photo inputs (initial + follow-up) accept `application/pdf` alongside images
- Each PDF page renders client-side via pdf.js to a `<canvas>`, then to a JPEG at the
  app's existing 1500px max-dimension cap — producing the exact same `{b64, mime, thumb}`
  shape as a resized photo, plus a `label` field (e.g. `"PDF p.2"`) shown as a small
  caption on the thumbnail
- Capped at `MAX_PDF_PAGES = 10` pages per PDF; a toast notes it when a PDF is truncated
- Once expanded to photo objects, PDF pages flow through the *exact same* pipeline as
  camera photos — batching, resizing, and all 4 AI calls are unchanged and PDF-unaware

### Results
- 2×2 AI card grid — mini macro table per AI, spinner while loading, error state
- Color coding: Claude `#d4956a`, GPT-5.5 `#74c99a`, Gemini `#7eb8f7`, Grok `#c4b5f7`
- Follow-up explanation shown in card above numbers after corrections
- "raw ↕" toggle on each full table card — shows all turns with JSON + prose per turn
- **Per-AI "⧉ copy" button** on each mini-card (appears once that AI has a result) AND
  on each full-table card header (always present there — the table only renders once a
  result exists): both call the same `copyAiResult(id)` formatter, copying that AI's
  latest itemized breakdown + totals as plain paste-friendly text — for when one AI
  nails a meal but the 5m+ conservative ceiling is off. Independent of the
  "🥗 copy for Nourish" button, which stays a session-wide consensus summary.
- **Muted model-ID labels** (`.ai-model`, tiny/dim monospace) on every mini-card and
  full-table header, e.g. "fable-5" / "gpt-5.5" / "gemini-3.5-flash" / "grok-4.3".
  Single source of truth: the `model` field on `AI_CONFIGS` — the mini-card spans are
  populated from it at load, and `renderFull()` reads it directly, so a future model
  swap only needs the `AI_CONFIGS` string updated (plus the actual call site).

### 5m stats
- **5m — calories:** Min / Mean / Median / Mode / Max across all AI calorie totals
- **5m+ — conservative ceiling:** max for cal/carb/fat/satfat, min for pro/fiber
- Each 5m+ value shows contributing AI name in that AI's color
- Source attribution pills: each AI's label + calorie total in AI color
- Updates live after every AI response (initial or follow-up)

### Multi-turn conversation
- Separate conversation history per AI stored in memory (`histories` object)
- All histories cleared on "↺ new meal"
- Follow-ups use image vision API calls when photos/PDF pages are attached
- Photo batching logic same as initial — sequential batches, JSON merged client-side

### Nourish summary
- "🥗 copy for Nourish" button appears after first estimates complete
- Calls Claude Sonnet 5 directly (formatting, not judgment — no judge stage, no
  fallback param) with all session data — consensus items (averaged per item across
  AIs) + 5m+ totals
- Returns plain-text food diary entry
- One-tap copy button + ↺ regenerate button
- Uses 5m+ values (not mean) for the totals line

### Email logging
- EmailJS (emailjs.com) — public key + service ID + template ID stored in settings
- Template variables: `to_email`, `subject`, `message`
- Default recipient: `echolightening@gmail.com` — configurable in settings, persists to localStorage
- Fires automatically on "↺ new meal" (if results exist)
- Also: "✉ send log" manual button in header + below follow-up input
- Email contains: date/time, meal description, top items by calorie, per-AI totals, 5m stats, 5m+ ceiling, full AI outputs (JSON per turn + prose)

### Settings export/import — the PRIMARY way to set up a new device
- "⇪ export settings" copies **all** `mk_*` localStorage keys (all 4 API keys + all 3
  EmailJS values + the recipient email) as a JSON blob to the clipboard
- "⇩ import settings" opens an inline textarea; pasting + "apply" validates the JSON and
  writes only the keys present in the blob
- **Import is a MERGE, not a replace** — only non-empty `mk_*` keys present in the pasted
  blob are written; every other existing localStorage setting is left untouched. This is
  what makes it safe to import a machine-only blob and a phone-only blob in either
  order and end up with the union of both, rather than one clobbering the other
- This export/import flow — not `tools/desktop-setup.sh` below — is the documented,
  primary way to move settings to a new device or browser

### tools/desktop-setup.sh — a best-effort convenience, not the primary path
A small local script for the operator's own machines: tries the 1Password CLI (`op`,
editable `OP_*_ITEM`/`OP_FIELD` variables at the top of the script) for the Gemini/xAI/
OpenAI keys, falls back to `~/local-ai/*.key` if `op` is missing or a lookup misses,
assembles the same import-blob JSON shape, and copies it to the clipboard with
`pbcopy`. There is no Anthropic key source on this machine (Claude Code auth is OAuth,
not an API key) — pass it as an optional argument, or add it afterward via the phone
export or `platform.anthropic.com`. Contains no secrets itself; not polished, not
meant to be robust — if it can't find a key, use the phone export/import path instead.

---

## State variables
```javascript
let photos = [];          // [{b64, mime, thumb, label?}] — initial meal photos/PDF pages
let followupPhotos = [];  // [{b64, mime, thumb, label?}] — cleared after each send
let results = {};         // {claude: {items, total}, ...} — latest per AI
let rawResponses = {};    // {claude: [{turn, data, prose}], ...} — full history
let histories = {claude:[], openai:[], gemini:[], grok:[]};  // conversation per AI
```
`label` is new (PDF ingestion): set to e.g. `"PDF p.2"` on photo objects that came from
a PDF page, `undefined` for camera/library photos. Everything else about the shape is
unchanged — this is why the PDF pipeline needed no changes to batching, resizing, or
the 4 AI call sites.

---

## Settings (localStorage keys)
| Key | Description | Default |
|---|---|---|
| `mk_claude` | Anthropic API key | — |
| `mk_openai` | OpenAI API key | — |
| `mk_gemini` | Google AI API key | — |
| `mk_grok` | xAI API key | — |
| `mk_ejs-pub` | EmailJS public key | — |
| `mk_ejs-svc` | EmailJS service ID | — |
| `mk_ejs-tpl` | EmailJS template ID | — |
| `mk_to-email` | Email recipient | `echolightening@gmail.com` |

These are exactly the keys covered by settings export/import — `ALL_KEYS` in the JS is
the single source of truth for both.

---

## Deployment
- Hosted: GitHub Pages (`echolightening.github.io/macrohub`)
- To update: commit to the local clone at `~/Projects/macrohub` → push to `main` → live
  in ~60 seconds
- iPhone install: open URL in Safari → Share → Add to Home Screen → "MacroHub"

---

## Instructions for Claude when working on this project
- Always read this briefing and `index.html` before making any changes
- The file is now ~1300 lines — use targeted `str_replace`/`Edit`-style edits, not full
  rewrites, unless major restructuring is needed
- When adding features, maintain the existing state architecture (photos, followupPhotos,
  results, rawResponses, histories) — the PDF-ingestion feature is the reference example
  of extending it (same shape + one optional `label` field) rather than branching it
- CSS variables work in stylesheets but NOT in inline JS-generated styles — use hex
  values for colors in JS (e.g. the PDF-label thumbnail badge uses `#f0ede8`, not
  `var(--text)`)
- All API keys use `getKey(id)` which checks input field first, then localStorage
- EmailJS send is always silent (no-op) if keys not configured
- `parseResponse(text)` returns `{data, prose}` — use this not `parseJSON` for follow-up responses
- `mergeResults(a, b)` combines two JSON results by concatenating items and summing totals
- Gemini conversation history uses a different format (parts array) — see `toGeminiContents()`
- Anthropic call sites: `callClaude()` two-stage branch = Sonnet 5 extractor;
  `judgeClaude()` = Fable 5 + Opus 4.8 fallback (the only routine call that uses the
  fallback beta); `callClaude()` direct branch = Fable 5 + fallback (door revert path);
  Nourish = Sonnet 5 plain. All four filter `content` for `type === 'text'` — keep
  that hardening in sync if any of them changes
- `PIPELINE_MODE` is the two-stage/direct door — flip to `'direct'` to revert both
  premium lanes to single frontier calls; don't delete the direct branches, they ARE
  the revert path
- This repo is **public** — do not add operator-personal context (names, habits,
  routines) to this briefing or to code comments; keep it technical/architectural only
