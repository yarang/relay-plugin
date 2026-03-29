# /relay:escalate

팀 내에서 해결할 수 없는 이슈를 상위팀에 전달합니다.

## 사용 주체

`team-leader`, `developer` (리더를 통해)

## 에스컬레이션 조건

다음 중 하나에 해당하면 에스컬레이션합니다:
- 팀 간 인터페이스 계약 충돌
- 아키텍처 결정이 필요한 기술 이슈
- 리소스·일정 충돌로 팀 내 해결 불가
- DDL 해석 불일치

## 파일 생성

파일: `.claude/relay/shared-context/escalations/ESC-{NNN}-{slug}.md`

```markdown
---
id: ESC-{NNN}
from_team: {팀명}
to: steering-team
status: OPEN | IN_REVIEW | RESOLVED
priority: high | medium | low
date: {YYYY-MM-DD}
related_ddl: {DDL-NNN 또는 null}
---

# ESC-{NNN}: {이슈 제목}

## 상황
{무슨 일이 발생했는가}

## 시도한 해결책
{팀 내에서 시도한 것들}

## 필요한 결정
{상위팀에서 결정해야 할 것}

## 영향
{이 이슈가 해결되지 않으면 어떻게 되는가}

## 기한
{언제까지 결정이 필요한가}
```

## 완료 후

상위팀의 `steering-orchestrator` 에이전트에게 ESC 파일 위치를 알립니다.
