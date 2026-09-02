# Requirement Checklist
## Task: Add Reset Button to Critical Error Notification
## Date: 260725

- [ ] [REQ-001] Critical 에러 알림(`showError`)에 "Reset Errors" 버튼 추가
- [ ] [REQ-002] "Reset Errors" 클릭 시 `~/.vibezoo-errors/registry.json` 파일 내용을 빈 배열 `[]`로 리셋
- [ ] [REQ-003] 리셋 후 `_lastCriticalCount` 초기화하여 알림 재발 방지
- [ ] [REQ-004] 리셋 후 StatusBar 에러 카운트 0으로 업데이트
