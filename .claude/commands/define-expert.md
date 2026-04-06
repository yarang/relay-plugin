# /relay:define-expert

전문가의 **기능 정의**를 작성하고 `.claude/relay/experts/` 에 저장합니다.

> **v0.6.0**: Expert는 역할 정의(페르소나, 역량, spec)만 담습니다.
> 실행 환경(CLI, 모델, phases, permission)은 `/relay:define-executor` → `/relay:define-agent` 에서 설정합니다.

## 사전 확인

`.claude/relay/domain-config.json` 이 없으면 `/relay:setup` 을 먼저 실행하도록 안내합니다.

## 대화 흐름

### 1. 역할 파악

> "어떤 전문가를 정의하시겠습니까?"

역할명과 분야를 파악합니다.

### 2. Domain 설정

> "이 전문가의 도메인을 선택하세요:"
> [1] general — 분석, 전략, 연구, 문서
> [2] development — 코드, 인프라, 보안

### 3. Spec 선택 — 이 전문가가 기본으로 사용할 기능 모듈

사용 가능한 spec 목록을 두 소스에서 읽어 표시합니다:

- **user scope**: 설치된 relay-plugin 캐시의 `modules/specs/` (구버전은 `capabilities/`)
- **project scope**: `{workspace}/.claude/relay/templates/modules/specs/`

```text
사용 가능한 Spec 모듈:
  [U] = user scope (읽기 전용)   [P] = project scope (커스텀)

  [U] rest-api         — REST API 엔드포인트 설계
  [U] crud             — CRUD 엔드포인트 구현
  [U] auth-jwt         — JWT 인증/인가
  [U] list-filter-sort — 목록 필터·정렬·페이지네이션
  ...

이 전문가에 연결할 spec을 선택하세요 (쉼표 구분 또는 번호):
```

- Spec을 선택하지 않으면 빈 배열(`specs: []`)로 저장합니다.
- `.claude/relay/templates/`가 없으면 이 단계를 건너뜁니다.

### 4. 페르소나·역량·제약 입력

역할명, 전문 분야, 소통 스타일, 할 수 있는 것, 하지 않는 것을 작성합니다.

### 5. 초안 확인 → 저장

## 저장 형식

파일: `.claude/relay/experts/{slug}.md`

```yaml
---
role: {역할명}
slug: {역할-슬러그}
domain: {general | development}
specs:
  - {spec-id}
created_at: {YYYY-MM-DD}
---

# {역할명}

## 페르소나
{직함, 전문 분야, 소통 스타일}

## 역량
- {할 수 있는 것}

## 제약
- {하지 않는 것}
```

## 완료 후

저장된 전문가를 실행하려면:

1. Executor 정의: `/relay:define-executor`
2. Agent 정의 (Expert + Executor 바인딩): `/relay:define-agent`
3. 팀 배치: `/relay:build-team`

기존 `backed_by` 방식 Expert 파일은 수정 없이 계속 사용 가능합니다 (마이그레이션 호환).
