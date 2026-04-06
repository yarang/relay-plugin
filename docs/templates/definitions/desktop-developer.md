---
id: desktop-developer
kind: composed-agent
owner: relay
version: 1
base: desktop-core
specs:
  - rest-api
  - list-filter-sort
available_platforms:
  - tauri
default_policy: blog-default
default_agent: relay:developer-zai
---

# desktop-developer

## Purpose
크로스플랫폼 데스크탑 애플리케이션 개발. Tauri/Rust 백엔드 + React 프론트엔드.

## Runtime Rules
- 플랫폼은 한 번에 하나만 선택한다
- 네이티브 기능은 Tauri 명령으로 래핑한다
- 크로스 플랫폼 호환성을 항상 확인한다
