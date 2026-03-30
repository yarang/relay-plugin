#!/usr/bin/env bash
# relay-plugin installer — project-level setup (no plugin install required)
# Usage: bash <(curl -fsSL https://raw.githubusercontent.com/yarang/relay-plugin/main/install.sh)

set -euo pipefail

REPO="https://github.com/yarang/relay-plugin.git"
RELAY_HOME="${RELAY_HOME:-$HOME/.local/share/relay-plugin}"

# ── colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; RESET='\033[0m'
info()    { echo -e "${CYAN}[relay]${RESET} $*"; }
success() { echo -e "${GREEN}[relay]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[relay]${RESET} $*"; }
error()   { echo -e "${RED}[relay] ERROR:${RESET} $*" >&2; exit 1; }

# ── prerequisites ────────────────────────────────────────────────────────────
command -v git >/dev/null 2>&1 || error "git not found."

PROJECT_DIR="${PWD}"
COMMANDS_DIR="$PROJECT_DIR/.claude/commands/relay"
AGENTS_DIR="$PROJECT_DIR/.claude/agents"
SETTINGS_FILE="$PROJECT_DIR/.claude/settings.json"

# ── clone or update relay-plugin ─────────────────────────────────────────────
if [[ -d "$RELAY_HOME/.git" ]]; then
  info "Updating relay-plugin at $RELAY_HOME ..."
  git -C "$RELAY_HOME" pull --ff-only --quiet
else
  info "Cloning relay-plugin to $RELAY_HOME ..."
  git clone --depth 1 "$REPO" "$RELAY_HOME" --quiet
fi

PLUGIN_SRC="$RELAY_HOME/relay-plugin"

# ── 1. commands (.claude/commands/relay/) ────────────────────────────────────
info "Installing commands to $COMMANDS_DIR ..."
mkdir -p "$COMMANDS_DIR/dev"

cp "$PLUGIN_SRC/commands/relay/"*.md "$COMMANDS_DIR/" 2>/dev/null || true
cp "$PLUGIN_SRC/commands/relay/dev/"*.md "$COMMANDS_DIR/dev/" 2>/dev/null || true

# ── 2. agents (.claude/agents/) ──────────────────────────────────────────────
info "Installing agents to $AGENTS_DIR ..."
mkdir -p "$AGENTS_DIR"
cp "$PLUGIN_SRC/agents/"*.md "$AGENTS_DIR/"

# ── 3. hooks (.claude/settings.json) ─────────────────────────────────────────
info "Merging hooks into $SETTINGS_FILE ..."
HOOKS_SRC="$PLUGIN_SRC/hooks/hooks.json"

if [[ ! -f "$SETTINGS_FILE" ]]; then
  mkdir -p "$(dirname "$SETTINGS_FILE")"
  # Create settings.json with hooks only
  python3 - <<PYEOF
import json, sys
with open("$HOOKS_SRC") as f:
    hooks_data = json.load(f)
result = {"hooks": hooks_data["hooks"]}
with open("$SETTINGS_FILE", "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print("  created $SETTINGS_FILE")
PYEOF
else
  # Merge relay hooks into existing settings.json
  python3 - <<PYEOF
import json, sys

with open("$SETTINGS_FILE") as f:
    settings = json.load(f)
with open("$HOOKS_SRC") as f:
    relay_hooks = json.load(f)["hooks"]

existing = settings.setdefault("hooks", {})
for event, entries in relay_hooks.items():
    if event not in existing:
        existing[event] = entries
    else:
        # Append relay hooks if not already present (dedup by prompt content)
        existing_prompts = {
            h.get("prompt", "") or h.get("hooks", [{}])[0].get("prompt", "")
            for h in existing[event]
        }
        for entry in entries:
            entry_prompt = entry.get("prompt", "") or entry.get("hooks", [{}])[0].get("prompt", "")
            if entry_prompt not in existing_prompts:
                existing[event].append(entry)

with open("$SETTINGS_FILE", "w") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
print("  merged into existing $SETTINGS_FILE")
PYEOF
fi

# ── done ──────────────────────────────────────────────────────────────────────
echo ""
success "relay 설치 완료."
echo ""
echo -e "설치된 항목:"
echo -e "  Commands : $COMMANDS_DIR"
echo -e "  Agents   : $AGENTS_DIR"
echo -e "  Hooks    : $SETTINGS_FILE"
echo -e "  Source   : $RELAY_HOME"
echo ""

cat <<EOF
${CYAN}────────────────────────────────────────────────────────────${RESET}
  다음 단계:

  1. Claude Code 를 실행하고 아래 명령어로 시작하세요.
       /relay:setup

  2. 외부 LLM(Gemini / OpenAI / Zhipu AI)을 사용하려면:
       /relay:setup-keys

     또는 수동으로 .mcp.json 을 설정하려면:
       cp $RELAY_HOME/mcp-servers/mcp.json.template .mcp.json
     이후 {{PROJECT_ROOT}} 를 $RELAY_HOME 으로 변경하세요.
${CYAN}────────────────────────────────────────────────────────────${RESET}
EOF
