# Coordinator Hybrid Rules

> Claude-Octopus (v8.9.0/v8.19.0) 방식을 기반으로 GLM/Claude 를 선택적 조합할 수 있는 코디네이터 규칙.

---

## 1. 코디네이터 모델 선택

### 1.1 선택 기준

| 코디네이터 | 비용 | Claude 한도 | 추론 품질 | 적합한 상황 |
|---|---|---|---|---|
| **Claude** | 사용량 소비 | 영향받음 | 최고 (Opus 4.6) | 복잡한 설계 결정, 보안 검토, 아키텍처 |
| **GLM** | 저비용/무료 | 영향없음 | 중간 (GLM-4) | 일반 구현, 테스트, 문서, 단순 작업 |

### 1.2 설정 위치

```json
// .claude/relay/domain-config.json
{
  "coordinator": "glm | claude",
  "coordinator_model": "glm-4-air | claude-sonnet-4-6 | claude-opus-4-6",
  "fallback_coordinator": "glm | claude | null"
}
```

### 1.3 자동 선택 규칙

```
작업 유형 감지:
  - "설계", "아키텍처", "보안", "전략" → Claude (opus 권장)
  - "구현", "테스트", "문서", "리팩터링" → GLM
  - "연구", "분석", "브레인스토밍" → GLM (비용 효율)

명시적 지정 시:
  - "claude로 분석해줘" → Claude 강제
  - "glm으로 구현해줘" → GLM 강제
```

---

## 2. 외부 모델 호출 방식

### 2.1 CLI Variant (Octo v8.9.0 기준)

Octo는 CLI별 variant를 구분합니다. relay-plugin도 동일하게 적용합니다.

| CLI | Variant | 모델 | 용도 |
|---|---|---|---|
| `gemini` | 기본 | `gemini-3-pro-preview` | 연구, 분석, 멀티모달 |
| `gemini-fast` | 빠른 처리 | `gemini-3-flash-preview` | 실시간, 대량 처리 |
| `codex` | 기본 | `gpt-5.3-codex` | 코드 생성, 아키텍처 |
| `codex-spark` | 초고속 | `gpt-5.3-codex-spark` | 빠른 리뷰, 단순 반복 (15x 빠름) |
| `codex-mini` | 경량 | `gpt-5.1-codex-mini` | 저비용 일반 작업 |
| `codex-reasoning` | 심층 추론 | `o3` | 복잡한 알고리즘, 의사결정 |
| `codex-large-context` | 대형 컨텍스트 | `gpt-4.1` | 1M 컨텍스트, 대규모 코드 분석 |
| `claude-opus` | Claude 직접 | `claude-opus-4-6` | 최고 품질 (Octo에서 사용) |
| `zai` | GLM | `glm-4-air` / `glm-4-flash` | **Relay 추가**: 저비용 코디네이터 |

### 2.2 CLI 호출 패턴

