# /relay:build-team

정의된 전문가들을 조합해 팀을 구성하고 `.claude/relay/teams/` 에 저장합니다.

## 사전 확인

- `.claude/relay/domain-config.json` 없으면 `/relay:setup` 안내
- `.claude/relay/experts/` 가 비어 있으면 `/relay:define-expert` 안내

## 대화 흐름

```
1. 팀 이름·목적 질문
2. 계층 위치 선택: upper(상위팀) / lower(하위팀)
3. 사용 가능한 전문가 목록 표시
4. 팀원 선택 (리더 1명 필수)
5. 의사결정 방식 선택
6. 하위팀인 경우: 상위팀 브릿지 멤버 설정
7. 초안 확인 → 저장
```

## 전문가 목록 표시

`.claude/relay/experts/` 디렉토리의 전문가 파일을 읽어 목록을 표시합니다.

```
사용 가능한 전문가:
  1. SNS 마케터 (sns-marketer)
     CLI: gemini-fast | 모델: gemini-3-flash-preview | Tier: trivial
     
  2. 백엔드 개발자 (backend-dev)
     CLI: codex | 모델: gpt-5.3-codex | Tier: premium
     
  3. 데이터 분석가 (data-analyst)
     CLI: gemini | 모델: gemini-3-pro-preview | Tier: standard
```

## 팀 유형

| 유형 | execution_mode | 역할 | 의사결정 방식 예시 |
|---|---|---|---|
| upper | `teammate` | 아키텍처·도메인 설계, 팀 간 조율 | `architect_veto` |
| lower | `inprocess` | 실제 구현, 기능 단위 개발 | `leader_decides` / `consensus` |

- **upper (teammate)**: 멤버들이 Agent Teams 로 스폰되어 병렬 실행됩니다. `SendMessage` 로 팀 내 통신합니다.
- **lower (inprocess)**: team-leader 세션 내에서 CLI 직접 호출로 순차 실행됩니다.

## 저장 형식

파일: `.claude/relay/teams/{팀-슬러그}.json`

```json
{
  "name": "{팀명}",
  "slug": "{팀-슬러그}",
  "type": "upper | lower",
  "execution_mode": "teammate | inprocess",
  "purpose": "{팀 목적}",
  "decision_mode": "leader_decides | consensus | vote | architect_veto",
  "members": [
    {
      "role": "{역할명}",
      "expert_slug": "{전문가 slug}",
      "cli": "{cli_variant}",
      "model": "{model_id}",
      "tier": "{trivial | standard | premium}",
      "permission_mode": "{plan | acceptEdits | default}",
      "phases": ["probe", "grasp", "tangle", "ink"],
      "is_leader": true
    }
  ],
  "bridge_to": "{상위팀 slug 또는 null}",
  "created_at": "{YYYY-MM-DD}"
}
```

각 멤버의 `cli`, `model`, `tier`, `permission_mode`, `phases` 값은 전문가 정의 파일에서 자동으로 읽어옵니다.

## 역할 카테고리 → CLI 자동 매핑

| 카테고리 | 기본 CLI | Tier | Permission |
|---|---|---|---|
| 아키텍트/설계자 | `codex` | premium | plan |
| 백엔드/프론트엔드 개발자 | `codex` | premium | acceptEdits |
| DB/Cloud 설계자 | `codex` | premium | plan |
| TDD/QA 엔지니어 | `codex-spark` | standard | acceptEdits |
| 코드 리뷰어 | `codex-spark` | standard | default |
| 보안 감사 | `codex` | premium | default |
| DevOps/디버거 | `codex` | standard | acceptEdits |
| AI/UX/비즈니스 분석가 | `gemini` | standard | plan |
| 마케팅/재무/법무 | `gemini` | standard | plan |
| 문서/다이어그램 | `gemini-fast` | trivial | plan |
| 전략/연구 종합 | `claude-opus` | premium | plan |
| GLM 범용 작업자 | `zai` | trivial | acceptEdits |

## 팀 크기 제한

| 팀 유형 | 최소 | 최대 | 권장 |
|---|---|---|---|
| upper | 2 | 8 | 3-5 |
| lower | 2 | 6 | 2-4 |

## 완료 후

팀 구성이 끝나면 다음 단계를 안내합니다:
- 상위팀: `steering-orchestrator` 에이전트 호출
- 하위팀: `team-leader` 에이전트 호출
- 구조 확인: `/relay:visualize-team` 으로 현재 팀 구조 도식화
