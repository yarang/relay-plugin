# /relay:invoke-agent

조합형 agent definition 또는 전문가 정의를 읽어 실행용 인스트럭션을 합성하고, 적절한 에이전트에 작업을 위임합니다.

## 목적

- 공통 capability 와 platform 모듈을 조합해 에이전트를 실행합니다.
- `backend developer` 같은 역할에서 `fastapi` 또는 `django` 를 런타임에 선택할 수 있게 합니다.
- 어떤 조합으로 실행했는지 `runs/` 에 기록합니다.

## 사전 확인

다음 순서로 존재 여부를 확인합니다.

1. `.claude/relay/domain-config.json`
2. `.claude/relay/agent-library/definitions/`
3. `.claude/relay/agent-library/modules/`
4. `.claude/relay/experts/`

정의 파일이 없으면 [docs/agent-definition-and-invocation.md](/Users/yarang/working/agent_teams/relay-plugin/docs/agent-definition-and-invocation.md) 형식에 맞춰 먼저 생성하도록 안내합니다.

## 입력 해석

사용자 입력에서 다음을 파악합니다.

- `target`
  - expert slug 또는 definition id
- `task`
  - 이번 실행에서 해야 할 일
- `model` *(선택, 런타임 오버라이드)*
  - 지정하면 `backed_by` 의 모델명을 덮어씁니다.
  - 네임스페이스는 `backed_by` 와 동일해야 합니다.
  - 예: `backed_by: gemini:gemini-2.5-flash` 인 전문가에게 `model: gemini-2.5-pro` 지정 가능
  - 예: `backed_by: codex:gpt-4o-mini` 인 전문가에게 `model: o3-mini` 지정 가능
  - 네임스페이스가 다르면 오류 처리 (예: gemini 전문가에게 codex 모델 불가)
- `platform override`
  - 명시되지 않으면 expert 의 `default_platform` 또는 definition 의 기본값 사용
- `capability override`
  - 추가 capability 또는 제외 capability

## 해석 규칙

### Case 1. target 이 expert slug 인 경우

1. `.claude/relay/experts/{slug}.md` 로드
2. `agent_profile` 이 있으면 해당 definition 사용 (capability·platform 조합 참조용)
3. `backed_by` 가 있으면 실행 백엔드 후보로 저장
4. `default_platform` 이 있으면 기본 platform 으로 사용

> **백엔드 우선순위**: expert 의 `backed_by` 가 definition 의 `default_agent` 보다 **항상 우선**합니다.
> expert 에 `backed_by` 가 명시된 경우, definition 의 `default_agent` 는 무시합니다.
>
> ```
> expert.backed_by    있음 → 이 값으로 실행 (definition.default_agent 무시)
> expert.backed_by    없음 → definition.default_agent 사용
> ```

### Case 2. target 이 definition id 인 경우

1. `.claude/relay/agent-library/definitions/{id}.md` 로드
2. `default_agent` 를 실행 백엔드 후보로 사용

## 조합 순서

항상 아래 순서로 합성합니다.

1. `base`
2. `capabilities`
3. `platform`
4. `policy`
5. `task overlay`

`platform` 은 한 번에 하나만 선택합니다.

## 충돌 검사

- `conflicts_with` 에 현재 선택된 모듈이 있으면 사용자에게 충돌을 알리고 하나만 선택하도록 유도합니다.
- `requires` 가 누락되면 자동으로 포함하거나, 불가능하면 중단 사유를 설명합니다.
- project policy 와 충돌 시 policy 를 우선합니다.

## 모델 파싱 규칙

`backed_by` 값은 `{namespace}:{model}` 형식입니다.

```
backed_by: gemini:gemini-2.5-flash
           ^^^^^^  ^^^^^^^^^^^^^^^^
           네임스페이스  모델명 (API에 그대로 전달)

backed_by: codex:gpt-4o-mini
           ^^^^^  ^^^^^^^^^^
           네임스페이스  모델명
```

런타임에 `model` 파라미터가 주어지면 모델명 부분만 교체합니다.

```
backed_by: gemini:gemini-2.5-flash  +  model: gemini-2.5-pro
→ 실제 호출: gemini_mcp.gemini_generate(model="gemini-2.5-pro", ...)

backed_by: codex:gpt-4o-mini  +  model: o3-mini
→ 실제 호출: codex_mcp.codex_generate(model="o3-mini", ...)
```

