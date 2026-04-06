---
id: backend-developer
kind: composed-agent
owner: relay
version: 1
base: backend-core
specs:
  - rest-api
  - crud
  - auth-jwt
  - list-filter-sort
  - markdown-renderer
available_platforms:
  - fastapi
default_policy: blog-default
default_agent: relay:developer-zai
---

# backend-developer

## Purpose
FastAPI/Python 백엔드 기능 구현. API 설계, CRUD, 인증, Markdown 렌더링 담당.

## Runtime Rules
- 플랫폼은 한 번에 하나만 선택한다
- policy는 프로젝트 규칙이므로 항상 마지막에 덮어쓴다
- 실행 결과는 runs 디렉토리에 남긴다
