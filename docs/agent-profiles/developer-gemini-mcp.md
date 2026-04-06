---
profile_id: developer-gemini-mcp
purpose: in-process 모드 전용 참조 프로파일 — teammate 모드는 agents/developer-gemini.md 사용
backed_by: gemini:gemini-3.1-flash
default_model: gemini-3.1-flash
override_models:
  - gemini-3.1-pro
  - gemini-2.5-flash
  - gemini-2.5-pro
---

# developer-gemini (in-process MCP 호출 프로파일)

> **실행 모드별 차이**
>
> | 모드 | 사용 파일 | MCP 호출 주체 |
> |---|---|---|
> | **in-process** (이 파일) | `docs/agent-profiles/developer-gemini-mcp.md` | `invoke-agent` |
> | **teammate** | `agents/developer-gemini.md` | teammate 자체 |
> | **subagent** | (별도 파일 없음, `.mcp.json` 상속) | subagent 자체 |
>
> 이 파일은 **in-process 모드**에서 `invoke-agent` 가 `gemini_mcp` 를 호출할 때
> 참조하는 프로파일입니다.

## 실행 방식

```python
gemini_mcp.gemini_generate(
  model   = "gemini-3.1-flash",     # backed_by 에서 파싱, model 오버라이드 가능
  system  = <페르소나 합성 결과>,   # invoke-agent 가 experts/{slug}.md 에서 자동 구성
  context = <이전 결과 요약>,       # 임계값(2,000자/4건) 초과 시 압축본, 미만 시 원본
  prompt  = <이번 task 지시문>,
)
```

## 페르소나 합성 (invoke-agent 자동 처리)

`experts/{slug}.md` 에서 아래 순서로 추출:

1. `## 페르소나` → 역할명 + 특성
2. `## 역량` → 있으면 포함
3. `## 제약` → 있으면 포함

합성된 내용은 `system` 파라미터로 전달됩니다. **별도 프롬프트 수정 불필요.**

## 사전 조건

`gemini_mcp` MCP 서버가 `.mcp.json` 에 등록되어야 합니다.
→ `/relay:setup-keys` → `[1] Google Gemini` → `GEMINI_API_KEY` 입력

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