네임스페이스 불일치는 오류로 처리합니다.

```
backed_by: gemini:gemini-2.5-flash  +  model: gpt-4o  ← ❌ 오류
→ "gemini 네임스페이스 전문가에게 codex 모델을 지정할 수 없습니다."
```

## 페르소나 합성 (MCP 경유 실행 시 필수)

`gemini:*` 또는 `codex:*` 백엔드는 relay 팀 구조를 전혀 모릅니다.
전문가 파일의 내용을 `system` 파라미터로 직접 합성해야만 페르소나가 적용됩니다.

### 합성 순서

전문가 파일(`.claude/relay/experts/{slug}.md`)에서 아래 섹션을 순서대로 추출합니다.

```
1. ## 페르소나   → 역할, 전문 분야, 소통 스타일
2. ## 역량       → 할 수 있는 것 (있으면 포함)
3. ## 제약       → 하지 않는 것 (있으면 포함)
```

추출한 내용을 합쳐 `system` 문자열을 만듭니다.

```
system =
  "당신은 {역할명}입니다.\n\n"
  + 페르소나 섹션 내용
  + "\n\n## 역량\n" + 역량 섹션 내용   ← 있을 때만
  + "\n\n## 제약\n" + 제약 섹션 내용   ← 있을 때만
```

### 예시

전문가 파일:
```markdown
---
role: SNS 마케터
slug: sns-marketer
backed_by: gemini:gemini-2.5-flash
---

## 페르소나
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

합성 결과 → `system` 파라미터:
```
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

### context 파라미터

이전 작업 결과는 **매 호출마다 압축하지 않습니다.**
누적량이 임계값을 넘을 때만 압축을 트리거하며, 그 전까지는 원본 결과를 그대로 전달합니다.

#### 압축 트리거 임계값

아래 조건 중 하나라도 해당되면 압축을 실행합니다.

```
조건 A: 누적 결과 전체 길이 > 2,000 자
조건 B: 누적 결과 개수 ≥ 4 건
```

두 조건은 의도적으로 수렴하도록 설계됩니다.
invoke 결과 1건 평균이 ~500자이므로 4건 ≈ 2,000자가 됩니다.

**임계값 설정 근거:**

| 항목 | 수치 | 이유 |
|---|---|---|
| 트리거 길이 | 2,000자 | 페르소나(~500자) + context 합산 2,000자를 넘으면 system prompt에서 페르소나 신호가 희석됨 |
| 트리거 건수 | 4건 | 결과 1건 평균 500자 × 4 = 2,000자 — 길이 조건과 수렴 |
| 압축 목표 크기 | **400자 이하** | 핵심 결정사항 8~10문장 = 충분한 컨텍스트 전달 가능 |
| 압축 비율 | 최소 5:1 | 2,000자 → 400자, 이후 3~4건이 다시 쌓여야 재압축 트리거 |

임계값 미만이면 이전 결과를 `context` 에 **그대로** 전달합니다 (압축 호출 없음).

```
누적 결과
  ├─ 임계값 미만 → context = 이전 결과 원문 (zai/Claude 호출 없음)
  └─ 임계값 초과 → 압축 트리거 → context = 압축 요약 (400자 이하)
```

#### 압축 담당 우선순위 (임계값 초과 시에만 적용)

```
1순위: zai 가 등록되어 있으면 → zai 에게 압축 위임 (비용 절감)
2순위: zai 없으면             → Claude 가 직접 압축
```

**context-compressor 존재 확인 (2단계):**

```
조건 1: .claude/relay/experts/context-compressor.md 존재
조건 2: .mcp.json 에 zai_mcp 등록 (ZHIPU_API_KEY 포함)

둘 다 ✅  → context-compressor 에게 압축 위임
하나라도 ❌ → Claude 가 직접 압축 (오류 없이 진행)
```

`context-compressor` 는 `backed_by: zai:glm-4-flash` 기반 전문가입니다.
`glm-4-flash` 는 무료 티어가 있어 압축 비용을 최소화할 수 있습니다.
정의 파일: `relay-plugin/docs/experts/context-compressor.md`

**context-compressor에게 압축 위임하는 경우:**

