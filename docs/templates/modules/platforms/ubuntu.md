---
id: ubuntu
type: platform
version: 1
scope: user
tags: [server, linux]
requires: []
conflicts_with: []
---

## Implementation Notes
- Ubuntu Server 22.04+ (ARM64)
- UFW 방화벽 (80, 443, 22만 개방)
- SSH 키 인증만 허용 (PasswordAuthentication no)
- systemd 서비스 관리
- apt 패키지 관리
- logrotate 로그 회전
