# VibeZoo v0.14.3 Release Notes

**Release Date**: 2026-06-05

## 🆕 New Feature: Guard.git

AI 에이전트가 실수로 `rm -rf *` / `rmdir /s /q` 등을 실행하여 프로젝트의 `.git` 폴더가 통째로 삭제되는 것을 방지합니다.

### 주요 기능
- **OS 레벨 ACL 보호**: Windows `icacls` / Linux `chattr` / macOS `chmod`로 `.git` 폴더 삭제 차단
- **VibeZoo 탭 토글**: TreeView에서 Guard.git On/Off 원클릭 제어
- **멀티 루트 워크스페이스 지원**: 여러 프로젝트 폴더 동시 보호
- **Git Worktree 대응**: Worktree 환경에서도 실제 git 디렉토리 추적 보호
- **FileSystemWatcher**: `.git` 삭제/이름변경 실시간 감시
- **Yocto 스냅샷**: `.git` 핵심 파일(HEAD, config, refs) 주기적 백업
- **SelfCheck 통합**: `.git` 무결성 자가진단

### 보안 강화
- `execFile()`만 사용하여 Shell injection 방지 (CVE 예방)
- Linux `sudo` 사용 금지 (VS Code Extension TTY 없음)
- 경로 검증 정규식 + 10초 타임아웃
- 잔여 ACL 자동 정리 (Extension crash 복구)

### 설정
- `vibezoo.guard.enabled`: Guard.git 전체 활성화 (기본: true)
- `vibezoo.guard.autoEnable`: YOLO 모드 진입 시 자동 활성화 (기본: true)
- `vibezoo.guard.yoctoBackupEnabled`: .git 스냅샷 사용 (기본: true)
- `vibezoo.guard.yoctoBackupIntervalMin`: 스냅샷 간격 (기본: 30분)
- `vibezoo.guard.integrityCheckIntervalMin`: 무결성 진단 간격 (기본: 5분)
- `vibezoo.guard.linuxUseChattr`: Linux에서 chattr 사용 (기본: false)
