# /relay:build-team

정의된 전문가들을 조합해 팀을 구성하고 `.claude/relay/teams/` 에 저장합니다.

## 사전 확인

- `.claude/relay/domain-config.json` 없으면 `/relay:setup` 안내
- `.claude/relay/experts/` 가 비어 있으면 `/relay:define-expert` 안내

## 대화 흐름

```
1. 팀 이름·목적 질문
2. 계층 위치 선택: upper(상위팀) / lower(하위팀)
3. 사용 가능한 전문가 목록 표시 (backed_by 포함)
4. 팀원 선택 (리더 1명 필수)
5. backed_by 있는 팀원에게는 외부 에이전트 자동 표시
6. 의사결정 방식 선택
7. 하위팀인 경우: 상위팀 브릿지 멤버 설정
8. 초안 확인 → 저장
```

## 전문가 목록 표시 형식

팀원 선택 시 `backed_by` 필드를 함께 표시합니다.

```
선택 가능한 전문가:
  1. SNS 마케터 (sns-marketer)          ← backed_by: moai:sns-content-creator
  2. 법무 검토 전문가 (legal-reviewer)   ← backed_by: moai:contract-reviewer
  3. 백엔드 개발자 (backend-dev)         ← backed_by: relay:developer
  4. 데이터 분석가 (data-analyst)        ← 직접 정의
```

## 팀 유형

| 유형 | 역할 | 의사결정 방식 예시 |
|---|---|---|
| upper | 아키텍처·도메인 설계, 팀 간 조율 | `architect_veto` |
| lower | 실제 구현, 기능 단위 개발 | `leader_decides` / `consensus` |

## 저장 형식

파일: `.claude/relay/teams/{팀-슬러그}.json`

```json
{
  "name": "{팀명}",
  "slug": "{팀-슬러그}",
  "type": "upper | lower",
  "purpose": "{팀 목적}",
  "decision_mode": "leader_decides | consensus | vote | architect_veto",
  "members": [
    {
      "role": "{역할명}",
      "expert_slug": "{전문가 slug}",
      "backed_by": "{플러그인:에이전트명 또는 null}",
      "is_leader": true
    },
    {
      "role": "{역할명}",
      "expert_slug": "{전문가 slug}",
      "backed_by": "{플러그인:에이전트명 또는 null}",
      "is_leader": false
    }
  ],
  "bridge_to": "{상위팀 slug 또는 null}",
  "created_at": "{YYYY-MM-DD}"
}
```

`backed_by` 값은 전문가 정의 파일(`.claude/relay/experts/{slug}.md`)에서 자동으로 읽어 옵니다.

## 완료 후

팀 구성이 끝나면 다음 단계를 안내합니다:
- 상위팀: `steering-orchestrator` 에이전트 호출
- 하위팀: `team-leader` 에이전트 호출
- 구조 확인: `/relay:visualize-team` 으로 현재 팀 구조 도식화
