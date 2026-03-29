---
id: auth-jwt
type: capability
version: 1
scope: [backend, security]
requires: []
conflicts_with: []
---

JWT 기반 인증. Access Token(30min) + Refresh Token(7d cookie). bcrypt 비밀번호 해시.
OAuth2PasswordBearer 헤더에서 토큰 추출. Owner/Agent 이중 인증 분기.
