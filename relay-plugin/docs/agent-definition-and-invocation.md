# Agent Definition And Invocation

relay는 전문가(`expert`)와 실행 프로필(`agent definition`)을 분리해서 관리합니다.

- 전문가는 팀 안에서의 역할, 권한, 보고 체계를 정의합니다.
- agent definition은 실제 실행에 필요한 공통 스킬과 플랫폼 선택을 정의합니다.

이 분리를 해두면 `backend developer` 같은 역할을 한 번 정의하고, 실행할 때만 `fastapi` 또는 `django` 를 선택할 수 있습니다.

## 1. 관리 원칙

- 공통 능력은 `capability` 모듈로 분리합니다.
- 프레임워크 차이는 `platform` 모듈로 분리합니다.
- 프로젝트 규칙은 `policy` 모듈로 분리합니다.
- 실행마다 어떤 조합을 썼는지 `run` 기록을 남깁니다.
- 전문가 파일은 팀 구조와 권한을 설명하고, 조합형 정의는 런타임 구성을 설명합니다.

## 2. 저장 구조

relay는 다음 디렉토리 구조를 기준으로 관리합니다.

```text
.claude/relay/
├── experts/
├── teams/
├── shared-context/
└── agent-library/
    ├── definitions/
    ├── modules/
    │   ├── base/
    │   ├── capabilities/
    │   ├── platforms/
    │   └── policies/
    └── runs/
```

## 3. Agent Definition 형식

파일 위치:

```text
.claude/relay/agent-library/definitions/{agent-id}.md
```

권장 형식:

```markdown
---
id: backend-developer
kind: composed-agent
owner: relay
version: 1
base: backend-core
capabilities:
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

## 4. Module 형식

### base

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

### platform

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

의미는 다음과 같습니다.

- `backed_by`: 실제 실행에 사용할 에이전트 백엔드
- `agent_profile`: 조합형 definition ID
- `default_platform`: 기본 플랫폼

## 6. 호출 규약

호출은 `/relay:invoke-agent` 로 통일합니다.

입력값:

- 대상 전문가 slug 또는 definition id
- task 설명
- 필요 시 platform override
- 필요 시 capability 추가/제외

조립 순서:

1. expert 파일 또는 definition 파일 로드
2. `base` 로드
3. `capabilities` 로드
4. 선택된 `platform` 로드
5. `policy` 로드
6. task overlay 결합
7. `backed_by` 또는 `default_agent` 로 실행
8. run 로그 저장

## 7. Backend Developer 예시

정의:

```text
definition: backend-developer
base: backend-core
capabilities: rest-api, crud, list-filter-sort
platforms: fastapi, django
default_agent: relay:developer
```

호출 예시 1:

```text
/relay:invoke-agent
target: backend-dev
platform: fastapi
task: 주문 목록 조회 API와 생성 API를 추가하고 테스트를 보강한다.
```

이 경우 로드되는 조합:

```text
backend-core
+ rest-api
+ crud
+ list-filter-sort
+ fastapi
+ project-default
+ task overlay
```

호출 예시 2:

```text
/relay:invoke-agent
target: backend-developer
platform: django
task: 관리자용 상품 CRUD endpoint를 구현한다.
```

## 8. Run 로그 형식

파일 위치:

```text
.claude/relay/agent-library/runs/{timestamp}-{target}.md
```

권장 형식:

```markdown
---
target: backend-dev
definition: backend-developer
resolved_agent: relay:developer
platform: fastapi
capabilities:
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

## 9. blog-system 검증 예시 (v1 실제 구성)

blog-system 프로젝트에서 검증된 조합형 구성입니다.

### 모듈 인벤토리

```text
base (6):
  backend-core, frontend-core, desktop-core,
  server-core, infra-core, specialist-core

capabilities (15):
  rest-api, crud, auth-jwt, list-filter-sort, markdown-renderer,
  docker-management, postgres-admin, nginx-config, dns-management,
  ssl-certificates, rate-limiting, security-audit, code-review,
  system-design, context-compression

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
capabilities:
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
capabilities:
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
```

### 템플릿 위치

모든 definition과 module 템플릿은 플러그인의 `docs/templates/` 에 있습니다:

```text
docs/templates/
├── definitions/     ← 14개 에이전트 정의
└── modules/
    ├── base/            ← 6개 기본 책임
    ├── capabilities/    ← 15개 기능 모듈
    ├── platforms/       ← 5개 실행 환경
    └── policies/        ← 1개 프로젝트 규칙
```

새 프로젝트에서는 이 템플릿을 `.claude/relay/agent-library/` 에 복사하여 시작합니다.

## 10. 운영 규칙

- platform은 기본적으로 하나만 선택합니다.
- `policy` 가 `base` 나 `capability` 와 충돌하면 `policy` 를 우선합니다.
- 동일 역할이라도 프로젝트가 다르면 별도 policy를 둡니다.
- runs 디렉토리는 실행 이력과 디버깅 근거로 유지합니다.
- 공통 capability에 프레임워크 구현 세부사항을 넣지 않습니다.
- 전문가 분리 기준은 "작업 공간"입니다 (외부 서비스 vs 서버 내부 vs 코드).
