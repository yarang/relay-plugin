# Team Building Rules

> 전문가 정의부터 팀 구축까지의 규칙. coordinator-hybrid-rules.md 와 함께 적용됩니다.

---

## 1. 전문가 정의 기준

### 1.1 역할 분류 매트릭스

역할을 정의할 때 아래 기준에 따라 Executor 추천과 Agent 기본값을 배정합니다.

> **v0.6.0**: CLI/모델은 Executor 파일에, phases/permission은 Agent 파일에 설정합니다.
> 아래 표는 권장 기본값입니다.

| 역할 카테고리 | 추천 Executor | 추천 Phases | 추천 Permission |
| --- | --- | --- | --- |
| **아키텍트** | `codex_gpt_5.4` | grasp | plan |
| **백엔드 개발자** | `codex_gpt_5.4` | tangle | acceptEdits |
| **프론트엔드 개발자** | `codex_gpt_5.4` | tangle | acceptEdits |
| **DB 설계자** | `codex_gpt_5.4` | grasp | plan |
| **TDD 오케스트레이터** | `codex_gpt_5.4` | tangle | acceptEdits |
| **QA 엔지니어** | `codex_spark` | ink | default |
| **코드 리뷰어** | `codex_spark` | ink | default |
| **보안 감사** | `codex_gpt_5.4` | ink | default |
| **DevOps** | `codex_gpt_5.4` | ink | acceptEdits |
| **디버거** | `codex_gpt_5.4` | tangle, ink | acceptEdits |
| **AI 엔지니어** | `gemini_pro` | probe, tangle | plan |
| **UX 리서처** | `gemini_pro` | probe, grasp | plan |
| **비즈니스 분석가** | `gemini_pro` | probe, grasp | plan |
| **마케팅 전략가** | `gemini_pro` | probe, grasp | plan |
| **재무 분석가** | `gemini_pro` | probe, grasp | plan |
| **법무 고문** | `gemini_pro` | probe, grasp | plan |
| **문서 설계자** | `gemini_flash` | ink | default |
| **컨텍스트 관리자** | `gemini_flash` | all | plan |
| **다이어그램 전문가** | `gemini_flash` | grasp, ink | plan |
| **전략 분석가** | `claude_opus` | probe, grasp | plan |
| **연구 종합가** | `claude_opus` | probe | plan |
| **Python 전문가** | `codex_gpt_5.4` | tangle | acceptEdits |
| **TypeScript 전문가** | `codex_gpt_5.4` | tangle | acceptEdits |
| **GLM 범용 작업자** | `zai_glm_4_air` | all | acceptEdits |
| **GLM 경량 작업자** | `zai_glm_4_flash` | all | acceptEdits |

### 1.2 CLI 선택 기준

```
작업 성격 → CLI 매핑:

정밀한 코드 생성/수정  → codex        (추론 + 코드 품질 최고)
빠른 피드백/리뷰       → codex-spark  (15x 빠름, 품질 약간 낮음)
저비용 대량 처리        → codex-mini   (비용 효율)
심층 추론/의사결정      → codex-reasoning (o3)
대형 코드베이스 분석    → codex-large-context (1M 컨텍스트)
연구/분석/멀티모달     → gemini       (이미지 분석, 긴 컨텍스트)
빠른 처리/실시간       → gemini-fast  (속도 우선)
최고 품질 전략/설계    → claude-opus  (비용最高, 품질最高)
저비용 범용            → zai          (GLM, 비용 최저)
```

### 1.3 Permission Mode 분류

| Mode | 도구 접근 | 사용 시점 |
| --- | --- | --- |
| `plan` | Read, Glob, Grep, WebSearch | 연구, 분석, 설계 (파일 수정 불가) |
| `acceptEdits` | Read + Write + Edit + Bash | 구현, 디버깅, 테스트 (파일 수정 가능) |
| `default` | 전체 도구 | 리뷰, 배포, 관리 (모든 도구) |

---

## 2. 팀 구축 규칙

### 2.1 팀 유형별 필수 역할

**상위팀 (upper / teammate):**

| 필수 역할 | 수 | 추천 Executor | 설명 |
| --- | --- | --- | --- |
| 오케스트레이터 | 1 | — | Claude Code 리더 (steering-orchestrator) |
| 아키텍트 | 1+ | `codex_gpt_5.4` | 기술 설계 결정 |
| 분석가 | 0+ | `gemini_pro` | 연구·분석 (선택) |
| 회의 서기 | 1 | — | meeting-recorder (haiku) |

**하위팀 (lower / inprocess):**

