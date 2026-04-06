# Architecture v2 — 모순·미결·확인 필요 항목

**작성일**: 2026-04-06  
**대상 문서**: docs/architecture-v2.md  
**상태**: 검토 중 — 결정 필요 항목은 `[DECIDE]`, 확인된 모순은 `[CONFLICT]`, 미완성은 `[INCOMPLETE]`

---

## [CONFLICT] 1. team-building-rules.md 스키마가 v2와 충돌

**위치**: `docs/team-building-rules.md` § 3.1, § 3.2

현재 `team-building-rules.md`의 전문가 파일 스키마:

```yaml
cli: {cli-variant}
model: {model-id}
fallback_cli: ...
tier: ...
permission_mode: ...
memory: ...
isolation: ...
phases: [...]
specs: []
```

v2 설계의 Expert 파일 스키마:

```yaml
role: ...
slug: ...
domain: ...
specs: []
created_at: ...
```

`cli`, `model`, `fallback_cli`, `tier`, `permission_mode`, `memory`, `isolation`, `phases`는 v2에서 Expert에서 제거되고 Executor/Agent로 이동합니다.  
**team-building-rules.md 전체 스키마 섹션을 v2 기준으로 재작성해야 합니다.**

---

## [CONFLICT] 2. team-building-rules.md § 1.1 역할 매트릭스가 Expert에 CLI/Tier를 배정

**위치**: `docs/team-building-rules.md` § 1.1

```text
| 백엔드 개발자 | codex | gpt-4o | premium | tangle | acceptEdits |
```

v2에서는 CLI/Tier/phases가 Expert가 아니라 Executor/Agent에 속합니다.
역할 매트릭스의 컬럼 구조를 바꿔야 합니다:

- `CLI`, `모델`, `Tier` → Executor 참조 추천값으로 표현
- `Phase`, `Permission` → Agent 기본값 추천으로 표현

---

## [CONFLICT] 3. build-team.md가 expert_slug를 멤버로 참조

**위치**: `.claude/commands/build-team.md` § 저장 형식

```json
"members": [{
  "role": "...",
  "expert_slug": "...",
  "cli": "...",
  ...
}]
```

v2에서는 `expert_slug` → `agent` (Agent.slug 참조)로 변경됩니다.  
build-team 커맨드 전체를 agent 선택 흐름으로 재작성해야 합니다.

---

## [CONFLICT] 4. define-expert.md가 CLI/모델/phases/tier 입력 단계를 포함

**위치**: `.claude/commands/define-expert.md` § 2. CLI 선택, § 3. Phase 배정, § 4. Tier 설정, § 5. Permission Mode

v2에서 이 단계들은 Expert 정의에서 제거됩니다.  
대신 `/relay:define-executor`와 `/relay:define-agent`로 분리됩니다.

---

## [CONFLICT] 5. expert-builder.md 저장 형식이 v2 Expert 스키마와 불일치

**위치**: `.claude/agents/expert-builder.md` § 저장 형식

현재 저장 형식에 `cli`, `model`, `fallback_cli`, `tier`, `permission_mode`, `memory`, `isolation`, `phases`가 포함됩니다.  
v2 Expert는 이 필드들을 갖지 않습니다.

---

## [CONFLICT] 6. agent-definition-and-invocation.md의 조립 순서가 v2와 맞지 않음

**위치**: `docs/agent-definition-and-invocation.md` § 6. 조립 순서

```text
1. expert 파일 또는 definition 파일 로드
2. base 로드
3. specs 로드
4. platform 로드
5. policy 로드
6. task overlay 결합
7. backed_by 또는 default_agent 로 실행
```

v2에서는 실행 주체가 `backed_by` → `execute_by (Executor)` 로 변경됩니다.  
7번 단계: `executor 파일 로드 → keys.json → 환경변수 → CLI 호출`로 재작성해야 합니다.

---

