# relay-plugin

> **프롬프트 기반 계층형 에이전트 팀 프레임워크**

사용자 정의 전문가와 계층형 팀 구조를 **프롬프트만으로** 유연하게 설계·운용하는 Claude Code 플러그인.

코드 없이, 지침과 명령어만으로 작동합니다.

**지원 LLM**: Claude (기본), Google Gemini, OpenAI GPT, Zhipu AI GLM

---

## 저장소 구조

이 저장소는 두 개의 독립적인 컴포넌트로 구성됩니다.

```
relay-plugin/          (저장소 루트 = 마켓플레이스)
├── relay-plugin/      ← 플러그인 소스 (name: relay)
│   ├── .claude-plugin/
│   │   └── plugin.json    ← 플러그인 매니페스트
│   ├── commands/
│   │   └── relay/         ← /relay:* 슬래시 명령어
│   │       ├── setup.md
│   │       ├── build-team.md
│   │       ├── define-expert.md
│   │       └── dev/
│   │           ├── tdd-cycle.md
│   │           └── ...
│   ├── agents/            ← teammate 모드 에이전트 정의
│   ├── docs/              ← 조합형 에이전트 템플릿 · 가이드
│   └── README.md          ← 상세 사용 문서
│
└── mcp-servers/       ← 외부 LLM MCP 래퍼 서버 (독립 컴포넌트)
    ├── gemini-wrapper/server.py    ← Google Gemini
    ├── codex-wrapper/server.py     ← OpenAI GPT / o 시리즈
    ├── zai-wrapper/server.py       ← Zhipu AI GLM
    └── mcp.json.template           ← .mcp.json 설정 템플릿
```

두 컴포넌트의 관계:

```
Claude Code
  └── relay 플러그인
        └── /relay:invoke-agent
              └── MCP 호출 → mcp-servers/ (외부 LLM 래퍼)
                    ├── gemini_mcp  → Google Gemini API
                    ├── codex_mcp   → OpenAI API
                    └── zai_mcp     → Zhipu AI API
```

> `mcp-servers/` 는 외부 LLM(`gemini:*`, `codex:*`, `zai:*`) 전문가를 사용할 때만 필요합니다.
> Claude만 사용하는 경우 `relay-plugin/` 만으로 충분합니다.

---

## 설치

### 플러그인 설치

```bash
# 1. 마켓플레이스 등록 (최초 1회)
claude plugin marketplace add yarang/relay-plugin

# 2. 플러그인 설치
claude plugin install relay@relay-plugin
```

설치 후 `/relay:*` 명령어와 teammate 에이전트가 등록됩니다.

### 사전 요구사항

