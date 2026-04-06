# /relay:invoke-agent

CLI 기반 외부 모델 호출로 전문가를 실행합니다.

## 목적

- 전문가 정의(`.claude/relay/experts/{slug}.md`)를 읽어 CLI 로 실행합니다.
- `codex`, `gemini`, `zai` CLI variant 를 통해 외부 모델을 호출합니다.
- Claude 사용량 소비 없이 작업을 위임합니다.

## 사전 확인

1. `.claude/relay/domain-config.json` 존재 확인
2. `.claude/relay/experts/{slug}.md` 존재 확인
3. CLI 설치 확인 (`which codex`, `which gemini`, `which zai`)

정의 파일이 없으면 `/relay:define-expert` 로 먼저 생성하도록 안내합니다.

## 실행 모드

팀 유형에 따라 실행 모드가 결정됩니다:

| 팀 유형 | execution_mode | 설명 |
|---|---|---|
| **upper** | `teammate` | Agent Teams 로 스폰, 병렬 실행, SendMessage 통신 |
| **lower** | `inprocess` | team-leader 세션 내에서 CLI 직접 호출, 순차 실행 |

### 상위팀 (teammate)

```
invoke-agent → teammate 스폰 (--model {model-id})
teammate     → expert 파일 읽기 → CLI 호출 (자체)
             → SendMessage 로 팀 내 통신
```

### 하위팀 (in-process)

```
invoke-agent → expert 파일 읽기 → 페르소나 합성
             → provider-router.sh 로 CLI 호출
             → 결과 수령 → runs/ 기록
```

### 코디네이터 선택

| 코디네이터 | 환경 변수 | 사용 시점 |
|---|---|---|
| Claude | 기본 설정 | 복잡한 추론, 전략 수립 |
| GLM | `ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic` | Claude 사용량 한계 회피 |

`domain-config.json` 의 `coordinator` 필드로 선택합니다.

---

## 입력 해석

사용자 입력에서 다음을 파악합니다.

- `target` — expert slug
- `task` — 이번 실행에서 해야 할 일
- `model` *(선택, 런타임 오버라이드)* — 모델명 교체

## CLI Variant 목록

| CLI | 모델 ID | 용도 | 평균 지연 |
|---|---|---|---|
| `codex` | `gpt-5.3-codex` | Flagship 코드 생성 | 1200ms |
| `codex-spark` | `gpt-5.3-codex-spark` | 초고속 리뷰 (15x 빠름) | 300ms |
| `codex-mini` | `gpt-5.1-codex-mini` | 저비용 단순 작업 | 800ms |
| `codex-reasoning` | `o3` | 심층 추론 | 5000ms |
| `codex-large-context` | `gpt-4.1` | 1M 컨텍스트 | 2000ms |
| `gemini` | `gemini-3-pro-preview` | 연구, 분석, 멀티모달 | 800ms |
| `gemini-fast` | `gemini-3-flash-preview` | 실시간 처리 | 400ms |
| `claude-opus` | `claude-opus-4-6` | 최고 품질 전략 | 3000ms |
| `zai` | `glm-4-air` | 저비용 범용 | 500ms |

---

## 페르소나 합성

CLI 호출 시 전문가 파일의 내용을 `system` 파라미터로 합성합니다.

### 합성 순서

```
1. ## 페르소나   → 역할, 전문 분야, 소통 스타일
2. ## 역량       → 할 수 있는 것 (있으면 포함)
3. ## 제약       → 하지 않는 것 (있으면 포함)
```

### 합성 결과 예시

```text
당신은 SNS 마케터입니다.

캐주얼하고 친근한 톤의 SNS 콘텐츠 전문가. MZ세대 트렌드에 밝으며
짧고 임팩트 있는 문장을 선호합니다.

## 역량
- 인스타그램, 스레드, X 게시물 작성
- 해시태그 전략 수립
- 바이럴 Hook 문구 생성

## 제약
- 경쟁사 직접 언급 금지
- 과장·허위 광고성 표현 금지
```

---

## CLI 호출 방식

### provider-router.sh 사용

```bash
# 라우팅 모드 설정
export RELAY_ROUTING_MODE=round-robin  # 또는 fastest, cheapest

# CLI 호출
./scripts/provider-router.sh invoke \
  "{cli_variant}" \
  "{model_id}" \
  "{system_prompt}" \
  "{user_prompt}"
```

### 직접 CLI 호출

```bash
# Gemini
gemini -p "{system_prompt}" "{user_prompt}"

# Gemini Fast
gemini-fast -p "{system_prompt}" "{user_prompt}"

# Codex
codex --model "{model_id}" "{user_prompt}" --system "{system_prompt}"

# Codex Spark
codex-spark "{user_prompt}" --system "{system_prompt}"

# Zai
zai --model "{model_id}" "{user_prompt}" --system "{system_prompt}"

# Claude Opus
claude-opus "{user_prompt}" --system "{system_prompt}"
```

---

## Fallback 체인

CLI 호출 실패 시 자동으로 fallback 합니다:

```
codex → codex-spark → gemini-fast → zai
```

`providers.json` 의 `fallback_cli` 필드를 참조합니다.

---

## Context 압축

누적 결과가 임계값을 넘으면 압축을 트리거합니다:

| 조건 | 임계값 |
|---|---|
| 누적 길이 | > 2,000자 |
| 누적 건수 | ≥ 4건 |

압축은 `zai:glm-4-flash` (무료 티어) 를 사용하거나, 없으면 Claude 가 직접 처리합니다.

---

## 실행 로그

실행 후 `.claude/relay/runs/{timestamp}-{target}.md` 에 기록합니다.

```markdown
---
target: {expert slug}
cli: {cli_variant}
model: {model_id}
status: {completed | failed}
duration_ms: {응답 시간}
---

# Task
{task}

## Result
{결과}
```

---

## 안내 규칙

실행 전 사용자에게 다음을 짧게 알립니다.

```text
sns-marketer 전문가를 사용합니다.
  페르소나  : 캐주얼 SNS 콘텐츠 전문가 (합성 완료)
  실행 CLI : gemini-fast → 모델: gemini-3-flash-preview
```

오버라이드 적용 시:

```text
sns-marketer 전문가를 사용합니다.
  페르소나  : 캐주얼 SNS 콘텐츠 전문가 (합성 완료)
  실행 CLI : gemini → 모델: gemini-3-pro-preview  ⚠ (기본값에서 오버라이드됨)
```
