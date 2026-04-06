# Agent Definition and Invocation

relay는 전문가(`expert`)와 실행 프로필(`agent definition`)을 분리해서 관리합니다.

- **전문가(expert)**: 팀 안에서의 역할, 권한, 보고 체계를 정의합니다.
- **agent definition**: 실제 실행에 필요한 공통 스킬과 플랫폼 선택을 정의합니다.

이 분리를 해두면 `backend developer` 같은 역할을 한 번 정의하고, 실행할 때만 `fastapi` 또는 `django` 를 선택할 수 있습니다.

---

## 조합 모델 요약

에이전트는 다음 5개 레이어를 순서대로 조합해서 구성됩니다.

```text
┌─────────────────────────────────────────────────────┐
│  task overlay       ← 이번 실행에서 추가된 지시사항    │
├─────────────────────────────────────────────────────┤
│  policy             ← 프로젝트 전용 규칙 (최우선)     │
├─────────────────────────────────────────────────────┤
│  platform           ← 실행 환경 (fastapi, nextjs…)   │
├─────────────────────────────────────────────────────┤
│  specs              ← 기능 모듈 (crud, auth-jwt…)    │
├─────────────────────────────────────────────────────┤
│  base               ← 역할 기본 책임                  │
└─────────────────────────────────────────────────────┘
```

**우선순위 규칙**: 위로 올라갈수록 아래 레이어를 덮어씁니다.

```
task overlay > policy > platform > capability > base
```

충돌 시 항상 상위 레이어의 규칙을 따릅니다.

---

## 1. 관리 원칙

- 공통 능력은 `capability` 모듈로 분리합니다.
- 프레임워크 차이는 `platform` 모듈로 분리합니다.
- 프로젝트 규칙은 `policy` 모듈로 분리합니다.
- 실행마다 어떤 조합을 썼는지 `run` 기록을 남깁니다.
- 전문가 파일은 팀 구조와 권한을 설명하고, 조합형 정의는 런타임 구성을 설명합니다.
- 공통 capability에 프레임워크 구현 세부사항을 넣지 않습니다.
- 전문가 분리 기준은 "작업 공간"입니다 (외부 서비스 vs 서버 내부 vs 코드).

---

## 2. 저장 구조

```text
.claude/relay/
├── experts/              ← 전문가 파일 (역할·권한·팀 구조)
├── teams/                ← 팀 구성 파일
├── shared-context/       ← 공유 컨텍스트 (design-decisions/ 등)
└── agent-library/
    ├── definitions/      ← 조합형 에이전트 정의 파일
    ├── modules/
    │   ├── base/         ← 역할 기본 책임
    │   ├── specs/        ← 기능 모듈
    │   ├── platforms/    ← 실행 환경
    │   └── policies/     ← 프로젝트 규칙
    └── runs/             ← 실행 이력
```

---

## 3. Agent Definition 형식

파일 위치: `.claude/relay/agent-library/definitions/{agent-id}.md`

```markdown
---
id: backend-developer
kind: composed-agent
owner: relay
version: 1
base: backend-core
specs:
  - rest-api
  - crud
  - list-filter-sort
available_platforms:
  - fastapi
  - django
default_policy: project-default
default_agent: relay:developer
---

# backend-developer

## Purpose
백엔드 기능 구현, API 설계, CRUD, 목록 조회, 검증, 에러 처리 담당.

## Runtime Rules
- 플랫폼은 한 번에 하나만 선택한다.
- `policy` 는 프로젝트 규칙이므로 항상 마지막에 덮어쓴다.
- 실행 결과는 runs 디렉토리에 남긴다.
```

---

## 4. Module 형식

### base

역할의 핵심 책임을 정의합니다. 다른 에이전트와 중복되지 않는 고유 역할 영역을 기술합니다.

```markdown
---
id: backend-core
type: base
version: 1
scope: [backend]
---

## Responsibilities
- API 설계
- CRUD 구현
- list/filter/sort/pagination
- validation
- error handling
```

### capability

재사용 가능한 기능 단위입니다. 하나의 capability는 하나의 기능에만 집중합니다.

