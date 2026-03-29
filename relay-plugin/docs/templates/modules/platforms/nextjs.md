---
id: nextjs
type: platform
version: 1
scope: [frontend, typescript]
requires: []
conflicts_with: []
---

## Implementation Notes
- Next.js 15 App Router (standalone 모드)
- Server Components 기본, Client Components 필요시 "use client"
- ISR revalidateTag/revalidatePath (Shared Contract C)
- Tailwind CSS 스타일링
- API Routes: /api/revalidate (ISR 수신)
- 환경변수: NEXT_PUBLIC_API_URL