```
invoke-agent(
  target = "context-compressor",
  task   = "다음 작업 결과들을 400자 이하로 압축해줘.
            - 결정된 사항, 수치, 제약 조건을 우선 보존할 것
            - 다음 단계 작업자({next_target})가 판단에 필요한 포인트 포함
            - 원문에 없는 내용 추가 금지
            ---
            {누적 결과 전문}"
)
→ 반환값을 context 로 교체 (누적 결과 초기화)
```

**zai 없이 Claude 가 직접 압축하는 경우:**

400자 이하를 목표로 아래 형식으로 요약합니다.

```
context = "결정 사항: [핵심 결정·수치·제약 조건]
           다음 작업 포인트: [다음 단계에서 고려할 사항 1~2개]"
```

#### 압축 후 누적 결과 초기화

압축이 완료되면 누적 결과를 압축본으로 교체하고 카운터를 리셋합니다.

```
압축 전: [결과1, 결과2, 결과3]  (3개 누적, 임계값 도달)
압축 후: context = "요약본"     (누적 카운터 리셋 → 0)
```

#### context 사용

`system` + `context` 는 MCP 서버 내부에서 아래와 같이 합산됩니다.

```
최종 system instruction =
  system (페르소나 합성)
  + "\n\n## 배경 컨텍스트\n" + context   ← context 있을 때만
```

### 합성 체크리스트

MCP 호출 전 반드시 확인합니다.

| 항목 | 확인 |
|---|---|
| `system` 에 페르소나(역할명 + 특성) 포함 | ✅ |
| `system` 에 역량·제약 포함 (섹션이 있을 경우) | ✅ |
| 누적 결과가 임계값 미만이면 압축 호출 생략 | ✅ |
| 임계값 초과 시: zai 있으면 위임, 없으면 Claude 직접 압축 | ✅ |
| `context` 는 압축 요약 또는 원문 (raw 대화 기록 금지) | ✅ |
| `prompt` 는 이번 task 지시문만 | ✅ |

---

## 실행 방식

backed_by 네임스페이스별로 다음과 같이 처리합니다.

### `relay:*`

relay 내부 agent template 를 직접 사용합니다.

```
relay:developer   → agents/developer.md
relay:team-leader → agents/team-leader.md
```

### `moai:*` (또는 기타 플러그인)

해당 플러그인 에이전트를 호출합니다.
relay의 회의 기록·진행 보고·escalation 규칙을 함께 부착합니다.

```
moai:sns-content-creator  → moai 플러그인 에이전트 호출
moai:contract-reviewer    → moai 플러그인 에이전트 호출
```

### `gemini:{model}` — MCP 경유

`gemini_mcp` MCP 서버의 `gemini_generate` 도구를 호출합니다.
**페르소나 합성 섹션**에서 만든 `system` 문자열을 반드시 함께 전달합니다.

```
gemini_mcp.gemini_generate(
  model   = "gemini-2.5-flash",   ← backed_by 에서 파싱
  system  = <페르소나 합성 결과>,  ← 전문가 파일에서 구성
  context = <이전 결과 요약>,      ← 있을 때만
  prompt  = <이번 task 지시문>,
)
```

사전 조건: `gemini_mcp` MCP 서버가 `.mcp.json` 에 등록되어 있어야 합니다.
등록 방법: `/relay:setup-keys` 실행

### `codex:{model}` — MCP 경유

`codex_mcp` MCP 서버의 `codex_generate` 도구를 호출합니다.
**페르소나 합성 섹션**에서 만든 `system` 문자열을 반드시 함께 전달합니다.

```
codex_mcp.codex_generate(
  model   = "gpt-4o",              ← backed_by 에서 파싱
  system  = <페르소나 합성 결과>,  ← 전문가 파일에서 구성
  context = <이전 결과 요약>,      ← 있을 때만
  prompt  = <이번 task 지시문>,
)
```

사전 조건: `codex_mcp` MCP 서버가 `.mcp.json` 에 등록되어 있어야 합니다.
등록 방법: `/relay:setup-keys` 실행

### `zai:{model}` — MCP 경유

`zai_mcp` MCP 서버의 `zai_generate` 도구를 호출합니다.
Zhipu AI (智谱AI) GLM 시리즈를 사용합니다.

