# /relay:read-context

공유 컨텍스트를 조회합니다. 모든 역할이 사용할 수 있습니다.

## 사용법

```
/relay:read-context                    # 전체 현황 요약
/relay:read-context ddl                # 설계 결정 목록
/relay:read-context ddl DDL-001        # 특정 DDL 내용
/relay:read-context domain             # 도메인 모델 목록
/relay:read-context plan               # 구현 계획 목록
/relay:read-context escalation         # 에스컬레이션 목록
```

## 전체 현황 요약 출력 형식

```
📁 .claude/relay/shared-context 현황
────────────────────────────────────

📋 설계 결정 (design-decisions/)
  DDL-001 [FINAL] 결제 모듈 독립 서비스 분리
  DDL-002 [REVIEW] 인증 서비스 아키텍처

🏗️ 도메인 모델 (domain-models/)
  DOMAIN-Order.md — Order, OrderItem, Payment
  DOMAIN-User.md  — User, UserProfile

📌 구현 계획 (implementation-plans/)
  PLAN-백엔드팀-DDL001.md — 진행률 60%

🚨 에스컬레이션 (escalations/)
  ESC-001 [OPEN] 결제 API 인터페이스 충돌
```

## 접근 권한 적용

역할의 접근 권한(`.claude/relay/experts/{slug}.md`)에 따라 보여주는 범위가 달라집니다.
