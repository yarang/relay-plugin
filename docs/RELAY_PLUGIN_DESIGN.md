# relay-plugin (Claude Code Plugin) — 설계 명세서

**버전**: 0.5.1 (비그 수정)  
**작성일**: 2026-04-04  
**현재 버전**: 0.4.1 기반 확장  
**변경 이력**: v0.5.1 — P2 inbox 큐, P3 PostToolUse hooks 배열 방식, P4 date -N macOS 버그 수정

---

## 1. 역할 정의

> relay-plugin은 **Claude Code의 계층형 멀티에이전트 오케스트레이션 프레임워크**다.  
> Expert 정의 → 팀 구성 → teammate/in-process 실행 → 파일 기반 상호 통신.

```
사용자 (Claude Code 터미널)
    │
    │ /relay:setup, /relay:define-expert, /relay:build-team
    ▼
relay-plugin (.claude-plugin/)
    ├── hooks.json        ← SessionStart, TeammateIdle, PostToolUse, SubagentStop
    ├── plugin.json       ← 슬래시 명령어 매니페스트
    └── .claude/commands/ ← 실행 로직 (Markdown 프롬프트)
         ↕ 파일 읽기/쓰기
.claude/relay/             ← 런타임 데이터 디렉터리
    ├── domain-config.json
    ├── experts/
    ├── teams/
    ├── notify/            ← 에이전트간 통신 채널
    └── shared-context/
```

---

## 2. 디렉터리 전체 구조 (v0.5.0 설계)

```
relay-plugin/
├── .claude-plugin/
│   ├── plugin.json               ← 플러그인 메타데이터 + 명령어 목록
│   └── hooks.json                ← Hook 정의 (현재 버전 + 확장)
│
├── .claude/
│   └── commands/
│       ├── setup.md              ← 초기화
│       ├── setup-keys.md         ← API 키 설정
│       ├── define-expert.md      ← Expert 정의
│       ├── build-team.md         ← 팀 구성
│       ├── invoke-agent.md       ← 에이전트 실행
│       ├── message.md            ← 에이전트간 메시지 전송
│       ├── broadcast.md          ← 팀 전체 공지
│       ├── escalate.md           ← 상위 에스컬레이션
│       ├── visualize-team.md     ← 팀 구조 시각화
│       ├── progress-sync.md      ← 진행 상황 동기화
│       ├── meeting.md            ← 회의록 관리
│       ├── read-context.md       ← 공유 컨텍스트 로드
│       ├── write-design-decision.md
│       ├── export-templates.md   ← project scope 템플릿 내보내기
│       ├── import-templates.md   ← 외부 템플릿 가져오기
│       └── dev/
│           ├── tdd-cycle.md
│           ├── ddd-design.md
│           └── create-implementation-plan.md
│
├── config/
│   ├── providers.json            ← CLI/모델 프로바이더 설정
│   └── domain-config.schema.json ← domain-config 유효성 스키마
│
├── docs/
│   ├── team-building-rules.md
│   ├── inter-agent-communication.md ← 통신 프로토콜 문서
│   └── notify-protocol.md           ← notify/ 스펙               ← 신규
│
└── shared-context-template/
    └── ...
```

---

## 3. hooks.json 확장 설계

현재 hooks.json(v0.4.1)에 아래 섹션을 추가:

> **[P3 수정]** `PostToolUse_FileNotify`는 Claude Code에 **존재하지 않는** Hook 이름입니다.  
> 올바른 방식: **기존 `PostToolUse` 배열에 command hook을 추가**하는 것입니다.

```json
{
  "PreToolUse": [ "...현재 유지..." ],
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "prompt",
          "prompt": "...기존 notify 기록 로직 (prompt hook)..."
        },
        {
          "type": "command",
          "async": true,
          "command": "./.claude-plugin/scripts/record-file-event.sh"
        }
      ]
    }
  ],
  "SessionStart": [ "...현재 유지..." ],
  "SubagentStop": [ "...현재 유지..." ],
  "TeammateIdle": [ "...현재 유지..." ],
  "Stop": [
    {
      "hooks": [{
        "type": "command",
        "async": true,
        "command": "./.claude-plugin/scripts/emit-vscode-event.sh stop"
      }]
    }
  ]
}
```

