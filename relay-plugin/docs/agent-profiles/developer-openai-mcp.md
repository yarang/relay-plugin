---
profile_id: developer-openai-mcp
purpose: invoke-agent MCP 호출 시 참조용 — Claude Code teammate 모드와 무관
backed_by: codex:gpt-4o
default_model: gpt-4o
override_models:
  - o3
  - o4-mini
  - gpt-4o-mini
auth_modes:
  - api_key
  - oauth
---

# developer-openai (MCP 호출 프로파일)

> **주의**: 이 파일은 `invoke-agent` 가 `codex_mcp` 를 통해 외부 LLM 을 호출할 때
> 참조하는 프로파일입니다. Claude Code teammate 모드 실행 파일(`agents/developer-openai.md`)
> 과는 완전히 다른 목적입니다.

## 실행 방식

```python
codex_mcp.codex_generate(
  model   = "gpt-4o",               # backed_by 에서 파싱, model 오버라이드 가능
  system  = <페르소나 합성 결과>,   # invoke-agent 가 experts/{slug}.md 에서 자동 구성
  context = <이전 결과 요약>,       # 임계값(2,000자/4건) 초과 시 압축본, 미만 시 원본
  prompt  = <이번 task 지시문>,
)
```

## 연결 인증 (둘 중 하나)

### 방식 1 — API 키

```json
"codex_mcp": {
  "env": { "OPENAI_API_KEY": "sk-..." }
}
```

### 방식 2 — OAuth (API 키 불필요)

```json
"codex_mcp": {
  "env": { "OPENAI_AUTH_TYPE": "oauth" }
}
```

Claude Code 가 `OPENAI_OAUTH_TOKEN` 을 런타임에 자동 주입합니다.
`OPENAI_API_KEY` 없어도 OAuth 설정만 있으면 정상 동작합니다.

→ `/relay:setup-keys` → `[2] OpenAI / Codex` → 방식 선택

## 연결 유효성 확인 순서 (invoke-agent 내부 로직)

```
1. OPENAI_API_KEY 설정 여부 확인  → 있으면 API 키 모드 진행
2. OPENAI_API_KEY 없으면 OPENAI_AUTH_TYPE 확인
   → "oauth" 이면 OAuth 모드 진행 (OPENAI_OAUTH_TOKEN 자동 주입)
3. 둘 다 없으면 중단 + 안내
   → "/relay:setup-keys 를 실행하세요."
```

## 페르소나 합성 (invoke-agent 자동 처리)

`experts/{slug}.md` 에서 아래 순서로 추출:

1. `## 페르소나` → 역할명 + 특성
2. `## 역량` → 있으면 포함
3. `## 제약` → 있으면 포함

## 컨텍스트 압축 임계값

```
조건 A: 누적 결과 > 2,000자
조건 B: 누적 결과 ≥ 4건

→ 초과 시: context-compressor(zai:glm-4-flash) 위임 or Claude 직접 압축
→ 목표: 400자 이하 (5:1)
```

## relay 팀 구조 통합

MCP 호출 결과는 invoke-agent 를 통해 아래 구조로 자동 편입됩니다.

- 완료 결과 → `/relay:progress-sync` 로 리더에게 보고
- 블로커 → `/relay:escalate` 로 에스컬레이션
- 발언 → `/relay:meeting log` 에 자동 기록