```markdown
---
id: crud
type: capability
version: 1
scope: [backend]
requires: [rest-api]
conflicts_with: []
---
```

`requires` 에 나열된 capability는 자동으로 함께 로드됩니다.
`conflicts_with` 에 나열된 capability와는 함께 사용할 수 없습니다.

### platform

실행 환경 또는 프레임워크를 정의합니다. 같은 domain 내에서는 한 번에 하나만 선택합니다.

```markdown
---
id: fastapi
type: platform
version: 1
scope: [backend, python]
requires: []
conflicts_with: [django]
---

## Implementation Notes
- APIRouter 사용
- Pydantic request/response 모델 사용
- dependency injection 과 service 분리
```

### policy

프로젝트 전용 규칙입니다. 다른 모든 레이어보다 우선하며, 팀 전체에 공통 적용됩니다.

```markdown
---
id: project-default
type: policy
version: 1
scope: [project]
---

## Rules
- 기존 디렉토리 구조를 우선 유지한다.
- 테스트를 먼저 보강한다.
- 위험한 마이그레이션은 별도 승인 없이 수행하지 않는다.
```

---

## 5. Expert 와의 연결

전문가 파일에는 실행 프로필 연결 정보를 추가할 수 있습니다.

```markdown
---
role: 백엔드 개발자
slug: backend-dev
domain: development
backed_by: relay:developer
agent_profile: backend-developer
default_platform: fastapi
created_at: 2026-03-28
---
```

| 필드 | 의미 |
|---|---|
| `backed_by` | 실제 실행에 사용할 에이전트 백엔드 (relay:*, gemini:*, codex:*, zai:*) |
| `agent_profile` | 조합형 definition ID |
| `default_platform` | 호출 시 platform을 지정하지 않으면 이 값을 사용 |

---

## 6. 조립 순서

`/relay:invoke-agent` 호출 시 다음 순서로 조립합니다.

```text
1. expert 파일 또는 definition 파일 로드
2. base 로드
3. capabilities 로드 (requires 체인 포함)
4. 선택된 platform 로드
5. policy 로드  ← 이 시점에서 충돌 항목은 policy가 덮어씀
6. task overlay 결합  ← 이번 실행 전용 지시사항 추가
7. backed_by 또는 default_agent 로 실행
8. run 로그 저장
```

호출 예시:

```text
/relay:invoke-agent
target: backend-dev
platform: fastapi
task: 주문 목록 조회 API와 생성 API를 추가하고 테스트를 보강한다.
```

결과적으로 로드되는 조합:

```text
backend-core
+ rest-api
+ crud
+ list-filter-sort
+ fastapi
+ project-default  (policy)
+ task overlay
```

---

## 7. 충돌 해결 규칙

| 상황 | 처리 방법 |
|---|---|
| `policy` 가 `base` 규칙과 충돌 | `policy` 우선 |
| `policy` 가 `capability` 와 충돌 | `policy` 우선 |
| 두 capability가 서로 `conflicts_with` | 나중에 로드된 capability 제거, 경고 출력 |
| 같은 `platform` 이 두 번 지정 | 첫 번째 적용, 두 번째 무시 |
| `platform` 이 `conflicts_with` 내 플랫폼과 충돌 | 호출 시점에 오류 반환 |
| task overlay 가 policy 와 충돌 | task overlay 우선 (단발성 override) |

---

## 8. Run 로그 형식

파일 위치: `.claude/relay/agent-library/runs/{timestamp}-{target}.md`

```markdown
---
target: backend-dev
definition: backend-developer
resolved_agent: relay:developer
platform: fastapi
specs:
  - rest-api
  - crud
  - list-filter-sort
policy: project-default
started_at: 2026-03-28T10:00:00+09:00
status: completed
---

# Task
주문 목록 조회 API와 생성 API를 추가하고 테스트를 보강한다.

## Result
- app/api/orders.py 수정
- tests/api/test_orders.py 수정
```

---

## 9. blog-system 검증 예시 (v1 실제 구성)

