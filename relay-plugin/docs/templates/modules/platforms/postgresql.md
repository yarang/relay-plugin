---
id: postgresql
type: platform
version: 1
scope: [database]
requires: []
conflicts_with: []
---

## Implementation Notes
- PostgreSQL 16 (호스트 직접 설치, ARM64)
- asyncpg 드라이버 (blog-api)
- shared_buffers=1GB, effective_cache_size=3GB (24GB RAM 기준)
- pg_dump + cron 자동 백업
- pg_stat_statements 확장으로 쿼리 모니터링