> **구현 방식**:
> - `Stop` Hook은 Claude Code 공식 지원 Hook입니다.
> - `PostToolUse`에 prompt hook과 command hook을 **배열로** 등록할 수 있습니다 (병행 실행).
> - Hook command 경로: `$CLAUDE_PROJECT_DIR` 변수는 공식 확인되지 않았으므로 **상대 경로** `./.claude-plugin/scripts/`를 사용합니다.

---

## 4. notify/ 디렉터리 프로토콜 (v0.5.0)

### 4-1. 전체 구조

```
.claude/relay/notify/
├── agents/                       ← 1:1 전용
│   └── {agent-slug}/
│       ├── inbox/                ← [P2 수정] 메시지 큐 (덮어쓰기 → 유실 없음)
│       │   └── {msg_id}.json     ← 메시지마다 별도 파일 (TeammateIdle 이후 삭제)
│       └── inbox.lock            ← 수신 처리 중 잠금 파일
│
├── channels/                     ← 1:N / relay
│   └── {team-id}/
│       ├── broadcast.json        ← 최신 공지 (덮어쓰기)
│       └── history/
│           └── {msg-id}.json     ← 공지 히스토리
│
├── bridge-relay/                 ← 브릿지 릴레이 감사 로그
│   └── {msg-id}.json
│
├── ack/                          ← 수신 확인
│   └── {msg-id}-{slug}.ack
│
└── events/                       ← VSCode 소비용 (읽고 삭제)
    └── {timestamp}-{type}.json
```

### 4-2. 메시지 공통 스키마

```json
{
  "msg_id":       "msg-1743856000-a3f2",
  "type":         "1:1",
  "from":         "system-designer",
  "to":           "steering-orchestrator",
  "content":      "아키텍처 검토 완료. tangle Phase 진입 승인 요청.",
  "timestamp":    "2026-04-04T16:09:20Z",
  "requires_ack": true,
  "ack_by":       [],
  "relay_to":     null,
  "relay_scope":  null,
  "priority":     "high",
  "phase":        "grasp"
}
```

### 4-3. 릴레이 메시지 스키마 (브릿지 작성)

```json
{
  "msg_id":        "relay-bcast-042",
  "type":          "relay",
  "from":          "bridge-member",
  "original_from": "steering-orchestrator",
  "original_msg_id": "bcast-042",
  "to":            "group:lower-team-1",
  "content":       "구현 Phase 시작. backend: API, frontend: UI 설계 착수.",
  "timestamp":     "2026-04-04T16:09:45Z",
  "relay_trace": {
    "relayed_by":      "bridge-member",
    "relay_timestamp": "2026-04-04T16:09:45Z",
    "transformation":  "adapted"
  },
  "requires_ack": true,
  "ack_by":       [],
  "priority":     "normal",
  "phase":        "tangle"
}
```

---

## 5. 통신 유형별 에이전트 동작 설계

### 5-1. 1:1 통신

**발신**: `/relay:message` 명령 또는 직접 파일 작성

```
[P2 수정] notify/agents/{recipient-slug}/inbox/{msg_id}.json 생성:
  msg_id: msg-{timestamp}-{random4}
  type: "1:1"
  from: {현재 에이전트 slug}
  to: {recipient-slug}
  content: {메시지 내용}

• 매 메시지마다 별도 파일 생성 → 동시 전송에도 메시지 유실 없음
• TeammateIdle hook: inbox/*.json glob 스캔 → 차례로 수신 후 파일 삭제
```

**수신**: TeammateIdle hook이 `agents/{자신}/inbox/*.json` glob 조회 후 발견된 모든 파일 차례로 체크

---

### 5-2. 1:N 브로드캐스트