blog-system 프로젝트에서 검증된 조합형 구성입니다.

### 모듈 인벤토리

```text
base (8):
  backend-core, frontend-core, desktop-core,
  server-core, infra-core, specialist-core,
  reviewer-core, qa-core

specs (17):
  rest-api, crud, auth-jwt, list-filter-sort, markdown-renderer,
  docker-management, postgres-admin, nginx-config, dns-management,
  ssl-certificates, rate-limiting, security-audit, code-review,
  system-design, context-compression,
  test-strategy, research-analysis

platforms (5):
  fastapi, nextjs, ubuntu, cloudflare, postgresql

policies (1):
  blog-default
```

### Definition 예시 (backend-developer)

```yaml
# definitions/backend-developer.md
id: backend-developer
kind: composed-agent
owner: relay
version: 1
base: backend-core
specs:
  - rest-api
  - crud
  - auth-jwt
  - list-filter-sort
  - markdown-renderer
available_platforms:
  - fastapi
default_policy: blog-default
default_agent: relay:developer-zai
```

### Definition 예시 (infra-network-admin)

```yaml
# definitions/infra-network-admin.md
id: infra-network-admin
kind: composed-agent
owner: relay
version: 1
base: infra-core
specs:
  - dns-management
  - ssl-certificates
  - rate-limiting
available_platforms:
  - cloudflare
default_policy: blog-default
default_agent: gemini:gemini-2.5-flash
```

### 모델 분포

```text
relay:developer-zai (GLM-5.1)  → 10명  구현, 리뷰, 서버 관리
gemini:gemini-2.5-flash         →  2명  인프라 네트워크, 시스템 설계
codex:gpt-4o                    →  1명  보안 감사
zai:glm-4                       →  1명  컨텍스트 압축
```

### Expert → Definition 매핑

```text
expert slug              → definition id          → platform
─────────────────────────────────────────────────────────────
backend-dev              → backend-developer       → fastapi
backend-tech-lead        → backend-tech-lead       → fastapi
frontend-dev             → frontend-developer      → nextjs
frontend-tech-lead       → frontend-tech-lead      → nextjs
desktop-dev              → desktop-developer       → tauri
desktop-tech-lead        → desktop-tech-lead       → tauri
database-arch            → database-architect      → postgresql
designer-gemini          → system-designer         → fastapi
security-auditor-openai  → security-auditor        → fastapi
server-admin             → server-administrator    → ubuntu
infra-network            → infra-network-admin     → cloudflare
tech-lead-zai            → tech-lead               → null
ux-designer              → ux-designer             → null
context-compressor       → context-compressor      → markdown
qa-engineer              → qa-engineer             → null
researcher               → researcher              → null
reviewer                 → reviewer                → null
specialist               → specialist              → null
devops-engineer          → devops-engineer         → null
```

### 템플릿 위치

모든 definition과 module 템플릿은 플러그인의 `docs/templates/` 에 있습니다.

```text
docs/templates/
├── definitions/     ← 에이전트 정의 템플릿
└── modules/
    ├── base/        ← 역할 기본 책임
    ├── specs/       ← 기능 모듈
    ├── platforms/   ← 실행 환경
    └── policies/    ← 프로젝트 규칙
```

새 프로젝트에서는 이 템플릿을 `.claude/relay/agent-library/` 에 복사하여 시작합니다.

---

## 10. 운영 규칙 요약

| 규칙 | 내용 |
|---|---|
| platform 선택 | 한 번에 하나만 선택 |
| 충돌 우선순위 | task overlay > policy > platform > capability > base |
| policy 범위 | 프로젝트 전체에 공통 적용, 다른 프로젝트는 별도 policy |
| run 기록 | 실행 이력과 디버깅 근거로 유지 |
| capability 세부사항 | 프레임워크 구현 세부사항은 platform 모듈에 기술 |
| 전문가 분리 기준 | 작업 공간 기준 (외부 서비스 / 서버 내부 / 코드) |
| platform이 없는 에이전트 | QA, 리뷰어, 리서처 등 도메인에 종속되지 않는 역할은 `null` |
