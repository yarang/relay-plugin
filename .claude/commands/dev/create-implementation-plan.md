# /relay:dev:create-implementation-plan

DDL을 체크리스트 기반 구현 계획(PLAN)으로 변환합니다. **dev 도메인 전용**, **팀 리더 전용** 스킬입니다.

> ⭐ **PLAN 파일이 생성되는 유일한 시점입니다.** DDL이 FINAL 상태가 된 후 팀 리더가 명시적으로 이 스킬을 호출해야 합니다.

## 사전 확인

1. `domain-config.json` 에 `dev` 팩 포함 여부 확인
2. 대상 DDL 번호 확인 (예: `DDL-001`)
3. DDL 상태가 `FINAL` 인지 확인 — FINAL이 아니면 생성 중단

## 전략 선택

```
작업 전략을 선택하세요:

  [1] Checklist-first   — UI 수정, 설정, 단순 CRUD
  [2] Outside-In TDD    — 신규 API, 유스케이스
  [3] Inside-Out TDD    — 복잡한 도메인 규칙
  [4] DDD + TDD         — 신규 도메인, 비즈니스 로직
  [5] Contract-first    — 팀 간 API·이벤트 계약
  [6] Spike-first       — 기술 불확실성이 큰 작업
  [7] Risk-first        — 보안·성능·무결성 리스크
  [8] Vertical Slice    — end-to-end 기능 전달
```

## 저장 형식

파일: `.claude/relay/shared-context/implementation-plans/PLAN-{팀슬러그}-{DDL번호}.md`

```markdown
---
plan_id: PLAN-{팀슬러그}-{DDL번호}
ddl: DDL-{NNN}
team: {팀명}
strategy: {주전략}
secondary_strategies: [{보조 전략}]
reason: {전략 선택 근거}
exit_criteria: {완료 조건}
created_at: {YYYY-MM-DD}
---

# PLAN: {DDL 제목}

## 전략
주전략: {전략명}
보조: {보조 전략명}
근거: {선택 이유}
완료 조건: {기준}

## 구현 항목

### {기능 단위 1}
- [ ] 🔴 RED: {실패 테스트 작성}
- [ ] 🟢 GREEN: {최소 구현}
- [ ] 🔵 REFACTOR: {코드 정리 + 언어 정렬}

### {기능 단위 2}
- [ ] 🔴 RED: ...
```

## 완료 후

PLAN 파일 경로를 팀원들에게 공유하고 구현 단위를 배분합니다.
