# Code Light Task Report

## Task Summary
D4-2: [`init_vibezoo.sh`](init_vibezoo.sh) 및 [`init_vibezoo.bat`](init_vibezoo.bat)에서 루트 `mcp-servers/` 또는 `REPO_DIR` 레벨의 `start_vibezoo_bridge.bat` 참조를 `extension/mcp-servers/` 경로로 교정. 092600 인벤토리 보고서의 [`init_vibezoo.sh#L16`](init_vibezoo.sh:16) 경로 문제 식별 건을 수행.

## Actions Taken

### 1. init_vibezoo.sh 수정
- **L16**: `"$REPO_DIR/start_vibezoo_bridge.bat"` → `"$REPO_DIR/extension/mcp-servers/start_vibezoo_bridge.bat"`
- L20~L23은 이미 `extension/mcp-servers/` 경로를 사용 중이어 수정 불필요
- 그 외 루트 `mcp-servers/` 참조 없음 확인

### 2. init_vibezoo.bat 추가 교정 (092600 보고서와 차이)
- 092600 보고서는 bat 파일이 이미 `extension`을 참조한다고 기술했으나, 실제 확인 결과 **L14도 동일 문제가 있었음**
- **L14**: `"%REPO_DIR%start_vibezoo_bridge.bat"` → `"%REPO_DIR%extension\mcp-servers\start_vibezoo_bridge.bat"`
- L19~L22는 이미 `extension\mcp-servers\` 경로 사용 중

### 3. 문법 검증
- Windows 환경에서 WSL 미설치로 `bash -n` 실행 불가
- 대체: `apply_diff` 후 `read_file`으로 수정 줄 시각 검증 수행 — 구문 정상 확인

## Result
✅ **Success** — 모든 mcp-servers 경로 교정 완료

| 파일 | 수정 줄 | Before | After |
|------|---------|--------|-------|
| [`init_vibezoo.sh`](init_vibezoo.sh:16) | L16 | `$REPO_DIR/start_vibezoo_bridge.bat` | `$REPO_DIR/extension/mcp-servers/start_vibezoo_bridge.bat` |
| [`init_vibezoo.bat`](init_vibezoo.bat:14) | L14 | `%REPO_DIR%start_vibezoo_bridge.bat` | `%REPO_DIR%extension\mcp-servers\start_vibezoo_bridge.bat` |

## Issues Discovered

### 🟡 init_vibezoo.bat L15-L16: 고아 .bat 참조 (범위 외)
- `init_vibezoo.bat` L15: `"%REPO_DIR%start_vibezoo_servers.bat"` — 파일이 프로젝트 어디에도 존재하지 않음
- `init_vibezoo.bat` L16: `"%REPO_DIR%watch_vibezoo_bridge.bat"` — 파일이 프로젝트 어디에도 존재하지 않음
- 현재 `.bat` 셀에 `copy /Y ... >nul` + `2>nul` 패턴이 없어 파일 미존재 시 silently fail 되거나 error 메시지 출력 가능
- **권장**: 별도 태스크에서 이 고아 참조 정리 필요 (D4-4 이후 범위 권장)

### 🟢 092600 보고서 inaccurate assessment
- 092600 보고서는 `init_vibezoo.bat`에 대해 "이미 extension을 참조한다"고 기술했으나, L14는 실제로 루트 레벨 `%REPO_DIR%start_vibezoo_bridge.bat` 참조 중이었음
- 이번 작업에서 교정 완료

## Next Step Recommendations
1. **D4-3**: `mcp-servers/` 루트 폴더 중복 코드 정리 작업으로 진행 (D4-4 아님 — D4-4에서 별도 처리 예정)
2. **D4-4 이후**: `init_vibezoo.bat` L15-L16 고아 `.bat` 참조 정리 (`start_vibezoo_servers.bat`, `watch_vibezoo_bridge.bat` 삭제 또는 경로 교정)
3. Windows 환경에서 WSL 설치 후 `bash -n init_vibezoo.sh` 문법 검증 재수행 권장

## Affected File List
| 파일 | 변경 유형 |
|------|----------|
| [`init_vibezoo.sh`](init_vibezoo.sh) | L16 경로 교정 |
| [`init_vibezoo.bat`](init_vibezoo.bat) | L14 경로 교정 |