| 필수 역할 | 수 | 추천 Executor | 설명 |
| --- | --- | --- | --- |
| 팀 리더 | 1 | — | Claude Code 리더 (team-leader) |
| 개발자 | 1+ | `codex_gpt_5.4` | 구현 담당 |
| 리뷰어 | 0+ | `codex_spark` | 코드 리뷰 (선택) |

### 2.2 팀 크기 제한

| 팀 유형 | 최소 | 최대 | 권장 |
| --- | --- | --- | --- |
| 상위팀 | 3 (오케스트레이터 + 아키텍트 + 서기) | 8 | 4~6 |
| 하위팀 | 2 (리더 + 개발자) | 6 | 3~4 |

### 2.3 브릿지 멤버 규칙

- 하위팀 리더(team-leader)는 상위팀의 **브릿지 멤버**로 자동 참여합니다.
- 브릿지 멤버는 상위팀에서 **발언권만** 가지며, 하위팀에 **결정을 전달**합니다.
- 하위팀 리더는 상위팀 결정을 **거부할 수 없습니다** (에스컬레이션만 가능).

### 2.4 역할 중복 방지

같은 팀 내에서 아래 조합은 **중복 경고**를 표시합니다:

| 충돌 조합 | 이유 | 해결 |
| --- | --- | --- |
| 아키텍트 2명 이상 | 설계 결정 충돌 | 1명만 지정 |
| 같은 phase 담당 3명 이상 | 병목 | Phase 분산 |
| 같은 Executor + 같은 역할 | 중복 실행 | Executor 분산 |
| 백엔드 개발자 + 풀스택 개발자 | 책임 중복 | 역할 명확화 |

---

## 3. 팀 구성 파일 스키마

### 3.1 Expert 파일 (기능 정의)

```yaml
# .claude/relay/experts/{slug}.md
---
role: {역할명}
slug: {역할-슬러그}
domain: {general | development}
specs:
  - {spec-id}              # 기본 spec 모듈 ID 목록
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

### 3.2 Executor 파일 (실행 설정)

```yaml
# .claude/relay/executors/{slug}.md
---
slug: {slug}
cli: {cli-variant}
model: {model-id}
fallback: {executor-slug 또는 null}
auth:
  pool: [{key-alias}, ...]
  strategy: fallback | round_robin | random
---
```

### 3.3 Agent 파일 (실행 인스턴스)

```yaml
# .claude/relay/agents/{slug}.md
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
created_at: {YYYY-MM-DD}
---
```

### 3.4 팀 구성 파일

```json
// .claude/relay/teams/{slug}.json
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

---

## 4. 빌드 플로우

### 4.1 /relay:build-team 실행 시 검증

팀 구성 완료 전 아래 검증을 수행합니다:

```
검증 1: 필수 역할 충족 여부
  → 상위팀: 오케스트레이터 + 아키텍트 + 서기
  → 하위팀: 리더 + 개발자

검증 2: 팀 크기 제한
  → 상위팀: 3~8명
  → 하위팀: 2~6명

검증 3: 역할 중복
  → 같은 카테고리 내 중복 경고

검증 4: CLI 가용성
  → members 의 cli 가 설치되어 있는지 확인
  → 미설치 시 fallback_cli 로 자동 대체

검증 5: Phase 커버리지
  → 모든 phase (probe/grasp/tangle/ink) 가 최소 1명에게 할당되었는지 확인

검증 6: Tier 분산
  → premium 이 전체의 50% 초과 시 경고
```

### 4.2 빌드 흐름도

```
1. 팀 이름·목적 입력
2. 계층 선택: upper(상위팀) / lower(하위팀)
3. coordinator 선택: claude / glm
4. 전문가 목록 표시 (cli, tier, phase 포함)
5. 팀원 선택 (드래그앤드롭 또는 번호)
   → 선택 시 자동으로 cli, tier, permission_mode 표시
6. 의사결정 방식 선택
7. 하위팀인 경우: 상위팀 bridge_to 설정
8. 검증 6종 실행
9. 결과 표시 + 확인
10. .claude/relay/teams/{slug}.json 저장
```

---

## 5. 의사결정 방식

| 방식 | 설명 | 적합 상황 |
|---|---|---|
| `leader_decides` | 리더가 최종 결정 | 하위팀 기본값, 빠른 실행 |
| `consensus` | 전원 합의 필요 | 소규모 팀, 중요 설계 |
| `vote` | 다수결 | 의견 분산 시 |
| `architect_veto` | 아키텍트 거부권 | 상위팀 기본값, 기술 결정 |