```markdown
<!-- .claude/commands/broadcast.md -->
# /relay:broadcast

## 사용법
/relay:broadcast {team-id} {내용} [--relay-to {lower-team-id}]

## 실행 로직
1. notify/channels/{team-id}/broadcast.json 생성
2. --relay-to 플래그가 있으면 relay_to, relay_scope 필드 설정
3. history/{msg-id}.json 백업
4. 완료 알림: "📢 {team-id} 전체에 broadcast 전송"
```

---

### 5-3. 1:group (브릿지 릴레이)

브릿지 팀원의 TeammateIdle 처리 흐름:

```
TeammateIdle hook 발화
      │
      ▼
notify/ 확인 → channels/{상위팀}/broadcast.json 읽음
      │
      ├── relay_to 필드 없음 → 팀 내 처리 후 종료
      │
      └── relay_to: "lower-team-1" 존재
                │
                ▼
           메시지 내용 분석 및 변환
                │
                ├── transformation: "passthrough" → 그대로 복사
                ├── transformation: "adapted"    → 상위팀 언어 → 하위팀 업무 기준으로 재작성
                └── transformation: "filtered"   → 하위팀 관련 항목만 추출
                │
                ▼
           notify/channels/lower-team-1/broadcast.json 작성
           notify/bridge-relay/{msg-id}.json 감사 로그 기록
```

---

## 6. hooks.json 확장 스크립트

### emit-vscode-event.sh (신규)

```bash
#!/bin/bash
# .claude-plugin/scripts/emit-vscode-event.sh
# 사용: emit-vscode-event.sh {event-type}
# [P4 수정] date -N은 macOS 미지원 → 초단위 + PID로 대체

EVENT_TYPE="${1:-unknown}"
EVENT_DIR=".claude/relay/events"
# macOS 호환: date -u +%s%N은 macOS에서 %N이 리터럴 "N"을 출력 → 초단위 + PID로 unique 보장
TIMESTAMP="$(date -u +%s)-$$"

mkdir -p "$EVENT_DIR"
PAYLOAD=$(cat 2>/dev/null || echo '{}')

cat > "${EVENT_DIR}/${TIMESTAMP}-${EVENT_TYPE}.json" << EOF
{
  "event_type": "${EVENT_TYPE}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "cwd": "$(pwd)",
  "payload": ${PAYLOAD}
}
EOF

exit 0
```

### record-file-event.sh (신규)

```bash
#!/bin/bash
# .claude-plugin/scripts/record-file-event.sh
# PostToolUse (Write/Edit) 이벤트를 VSCode notify/events/ 에 기록
# [P4 수정] date -N macOS 호환 문제 해결

EVENT_DIR=".claude/relay/events"
# 초단위 + PID: macOS/Linux 모두 안전
TIMESTAMP="$(date -u +%s)-$$"

mkdir -p "$EVENT_DIR"
PAYLOAD=$(cat)
FILE_PATH=$(echo "$PAYLOAD" | grep -o '"file_path":"[^"]*"' | cut -d'"' -f4)

# relay/ 하위 파일만 이벤트 기록
if [[ "$FILE_PATH" != *".claude/relay/"* ]]; then
  exit 0
fi

cat > "${EVENT_DIR}/${TIMESTAMP}-file-changed.json" << EOF
{
  "event_type": "file_changed",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "file_path": "${FILE_PATH}",
  "tool_name": "$(echo "$PAYLOAD" | grep -o '"tool_name":"[^"]*"' | cut -d'"' -f4)"
}
EOF

exit 0
```

---

## 7. 실행 흐름

### 7-1. Teammate 모드 (상위팀)

```
환경 조건: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

/relay:invoke-agent upper-team-1
         │
         ▼
Orchestrator (Claude Code 메인)
    │ teammate로 스폰
    ├──→ Architect (system-designer) — gemini
    ├──→ Bridge Member (bridge-member) — codex
    └──→ Recorder (meeting-recorder) — gemini-fast

에이전트간 통신:
  - SendMessage(teammate) → Claude Code 내부 IPC (빠름)
  - notify/ 파일 → TeammateIdle hook 처리 (비동기)

VSCode 연동:
  - PostToolUse command hook → notify/events/ 에 기록
  - VSCode FileSystemWatcher 감지 → 패널 갱신
```