```
┌─────────────────────────────────────────────────┐
│  Coordinator (Claude 또는 GLM)                   │
│  Bash 도구로 CLI 실행                            │
├─────────────────────────────────────────────────┤
│                                                  │
│  Bash("gemini -p '...' '...'")                  │
│  Bash("codex-spark '...'")                      │
│  Bash("zai --model glm-4-flash '...'")          │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 2.3 CLI 사전 조건

| CLI | 환경 변수 | 설치 방법 |
|---|---|---|
| `gemini` | `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY` | Google Gemini CLI |
| `codex` | `OPENAI_API_KEY` | OpenAI Codex CLI |
| `zai` | `ZHIPU_API_KEY` | Zhipu AI CLI |

---

## 3. Provider Router

### 3.1 라우팅 모드

Octo v8.7.0 기준 세 가지 모드만 지원합니다.

| 모드 | 동작 | 사용 시점 |
|---|---|---|
| `round-robin` | 순차 분산 | 기본값, 부하 분산 |
| `fastest` | 응답시간 최단 우선 | 실시간성 중요 |
| `cheapest` | 비용 최저 우선 | 대량 처리 |

환경 변수: `RELAY_ROUTING_MODE=round-robin|fastest|cheapest`

### 3.2 Provider 설정

```json
// .claude/relay/providers.json
{
  "providers": {
    "gemini": {
      "cli": "gemini",
      "fallback_cli": "gemini-fast",
      "models": {
        "pro": "gemini-3-pro-preview",
        "flash": "gemini-3-flash-preview"
      },
      "cost_per_1k_tokens": { "input": 0.00001, "output": 0.00003 },
      "avg_latency_ms": 800
    },
    "codex": {
      "cli": "codex",
      "fallback_cli": "codex-spark",
      "models": {
        "flagship": "gpt-5.3-codex",
        "fast": "gpt-5.3-codex-spark",
        "standard": "gpt-5.2-codex",
        "mini": "gpt-5.1-codex-mini",
        "reasoning": "o3",
        "large-context": "gpt-4.1"
      },
      "cost_per_1k_tokens": { "input": 0.00015, "output": 0.0006 },
      "avg_latency_ms": 1200
    },
    "zai": {
      "cli": "zai",
      "fallback_cli": null,
      "models": {
        "flash": "glm-4-flash",
        "air": "glm-4-air",
        "standard": "glm-4",
        "long": "glm-4-long"
      },
      "cost_per_1k_tokens": { "input": 0.000001, "output": 0.000001 },
      "avg_latency_ms": 500
    }
  },
  "routing_mode": "round-robin"
}
```

### 3.3 라우터 로직

```bash
# scripts/provider-router.sh (Octo 방식과 동일)
select_provider() {
  local mode="${RELAY_ROUTING_MODE:-round-robin}"
  local candidates=("$@")

  case "$mode" in
    fastest)
      # .provider-stats.json 에서 avg_latency_ms 최소 provider 선택
      local best="" best_latency=999999
      for candidate in "${candidates[@]}"; do
        local base="${candidate%%-*}"
        local latency
        latency=$(jq -r ".providers.\"$base\".avg_latency_ms // 999999" "$_ROUTER_STATS_FILE" 2>/dev/null || echo "999999")
        if awk -v a="$latency" -v b="$best_latency" 'BEGIN { exit !(a < b) }'; then
          best="$candidate"; best_latency="$latency"
        fi
      done
      echo "${best:-${candidates[0]}}"
      ;;
    cheapest)
      # .provider-stats.json 에서 avg_cost_usd 최소 provider 선택
      local best="" best_cost=999999
      for candidate in "${candidates[@]}"; do
        local base="${candidate%%-*}"
        local cost
        cost=$(jq -r ".providers.\"$base\".avg_cost_usd // 999999" "$_ROUTER_STATS_FILE" 2>/dev/null || echo "999999")
        if awk -v a="$cost" -v b="$best_cost" 'BEGIN { exit !(a < b) }'; then
          best="$candidate"; best_cost="$cost"
        fi
      done
      echo "${best:-${candidates[0]}}"
      ;;
    round-robin | *)
      # provider-index 파일 기반 순환
      local idx=0
      [[ -f "$_ROUTER_STATE_FILE" ]] && idx=$(cat "$_ROUTER_STATE_FILE" 2>/dev/null || echo "0")
      local selected="${candidates[$((idx % ${#candidates[@]}))]}"
      echo $(( (idx + 1) % ${#candidates[@]} )) > "$_ROUTER_STATE_FILE"
      echo "$selected"
      ;;
  esac
}
```

---

## 4. Phase-Model Routing

Octo의 `phase_model_routing` 개념을 relay 워크플로우에 매핑합니다.

### 4.1 Phase → 모델 매핑

| Phase | Relay 워크플로우 | 기본 CLI | 기본 모델 | 설명 |
|---|---|---|---|---|
| `probe` | 요구사항 분석 / SPEC | `codex` | `gpt-5.3-codex` | 심층 분석 |
| `grasp` | 아키텍처 설계 / DDL | `codex` | `gpt-5.3-codex` | 정밀 설계 |
| `tangle` | 구현 / TDD | `codex` | `gpt-5.3-codex` | 복잡 구현 |
| `ink` | 리뷰 / 배포 | `codex-spark` | `gpt-5.3-codex-spark` | 빠른 피드백 |
| `quick` | 간단 작업 | `codex-spark` | `gpt-5.3-codex-spark` | 속도 우선 |
| `security` | 보안 감사 | `codex` | `gpt-5.3-codex` | 철저한 분석 |

### 4.2 설정

```json
// .claude/relay/providers.json → phase_routing
{
  "phase_routing": {
    "probe":   { "cli": "codex", "model": "gpt-5.3-codex" },
    "grasp":   { "cli": "codex", "model": "gpt-5.3-codex" },
    "tangle":  { "cli": "codex", "model": "gpt-5.3-codex" },
    "ink":     { "cli": "codex-spark", "model": "gpt-5.3-codex-spark" },
    "quick":   { "cli": "codex-spark", "model": "gpt-5.3-codex-spark" },
    "security":{ "cli": "codex", "model": "gpt-5.3-codex" }
  }
}
```

---

## 5. 에이전트 설정 스키마

Octo의 `agents/config.yaml` 스키마를 relay 전문가 정의에 매핑합니다.

### 5.1 전문가 정의 파일

```yaml
# .claude/relay/experts/{slug}.md frontmatter
---
role: 백엔드 개발자
slug: backend-dev
cli: codex                    # CLI variant
model: gpt-5.3-codex         # 기본 모델
fallback_cli: codex-spark     # CLI 실패 시 대체
tier: premium | standard | trivial   # 비용 등급
permission_mode: plan | acceptEdits | default  # 도구 권한
memory: project | user | local       # 컨텍스트 범위
isolation: worktree | null           # 작업 격리
phases: [probe, tangle]              # 담당 phase
---
```

### 5.2 필드 설명

| 필드 | 값 | 설명 |
|---|---|---|
| `cli` | `codex`, `codex-spark`, `codex-mini`, `codex-reasoning`, `codex-large-context`, `gemini`, `gemini-fast`, `zai` | 호출할 CLI |
| `model` | 실제 모델 ID | CLI에 전달할 모델 |
| `fallback_cli` | 동일 또는 null | CLI 실패 시 대체 CLI |
| `tier` | `trivial`, `standard`, `premium` | 비용 등급 |
| `permission_mode` | `plan` (읽기전용), `acceptEdits` (쓰기가능), `default` (표준) | 도구 접근 권한 |
| `memory` | `project` (코드베이스), `user` (사용자), `local` (실행마다) | 컨텍스트 유지 범위 |
| `isolation` | `worktree` 또는 null | git worktree 격리 여부 |
| `phases` | 배열 | 이 전문가가 담당할 phase |

---

## 6. 실행 모드 조합

### 6.1 모드 매트릭스

| 코디네이터 | 외부 모델 | 총 비용 | Claude 한도 | 적합 상황 |
|---|---|---|---|---|
| Claude | Gemini/Codex | Claude + 외부 | 영향 | 최고 품질 설계 |
| Claude | GLM | Claude + GLM | 영향 | 설계 + 저비용 실행 |
| GLM | Gemini/Codex | GLM + 외부 | **영향없음** | 일반 작업 + 고품질 실행 |
| GLM | GLM | GLM만 | **영향없음** | 최저비용 대량 처리 |

### 6.2 팀 유형별 기본 조합

```json
// .claude/relay/teams/{slug}.json
{
  "type": "upper",
  "coordinator": "claude",
  "coordinator_model": "claude-opus-4-6",
  "default_cli": "codex",
  "fallback_cli": "gemini",
  "phase_routing": { "probe": "codex", "grasp": "codex", "ink": "codex-spark" }
}

{
  "type": "lower",
  "coordinator": "glm",
  "coordinator_model": "glm-4-air",
  "default_cli": "zai",
  "fallback_cli": "gemini-fast",
  "phase_routing": { "tangle": "zai", "ink": "zai" }
}
```

---

## 7. 호출 규약

### 7.1 invoke-agent 명령어 확장

```
/relay:invoke-agent {target} {task} [--cli {cli-variant}] [--model {model-id}]
```

**예시:**
```
# 기본값 (전문가 정의 파일 기준)
/relay:invoke-agent backend-dev "API 구현"

# CLI variant 지정
/relay:invoke-agent backend-dev "빠른 리뷰" --cli codex-spark

# 모델 강제 지정
/relay:invoke-agent backend-dev "복잡한 추론" --cli codex-reasoning --model o3

# 대형 컨텍스트 분석
/relay:invoke-point codebase-analyst "전체 코드 분석" --cli codex-large-context
```

### 7.2 Fallback 체인

```
1차: 전문가 정의의 cli
2차: 전문가 정의의 fallback_cli
3차: 팀 설정의 fallback_cli
4차: zai (최저비용 보험)
```

### 7.3 에러 처리

```bash
try_cli() {
  local cli="$1"
  shift
  local args=("$@")

  if ! command -v "${cli}" &>/dev/null; then
    echo "ERROR: ${cli} CLI not found" >&2
    return 1
  fi

  local result exit_code
  result=$("${cli}" "${args[@]}" 2>&1)
  exit_code=$?

  if [[ $exit_code -ne 0 ]]; then
    echo "ERROR: ${cli} failed (exit ${exit_code}): ${result}" >&2
    return 1
  fi

  echo "$result"
}

# Fallback 체인
result=$(try_cli codex "$prompt") || \
result=$(try_cli codex-spark "$prompt") || \
result=$(try_cli zai --model glm-4-flash "$prompt")
```

---

## 8. 비용 추적

### 8.1 호출별 메트릭

```json
// .claude/relay/metrics/{timestamp}-{call-id}.json
{
  "call_id": "call-001",
  "timestamp": "2026-04-04T10:30:00Z",
  "coordinator": "glm",
  "coordinator_tokens": { "input": 150, "output": 50 },
  "cli": "codex",
  "model": "gpt-5.3-codex",
  "provider_tokens": { "input": 2000, "output": 500 },
  "estimated_cost_usd": 0.0012,
  "duration_ms": 850,
  "fallback_used": false
}
```

### 8.2 Provider 통계 (Octo 방식)

```json
// .claude/relay/.provider-stats.json
{
  "providers": {
    "codex": { "avg_latency_ms": 1200, "call_count": 15, "avg_cost_usd": 0.003 },
    "gemini": { "avg_latency_ms": 800, "call_count": 8, "avg_cost_usd": 0.001 },
    "zai": { "avg_latency_ms": 500, "call_count": 20, "avg_cost_usd": 0.0001 }
  },
  "updated_at": "2026-04-04T12:00:00Z"
}
```

---

## 9. 환경 변수 요약

| 변수 | 필수 | 설명 |
|---|---|---|
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Yes | Agent Teams 활성화 (`1`) |
| `ANTHROPIC_API_KEY` | Claude 코디네이터 시 | Claude API 키 |
| `ANTHROPIC_BASE_URL` | GLM 코디네이터 시 | `https://api.z.ai/api/anthropic` |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | GLM 코디네이터 시 | `glm-4-air` 등 |
| `GEMINI_API_KEY` | Gemini 사용 시 | Google API 키 |
| `OPENAI_API_KEY` | Codex 사용 시 | OpenAI API 키 |
| `ZHIPU_API_KEY` | Zai 사용 시 | Zhipu API 키 |
| `RELAY_ROUTING_MODE` | No | `round-robin` (기본) / `fastest` / `cheapest` |

---

## 10. 마이그레이션 가이드

### 10.1 MCP → CLI 전환

**이전 (MCP):**
```python
gemini_mcp.gemini_generate(model="gemini-3-pro-preview", system=system, prompt=prompt)
```

**이후 (CLI):**
```bash
gemini -p "$system" "$prompt"
```

### 10.2 설정 파일 업데이트

```yaml
# 이전
backed_by: gemini:gemini-3.1-flash

# 이후
cli: gemini
model: gemini-3-flash-preview
fallback_cli: null
tier: standard
```

### 10.3 주요 변경 사항

| 항목 | 이전 | 이후 |
|---|---|---|
| 호출 방식 | MCP 도구 | CLI 직접 실행 |
| 모델 지정 | `backed_by: namespace:model` | `cli` + `model` 분리 |
| Fallback | `fallback_provider` | `fallback_cli` (Octo 방식) |
| 라우팅 | 없음 | `round-robin` / `fastest` / `cheapest` |
| 비용 추적 | 없음 | per-call 메트릭 + provider 통계 |

---

## 11. 요약

| 구분 | Octo 원본 | Relay-plugin 적용 |
|---|---|---|
| 코디네이터 | Claude 고정 | **Claude / GLM 선택 가능** |
| CLI variant | codex/codex-spark/gemini/gemini-fast/claude-opus | 동일 + `zai` 추가 |
| 라우팅 | round-robin/fastest/cheapest | 동일 |
| Phase routing | probe/grasp/tangle/ink | 동일 + relay 워크플로우 매핑 |
| Fallback | fallback_cli | 동일 |
| 비용 추적 | per-call 메트릭 | 동일 |
| Claude 한도 | 영향받음 | **GLM 코디네이터 시 영향없음** |
