---
id: cloudflare
type: platform
version: 1
scope: user
tags: [infrastructure, dns]
requires: []
conflicts_with: []
---

## Implementation Notes
- Cloudflare Dashboard / API로 관리
- SSL/TLS 모드: Full (Strict)
- Origin CA 인증서 (15년 유효, Nginx에 설치)
- Cloudflare real_ip_header: CF-Connecting-IP
- Proxy 모드 (주황색 구름) 활성화
- DNS 전파 확인: dig/nslookup
