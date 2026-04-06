# relay-plugin Architecture v2 — Expert / Executor / Agent / Team 분리 설계

**작성일**: 2026-04-06  
**상태**: 설계 확정 (구현 예정)  
**대상 버전**: v0.6.0  

---

## 1. 설계 동기

### 현재 구조의 문제

v0.5.x의 `Expert` 파일은 **정체성(who)**과 **실행 설정(how)**을 동시에 담고 있습니다.

```yaml
# 현재 — 한 파일에 역할 정의와 실행 방식이 혼재
role: Backend Developer
backed_by: codex:gpt-5.4     ← 실행 방식
cli: codex                   ← 실행 방식
model: gpt-5.4               ← 실행 방식
tier: premium                ← 실행 방식 (model에서 자동 파생 가능)
permission_mode: acceptEdits ← 실행 방식
phases: [tangle, ink]        ← 팀 배치 방식
specs: [rest-api, crud]      ← 기능 정의
```

이 구조에서는 **같은 역할을 다른 LLM으로 실행**하려면 Expert 파일을 복사해야 합니다.  
`backend-developer-codex.md`, `backend-developer-zai.md` 처럼 파일이 중복됩니다.

### 목표

```
Expert   = 무엇을 잘하는가 (기능 정의)
Executor = 어떻게 호출되는가 (실행 설정)
Agent    = 실제 실행 인스턴스 (Expert + Executor 바인딩)
Team     = 함께 어떻게 일하는가 (운영 정의)
```

같은 `backend-developer` Expert를 `codex_gpt_5.4` 와 `zai_glm_4_air` 로 각각 실행하는 두 Agent가 팀 안에서 협의할 수 있습니다.

---

## 2. 개체 정의

### 2-1. Expert (기능 정의)

**무엇을 잘하는가.** 페르소나, 역량, 제약, 기본 spec 조합을 정의합니다.  
실행 관련 필드(cli, model, tier, permission, phases)를 포함하지 않습니다.

```yaml
# .claude/relay/experts/backend-developer.md
---
role: Backend Developer
slug: backend-developer
domain: development
specs:
  - rest-api
  - crud
  - auth-jwt
  - list-filter-sort
created_at: 2026-04-06
---

# Backend Developer

## 페르소나
백엔드 시스템 설계와 API 구현 전문가. 간결하고 명확하게 소통합니다.

## 역량
- REST API 설계 및 구현
- 데이터베이스 모델링
- 인증/인가 시스템

## 제약
- 프론트엔드 UI 작업은 담당하지 않습니다
- 프로덕션 배포는 승인 후에만 진행합니다
```

**필드 정의**

| 필드 | 필수 | 설명 |
|------|------|------|
| `role` | ✅ | 표시용 역할명 |
| `slug` | ✅ | 파일명과 동일 |
| `domain` | ✅ | `general` \| `development` |
| `specs` | — | 기본 spec ID 목록. Definition이 있으면 Definition이 override |
| `created_at` | ✅ | 생성일 |

---

### 2-2. Executor (실행 설정)

**어떻게 호출되는가.** CLI, 모델, 인증, fallback을 정의합니다.  
`providers.json`의 카탈로그에서 실제 사용할 조합을 명명한 인스턴스입니다.

```yaml
# .claude/relay/executors/codex_gpt_5.4.md
---
slug: codex_gpt_5.4
cli: codex
model: gpt-5.4
fallback: claude_sonnet_4.6
auth:
  pool: [openai_primary, openai_secondary]
  strategy: round_robin
---
```

```yaml
# .claude/relay/executors/zai_glm_4_air.md
---
slug: zai_glm_4_air
cli: zai
model: glm-4-air
fallback: null
auth:
  pool: [glm_free]
  strategy: fallback
---
```

```yaml
# .claude/relay/executors/codex_default.md (alias)
---
slug: codex_default
alias: codex_gpt_5.4     ← 이 executor를 그대로 사용
---
```

**필드 정의**

