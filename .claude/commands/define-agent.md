# /relay:define-agent

Expert + Executor를 바인딩하여 실행 인스턴스(Agent)를 정의하고 `.claude/relay/agents/` 에 저장합니다.

Agent는 "이 전문가를 어떤 실행 환경으로, 어떤 권한으로 운용하는가"를 정의합니다.

## 사전 확인

- `.claude/relay/domain-config.json` 없으면 `/relay:setup` 안내
- `.claude/relay/experts/` 가 비어 있으면 `/relay:define-expert` 안내
- `.claude/relay/executors/` 가 비어 있으면 `/relay:define-executor` 안내

## 대화 흐름

### 1. Agent Slug 입력

```text
예시:
  backend-dev           ← 단일 인스턴스
  backend-dev-budget    ← 저비용 버전
  backend-dev-review    ← 리뷰 전용
```

### 2. Expert 선택

`.claude/relay/experts/` 목록을 표시합니다.

```text
사용 가능한 Expert:
  [1] Backend Developer       (backend-developer)   specs: rest-api, crud, auth-jwt
  [2] Frontend Developer      (frontend-developer)  specs: component-design
  [3] Security Auditor        (security-auditor)    specs: security-audit
```

### 3. Executor 선택

`.claude/relay/executors/` 목록을 표시합니다.

```text
사용 가능한 Executor:
  [1] codex_gpt_5.4       cli: codex   model: gpt-5.4        auth: openai_primary, openai_secondary
  [2] codex_default       alias: codex_gpt_5.4
  [3] zai_glm_4_air       cli: zai     model: glm-4-air       auth: glm_free
  [4] claude_sonnet_4.6   cli: claude  model: claude-sonnet-4-6
```

### 4. Definition 선택 (선택 — 5-layer 조합 필요 시)

`.claude/relay/agent-library/definitions/` 목록을 표시합니다.

```text
정의 파일 (5-layer 조합):
  [1] backend-developer   base: backend-core, specs: rest-api+crud+auth-jwt, platform: fastapi
  [2] frontend-developer  base: frontend-core, specs: component-design, platform: nextjs
  [skip] 사용 안 함 (Expert.specs만 사용)
```

Definition을 선택하면 Definition.specs가 Expert.specs를 override합니다.

### 5. Phases 배정

```text
이 Agent가 담당할 Phase를 선택하세요:
  [ ] probe   — 연구, 요구사항 분석
  [ ] grasp   — 설계, 아키텍처
  [ ] tangle  — 구현, 개발
  [ ] ink     — 리뷰, 배포
```

### 6. Permission Mode 설정

```text
[1] plan         — 읽기 전용 (연구, 설계)
[2] acceptEdits  — 파일 수정 가능 (구현, 디버깅)
[3] default      — 전체 도구 (리뷰, 배포)
```

### 7. Memory 설정

```text
[1] project  — 코드베이스 전체 학습 (기본값)
[2] user     — 사용자 설정, 크로스 프로젝트
[3] local    — 현재 세션만
```

### 8. Isolation 설정

```text
[1] worktree  — git worktree 격리 (파일 충돌 방지)
[2] null      — 격리 없음 (기본값)
```

### 9. Auth Override 설정 (선택)

이 Agent에서만 다른 키 풀을 사용하려면 입력합니다. 없으면 Enter.

```text
Executor auth pool을 override할 key alias (쉼표 구분, 없으면 Enter):
> openai_team
```

### 10. 초안 확인 → 저장

## 저장 형식

파일: `.claude/relay/agents/{slug}.md`

```yaml
---
slug: {slug}
expert: {expert-slug}
execute_by: {executor-slug}
definition: {definition-id 또는 null}
phases:
  - {phase}
permission_mode: {plan | acceptEdits | default}
memory: {project | user | local}
isolation: {worktree | null}
auth_override:
  pool: [{key-alias}]      # 선택 — 없으면 이 필드 생략
created_at: {YYYY-MM-DD}
---
```

## 마이그레이션 호환

기존 `backed_by` 필드를 가진 Expert 파일은 Agent 파일 없이도 동작합니다.

```
invoke-agent 호출 시:
  Agent 파일 있음 → execute_by Executor 사용
  Agent 파일 없음 + Expert.backed_by 있음 → 인라인 executor로 파싱
  둘 다 없음 → 오류
```

## 완료 후

Agent를 팀에 배치하려면: `/relay:build-team`
Agent를 직접 실행하려면: `/relay:invoke-agent {agent-slug} "작업 내용"`
