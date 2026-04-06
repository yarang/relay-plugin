# /relay:define-executor

실행 환경을 정의하고 `.claude/relay/executors/` 에 저장합니다.

Executor는 "어떻게 호출되는가"를 정의합니다 — CLI, 모델, 인증 키 풀, fallback.

## 사전 확인

`.claude/relay/domain-config.json` 이 없으면 `/relay:setup` 을 먼저 실행하도록 안내합니다.

## 대화 흐름

### 1. Slug 입력

네이밍 규칙: `{cli}_{model_identifier}`

```text
예시:
  codex_gpt_5.4
  claude_sonnet_4.6
  zai_glm_4_air
  gemini_flash_3
  codex_default         ← alias 용도
```

### 2. CLI 선택

`config/providers.json` 에서 사용 가능한 CLI 목록을 읽어 표시합니다.

```text
사용 가능한 CLI:
  [1] codex              — OpenAI Codex (코드 생성, 아키텍처)
  [2] codex-spark        — OpenAI Codex Spark (초고속 리뷰)
  [3] codex-mini         — OpenAI Codex Mini (저비용)
  [4] codex-reasoning    — OpenAI o3 (심층 추론)
  [5] gemini             — Google Gemini Pro (연구, 분석)
  [6] gemini-fast        — Google Gemini Flash (실시간 처리)
  [7] claude-opus        — Anthropic Claude Opus (최고 품질)
  [8] zai                — Zhipu AI GLM (저비용 범용)
  [9] alias              — 다른 Executor를 포인팅
```

### 3. 모델 선택

선택한 CLI의 모델 목록을 `providers.json` 에서 읽어 표시합니다.

```text
codex 사용 가능한 모델:
  [1] gpt-5.4-codex       (flagship — 기본값)
  [2] gpt-5.4-codex-spark (fast)
  [3] o3                  (reasoning)
  [4] gpt-4.1             (large-context, 1M ctx)
  [5] 직접 입력
```

### 4. Fallback Executor 설정 (선택)

이 Executor 실패 시 사용할 다른 Executor slug를 입력합니다. 없으면 Enter.

### 5. Auth 설정 (선택)

`keys.json` 에 등록된 key alias 목록을 표시합니다. 없으면 이 단계를 건너뜁니다.

```text
등록된 Key:
  [1] openai_primary    (codex, OPENAI_API_KEY)
  [2] openai_secondary  (codex, OPENAI_API_KEY_2)
  [3] openai_oauth      (codex, oauth)
  [4] gemini_personal   (gemini, GEMINI_API_KEY)
  [5] glm_free          (zai, ZAI_API_KEY)

이 Executor에서 사용할 key를 선택하세요 (쉼표 구분):
```

```text
인증 전략을 선택하세요:
  [1] fallback     — 순서대로 시도 (기본값)
  [2] round_robin  — 순환 (rate limit 분산)
  [3] random       — 무작위
```

### 6. Alias 모드 (선택한 경우)

다른 Executor slug를 입력합니다. 해당 Executor의 설정을 그대로 사용합니다.

```yaml
slug: codex_default
alias: codex_gpt_5.4
```

### 7. 초안 확인 → 저장

## 저장 형식

파일: `.claude/relay/executors/{slug}.md`

```yaml
---
slug: {slug}
cli: {cli-variant}
model: {model-id}
fallback: {executor-slug 또는 null}
auth:
  pool: [{key-alias}, ...]
  strategy: fallback | round_robin | random
---
```

alias 전용:

```yaml
---
slug: {slug}
alias: {target-executor-slug}
---
```

## Auth Strategy 설명

| strategy | 동작 |
|---|---|
| `fallback` | pool 순서대로 시도. primary 실패 시 다음 키 (기본값) |
| `round_robin` | 호출마다 pool을 순환. rate limit 분산에 적합 |
| `random` | 매 호출 무작위 선택 |

`auth` 가 없으면 환경변수에서 provider 기본 키를 직접 조회합니다.

## 완료 후

Executor를 Agent에 연결하려면: `/relay:define-agent`