| 필드 | 필수 | 설명 |
|------|------|------|
| `slug` | ✅ | 파일명과 동일 |
| `cli` | ✅ (alias 제외) | CLI 실행기 이름 (`providers.json` key) |
| `model` | ✅ (alias 제외) | 모델 ID |
| `fallback` | — | 실패 시 사용할 다른 Executor slug |
| `auth.pool` | — | 사용할 key alias 목록 (`keys.json` 참조) |
| `auth.strategy` | — | `round_robin` \| `fallback` \| `random`. 기본값: `fallback` |
| `alias` | — | 다른 Executor slug를 포인팅 (alias 전용) |

**auth.strategy 의미**

| strategy | 동작 |
|----------|------|
| `round_robin` | 호출마다 pool을 순환 (rate limit 분산) |
| `fallback` | primary 실패 시 순서대로 다음 키 시도 |
| `random` | 호출마다 무작위 선택 |

**슬러그 네이밍 규칙**

- 명시적 버전 권장: `codex_gpt_5.4`, `claude_sonnet_4.6`
- alias 허용: `codex_default` → `alias: codex_gpt_5.4`
- 업그레이드 시 alias 파일만 수정하면 참조 Agent 파일 변경 불필요

---

### 2-3. Agent (실행 인스턴스)

**실제 실행 단위.** Expert + Executor를 바인딩하고, 팀 배치에 필요한 운용 정책을 정의합니다.

```yaml
# .claude/relay/agents/backend-dev.md
---
slug: backend-dev
expert: backend-developer
execute_by: codex_gpt_5.4
definition: backend-developer    # optional — 5-layer 조합 사용 시
phases: [tangle, ink]
permission_mode: acceptEdits
memory: project
isolation: worktree
created_at: 2026-04-06
---
```

```yaml
# .claude/relay/agents/backend-dev-budget.md
---
slug: backend-dev-budget
expert: backend-developer        # 같은 Expert
execute_by: zai_glm_4_air        # 다른 Executor
phases: [tangle]
permission_mode: acceptEdits
memory: project
isolation: null
auth_override:
  pool: [glm_free]               # 이 Agent만 특정 키 전용 사용
created_at: 2026-04-06
---
```

**필드 정의**

| 필드 | 필수 | 설명 |
|------|------|------|
| `slug` | ✅ | 파일명과 동일 |
| `expert` | ✅ | Expert.slug 참조 |
| `execute_by` | ✅ | Executor.slug 참조 |
| `definition` | — | AgentDefinition.id 참조 (5-layer 조합 사용 시) |
| `phases` | ✅ | 이 Agent가 담당하는 phase 목록 |
| `permission_mode` | ✅ | `plan` \| `acceptEdits` \| `default` |
| `memory` | — | `project` \| `user` \| `local` |
| `isolation` | — | `worktree` \| `null` |
| `auth_override` | — | Executor auth를 이 Agent에 한해 override |

**Expert 단독 실행 없음**: `/relay:invoke-agent`는 Agent slug만 받습니다.  
Expert를 직접 실행하는 경로는 존재하지 않습니다.

---

### 2-4. Team (운영 정의)

**함께 어떻게 일하는가.** Agent를 참조하고 팀 구조와 운영 방식을 정의합니다.  
멤버 속성을 복사하지 않고 `agent` slug만 참조합니다.

```json
{
  "name": "개발팀",
  "slug": "dev-team",
  "type": "lower",
  "execution_mode": "inprocess",
  "coordinator": "claude",
  "coordinator_model": "claude-opus-4-6",
  "purpose": "기능 구현 및 API 개발",
  "decision_mode": "leader_decides",
  "members": [
    { "agent": "backend-dev",        "role": "Backend Developer", "is_leader": true,  "is_bridge": false },
    { "agent": "frontend-dev",       "role": "Frontend Developer","is_leader": false, "is_bridge": false },
    { "agent": "backend-dev-budget", "role": "Junior Backend",    "is_leader": false, "is_bridge": false }
  ],
  "phase_routing": {
    "probe":  "gemini_flash",
    "grasp":  "codex_gpt_5.4",
    "tangle": "codex_gpt_5.4",
    "ink":    "zai_glm_4_air"
  },
  "bridge_to": null,
  "created_at": "2026-04-06"
}
```

`team_role` (`is_leader`, `is_bridge`)은 Team의 members 참조 안에 있습니다.  
같은 Agent가 팀마다 다른 역할을 가질 수 있습니다.

---

### 2-5. AgentDefinition (5-layer 조합 레시피)

