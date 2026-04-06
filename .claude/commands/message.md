# /relay:message

에이전트 간 실시간 메시지를 전송합니다.

> Claude Code의 `SendMessage` 툴을 래핑한 커맨드입니다.
> 수신자가 idle 상태라면 자동으로 재개(resume)됩니다.

## 사용법

```
/relay:message {수신자-이름} "{내용}"
```

**수신자 이름** — 팀 내 에이전트 이름 (예: `team-leader`, `steering-orchestrator`, `developer`, `meeting-recorder`)
**브로드캐스트** — `*` 를 수신자로 지정하면 전체 팀원에게 전송됩니다.

## 동작

```
SendMessage("{수신자-이름}", "{내용}")
```

- 수신자가 실행 중이면 → 현재 턴에 메시지 주입 (in-process)
- 수신자가 idle 상태면 → mailbox 에 기록 후 자동 재개
- 수신자가 없으면 → mailbox 파일에 기록 (`~/.claude/teams/{팀명}/inboxes/{수신자}.json`)

## 예시

```
# 팀 리더에게 블로커 보고
/relay:message team-leader "payments API 설계가 기존 DDL-003 과 충돌합니다. 검토 요청."

# 전체 팀에게 공지
/relay:message * "DDL-005 가 FINAL 상태가 되었습니다. 구현 준비하세요."

# 회의록에 직접 발언 기록
/relay:message meeting-recorder "developer(backend): 결제 모듈 분리 완료. PR #42 올렸습니다."
```

## 메시지 타입

| 대상 | 목적 | 예시 |
|---|---|---|
| `meeting-recorder` | 발언 기록 | `"역할명: 발언 내용"` |
| `team-leader` | 보고·블로커 | 자유 형식 |
| `steering-orchestrator` | 에스컬레이션 | 자유 형식 (에스컬레이션은 `/relay:escalate` 우선) |
| `*` | 전체 공지 | 자유 형식 |

## 참고

- 에스컬레이션은 `/relay:escalate` 를 사용합니다 (escalation 파일 자동 생성 포함).
- 회의록 기록은 TeammateIdle 훅이 자동 처리하므로 별도 호출이 불필요합니다.
