---
id: frontend-developer
kind: composed-agent
owner: relay
version: 1
base: frontend-core
capabilities:
  - rest-api
  - crud
  - list-filter-sort
available_platforms:
  - nextjs
default_policy: blog-default
default_agent: relay:developer-zai
---

# frontend-developer

## Purpose
Next.js/TypeScript 프론트엔드 구현. SSR 페이지, Admin UI, ISR 연동 담당.

## Runtime Rules
- Server Components를 기본으로 사용한다
- 플랫폼은 한 번에 하나만 선택한다
- policy는 항상 마지막에 덮어쓴다
