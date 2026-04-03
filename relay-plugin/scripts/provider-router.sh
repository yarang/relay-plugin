#!/usr/bin/env bash
# Provider Router for relay v1.0.0
# Latency-based provider routing with round-robin, fastest, and cheapest strategies
# Compatible with Claude Octopus v8.7.0 pattern

set -euo pipefail

# Configuration paths
RELAY_DIR="${RELAY_DIR:-${HOME}/.claude/relay}"
PROVIDERS_FILE="${RELAY_DIR}/config/providers.json"
ROUTER_STATE_FILE="${RELAY_DIR}/.router-state"
ROUTER_STATS_FILE="${RELAY_DIR}/.provider-stats.json"

# Routing mode (default: round-robin)
RELAY_ROUTING_MODE="${RELAY_ROUTING_MODE:-round-robin}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log function
log() {
  echo "[provider-router] $*" >&2
}

error() {
  echo -e "${RED}[ERROR]${NC} $*" >&2
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

# Check if jq is available
require_jq() {
  if ! command -v jq &>/dev/null; then
    error "jq is required but not installed. Install with: brew install jq"
    exit 1
  fi
}

# Build provider stats from metrics
build_provider_stats() {
  require_jq

  local metrics_dir="${RELAY_DIR}/metrics"
  local metrics_file="${metrics_dir}/session-summary.json"

  if [[ ! -f "$metrics_file" ]]; then
    warn "No metrics file found at ${metrics_file}"
    return 1
  fi

  mkdir -p "${RELAY_DIR}"

  # Extract per-provider average latency and cost
  jq '{
    providers: (
      [.providers // {} | to_entries[] | {
        key: .key,
        value: {
          avg_latency_ms: .value.avg_latency_ms // 999999,
          call_count: .value.calls // 0,
          avg_cost_usd: .value.total_cost_usd // 0
        }
      }] | from_entries
    ),
    updated_at: (now | todate)
  }' "$metrics_file" > "$ROUTER_STATS_FILE" 2>/dev/null || {
    warn "Failed to build provider stats"
    return 1
  }

  log "Provider stats updated at $(date)"
}

# Select provider based on routing mode
# Args: candidate1 candidate2 ...
select_provider() {
  local candidates=("$@")

  if [[ ${#candidates[@]} -eq 0 ]]; then
    error "No candidates provided"
    return 1
  fi

  case "$RELAY_ROUTING_MODE" in
    round-robin)
      _select_round_robin "${candidates[@]}"
      ;;
    fastest)
      _select_fastest "${candidates[@]}"
      ;;
    cheapest)
      _select_cheapest "${candidates[@]}"
      ;;
    *)
      warn "Unknown routing mode: ${RELAY_ROUTING_MODE}, using first candidate"
      echo "${candidates[0]}"
      ;;
  esac
}

