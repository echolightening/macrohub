#!/usr/bin/env bash
# MacroHub desktop key-seeding -- a NICE-TO-HAVE convenience, not the primary path.
# The primary way to set up a new device is still: MacroHub Settings -> export
# (existing device) -> Settings -> import (this one). See MacroHub-Project-Briefing.md.
#
# Best-effort shortcut for Gemini/xAI/OpenAI only -- no Anthropic source exists on
# this machine (Claude Code uses OAuth). Tries 1Password first, falls back to
# ~/local-ai/*.key. Contains no secrets itself.
#
# Usage: ./tools/desktop-setup.sh [anthropic_key]

set -euo pipefail

# Edit these if `op item get` can't find your items:
OP_GEMINI_ITEM="Gemini API"; OP_XAI_ITEM="xAI"; OP_OPENAI_ITEM="OpenAI"; OP_FIELD="credential"

ANTHROPIC_KEY="${1:-}"
GEMINI_KEY="" XAI_KEY="" OPENAI_KEY=""

if command -v op >/dev/null 2>&1; then
  GEMINI_KEY=$(op item get "$OP_GEMINI_ITEM" --fields "label=$OP_FIELD" --reveal 2>/dev/null || true)
  XAI_KEY=$(op item get "$OP_XAI_ITEM" --fields "label=$OP_FIELD" --reveal 2>/dev/null || true)
  OPENAI_KEY=$(op item get "$OP_OPENAI_ITEM" --fields "label=$OP_FIELD" --reveal 2>/dev/null || true)
fi
[ -z "$GEMINI_KEY" ] && [ -f ~/local-ai/.gemini_key ] && GEMINI_KEY=$(cat ~/local-ai/.gemini_key)
[ -z "$XAI_KEY" ]    && [ -f ~/local-ai/.xai_key ]    && XAI_KEY=$(cat ~/local-ai/.xai_key)
[ -z "$OPENAI_KEY" ] && [ -f ~/local-ai/.openai_key ] && OPENAI_KEY=$(cat ~/local-ai/.openai_key)

if [ -z "$GEMINI_KEY$XAI_KEY$OPENAI_KEY$ANTHROPIC_KEY" ]; then
  echo "No keys found via 1Password ($OP_GEMINI_ITEM/$OP_XAI_ITEM/$OP_OPENAI_ITEM) or ~/local-ai/*.key." >&2
  echo "Edit the OP_*_ITEM variables above, or just use the phone export/import path instead." >&2
  exit 1
fi

BLOB=$(GEMINI_KEY="$GEMINI_KEY" XAI_KEY="$XAI_KEY" OPENAI_KEY="$OPENAI_KEY" ANTHROPIC_KEY="$ANTHROPIC_KEY" python3 -c '
import json, os
b = {}
if os.environ.get("GEMINI_KEY"):    b["mk_gemini"] = os.environ["GEMINI_KEY"]
if os.environ.get("XAI_KEY"):       b["mk_grok"] = os.environ["XAI_KEY"]
if os.environ.get("OPENAI_KEY"):    b["mk_openai"] = os.environ["OPENAI_KEY"]
if os.environ.get("ANTHROPIC_KEY"): b["mk_claude"] = os.environ["ANTHROPIC_KEY"]
print(json.dumps(b))
')
printf '%s' "$BLOB" | pbcopy
echo "Settings blob copied -- open MacroHub, Settings -> import, paste."
echo "Add any missing keys (Claude, EmailJS) via the phone export or platform.anthropic.com."
