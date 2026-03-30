# /relay:define-expert

전문가를 정의하고 `.claude/relay/experts/` 에 저장합니다.

## 사전 확인

`.claude/relay/domain-config.json` 이 없으면 `/relay:setup` 을 먼저 실행하도록 안내합니다.

## 대화 흐름

```
1. "어떤 전문가를 정의하시겠습니까?" 질문
2. 역할명·분야 파악
3. 외부 에이전트 위임 여부 질문:

   "이 역할의 실제 작업을 외부 LLM 에이전트에게 위임하시겠습니까?
    예) gemini:gemini-2.5-flash, codex:gpt-4o, zai:glm-4-flash, relay:developer
    직접 정의하려면 '없음'을 선택하세요."

   → 위임함 : backed_by 에 외부 에이전트 지정 후 4번으로 이동
   → 직접 정의: 4개 레이어 순서대로 채우기

4. 조합형 실행 프로필 연결 여부 질문:

   "이 전문가를 공통 모듈 + 플랫폼 선택 방식으로 실행하시겠습니까?
    예) backend-developer, default platform: fastapi"

5. 초안 제시 → 피드백 반영
6. .claude/relay/experts/{slug}.md 저장
```

## 저장 형식

```markdown
---
role: {역할명}
slug: {역할-슬러그}
domain: {소속 도메인 또는 core}
backed_by: {플러그인:에이전트명 또는 null}
agent_profile: {조합형 definition id 또는 null}
default_platform: {기본 platform 또는 null}
created_at: {YYYY-MM-DD}
---

# {역할명}

## 페르소나
{직함, 전문 분야, 소통 스타일}
※ backed_by 가 있으면 해당 에이전트의 기본 특성을 따르며,
  relay의 팀 구조(회의 기록·보고·에스컬레이션)에 편입됩니다.

## 역량
- {할 수 있는 것}

## 제약
- {하지 않는 것}

## 접근 권한
| 디렉토리 | 읽기 | 쓰기 |
|---|---|---|
| design-decisions/ | ✅ | ❌ |

## 위임 설정
backed_by: {플러그인:에이전트명 또는 null}
agent_profile: {조합형 definition id 또는 null}
default_platform: {기본 platform 또는 null}
```

## backed_by 예시

```yaml
# ── relay 내부 에이전트 ────────────────────────────
backed_by: relay:developer             # relay 기본 개발자

# ── Google Gemini (MCP 필요) ───────────────────────
backed_by: gemini:gemini-2.5-flash     # 빠른 처리 / 경량 작업
backed_by: gemini:gemini-2.5-pro       # 고품질 추론 / 복잡한 작업

# ── OpenAI GPT / o 시리즈 (MCP 필요) ──────────────
backed_by: codex:gpt-4o                # 범용 고성능
backed_by: codex:gpt-4o-mini           # 경량·비용 효율
backed_by: codex:o3-mini               # 추론 특화

# ── Zhipu AI GLM 시리즈 (MCP 필요) ─────────────────
backed_by: zai:glm-4-flash             # 무료 티어 / 컨텍스트 압축 권장
backed_by: zai:glm-4-air               # 저비용 범용
backed_by: zai:glm-4                   # 고성능
backed_by: zai:glm-4-long              # 128K 컨텍스트 / 장문 처리

# ── 직접 정의 ──────────────────────────────────────
backed_by: null                        # 외부 위임 없음, 직접 정의
```

`gemini:*`, `codex:*`, `zai:*` 선택 시 MCP 서버 등록이 필요합니다.
→ `mcp-servers/` 디렉토리의 서버를 설치하고 `.mcp.json` 에 등록하세요.

## 완료 후

저장된 전문가를 팀에 배치하려면 `/relay:build-team` 을 실행합니다.
조합형 프로필이 연결된 전문가는 `/relay:invoke-agent` 로 호출할 수 있습니다.
