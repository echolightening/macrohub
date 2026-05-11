# MacroHub

A single-file PWA for daily macro estimation. Paste a meal description and/or upload photos — MacroHub calls Claude, GPT-4o, Gemini, and Grok simultaneously, shows itemized macro tables from each, calculates statistics across all results, and emails a full session log before clearing.

Installable on iPhone via Safari → Add to Home Screen. No backend, no build step, no framework.

---

## Features

### Input
- **Text** — describe your meal in natural language
- **Photos** — up to 20 images, auto-resized to 1500px and auto-batched into chunks of 10 per API call
- **Both together** — AIs cross-reference photo and text for better accuracy
- Either text or photo required; both optional together

### AI estimation
- Calls Claude, GPT-4o, Gemini 2.5 Flash Lite, and Grok 4.3 in parallel
- Each returns an itemized JSON breakdown: calories, protein, carbs, fat, saturated fat, fiber
- Results render live as each AI responds — no waiting for all four

### Statistics
- **5m** — Min / Mean / Median / Mode / Max across all AI calorie totals
- **5m+** — Conservative ceiling: max for cal/carb/fat/sat fat, min for protein/fiber
- Each 5m+ value labeled with the contributing AI in its color (Claude orange, GPT-4o green, Gemini blue, Grok purple)
- Source attribution pills showing each AI's calorie total

### Multi-turn conversation
- Full conversation history maintained per AI across the session
- **Follow-up input** — text and/or photos; at least one required
- Follow-up responses include plain-English explanation of what changed and why, plus updated numbers
- 5m and 5m+ update automatically after every follow-up

### Raw output
- Each full table card has a "raw ↕" toggle showing the complete JSON response per turn, with prose explanations where present

### Nourish summary
- "🥗 copy for Nourish" button synthesizes the entire session via Claude
- Averages item macros across all AIs; uses 5m+ values for totals
- Incorporates all follow-up corrections
- Plain-text output ready to paste into Nourish food diary
- One-tap copy button; regenerate button for a fresh synthesis

### Email logging
- "✉ send log" button available after estimates complete (in header and below follow-up input)
- Also fires automatically when "↺ new meal" is tapped
- Email includes: date/time, meal description, top items by calorie, per-AI totals, 5m stats, 5m+ ceiling, full AI outputs with JSON per turn
- Recipient address configurable in settings (defaults to echolightening@gmail.com, persists to localStorage)
- Powered by EmailJS (free tier: 200 emails/month)

---

## Setup

### 1. API Keys

| Service | Where to get it | Starts with |
|---|---|---|
| Anthropic (Claude) | platform.anthropic.com → API Keys | `sk-ant-` |
| OpenAI (GPT-4o) | platform.openai.com → API Keys | `sk-` |
| Google (Gemini) | aistudio.google.com → Get API Key | `AIza` |
| xAI (Grok) | console.x.ai → API Keys | `xai-` |

All four are pay-as-you-go. At daily meal logging volume (~1 query/day), expect under $3/month total across all four. Gemini has a free tier.

### 2. EmailJS (for email logging)

1. Sign up at emailjs.com
2. Add Gmail as a service → connect your Gmail account → copy **Service ID**
3. Create a template with `{{to_email}}` / `{{subject}}` / `{{message}}` → copy **Template ID**
4. Account → General → copy **Public Key**

### 3. Deploy

Upload `index.html` to any static host. Recommended: GitHub Pages (free).

1. Create a GitHub repo
2. Upload `index.html` — rename to `index.html` if needed
3. Settings → Pages → Branch: main, folder: / (root) → Save
4. Your URL: `yourusername.github.io/reponame`

### 4. Install on iPhone

1. Open the URL in **Safari**
2. Share button → **Add to Home Screen**
3. Name it "MacroHub" → Add
4. Opens full-screen like a native app

### 5. Enter keys in app

Tap "configure keys ↓" → paste all API keys and EmailJS credentials → "save keys locally"

Keys are stored in localStorage on your device only. Never transmitted anywhere except directly to each AI's API endpoint.

---

## Models used

| AI | Model | Notes |
|---|---|---|
| Claude | `claude-opus-4-5-20251101` | Vision + text; requires `anthropic-dangerous-direct-browser-access: true` header |
| GPT-4o | `gpt-4o` | Vision + text |
| Gemini | `gemini-2.5-flash-lite` | Vision + text; lower capacity pressure than 2.5-flash |
| Grok | `grok-4.3` | Vision + text natively (no separate vision model) |

---

## Architecture

Single HTML file. No dependencies except EmailJS CDN (loaded via script tag). All state is in-memory per session. API keys in localStorage. No server, no backend, no data leaves the device except direct API calls to each AI provider and EmailJS.

```
index.html
├── <style>          — all CSS, dark theme, iOS safe areas
├── <body>           — settings panel, meal input, photo grid,
│                      AI cards, follow-up, 5m/5m+, full tables,
│                      Nourish summary section
└── <script>
    ├── State        — photos, followupPhotos, results, rawResponses, histories
    ├── Keys         — localStorage get/set with defaults
    ├── Image        — resizeImage (canvas), handleImages, renderPhotoGrid
    ├── API          — callClaude, callOpenAI, callGemini, callGrok
    ├── runAI        — per-AI orchestrator: batching, history, parsing, merging
    ├── runAll       — parallel Promise.allSettled across all AIs
    ├── sendFollowup — handles text+photo followups, passes to runAI
    ├── updateFiveM  — 5m stats + 5m+ with source attribution
    ├── generateNourish — Claude synthesis call → plain-text diary entry
    ├── buildEmailSummary — formats full session for email
    ├── sendMealEmail — EmailJS send
    └── newMeal      — sends email, clears all state
```

---

## Photo limits

| AI | Per-request limit | Notes |
|---|---|---|
| Claude | 20 images | Max 1500px per image (enforced by client-side resize) |
| GPT-4o | 10 images | Binding constraint — batch size set to 10 |
| Gemini | 3,600 images | No practical limit |
| Grok | ~20 images | Token-budget constrained in practice |

App enforces max 20 photos total, batched into chunks of 10 per API call. Second batch instructs AI to add items to the first estimate.

---

## Macro fields

| Field | Key | Notes |
|---|---|---|
| Calories | `cal` | kcal |
| Protein | `pro` | grams |
| Carbohydrates | `carb` | grams |
| Total fat | `fat` | grams |
| Saturated fat | `satfat` | grams |
| Fiber | `fiber` | grams |

---

## 5m+ logic

Conservative ceiling for logging on the safe side:

- **Max** across AIs: calories, carbs, fat, saturated fat
- **Min** across AIs: protein, fiber

Used as the totals line in the Nourish summary output.
