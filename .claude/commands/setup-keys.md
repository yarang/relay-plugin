# /relay:setup-keys

외부 LLM API(Gemini, OpenAI, Zhipu AI)의 API 키를 안전하게 설정합니다.
키는 프로젝트 루트의 `.mcp.json` 에 저장되며, `.gitignore` 에 자동 등록됩니다.

## 동작 순서

### 1. 현재 상태 확인

다음 파일들의 존재 여부를 순서대로 확인합니다.

```
{프로젝트 루트}/.mcp.json
{프로젝트 루트}/.gitignore
```

### 2. 서비스 선택

사용자에게 설정할 서비스를 선택하게 합니다.

```
API 키를 설정할 서비스를 선택하세요 (복수 선택 가능):
  [1] Google Gemini   (backed_by: gemini:*)
  [2] OpenAI / Codex  (backed_by: codex:*)
  [3] Zhipu AI (GLM)  (backed_by: zai:*)   ← 컨텍스트 압축 용도, 무료 티어 있음
  [4] 전체
  [5] 현재 설정 확인만
```

### 3. 키 입력 받기

선택한 서비스별로 키를 입력받습니다.

**Gemini:**
```
Gemini API 키를 입력하세요:
(https://aistudio.google.com/app/apikey 에서 발급)
→ 입력: AIza...
```

**OpenAI / Codex — 인증 방식 먼저 선택:**
```
OpenAI 연결 방식을 선택하세요:
  [1] API 키  (sk-... 또는 proj-... 형식)
  [2] OAuth   (이미 OAuth로 연결된 경우 — API 키 불필요)
```

- `[1] API 키` 선택 시:
  ```
  OpenAI API 키를 입력하세요:
  (https://platform.openai.com/api-keys 에서 발급)
  → 입력: sk-...
  ```
  → `.mcp.json` 의 `codex_mcp.env.OPENAI_API_KEY` 에 저장

- `[2] OAuth` 선택 시:
  → API 키 입력 생략
  → `.mcp.json` 의 `codex_mcp.env.OPENAI_AUTH_TYPE` 을 `oauth` 로 설정
  → MCP 서버가 런타임에 `OPENAI_OAUTH_TOKEN` 환경 변수를 자동 탐색

**Zhipu AI:**
```
Zhipu AI API 키를 입력하세요:
(https://bigmodel.cn → 개인 설정 → API 키 에서 발급, glm-4-flash 무료)
→ 입력: ...
```

입력된 키는 화면에 마스킹하여 표시합니다 (`AIza****...****`).

### 4. .mcp.json 생성 또는 갱신

`.mcp.json` 이 없으면 새로 생성하고, 있으면 해당 서비스의 `env` 값만 업데이트합니다.

**생성되는 `.mcp.json` 형식 — API 키 방식:**

```json
{
  "mcpServers": {
    "gemini_mcp": {
      "command": "uv",
      "args": ["run", "{MCP_SERVERS_PATH}/gemini-wrapper/server.py"],
      "env": { "GEMINI_API_KEY": "{입력된 키}" }
    },
    "codex_mcp": {
      "command": "uv",
      "args": ["run", "{MCP_SERVERS_PATH}/codex-wrapper/server.py"],
      "env": { "OPENAI_API_KEY": "{입력된 키}" }
    },
    "zai_mcp": {
      "command": "uv",
      "args": ["run", "{MCP_SERVERS_PATH}/zai-wrapper/server.py"],
      "env": { "ZHIPU_API_KEY": "{입력된 키}" }
    }
  }
}
```

**OAuth 방식 선택 시 `codex_mcp` 항목:**

```json
"codex_mcp": {
  "command": "uv",
  "args": ["run", "{MCP_SERVERS_PATH}/codex-wrapper/server.py"],
  "env": {
    "OPENAI_AUTH_TYPE": "oauth"
  }
}
```

`OPENAI_API_KEY` 가 없고 `OPENAI_AUTH_TYPE=oauth` 이면 서버가 런타임에
`OPENAI_OAUTH_TOKEN` 환경 변수를 탐색합니다. OAuth 토큰은 시스템 또는
Claude Code가 자동 주입하므로 `.mcp.json` 에 직접 기재하지 않습니다.

`{MCP_SERVERS_PATH}` 는 플러그인 설치 경로를 기반으로 자동 결정합니다.
기본값: `~/.claude/plugins/relay/mcp-servers` 또는 플러그인 소스 경로.

### 5. .gitignore 등록

`.gitignore` 파일에 `.mcp.json` 이 없으면 자동으로 추가합니다.

```
# relay plugin — API keys (do not commit)
.mcp.json
```

이미 등록된 경우에는 건너뜁니다.

### 6. 완료 메시지

```
✅ API 키 설정 완료

  Gemini    : gemini_mcp  ← AIza****...****
  OpenAI    : codex_mcp   ← sk-****...****
  Zhipu AI  : zai_mcp     ← ****...****

  저장 위치 : .mcp.json (gitignore 등록됨)

다음 단계:
  1. Claude Code를 재시작하여 MCP 서버를 로드합니다.
  2. 전문가 정의 시 backed_by: gemini:gemini-2.5-flash,
     backed_by: codex:gpt-4o, backed_by: zai:glm-4-flash 중 선택 가능합니다.
  3. 컨텍스트 압축 전담 전문가를 등록하려면:
     docs/experts/context-compressor.md 를 .claude/relay/experts/ 에 복사
```

## 현재 설정 확인 ([4] 선택 시)

`.mcp.json` 이 없으면:
```
.mcp.json 파일이 없습니다.
/relay:setup-keys 를 실행해 키를 설정하세요.
```

있으면 등록된 서비스 목록과 키 마스킹 값을 출력합니다:
```
현재 등록된 MCP 서버:
  gemini_mcp  GEMINI_API_KEY   = AIza****...****  ✅
  codex_mcp   OPENAI_API_KEY   = (미설정)         ❌
              OPENAI_AUTH_TYPE = oauth             ✅ ← OAuth 연결 시 API 키 불필요
  zai_mcp     ZHIPU_API_KEY    = (미설정)         ❌  ← context-compressor 전담
```

`OPENAI_AUTH_TYPE=oauth` 가 설정된 경우 `OPENAI_API_KEY` 미설정은 오류가 아닙니다.

## 보안 규칙

- 키는 `.mcp.json` 에만 저장합니다. `.claude/relay/` 나 다른 플러그인 데이터 경로에 복사하지 않습니다.
- `.mcp.json` 은 반드시 `.gitignore` 에 등록합니다.
- 화면 출력 시 키 앞 4자리와 뒤 4자리만 표시하고 나머지는 `*` 로 마스킹합니다.
- 키 교체 시 이전 키를 로그에 기록하지 않습니다.
