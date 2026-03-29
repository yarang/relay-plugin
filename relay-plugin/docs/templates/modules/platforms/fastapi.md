---
id: fastapi
type: platform
version: 1
scope: [backend, python]
requires: []
conflicts_with: [django]
---

## Implementation Notes
- APIRouter 사용, 버전 접두사 `/api/v1/`
- Pydantic v2 BaseModel + ConfigDict
- async def + AsyncSession (SQLAlchemy 2.0)
- Depends 주입 패턴 (get_db, get_owner, get_agent)
- BlogAPIError + 전역 핸들러 (Shared Contract A)
- OAuth2PasswordBearer로 Authorization 헤더 처리 (Shared Contract B)
