---
id: blog-default
type: policy
version: 1
scope: [project]
---

## Rules
- 기존 디렉토리 구조를 우선 유지한다
- Shared Contracts A/B/C/D를 준수한다 (CLAUDE.md 참조)
- 에이전트 포스트는 반드시 pending_review로 생성한다 (bypass 금지)
- MinIO 직접 접근 금지, Presigned URL 방식만 허용
- API 응답은 envelope 형식 ({data, meta} 또는 {error})
- 커밋 메시지: feat:/fix:/chore:/docs: 접두사
- 위험한 마이그레이션(마이그레이션 실패, 데이터 손실 가능)은 사전 승인 필수
- 프로덕션 파괴적 작업(rm -rf, DROP TABLE)은 사전 승인 필수
- 보안 민감 정보(API 키, 비밀번호)는 코드에 하드코딩하지 않는다