```
zai_mcp.zai_generate(
  model   = "glm-4-flash",         ← backed_by 에서 파싱 (무료 티어)
  system  = <페르소나 합성 결과>,
  context = <이전 결과 요약>,      ← 있을 때만
  prompt  = <이번 task 지시문>,
)
```

주요 모델:
```
zai:glm-4-flash    → 무료 티어, 컨텍스트 압축에 권장
zai:glm-4-air      → 저비용 범용
zai:glm-4          → 고성능
zai:glm-4-long     → 128K 컨텍스트
```

사전 조건: `zai_mcp` MCP 서버가 `.mcp.json` 에 등록되어 있어야 합니다.
등록 방법: `/relay:setup-keys` 실행

### MCP 서버 미등록 시 처리

#### `gemini:*` 미등록

`gemini_mcp` MCP 서버가 없거나 `GEMINI_API_KEY` 가 없으면 **중단**합니다.

```
gemini_mcp MCP 서버가 등록되지 않았습니다.
/relay:setup-keys 를 실행하여 GEMINI_API_KEY 를 등록하세요.
```

#### `codex:*` — API 키 / OAuth 분기

`codex_mcp` 연결 유효성은 아래 순서로 확인합니다.

```
1. OPENAI_API_KEY 설정 여부 확인
   → 있으면 API 키 모드로 정상 진행

2. OPENAI_API_KEY 없으면 OPENAI_AUTH_TYPE 확인
   → "oauth" 이면 OAuth 모드로 정상 진행
      (OPENAI_OAUTH_TOKEN 은 시스템/Claude Code 가 자동 주입)

3. 둘 다 없으면 중단 + 안내
   → "OPENAI_API_KEY 또는 OAuth 연결이 필요합니다.
      /relay:setup-keys 를 실행하세요."
```

OAuth 모드일 때는 API 키 미설정을 오류로 처리하지 않습니다.

#### `zai:*` 미등록 / `context-compressor` 미설치 (선택 구성 요소)

`context-compressor` 는 선택 구성 요소입니다. 없어도 오류 없이 동작합니다.

```
context-compressor 전문가 또는 zai_mcp 가 없습니다.
→ Claude 가 직접 컨텍스트를 압축합니다. (정상 진행)
```

`context-compressor` 를 활성화하려면:
1. `docs/experts/context-compressor.md` 를 `.claude/relay/experts/` 에 복사
2. `/relay:setup-keys` 에서 Zhipu AI API 키 입력 (glm-4-flash 무료 티어)

## 실행 로그

실행 후 다음 형식으로 `.claude/relay/agent-library/runs/{timestamp}-{target}.md` 에 남깁니다.

```markdown
---
target: {expert slug 또는 definition id}
definition: {resolved definition id}
resolved_agent: {relay:developer | plugin:agent}
platform: {selected platform}
capabilities:
  - {capability}
policy: {resolved policy}
status: {planned | running | completed | blocked}
started_at: {ISO8601}
---

# Task
{task}

## Result
- {변경 사항 또는 산출물}
```

## 안내 규칙

실행 전 사용자에게 다음을 짧게 알립니다.

- 어떤 definition 을 선택했는지
- 어떤 platform 으로 해석했는지
- 어떤 agent backend / 모델로 위임하는지
- 런타임 오버라이드가 적용됐으면 명시

예시 (오버라이드 없음):

```text
sns-marketer 전문가를 사용합니다.
  페르소나  : 캐주얼 SNS 콘텐츠 전문가 (합성 완료)
  실행 백엔드: gemini_mcp → 모델: gemini-2.5-flash
```

예시 (모델 오버라이드 적용):

```text
sns-marketer 전문가를 사용합니다.
  페르소나  : 캐주얼 SNS 콘텐츠 전문가 (합성 완료)
  실행 백엔드: gemini_mcp → 모델: gemini-2.5-pro  ⚠ (기본값 gemini-2.5-flash 에서 오버라이드됨)
```

예시 (context 포함):

```text
sns-marketer 전문가를 사용합니다.
  페르소나  : 캐주얼 SNS 콘텐츠 전문가 (합성 완료)
  실행 백엔드: gemini_mcp → 모델: gemini-2.5-flash
  컨텍스트  : "이전 브레인스토밍 결과 요약 전달" (압축 요약 포함됨)
```
