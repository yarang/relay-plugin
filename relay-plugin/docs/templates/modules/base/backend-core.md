---
id: backend-core
type: base
version: 1
scope: [backend, python]
---

## Responsibilities
- API 설계 및 엔드포인트 구현
- 비동기 데이터베이스 조작 (SQLAlchemy 2.0 async)
- Pydantic v2 스키마 검증
- 에러 처리 (BlogAPIError envelope)
- 서비스 레이어 분리 (router → service → model)
- 인증/인가 로직 (JWT + Bearer Token)
