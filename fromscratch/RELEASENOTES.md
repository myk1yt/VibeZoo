# VibeZoo v0.14.4 Release Notes

**Release Date**: 2026-06-06

## 🆕 New Feature: 다국어 분석 엔진 고도화

VibeZoo Bridge의 `review_code` 및 `find_bugs` 도구가 C++, Rust(완전 AST), Go(고도화), Shell, Dockerfile, YAML/JSON을 지원합니다.

### C++ 지원 (AST 기반)
- raw pointer 지양 검사, new/delete 불일치 감지, 경계검사 우회(`[]` vs `.at()`), RAII 락 누락, C-style cast, printf/scanf
- config.py: SOURCE_EXTS에 C++ 확장자 추가

### Rust AST 완전 분석
- unsafe 블록 복잡도 제어, 묵살된 Result/Option, panic/unwrap!, clone 남용, `as` 캐스트, println! 디버그

### Go 분석 고도화
- 고루틴 루프 변수 캡처, defer 내 recover() 부재, unbuffered 채널 데드락, Mutex Unlock 누락, nil map 할당

### 일반 소스 파일 지원
- Shell Script: 따옴표 누락, `set -e`/`pipefail`, shellcheck 연동
- Dockerfile: latest 태그, apt-get 캐시, USER 부재, ADD vs COPY
- YAML/JSON: 중복 키, 하드코딩 시크릿

### find_bugs 네이티브 린터 연동
- Rust: `cargo clippy --frozen`
- Go: `go vet -mod=readonly`
- C++: `cppcheck --enable=all --xml`

### 🐛 Bug Fixes
- Dockerfile 리뷰 경로 차단 수정 (확장자 없는 파일 처리)
- 정규식 개선: C++ raw pointer, Rust as cast, Go 고루틴 캡처, Shell 변수 등
- 서브프로세스 타임아웃 증가 (cargo/cppcheck 120s, go vet 60s)
- cppcheck XML 파싱 xml.etree.ElementTree 사용
- 보안: cargo clippy --frozen, go vet -mod=readonly

---

## 🆕 New Feature: Guard.git (v0.14.3)

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

### 🐛 Bug Fixes (v0.14.3)
- **한글 경로 문제**: `SAFE_PATH_REGEX` → `DANGEROUS_PATH_REGEX`로 변경하여 유니코드 문자(한글 포함) 허용
- **Race condition 수정**: `activate()`/`enable()`에 `await` 추가로 순차 실행 보장
- **확장 로딩 경로 동기화**: TypeScript 컴파일 + 설치된 확장 디렉토리 동기화로 Guard.git 동작 불일치 해소
- **Shell injection 방지**: `exec()` → `execFile()` 전환, 경로 검증 정규식 + 10초 타임아웃
- **sudo hang 방지**: Linux `sudo` 사용 금지, Watcher+Yocto fallback 즉시 전환
- **잔여 ACL 정리**: Extension crash 후 재시작 시 자동 정리 (`_cleanupResidualACL`)
- **빈 gitDirPaths 허위 성공**: `.git` 없을 때 `{success:false}` 반환
- **사용자 알림**: enable 실패 시 `showWarningMessage` 표시
