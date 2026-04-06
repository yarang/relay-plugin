# /relay:setup

팀 운용 환경을 초기화합니다. **프로젝트 시작 시 1회 실행**합니다.

## 사전 요구사항

relay 플러그인은 **Claude Code Agent Teams 모드 전용**입니다.

`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 설정 여부를 먼저 확인합니다.
미설정 시 아래 안내를 출력하고 이후 단계를 중단합니다:

```text
⚠️ Agent Teams 모드가 필요합니다.

~/.claude/settings.json 의 env 섹션에 추가하세요:
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}

추가 후 Claude Code 를 재시작하면 적용됩니다.
```

## 수행 단계

1. `.claude/relay/domain-config.json` 존재 여부 확인
2. 존재하면 현재 설정을 보여주고 변경 여부를 물음
3. 없으면 도메인 선택 대화 시작

## 도메인 선택

```text
사용할 도메인 팩을 선택하세요:

  [1] development  — TDD, DDD, 구현 계획 스킬 활성화
  [2] general      — 코어 스킬만 사용 (팀 구조·회의록·보고)
  [3] custom       — 직접 팩 목록 지정
```

## domain-config.json 생성

파일 위치: `.claude/relay/domain-config.json`

```json
{
  "domain": "{선택한 도메인}",
  "active_packs": ["{팩 이름}"],
  "project_name": "{프로젝트명}",
  "configured_at": "{YYYY-MM-DD}"
}
```

## 디렉토리 초기화

`domain-config.json` 생성 후 공유 컨텍스트 디렉토리를 생성합니다:

```text
.claude/relay/
├── domain-config.json
├── templates/                    ← project scope (user scope 덮어쓰기 가능)
│   ├── definitions/              ← 커스텀 composed-agent 정의
│   └── modules/
│       ├── specs/                ← 프로젝트별 spec 덮어쓰기 (동일 id 우선)
│       ├── platforms/            ← 프로젝트별 플랫폼 어댑터
│       └── policies/             ← 프로젝트 정책 (항상 프로젝트 scope)
├── experts/
├── teams/
└── shared-context/
    ├── design-decisions/
    ├── domain-models/            ← dev 도메인만
    ├── implementation-plans/     ← dev 도메인만
    ├── test-reports/             ← dev 도메인만
    ├── interface-contracts/
    ├── status-board/
    ├── escalations/
    └── meetings/
```

### 모듈 우선순위 규칙

- **user scope** (`relay-plugin/docs/templates/`) — 플러그인 기본 제공, 읽기 전용
- **project scope** (`.claude/relay/templates/`) — 프로젝트별 커스텀, 동일 `id`이면 project scope 우선

`templates/modules/` 하위 각 파일의 frontmatter:

```yaml
scope: project   # project scope 파일임을 명시
```

## 완료 메시지

```text
✅ relay 설정 완료

도메인: {domain}
활성 팩: {active_packs}
데이터 위치: .claude/relay/

다음 단계:
  /relay:define-expert  — 전문가 정의
  /relay:build-team     — 팀 구성
  /relay:invoke-agent   — 조합형 에이전트 호출
  /relay:visualize-team — 현재 팀 구조 도식화
```