## [CONFLICT] 7. phase_routing 값 타입 불일치

**위치**: `docs/architecture-v2.md` § 2-4 Team 예시

```json
"phase_routing": {
  "probe":  "gemini",
  "grasp":  "codex_gpt_5.4",
  "tangle": "codex_gpt_5.4",
  "ink":    "zai_glm_4_air"
}
```

`probe`는 CLI 이름(`gemini`), 나머지는 Executor slug(`codex_gpt_5.4`)가 혼용됩니다.  
**phase_routing 값이 CLI 이름인지 Executor slug인지 통일해야 합니다.**  
v2 구조에서는 Executor slug로 통일하는 것이 일관됩니다.

---

## [CONFLICT] 8. 검증 4 "CLI 가용성"이 Agent 기반으로 변경되어야 함

**위치**: `docs/team-building-rules.md` § 4.1, `.claude/commands/build-team.md` § 6종 검증

현재: `members의 cli가 설치되어 있는지 확인`  
v2: TeamMember는 cli를 직접 갖지 않음. Agent → Executor → cli 를 따라가야 함.  
검증 로직: `member.agent → agents/{slug}.md → execute_by → executors/{slug}.md → cli 확인`

---

## [CONFLICT] 9. 검증 6 "Tier 분산"이 v2에서 의미 없음

**위치**: `build-team.md` § 검증 6, `team-building-rules.md` § 4.1

v2에서 `tier`가 제거됩니다. Executor의 `model`로 비용 추론해야 합니다.  
**검증 6을 "비용 집중도" 검증으로 재정의하거나 제거해야 합니다.**

---

## [DECIDE] 10. backed_by 호환 파싱에서 Agent가 없는 경우 처리

**위치**: `docs/architecture-v2.md` § 5. 마이그레이션

마이그레이션 파싱 규칙이 "Agent에 execute_by 없고 Expert에 backed_by 있음"을 다룹니다.  
그런데 v2에서 `/relay:invoke-agent`는 Agent slug만 받습니다.  
**기존 Expert만 있고 Agent 파일이 없을 때 어떻게 invoke-agent를 호출하는가?**

선택지:

- A. `invoke-agent {expert-slug}` 도 허용 (Expert slug → 임시 Agent 생성)
- B. 마이그레이션 커맨드 (`/relay:migrate`)로 Agent 파일 먼저 생성 강제
- C. Expert에 `backed_by`가 있으면 Agent 파일 없이도 인라인 실행 허용

---

## [DECIDE] 11. agent-profiles/ 처리 방향 미결

**위치**: `docs/architecture-v2.md` § 9. 미결 사항, `docs/agent-profiles/`

현재 두 파일 존재:

- `docs/agent-profiles/developer-gemini-mcp.md` — `backed_by: gemini:...`, `override_models`, MCP 호출 방식
- `docs/agent-profiles/developer-openai-mcp.md` — `auth_modes: [api_key, oauth]`, MCP 호출 방식

Executor가 `cli + model + auth`를 담으면 이 파일들의 내용 대부분이 중복됩니다.  
**Executor로 완전 통합 또는 `executor.profile_ref`로 참조 유지 중 결정 필요.**

---

## [DECIDE] 12. build-team 검증에서 Agent 미존재 시 처리

팀 구성 시 선택한 agent slug에 해당하는 파일이 없을 경우:

- 오류로 중단?
- 경고 후 진행 (나중에 생성)?
- Agent 파일을 인라인으로 즉시 생성?

**build-team 흐름에서 agent 파일 존재 여부 검증 규칙이 없습니다.**

---

## [INCOMPLETE] 13. /relay:define-executor 커맨드 파일 없음

**위치**: `docs/architecture-v2.md` § 7. 슬래시 커맨드

신규 커맨드로 명시되었으나 `.claude/commands/define-executor.md` 파일이 존재하지 않습니다.

---

## [INCOMPLETE] 14. /relay:define-agent 커맨드 파일 없음