기존 `definitions/` 구조를 유지합니다. Agent에서 선택적으로 참조합니다.

```yaml
# .claude/relay/agent-library/definitions/backend-developer.md
---
id: backend-developer
kind: composed-agent
base: backend-core
specs:
  - rest-api
  - crud
  - auth-jwt
  - list-filter-sort
available_platforms:
  - fastapi
  - django
default_policy: project-default
---
```

**Expert.specs vs Definition.specs 우선순위**

```
definition_ref 있음 → Definition.specs가 우선 (Expert.specs 무시)
definition_ref 없음 → Expert.specs 사용 (base/platform/policy 없음)
```

---

## 3. Key Registry

실제 키 값은 환경변수에만 존재합니다. `keys.json`은 alias → 환경변수 이름 매핑만 담습니다.

```json
// .claude/relay/keys.json (git 커밋 가능)
{
  "openai_primary":   { "provider": "codex",  "env": "OPENAI_API_KEY" },
  "openai_secondary": { "provider": "codex",  "env": "OPENAI_API_KEY_2" },
  "openai_oauth":     { "provider": "codex",  "type": "oauth", "env": "OPENAI_AUTH_TYPE" },
  "gemini_personal":  { "provider": "gemini", "env": "GEMINI_API_KEY" },
  "glm_free":         { "provider": "zai",    "env": "ZAI_API_KEY" }
}
```

```
# .env (gitignore — 실제 값)
OPENAI_API_KEY=sk-...
OPENAI_API_KEY_2=sk-...
GEMINI_API_KEY=AIza...
ZAI_API_KEY=...
```

```
# .env.example (git 커밋 — 팀 공유 템플릿)
OPENAI_API_KEY=
OPENAI_API_KEY_2=
GEMINI_API_KEY=
ZAI_API_KEY=
```

**런타임 키 선택 흐름**

```
invoke-agent 호출
  → Executor 로드 (auth.pool, auth.strategy)
  → pool에서 strategy에 따라 key alias 선택
  → keys.json에서 alias → env 이름 조회
  → 환경변수에서 실제 값 읽기
  → 실패 시 pool 내 다음 키 시도
  → pool 전체 실패 시 fallback Executor로
```

**`setup-keys` 역할**

1. key alias 등록 → `keys.json` 편집
2. 실제 값 입력 → `.env` 파일 편집
3. `.env.example` 자동 갱신 (값 제거, 키 이름만 유지)

---

## 4. 디렉터리 구조 (v0.6.0)

```
.claude/relay/
├── domain-config.json
├── keys.json                    ← key alias 레지스트리 (신규)
│
├── experts/                     ← 기능 정의 (기존, 슬림화)
│   └── {slug}.md
│
├── executors/                   ← 실행 설정 (신규)
│   ├── codex_gpt_5.4.md
│   ├── zai_glm_4_air.md
│   ├── claude_sonnet_4.6.md
│   └── codex_default.md        ← alias
│
├── agents/                      ← 실행 인스턴스 (신규)
│   └── {slug}.md
│
├── teams/                       ← 운영 정의 (기존, TeamMember 슬림화)
│   └── {slug}.json
│
├── agent-library/               ← 5-layer 조합 (기존 유지)
│   ├── definitions/
│   └── modules/
│       ├── base/
│       ├── specs/
│       ├── platforms/
│       └── policies/
│
├── shared-context/
└── notify/
```

---

## 5. 마이그레이션 전략

기존 `backed_by` 인라인 방식 Expert 파일을 수정 없이 계속 사용할 수 있습니다.

**`invoke-agent` 호환 파싱 규칙**

```
Agent에 execute_by 있음
  → executors/{execute_by}.md 로드

Agent에 execute_by 없고 Expert에 backed_by 있음
  → "provider:model" 문자열을 인라인 executor로 파싱
  → 예: backed_by: codex:gpt-5.4 → cli=codex, model=gpt-5.4

둘 다 없음 → 오류
```

**`/relay:define-expert` 변경**

- 신규 저장 시 실행 속성(cli, model, tier, phases) 입력 단계 제거
- Expert 파일에는 role, domain, specs, persona, constraints만 저장

**`/relay:define-agent` 신규 추가**

- Expert 선택 → Executor 선택 → phases, permission, memory, isolation 입력 → Agent 파일 저장

