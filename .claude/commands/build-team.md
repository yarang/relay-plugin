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

### 4. 전문가 목록 표시

`.claude/relay/experts/` 디렉토리의 전문가 파일을 읽어 아래 형식으로 표시합니다.

```text
사용 가능한 전문가:
  1. SNS 마케터 (sns-marketer)
     CLI: gemini-fast | 모델: gemini-3-flash-preview | Tier: trivial | Specs: 2

  2. 백엔드 개발자 (backend-dev)
     CLI: codex | 모델: gpt-5.3-codex | Tier: premium | Specs: 5

  3. 데이터 분석가 (data-analyst)
     CLI: gemini | 모델: gemini-3-pro-preview | Tier: standard | Specs: 0
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

멤버의 `cli`가 `setup-keys.md` 에서 설정된 키 목록에 없으면 **경고**.
`fallback_cli`가 있으면 자동 대체, 없으면 수동 변경 요청.

### 검증 5 — Phase 커버리지

모든 Phase(probe/grasp/tangle/ink) 에 최소 1명이 배정되어야 합니다.
미배정 Phase가 있으면 **경고**.

### 검증 6 — Tier 분산

premium 비율이 전체의 50% 초과 시 **경고** (비용 과다).

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
      "role": "{역할명}",
      "expert_slug": "{전문가 slug}",
      "cli": "{cli_variant}",
      "model": "{model_id}",
      "fallback_cli": "{cli_variant 또는 null}",
      "tier": "{trivial | standard | premium}",
      "permission_mode": "{plan | acceptEdits | default}",
      "memory": "{project | user | local}",
      "isolation": "{worktree | null}",
      "phases": ["probe", "grasp", "tangle", "ink"],
      "is_leader": false,
      "is_bridge": false
    }
  ],
  "phase_routing": {
    "probe": "{cli}",
    "grasp": "{cli}",
    "tangle": "{cli}",
    "ink": "{cli}"
  },
  "bridge_to": "{상위팀 slug 또는 null}",
  "created_at": "{YYYY-MM-DD}"
}
```

각 멤버의 `cli`, `model`, `fallback_cli`, `tier`, `permission_mode`, `phases` 값은 전문가 정의 파일에서 자동으로 읽어옵니다.

## 완료 후

팀 구성이 끝나면 다음 단계를 안내합니다.

- 상위팀: `steering-orchestrator` 에이전트 호출
- 하위팀: `team-leader` 에이전트 호출
- 구조 확인: `/relay:visualize-team` 으로 현재 팀 구조 도식화
