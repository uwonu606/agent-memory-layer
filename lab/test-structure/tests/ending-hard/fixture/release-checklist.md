---
name: release-checklist
description: 배포 전에 확인하는 목록
metadata:
  type: project
---

1. 변경 목록을 `CHANGELOG.md`에 옮긴다.
2. 결제 스테이징(`pay-stg.internal:8443`)에서 결제 한 건을 돌려 본다.
3. 목요일 오전 10시 이전에 태그를 단다.