### 7-2. In-process 모드 (하위팀)

```
/relay:invoke-agent lower-team-1 (in-process)
         │
         ▼
Team Leader (claude-opus) — 모든 하위팀 지시 통합
    │ 순차 또는 병렬 실행
    ├── Backend Developer (codex) — REST API 설계
    ├── Frontend Developer (codex) — UI 컴포넌트 설계
    └── QA Engineer (gemini-flash) — 테스트 시나리오

통신: Team Leader가 각 역할을 순서대로 invoke
상태: notify/channels/lower-team-1/broadcast.json 갱신
```

---

## 8. 슬래시 명령어 전체 매니페스트 (v0.5.0)

| 명령어 | 역할 | 신규 |
|--------|------|------|
| `/relay:setup` | 도메인 초기화 | — |
| `/relay:setup-keys` | API 키 설정 | — |
| `/relay:define-expert` | Expert 정의 | — |
| `/relay:build-team` | 팀 구성 | — |
| `/relay:invoke-agent` | 에이전트 실행 | — |
| `/relay:message` | 1:1 메시지 전송 | ✅ |
| `/relay:broadcast` | 팀 전체 공지 | ✅ |
| `/relay:escalate` | 상위 에스컬레이션 | — |
| `/relay:visualize-team` | 팀 구조 시각화 | — |
| `/relay:meeting` | 회의록 관리 | — |
| `/relay:read-context` | 공유 컨텍스트 로드 | — |
| `/relay:progress-sync` | 진행 상황 동기화 | — |
| `/relay:write-design-decision` | DDL 파일 작성 | — |
| `/relay:export-templates` | project scope 템플릿 내보내기 | ✅ |
| `/relay:import-templates` | 외부 템플릿 가져오기 | ✅ |

---

## 9. Expert/Team 스키마 요약 (최종)

### Expert 파일 (`.claude/relay/experts/{slug}.md`)

```markdown
---
role: Backend Developer
slug: backend-developer
domain: development
backed_by: "codex:gpt-4o"
cli: codex
model: gpt-4o
fallback_cli: null
tier: premium
permission_mode: acceptEdits
memory: project
isolation: null
phases:
  - tangle
  - ink
agent_profile: backend-developer
default_platform: fastapi
created_at: "2026-04-04"
---

# Backend Developer

## 페르소나
...

## 역량
- REST API 설계
- CRUD 구현
```

### Team 파일 (`.claude/relay/teams/{team-id}.json`)

```json
{
  "id": "upper-team-1",
  "name": "상위팀",
  "slug": "upper-team-1",
  "type": "upper",
  "execution_mode": "teammate",
  "coordinator": "claude",
  "coordinator_model": "claude-opus-4-5",
  "purpose": "아키텍처 결정 및 팀 간 조율",
  "decision_mode": "architect_veto",
  "members": [
    { "role": "Orchestrator", "expert_slug": "steering-orchestrator",
      "is_leader": true,  "is_bridge": false },
    { "role": "Architect",    "expert_slug": "system-designer",
      "cli": "gemini",    "is_leader": false, "is_bridge": false },
    { "role": "Bridge",       "expert_slug": "bridge-member",
      "is_leader": false, "is_bridge": true }
  ],
  "phase_routing": {
    "probe": "gemini",
    "grasp": "gemini",
    "tangle": "codex",
    "ink": "codex"
  },
  "bridge_to": "lower-team-1",
  "created_at": "2026-04-04"
}
```

---

## 10. .gitignore 추가

```gitignore
# notify/ 런타임 파일 (에이전트 통신)
# [P2 수정] inbox.json → inbox/ 디렉토리 큐 방식
.claude/relay/notify/agents/*/inbox/
.claude/relay/notify/agents/*/inbox.lock
.claude/relay/notify/channels/*/broadcast.json
.claude/relay/notify/events/
.claude/relay/notify/ack/
.claude/relay/notify/bridge-relay/

# 실행 이력
.claude/relay/runs/
.claude/relay/meetings/ACTIVE.json
```
