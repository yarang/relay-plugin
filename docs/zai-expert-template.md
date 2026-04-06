# Zai(GLM) 기반 전문가 작성 가이드

`backed_by: zai:*` 를 사용하는 전문가를 정의할 때 참고하는 가이드입니다.
context-compressor 전문가 설치는 [docs/experts/context-compressor.md](experts/context-compressor.md) 를 사용하세요.

---

## 모델 선택 가이드

| 모델 | 비용 | 컨텍스트 | 추천 용도 |
|---|---|---|---|
| `zai:glm-4-flash` | **무료** | 128K | 컨텍스트 압축·요약, 비용 최소화 |
| `zai:glm-4-air` | 저가 | 128K | 가벼운 범용 작업, 초안 생성 |
| `zai:glm-4` | 중가 | 128K | 고품질 추론, 기술 설계 |
| `zai:glm-4-long` | 중가 | **1M** | 초장문 문서 처리 |

API 키: [Zhipu AI BigModel Platform](https://bigmodel.cn)
등록 방법: `/relay:setup-keys` → `[3] Zhipu AI (GLM)`

---

## 전문가 파일 형식 (zai:* 전용)

```markdown
---
role: {역할명}
slug: {역할-슬러그}
domain: {소속 도메인}
backed_by: zai:glm-4          ← 모델 선택 (위 가이드 참고)
agent_profile: {definition id 또는 null}
default_platform: {플랫폼 또는 null}
created_at: {YYYY-MM-DD}
---

# {역할명}

## 페르소나
{직함, 전문 분야, 소통 스타일}
backed_by: zai:{모델} 의 기본 특성을 따르며, relay의 팀 구조에 편입됩니다.

## 역량
- {할 수 있는 것}

## 제약
- {하지 않는 것}

## 위임 설정
backed_by: zai:{모델}
agent_profile: {definition id 또는 null}
default_platform: {플랫폼 또는 null}
```

---

## invoke-agent 호출 시 동작

```python
zai_mcp.zai_generate(
  model   = "{glm-4-flash 등}",   # backed_by 에서 파싱
  system  = <페르소나 합성 결과>, # 페르소나 + 역량 + 제약 자동 합성
  context = <이전 결과 요약>,     # 임계값 초과 시 압축본, 미만 시 원본
  prompt  = <이번 task 지시문>,
)
```

`system` 파라미터는 `/relay:invoke-agent` 가 expert 파일에서 자동 합성합니다.
별도 프롬프트 수정 불필요.

---

## 활용 예시

### 비용 절감형 팀 리더

```yaml
backed_by: zai:glm-4
agent_profile: tech-lead
```

### 범용 개발자 (저비용)

```yaml
backed_by: zai:glm-4-air
agent_profile: backend-developer
default_platform: fastapi
```

### 컨텍스트 압축기 (무료)

→ [docs/experts/context-compressor.md](experts/context-compressor.md) 참조
