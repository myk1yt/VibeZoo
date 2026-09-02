# Requirement Checklist
## Task: VibeZoo 재설치 복구 + 품질 개선 + 설치 가이드 + README 갱신 + Push
## Date: 260830
## Session Folder: docs/260830_0001_session_reinstall-recovery-and-quality/
## Final Status (P7 VP Review 120000): 11/12 ✅ + REQ-012 🔶 (push 사용자 인증 대기)

- [x] [REQ-001] 저장소 연결 복구 — HTTPS remote 전환+GCM 준비, 로컬 main=origin/main(ef18b1f 시작) 확인. 커밋 d94e4df에서 총 16커밋
- [x] [REQ-002] Crow Memory MCP — 세션 실사용(recall/ingest) 정상, 글로벌 mcp_settings 9027 경로 확인 (093000)
- [x] [REQ-003] i18n 완전 지원 — ja nls 69/69키, py translations 212키×20언어 Missing=0/Empty=0 (094000/095500/114000)
- [x] [REQ-004] web_search Exa 설명 — 093000에서 이미 교정 확인, README 일치 (120000)
- [x] [REQ-005] 코드베이스 검색 정상화 — embedding TTL/백오프 + index_cache 영속화 + rebuild 툴/커맨드 복원 + 다운 안내 (7b0833a/ad38d6e/a88c63b/b4bc4cf/96ddbc1)
- [x] [REQ-006] 기능 쓸모 평가+삭제 — 9 MCP 툴, 13 커맨드, 메뉴 8, 설정 5 제거. 33툴/20커맨드 유지 (110000/111000/112000, 6109781/96ddbc1)
- [x] [REQ-007] 이미지 붙여넣기 UX — Dropzone 개편(자동저장+썸네일+마크다운 클립보드+히스토리)+vision 폴백 (287ee6b/b42470d)
- [x] [REQ-008] 일회성/오래된 docs 정리 — -p/, set_exa_key.py 등 휴지통, 구세션 docs→archive/260725/ git mv (115000, 7aefdec)
- [x] [REQ-009] Windows 설치 가이드 — docs/INSTALLATION.md 8단계 원큐+트러블슈팅 (d94e4df)
- [x] [REQ-010] macOS/Linux 설치 가이드 — 동일 파일 brew/apt 8단계 (d94e4df)
- [x] [REQ-011] README 전수 최신화 — 33툴/20커맨드/버전 0.15.1/링크 0 오류 (115500, d94e4df)
- [x] [REQ-012] git commit — 16커밋 논리 분리 완료(테스트 111/111 통과 후). push는 사용자 GCM 브라우저 인증 직후 실행 예정