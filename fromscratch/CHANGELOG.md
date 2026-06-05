# Changelog

## v0.14.3 (2026-06-05)

### 🆕 New Feature: Guard.git
- `.git` 폴더 삭제 방지 기능 (OS 레벨 ACL: Windows icacls / Linux chattr / macOS chmod)
- VibeZoo 사이드바 Active Subagents에 Guard.git On/Off 토글 노드
- 멀티 루트 워크스페이스 지원
- Git Worktree 대응
- Yocto 스냅샷 + SelfCheck 무결성 진단

### 🐛 Bug Fixes
- **Shell injection 방지**: `exec()` → `execFile()` 전환, 경로 검증, 10초 타임아웃
- **sudo hang 방지**: Linux `sudo` 사용 금지, 즉시 Watcher+Yocto fallback
- **멀티 루트 지원**: `workspaceFolders` 배열 전체 순회, 동적 폴더 변경 대응
- **한글 경로 문제**: `SAFE_PATH_REGEX` → `DANGEROUS_PATH_REGEX`로 변경 (유니코드 문자 허용)
- **Race condition**: `activate()`/`enable()` `await` 추가로 순차 실행 보장
- **잔여 ACL 정리**: Extension crash 후 재시작 시 자동 정리
- **빈 gitDirPaths 허위 성공**: `.git` 없을 때 `{success:false}` 반환
- **사용자 알림**: enable 실패 시 `showWarningMessage` 표시

### 🔧 Maintenance
- TypeScript 컴파일 + 설치된 확장 디렉토리 동기화
- `out/` 디렉토리 Git 트래킹 (`.gitignore` 우회)
- l10n: 영문/한국어 로컬라이제이션