| 항목 | 버전 | 필요 시점 |
|---|---|---|
| Claude Code | 최신 | 항상 |
| [uv](https://docs.astral.sh/uv/) | 최신 | 외부 LLM MCP 서버 실행 시 |

### 설치 후 프로젝트 초기화

플러그인 설치 후, 각 프로젝트에서 한 번 실행합니다.

```
/relay:setup       ← 도메인 선택·훅 등록 (필수)
/relay:setup-keys  ← 외부 LLM API 키 설정 (선택)
```

| 도메인 | 설명 |
|---|---|
| `general` | 마케팅·법무·기획·영업 등 범용 팀 |
| `development` | 소프트웨어 개발팀 (TDD·DDD 스킬 포함) |

### 수동 설치 (대안)

```bash
# 저장소를 직접 클론 후 스크립트 실행
git clone https://github.com/yarang/relay-plugin.git ~/.local/share/relay-plugin
cd /your/project
bash ~/.local/share/relay-plugin/install.sh
```

---

## mcp-servers/ 상세

### 개요

각 서버는 외부 LLM API를 MCP(Model Context Protocol) 도구로 노출합니다.
relay 플러그인의 `/relay:invoke-agent` 가 이 도구를 호출하여 외부 LLM에 작업을 위임합니다.

### 서버 목록

| 디렉토리 | MCP 서버 ID | 지원 모델 |
|---|---|---|
| `gemini-wrapper/` | `gemini_mcp` | gemini-2.5-flash, gemini-2.5-pro |
| `codex-wrapper/` | `codex_mcp` | gpt-4o, gpt-4o-mini, o3-mini |
| `zai-wrapper/` | `zai_mcp` | glm-4-flash (무료), glm-4-air, glm-4, glm-4-long |

### 실행 방식

모든 서버는 [PEP 723 인라인 의존성](https://peps.python.org/pep-0723/)으로 작성되어 있습니다.
별도의 `pip install` 없이 `uv run` 으로 즉시 실행됩니다.

```bash
uv run mcp-servers/gemini-wrapper/server.py
uv run mcp-servers/codex-wrapper/server.py
uv run mcp-servers/zai-wrapper/server.py
```

실제 실행은 Claude Code가 `.mcp.json` 을 읽어 자동으로 처리합니다.

### MCP 도구 인터페이스

세 서버 모두 동일한 파라미터 구조를 사용합니다.

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `prompt` | string | 이번 작업 지시문 |
| `model` | string | 사용할 모델명 |
| `system` | string (선택) | 페르소나·역할·제약 (전문가 파일에서 자동 합성) |
| `context` | string (선택) | 이전 작업의 압축 요약 |
| `temperature` | float | 생성 다양성 (0.0~1.0) |
| `max_tokens` | int | 최대 출력 토큰 |

`system` 과 `context` 는 `/relay:invoke-agent` 가 자동으로 채웁니다.
직접 호출할 때는 수동으로 입력합니다.

### .mcp.json 수동 설정

`/relay:setup-keys` 대신 직접 설정할 경우:

1. 템플릿을 프로젝트 루트에 복사합니다.

   ```bash
   cp ~/.claude/plugins/relay/mcp-servers/mcp.json.template .mcp.json
   ```

2. `{{PROJECT_ROOT}}` 를 실제 경로로, `YOUR_*_API_KEY_HERE` 를 실제 키로 변경합니다.

3. `.gitignore` 에 `.mcp.json` 을 추가합니다.

### codex OAuth 방식

OpenAI를 API 키 없이 OAuth로 연결할 경우:

```json
"codex_mcp": {
  "command": "uv",
  "args": ["run", "/경로/mcp-servers/codex-wrapper/server.py"],
  "env": { "OPENAI_AUTH_TYPE": "oauth" }
}
```

서버가 런타임에 `OPENAI_OAUTH_TOKEN` 을 자동으로 탐색합니다.

---

## relay-plugin/ 상세

플러그인의 내부 구조와 사용법은 **[relay-plugin/README.md](relay-plugin/README.md)** 를 참조하세요.

주요 내용:

- 빠른 시작 (general/development 워크플로우)
- 핵심 개념 (도메인 팩, 팀 계층 구조, 조합형 에이전트)
- 전문가 백엔드 (`backed_by`) 전체 네임스페이스
- 실행 모드 (in-process / teammate / subagent)
- context-compressor 컨텍스트 압축 시스템
- 스킬 레퍼런스 (`/relay:*` 명령어 전체)
- 회의록 자동화
- 데이터 저장 구조

---

## 지원 외부 LLM

외부 LLM은 전문가의 `backed_by` 에 네임스페이스로 지정합니다. MCP 서버 등록이 필요합니다.

| 네임스페이스 | 제공사 | API 키 | 무료 티어 |
|---|---|---|---|
| `gemini:*` | Google Gemini | `GEMINI_API_KEY` | — |
| `codex:*` | OpenAI GPT / o 시리즈 | `OPENAI_API_KEY` 또는 OAuth | — |
| `zai:*` | Zhipu AI GLM | `ZHIPU_API_KEY` | glm-4-flash 무료 |

> `relay:*` · `null` 은 LLM이 아닌 에이전트 네임스페이스입니다.
> 전체 `backed_by` 네임스페이스 목록은 [relay-plugin/README.md](relay-plugin/README.md#전문가-백엔드--backed_by) 를 참조하세요.

---

## 개발 현황

| 버전 | 상태 |
|---|---|
| v0.4.0 | 개발 중 — 코어 기능 구현 완료, MCP 래퍼 서버 구현 완료 |

### 완료

- 도메인 팩 시스템 (general / development)
- 계층형 팀 구조 (Steering Team → Team Leader → Developer)
- 외부 LLM 연동 MCP 서버 (Gemini, OpenAI, Zhipu AI)
- 컨텍스트 압축 시스템 (context-compressor)
- 회의록 자동화 (SessionStart / SubagentStop 훅)
- TDD 사이클 지원
- 플러그인 매니페스트 (`relay-plugin/.claude-plugin/plugin.json`)

### 진행 중

- 추가 템플릿 검증
- 통합 테스트

---

## 기여

1. 이슈 리포트: GitHub Issues
2. 기능 제안: GitHub Discussions
3. 코드 기여: Pull Request