---

## 6. 타입 정의 (TypeScript)

```typescript
// Expert: 기능 정의
interface Expert {
  role: string;
  slug: string;
  domain: 'general' | 'development';
  specs?: string[];
  persona?: string;
  constraints?: string[];
  created_at: string;
}

// Executor: 실행 설정
interface Executor {
  slug: string;
  alias?: string;              // alias 전용
  cli?: string;
  model?: string;
  fallback?: string;           // Executor.slug 참조
  auth?: {
    pool: string[];            // keys.json key alias 목록
    strategy: 'round_robin' | 'fallback' | 'random';
  };
}

// Agent: 실행 인스턴스
interface Agent {
  slug: string;
  expert: string;              // Expert.slug 참조
  execute_by: string;          // Executor.slug 참조
  definition?: string;         // AgentDefinition.id 참조 (optional)
  phases: string[];
  permission_mode: 'plan' | 'acceptEdits' | 'default';
  memory?: 'project' | 'user' | 'local';
  isolation?: 'worktree' | null;
  auth_override?: {
    pool: string[];
  };
  created_at: string;
}

// TeamMember: agent 참조만 (속성 복사 없음)
interface TeamMember {
  agent: string;               // Agent.slug 참조
  role: string;                // 팀 내 표시용 역할명
  is_leader: boolean;
  is_bridge: boolean;
}

// Team: 운영 정의
interface Team {
  name: string;
  slug: string;
  type: 'upper' | 'lower';
  execution_mode: 'teammate' | 'inprocess';
  coordinator: 'claude' | 'glm';
  coordinator_model: string;
  purpose: string;
  decision_mode: 'leader_decides' | 'consensus' | 'vote' | 'architect_veto';
  members: TeamMember[];
  phase_routing: Record<string, string>;
  bridge_to?: string | null;
  created_at: string;
}

// KeyEntry: key alias 레지스트리
interface KeyEntry {
  provider: string;
  env: string;
  type?: 'api_key' | 'oauth';
}
```

---

## 7. 슬래시 커맨드 변경

| 커맨드 | v0.5.x | v0.6.0 |
|--------|--------|--------|
| `/relay:define-expert` | Expert + 실행 속성 | Expert만 (페르소나, specs) |
| `/relay:define-agent` | 없음 | **신규** — Expert + Executor 바인딩 |
| `/relay:define-executor` | 없음 | **신규** — cli, model, auth 설정 |
| `/relay:setup-keys` | API 키 등록 | keys.json alias 등록 + .env 편집 |
| `/relay:build-team` | expert_slug 참조 | **agent slug 참조로 변경** |
| `/relay:invoke-agent` | expert or team | agent slug만 받음 |

---

## 8. 설계 결정 사항 요약

| 결정 | 내용 | 이유 |
|------|------|------|
| Expert에서 phases 제거 | Agent로 이동 | 같은 Expert를 phase별로 다른 Agent로 배치 가능 |
| Expert 단독 실행 없음 | Agent가 반드시 필요 | 실행 설정 없이는 호출 불가 |
| tier 제거 | cli+model에서 자동 파생 | 중복 정보 |
| backed_by 호환 유지 | 인라인 파싱 fallback | 기존 파일 마이그레이션 불필요 |
| Executor alias 허용 | codex_default → codex_gpt_5.4 | 업그레이드 시 단일 파일만 수정 |
| TeamMember에서 속성 제거 | agent slug만 참조 | 드리프트 방지 |
| team_role은 Team.members에 | Agent 파일에 없음 | 같은 Agent가 팀마다 다른 역할 가능 |
| keys.json은 alias만 | 실제 값은 .env | keys.json 커밋 가능, 값 노출 없음 |
| auth는 Executor에 | Agent에서 override 가능 | 환경별 키 전략 분리 |

---

## 9. 미결 사항

- `agent-profiles/` 디렉터리 처리 — Executor로 완전 흡수 또는 `executor.agent_profile_ref`로 참조 유지 (1차 구현 후 결정)
- `coordination_prompt` — Team에 추가 여부 (실제 필요성 확인 후 결정)
- `/relay:migrate` 커맨드 — `backed_by` 인라인을 executor/agent 파일로 자동 변환 (선택적)
