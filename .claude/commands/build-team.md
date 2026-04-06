# /relay:build-team

정의된 전문가들을 조합해 팀을 구성하고 `.claude/relay/teams/` 에 저장합니다.

## 사전 확인

- `.claude/relay/domain-config.json` 없으면 `/relay:setup` 안내
- `.claude/relay/experts/` 가 비어 있으면 `/relay:define-expert` 안내

## 대화 흐름

### 1. 팀 이름·목적 입력

### 2. 계층 위치 선택

> [1] upper — 아키텍처·도메인 설계, 팀 간 조율 (teammate 모드, 병렬 실행)
> [2] lower — 실제 구현, 기능 단위 개발 (inprocess 모드, 순차 실행)

### 3. Coordinator 선택

> [1] claude — 고품질 의사결정 (기본값)
> [2] glm    — 저비용 대량 처리

### 4. Agent 목록 표시

`.claude/relay/agents/` 디렉토리의 Agent 파일을 읽어 아래 형식으로 표시합니다.
Agent 파일이 없으면 Expert 파일 목록으로 fallback (마이그레이션 호환).

```text
사용 가능한 Agent:
  1. backend-dev          (expert: backend-developer)
     Executor: codex_gpt_5.4 | CLI: codex | Model: gpt-5.4 | Phases: tangle, ink

  2. backend-dev-budget   (expert: backend-developer)
     Executor: zai_glm_4_air  | CLI: zai   | Model: glm-4-air | Phases: tangle

  3. data-analyst         (expert: data-analyst)
     Executor: gemini_flash_3  | CLI: gemini-fast | Model: gemini-3-flash | Phases: probe, grasp
```

### 5. 팀원 선택

리더 1명 필수. 번호 또는 쉼표 구분으로 입력합니다.

### 6. 의사결정 방식 선택

> [1] leader\_decides  — 리더가 최종 결정 (하위팀 기본값)
> [2] consensus       — 전원 합의
> [3] vote            — 다수결
> [4] architect\_veto — 아키텍트 거부권 (상위팀 기본값)

### 7. 하위팀인 경우 — 상위팀 bridge\_to 설정

### 8. 6종 검증 실행

검증 결과를 요약해 표시합니다. 경고는 계속 진행 가능하며, 오류는 수정 후 재시도합니다.

```text
검증 결과:
  [OK] 필수 역할 충족
  [OK] 팀 크기: 3명 (상위팀 권장: 3-5명)
  [WARN] 역할 중복: 백엔드 개발자 2명
  [OK] CLI 가용성
  [WARN] Phase 커버리지: probe 단계 담당자 없음
  [OK] Tier 분산: premium 33%
```

### 9. 초안 확인 → 저장

## 6종 검증 규칙

### 검증 1 — 필수 역할 충족

| 팀 유형 | 필수 역할 |
| --- | --- |
| upper | 오케스트레이터(리더) + 아키텍트 + 서기 |
| lower | 리더 + 개발자 최소 1명 |

미충족 시 **오류** — 저장 불가.

### 검증 2 — 팀 크기

| 팀 유형 | 최소 | 최대 | 권장 |
| --- | --- | --- | --- |
| upper | 2 | 8 | 3–5 |
| lower | 2 | 6 | 2–4 |

범위 초과 시 **오류**, 권장 범위 밖이면 **경고**.

### 검증 3 — 역할 중복

같은 카테고리 내 동일 역할이 2명 이상이면 **경고**.

### 검증 4 — CLI 가용성

멤버의 Agent → Executor → cli 체인을 따라 CLI 가용성을 확인합니다.
`member.agent` → `agents/{slug}.md` → `execute_by` → `executors/{slug}.md` → `cli`.
Executor의 `fallback`이 있으면 자동 대체, 없으면 수동 변경 요청.
마이그레이션 호환: Agent 없이 Expert의 `backed_by`를 직접 사용하는 경우도 검증합니다.

### 검증 5 — Phase 커버리지

모든 Phase(probe/grasp/tangle/ink) 에 최소 1명이 배정되어야 합니다.
미배정 Phase가 있으면 **경고**.

### 검증 6 — 비용 집중도

팀 내 Executor의 모델 분포를 분석합니다.
고비용 모델(flagship/reasoning급)이 전체의 50% 초과 시 **경고** (비용 과다).
저비용 모델(mini/flash/zai급) 없이 전원 고비용 모델 사용 시 **경고**.
`tier` 필드는 v0.6.0에서 제거됩니다 — Executor의 `model`로 비용 추론합니다.

## 팀 유형

| 유형 | execution\_mode | 역할 | 기본 의사결정 |
| --- | --- | --- | --- |
| upper | `teammate` | 아키텍처·도메인 설계, 팀 간 조율 | `architect_veto` |
| lower | `inprocess` | 실제 구현, 기능 단위 개발 | `leader_decides` |

- **upper**: 멤버들이 Agent Teams로 스폰되어 병렬 실행됩니다. `SendMessage`로 팀 내 통신합니다.
- **lower**: team-leader 세션 내에서 CLI 직접 호출로 순차 실행됩니다.

## 저장 형식

파일: `.claude/relay/teams/{팀-슬러그}.json`

```json
{
  "name": "{팀명}",
  "slug": "{팀-슬러그}",
  "type": "upper | lower",
  "execution_mode": "teammate | inprocess",
  "coordinator": "claude | glm",
  "coordinator_model": "claude-opus-4-6 | glm-4-air",
  "purpose": "{팀 목적}",
  "decision_mode": "leader_decides | consensus | vote | architect_veto",
  "members": [
    {
      "agent": "{agent-slug}",
      "role": "{팀 내 표시 역할명}",
      "is_leader": false,
      "is_bridge": false
    }
  ],
  "phase_routing": {
    "probe": "{executor-slug}",
    "grasp": "{executor-slug}",
    "tangle": "{executor-slug}",
    "ink": "{executor-slug}"
  },
  "bridge_to": "{상위팀 slug 또는 null}",
  "created_at": "{YYYY-MM-DD}"
}
```

멤버는 `agent` slug만 참조합니다. 실행 속성(cli, model, permission 등)은 Agent/Executor 파일에서 읽습니다.
`phase_routing` 값은 Executor slug를 사용합니다.
마이그레이션 호환: Agent 파일 없이 Expert의 `backed_by`를 직접 사용하는 멤버는 `expert_slug` 필드로 저장됩니다.

## 완료 후

팀 구성이 끝나면 다음 단계를 안내합니다.

- 상위팀: `steering-orchestrator` 에이전트 호출
- 하위팀: `team-leader` 에이전트 호출
- 구조 확인: `/relay:visualize-team` 으로 현재 팀 구조 도식화
