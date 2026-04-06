# /relay:progress-sync

역할에 따라 맞춤화된 진행 현황을 조회·보고합니다.

## 사용법

```
/relay:progress-sync            # 현재 역할에 맞는 뷰 자동 선택
/relay:progress-sync report     # 현재 역할의 진행 상황을 공유 컨텍스트에 기록
```

## 뷰별 출력

### 상위팀 뷰 (steering-orchestrator)

```
🏛️ 전체 프로젝트 현황
────────────────────
팀                진행률    상태
백엔드팀          ████░░  60%   정상
프론트엔드팀      ██░░░░  30%   지연
인프라팀          ██████ 100%  완료

🚨 미해결 에스컬레이션: 1건
📋 FINAL DDL 중 PLAN 미생성: 1건
```

### 팀 리더 뷰 (team-leader)

```
👔 {팀명} 진행 현황
────────────────────
PLAN: PLAN-백엔드팀-DDL001.md

구현 항목              상태      담당
결제 도메인 엔티티    🔵 REFACTOR  developer-A
주문 리포지토리       🟢 GREEN     developer-B
결제 API 엔드포인트   🔴 RED       developer-A

전체: 3/8 완료 (37%)
블로커: 없음
```

### 개발자 뷰 (developer)

```
💻 {전문가명} 진행 현황
────────────────────
현재 작업: 결제 도메인 엔티티
단계: 🔵 REFACTOR
PLAN 체크박스: 3/5 완료

다음 작업: 주문 리포지토리 (🔴 RED 예정)
```

## report 모드

진행 상황을 `.claude/relay/shared-context/status-board/{팀-슬러그}.md` 에 기록합니다.