신규 커맨드로 명시되었으나 `.claude/commands/define-agent.md` 파일이 존재하지 않습니다.

---

## [INCOMPLETE] 15. plugin.json에 신규 커맨드 미등록

**위치**: `.claude-plugin/plugin.json`

`define-executor`, `define-agent`가 commands 배열에 없습니다.

---

## [INCOMPLETE] 16. TypeScript 타입에서 backed_by 호환 필드 누락

**위치**: `docs/architecture-v2.md` § 6. 타입 정의, `vscode-agent-manager/src/types/index.ts`

v2 TypeScript `Expert` 인터페이스에 `backed_by`가 없습니다.  
마이그레이션 호환성을 위해 `backed_by?: string` (deprecated)을 포함해야 합니다.

현재 `types/index.ts`의 Expert 인터페이스에는 `capabilities?: string[]`도 남아 있습니다.  
v2에서는 제거 대상입니다.

---

## [INCOMPLETE] 17. keys.json 스키마에 strategy 기본값 없음

**위치**: `docs/architecture-v2.md` § 3. Key Registry

`keys.json` 항목에는 `provider`, `env`, `type`만 있습니다.  
Executor의 `auth.strategy`가 없을 때 기본값이 정의되지 않았습니다.  
**기본값 `fallback`으로 명시 필요.**

---

## 요약

| 번호 | 유형 | 대상 파일 | 상태 | 조치 |
| --- | --- | --- | --- | --- |
| 1 | CONFLICT | team-building-rules.md § 3 | ✅ 완료 | Expert/Executor/Agent/Team 스키마 v2로 재작성 |
| 2 | CONFLICT | team-building-rules.md § 1.1 | ✅ 완료 | 역할 매트릭스 Executor slug 기준으로 변경 |
| 3 | CONFLICT | build-team.md | ✅ 완료 | expert_slug → agent 참조로 변경, phase_routing Executor slug 통일 |
| 4 | CONFLICT | define-expert.md | ✅ 완료 | CLI/Phase/Tier 입력 단계 제거, v2 흐름으로 재작성 |
| 5 | CONFLICT | expert-builder.md | ✅ 완료 | 저장 형식 v2 Expert로 업데이트 |
| 6 | CONFLICT | agent-definition-and-invocation.md | ⏳ 미완 | 조립 7단계 executor 기반으로 재작성 필요 |
| 7 | CONFLICT | architecture-v2.md | ✅ 완료 | phase_routing 값 Executor slug로 통일 |
| 8 | CONFLICT | build-team.md, team-building-rules.md | ✅ 완료 | 검증 4 Agent→Executor→cli 체인으로 변경 |
| 9 | CONFLICT | build-team.md, team-building-rules.md | ✅ 완료 | 검증 6 비용 집중도로 재정의 |
| 10 | DECIDE | architecture-v2.md § 5 | ⏳ 미결 | Agent 없는 Expert invoke: backed_by 인라인 fallback 허용 (define-agent.md에 명시됨) |
| 11 | DECIDE | agent-profiles/ | ⏳ 미결 | Executor 통합 여부 — 1차 구현 후 결정 |
| 12 | DECIDE | build-team.md | ⏳ 미결 | Agent 파일 미존재 시 처리 방식 결정 |
| 13 | INCOMPLETE | commands/ | ✅ 완료 | define-executor.md 신규 작성 |
| 14 | INCOMPLETE | commands/ | ✅ 완료 | define-agent.md 신규 작성 |
| 15 | INCOMPLETE | plugin.json | ✅ 완료 | define-executor, define-agent 등록 |
| 16 | INCOMPLETE | types/index.ts | ⏳ 미완 | Expert 타입 v2 기준 업데이트 필요 |
| 17 | INCOMPLETE | architecture-v2.md | ✅ 완료 | auth.strategy 기본값 `fallback` 명시 |
