# /relay:define-expert

전문가를 정의하고 `.claude/relay/experts/` 에 저장합니다.

## 사전 확인

`.claude/relay/domain-config.json` 이 없으면 `/relay:setup` 을 먼저 실행하도록 안내합니다.

## 대화 흐름

```
1. "어떤 전문가를 정의하시겠습니까?" 질문
2. 역할명·분야 파악
3. CLI variant 선택 (역할 매트릭스 기반 자동 추천)

   > "이 역할에 추천되는 CLI는 'codex' 입니다.
   >  다른 CLI를 선택하시겠습니까?
   >  [1] codex (추천) - 코드 생성, 아키텍처
   >  [2] gemini - 연구, 분석, 멀티모달
   >  [3] gemini-fast - 실시간, 대량 처리
   >  [4] codex-spark - 빠른 리뷰 (15x 빠름)
   >  [5] zai - 저비용 범용
   >  [6] 직접 입력"

4. Phase 배정

   > "이 전문가가 담당할 Phase를 선택하세요:"
   >  [ ] probe (연구/요구사항)
   >  [ ] grasp (설계/아키텍처)
   >  [ ] tangle (구현/개발)
   >  [ ] ink (리뷰/배포)

5. Tier 설정 (자동 추천)

   > "Tier: standard (추천)"
   >  [1] trivial - 단순 반복, 최저비용
   >  [2] standard - 일반 분석, 표준 개발
   >  [3] premium - 아키텍처, 복잡한 추론

6. Permission Mode 설정 (자동 추천)

   > "Permission Mode: plan (추천)"
   >  [1] plan - 읽기전용, 연구/설계
   >  [2] acceptEdits - 쓰기가능, 구현/디버깅
   >  [3] default - 전체도구, 리뷰/관리

7. 초안 제시 → 피드백 반영
8. .claude/relay/experts/{slug}.md 저장
```

## 저장 형식

```yaml
---
role: {역할명}
slug: {역할-슬러그}
cli: {cli-variant}                    # codex, codex-spark, gemini, gemini-fast, zai, claude-opus
model: {model-id}                     # gpt-5.3-codex, gemini-3-pro-preview, glm-4-air 등
fallback_cli: {cli-variant 또는 null}  # 실패 시 대체 CLI
tier: {trivial | standard | premium}  # 비용 등급
permission_mode: {plan | acceptEdits | default}  # 도구 권한
memory: {project | user | local}      # 컨텍스트 범위
isolation: {worktree | null}          # git worktree 격리
phases: [probe, grasp, tangle, ink]   # 담당 phase
capabilities: []                       # 역량 태그
created_at: {YYYY-MM-DD}
---

# {역할명}

## 페르소나
{직함, 전문 분야, 소통 스타일}

## 역량
- {할 수 있는 것}

## 제약
- {하지 않는 것}
```

## CLI Variant 목록

| CLI | 모델 | 용도 | Tier |
|---|---|---|---|
| `codex` | `gpt-5.3-codex` | 코드 생성, 아키텍처 | premium |
| `codex-spark` | `gpt-5.3-codex-spark` | 빠른 리뷰 (15x 빠름) | standard |
| `codex-mini` | `gpt-5.1-codex-mini` | 저비용 단순 작업 | trivial |
| `codex-reasoning` | `o3` | 심층 추론, 알고리즘 | premium |
| `codex-large-context` | `gpt-4.1` | 대형 코드 분석 (1M ctx) | premium |
| `gemini` | `gemini-3-pro-preview` | 연구, 분석, 멀티모달 | premium |
| `gemini-fast` | `gemini-3-flash-preview` | 실시간, 대량 처리 | standard |
| `claude-opus` | `claude-opus-4-6` | 전략, 최고 품질 | premium |
| `zai` | `glm-4-air` | 저비용 범용 | trivial |

## 역할 카테고리 → CLI 자동 매핑

| 카테고리 | 기본 CLI | Tier | Permission |
|---|---|---|---|
| 아키텍트/설계자 | `codex` | premium | plan |
| 백엔드/프론트엔드 개발자 | `codex` | premium | acceptEdits |
| DB/Cloud 설계자 | `codex` | premium | plan |
| TDD/QA 엔지니어 | `codex-spark` | standard | acceptEdits |
| 코드 리뷰어 | `codex-spark` | standard | default |
| 보안 감사 | `codex` | premium | default |
| DevOps/디버거 | `codex` | standard | acceptEdits |
| AI/UX/비즈니스 분석가 | `gemini` | standard | plan |
| 마케팅/재무/법무 | `gemini` | standard | plan |
| 문서/다이어그램 | `gemini-fast` | trivial | plan |
| 전략/연구 종합 | `claude-opus` | premium | plan |
| GLM 범용 작업자 | `zai` | trivial | acceptEdits |

## 완료 후

저장된 전문가를 팀에 배치하려면 `/relay:build-team` 을 실행합니다.