# Round-robin selection
_select_round_robin() {
  local candidates=("$@")
  local idx=0

  if [[ -f "$ROUTER_STATE_FILE" ]]; then
    idx=$(cat "$ROUTER_STATE_FILE" 2>/dev/null || echo "0")
  fi

  local selected="${candidates[$((idx % ${#candidates[@]}))]}"

  # Increment and save state
  echo $(( (idx + 1) % ${#candidates[@]} )) > "$ROUTER_STATE_FILE"

  echo "$selected"
}

# Fastest selection (lowest latency)
_select_fastest() {
  local candidates=("$@")

  if [[ ! -f "$ROUTER_STATS_FILE" ]]; then
    warn "No stats file, using first candidate"
    echo "${candidates[0]}"
    return
  fi

  local best=""
  local best_latency=999999

  for candidate in "${candidates[@]}"; do
    local base_provider="${candidate%%-*}"
    local latency

    latency=$(jq -r ".providers.\"$base_provider\".avg_latency_ms // 999999" "$ROUTER_STATS_FILE" 2>/dev/null || echo "999999")

    if awk -v a="$latency" -v b="$best_latency" 'BEGIN { exit !(a < b) }'; then
      best="$candidate"
      best_latency="$latency"
    fi
  done

  echo "${best:-${candidates[0]}}"
}

# Cheapest selection (lowest cost)
_select_cheapest() {
  local candidates=("$@")

  if [[ ! -f "$ROUTER_STATS_FILE" ]]; then
    warn "No stats file, using first candidate"
    echo "${candidates[0]}"
    return
  fi

  local best=""
  local best_cost=999999

  for candidate in "${candidates[@]}"; do
    local base_provider="${candidate%%-*}"
    local cost

    cost=$(jq -r ".providers.\"$base_provider\".avg_cost_usd // 999999" "$ROUTER_STATS_FILE" 2>/dev/null || echo "999999")

    if awk -v a="$cost" -v b="$best_cost" 'BEGIN { exit !(a < b) }'; then
      best="$candidate"
      best_cost="$cost"
    fi
  done

  echo "${best:-${candidates[0]}}"
}

# Get CLI command for a provider
# Args: provider_name
get_cli() {
  local provider="$1"

  if [[ ! -f "$PROVIDERS_FILE" ]]; then
    error "Providers file not found: ${PROVIDERS_FILE}"
    return 1
  fi

  local cli
  cli=$(jq -r ".providers.\"${provider}\".cli // empty" "$PROVIDERS_FILE" 2>/dev/null)

  if [[ -z "$cli" ]]; then
    error "Provider not found: ${provider}"
    return 1
  fi

  echo "$cli"
}

# Get model ID for a provider
# Args: provider_name [model_alias]
get_model() {
  local provider="$1"
  local model_alias="${2:-default}"

  if [[ ! -f "$PROVIDERS_FILE" ]]; then
    error "Providers file not found: ${PROVIDERS_FILE}"
    return 1
  fi

  local model
  model=$(jq -r ".providers.\"${provider}\".models.\"${model_alias}\".id // .providers.\"${provider}\".default_model // empty" "$PROVIDERS_FILE" 2>/dev/null)

  if [[ -z "$model" ]]; then
    error "Model not found: ${provider}/${model_alias}"
    return 1
  fi

  echo "$model"
}

# Get fallback CLI for a provider
# Args: provider_name
get_fallback_cli() {
  local provider="$1"

  if [[ ! -f "$PROVIDERS_FILE" ]]; then
    return 1
  fi

  jq -r ".providers.\"${provider}\".fallback_cli // empty" "$PROVIDERS_FILE" 2>/dev/null
}

# Get CLI for a phase
# Args: phase_name
get_phase_cli() {
  local phase="$1"

  if [[ ! -f "$PROVIDERS_FILE" ]]; then
    echo "codex"
    return
  fi

  jq -r ".phase_routing.\"${phase}\".cli // \"codex\"" "$PROVIDERS_FILE" 2>/dev/null || echo "codex"
}

# Invoke external model via CLI
# Args: provider model system prompt
invoke_model() {
  local provider="$1"
  local model="$2"
  local system="$3"
  local prompt="$4"

  local cli
  cli=$(get_cli "$provider") || {
    # Try fallback
    local fallback
    fallback=$(get_fallback_cli "$provider")
    if [[ -n "$fallback" ]]; then
      warn "Primary CLI failed, using fallback: ${fallback}"
      cli="$fallback"
    else
      return 1
    fi
  }

  # Check CLI availability
  if ! command -v "${cli}" &>/dev/null; then
    error "CLI not found: ${cli}"

    # Try fallback chain
    local fallback
    fallback=$(get_fallback_cli "$provider")
    if [[ -n "$fallback" ]] && command -v "${fallback}" &>/dev/null; then
      warn "Using fallback CLI: ${fallback}"
      cli="$fallback"
    else
      return 1
    fi
  fi

  # Execute based on CLI type
  local result exit_code start_time end_time duration

  start_time=$(date +%s%3N)

  case "$cli" in
    gemini|gemini-fast)
      result=$("${cli}" -p "$system" "$prompt" 2>&1) || true
      ;;
    codex|codex-spark|codex-mini|codex-reasoning|codex-large-context)
      result=$("${cli}" --model "$model" "$prompt" --system "$system" 2>&1) || true
      ;;
    zai)
      result=$("${cli}" --model "$model" "$prompt" --system "$system" 2>&1) || true
      ;;
    claude-opus)
      result=$("${cli}" "$prompt" --system "$system" 2>&1) || true
      ;;
    *)
      error "Unknown CLI: ${cli}"
      return 1
      ;;
  esac

  exit_code=$?
  end_time=$(date +%s%3N)
  duration=$((end_time - start_time))

  if [[ $exit_code -ne 0 ]]; then
    error "CLI ${cli} failed (exit ${exit_code}): ${result}"
    return 1
  fi

  # Log metrics
  log "Invoked ${cli}:${model} in ${duration}ms"

  echo "$result"
}

# Refresh provider stats (call after agent completion)
refresh_provider_stats() {
  build_provider_stats 2>/dev/null || true
}

# Show help
show_help() {
  cat << 'EOF'
Provider Router for relay

Usage:
  provider-router.sh select <candidate1> [candidate2] ...
  provider-router.sh invoke <provider> <model> <system> <prompt>
  provider-router.sh get-cli <provider>
  provider-router.sh get-model <provider> [model_alias]
  provider-router.sh get-phase-cli <phase>
  provider-router.sh refresh-stats

Environment Variables:
  RELAY_ROUTING_MODE   Routing strategy (round-robin|fastest|cheapest)
  RELAY_DIR            Relay configuration directory

Examples:
  # Select provider using routing strategy
  provider-router.sh select codex gemini zai

  # Invoke Gemini with system prompt
  provider-router.sh invoke gemini gemini-3-pro-preview "You are an expert" "Analyze this code"

  # Get CLI for a phase
  provider-router.sh get-phase-cli probe

  # Refresh stats after session
  provider-router.sh refresh-stats
EOF
}

# Main entry point
main() {
  local command="${1:-help}"
  shift || true

  case "$command" in
    select)
      select_provider "$@"
      ;;
    invoke)
      invoke_model "$@"
      ;;
    get-cli)
      get_cli "$@"
      ;;
    get-model)
      get_model "$@"
      ;;
    get-fallback)
      get_fallback_cli "$@"
      ;;
    get-phase-cli)
      get_phase_cli "$@"
      ;;
    refresh-stats)
      refresh_provider_stats
      ;;
    build-stats)
      build_provider_stats
      ;;
    help|--help|-h)
      show_help
      ;;
    *)
      error "Unknown command: ${command}"
      show_help
      exit 1
      ;;
  esac
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
