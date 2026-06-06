# Changelog

## v0.14.4 (2026-06-06)

### 🆕 New Feature: 다국어 분석 엔진 고도화

VibeZoo Bridge의 `review_code` 및 `find_bugs` 도구가 C++, Rust(완전 AST), Go(고도화), Shell, Dockerfile, YAML/JSON을 지원합니다.

#### C++ 지원 (AST 기반)
- raw pointer 지양 검사, new/delete 불일치 감지, 경계검사 우회(`[]` vs `.at()`), RAII 락 누락, C-style cast, printf/scanf
- config.py: SOURCE_EXTS에 C++ 확장자 추가

#### Rust AST 완전 분석
- unsafe 블록 복잡도 제어, 묵살된 Result/Option, panic/unwrap!, clone 남용, `as` 캐스트, println! 디버그

#### Go 분석 고도화
- 고루틴 루프 변수 캡처, defer 내 recover() 부재, unbuffered 채널 데드락, Mutex Unlock 누락, nil map 할당

#### 일반 소스 파일 지원
- Shell Script: 따옴표 누락, `set -e`/`pipefail`, shellcheck 연동
- Dockerfile: latest 태그, apt-get 캐시, USER 부재, ADD vs COPY
- YAML/JSON: 중복 키, 하드코딩 시크릿

#### find_bugs 네이티브 린터 연동
- Rust: `cargo clippy --frozen`
- Go: `go vet -mod=readonly`
- C++: `cppcheck --enable=all --xml`

### 🐛 Bug Fixes
- Dockerfile 리뷰 경로 차단 수정 (확장자 없는 파일 처리)
- 정규식 개선: C++ raw pointer, Rust as cast, Go 고루틴 캡처, Shell 변수 등
- 서브프로세스 타임아웃 증가 (cargo/cppcheck 120s, go vet 60s)
- cppcheck XML 파싱 xml.etree.ElementTree 사용
- 보안: cargo clippy --frozen, go vet -mod=readonly

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
