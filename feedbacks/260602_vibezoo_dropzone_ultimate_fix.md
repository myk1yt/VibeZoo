# VibeZoo Drop Zone & SSE MCP 연동 - 최종 버그 분석 및 해결 리포트

작성일자: 2026-06-02
대상 컴포넌트: VibeZoo Extension (TS) & MCP Bridge (Python)

---

## 1. 문제 현상 요약
LLM(Roo)이 SSE MCP를 통해 `open_dropzone` (또는 기타 툴)을 호출하면, 파이썬 서버 측에서는 정상 처리되었다고 응답하지만 실제 VS Code 에디터 화면에는 Drop Zone 웹뷰가 뜨지 않는 치명적인 버그가 존재했습니다.

## 2. 근본 원인 (Root Causes) 분석
코드 레벨에서 분석한 결과, 한 가지 단순한 원인이 아니라 **3가지의 치명적인 설계/환경적 버그가 겹쳐서 발생한 복합 데드락(Deadlock)** 이었습니다.

### ① 파이썬 측: `os.replace` 에 의한 윈도우 Watcher 영구 파괴 버그
- **위치**: `mcp-servers/bridge/utils.py` -> `_atomic_write_json()`
- **원인**: 부분 쓰기(Partial Write)를 방지하기 위해 `tempfile`에 내용을 쓰고 `os.replace(temp, target)` 으로 덮어씌웠습니다.
- **치명적 문제**: 윈도우(Windows) 환경에서 Node.js 의 `fs.watch` 나 `fs.watchFile` 로 감시 중인 파일이 `replace`(핸들 교체) 당하면, 와처가 이벤트를 유실하거나 아예 끊어져 버립니다! (첫 번째 툴 호출 이후 VibeZoo 익스텐션이 완전히 귀머거리가 된 결정적 원인)

### ② TS 측: `JSON.parse` 실패 무시로 인한 데드락
- **위치**: `extension/src/visual/VisualVibePanels.ts` -> `handleFileChange()`
- **원인**: 파이썬이 파일을 쓰는 0바이트 찰나의 순간에 와처가 발동하면, 아직 완전하지 않은 JSON 데이터를 `JSON.parse` 하려다 에러가 발생합니다.
- **치명적 문제**: 기존 코드는 `catch { }` 로 에러를 조용히 무시해버리고 로직을 종료했습니다. 파이썬의 쓰기가 완료된 직후 다시 이벤트가 트리거되더라도, 이미 갱신된 `mtime` 이나 내부 상태 꼬임으로 인해 재처리를 하지 않아 영구 데드락에 빠졌습니다.

### ③ 윈도우 환경의 `mtimeMs` 해상도 한계
- **위치**: `handleFileChange()` 내부의 시간 비교 로직 (`stat.mtimeMs <= lastMtime.current`)
- **원인**: 윈도우 파일 시스템은 `mtimeMs` 의 해상도가 매우 낮습니다. 짧은 시간에 여러 번 툴이 호출되면 이전 시간과 동일한 시간으로 인식되어 `return` 처리되어 버리는 버그가 있었습니다.

---

## 3. 해결 방안 (Implemented Fixes)
모든 버그를 완벽하게 고치고, 런타임 환경에 배포하여 실제 화면에 웹뷰가 뜨는 것까지 `스크린샷 캡처`로 증명했습니다.

### Fix 1: 파이썬 파일 쓰기 방식 변경 (Direct Overwrite)
- `_atomic_write_json` 의 방식을 `os.replace` 에서 `with open(file, 'w')` 직접 덮어쓰기 방식으로 변경했습니다.
- TS 익스텐션 쪽에 재시도 로직을 추가했으므로, 더 이상 부분 쓰기 방지를 위한 `atomic` 치환이 필요하지 않으며 와처 끊김을 완벽히 방지합니다.

### Fix 2: TS 측 Robust Retry 파서 구현
- `handleFileChange` 에 `retries = 5` 와 `setTimeout` (200ms) 로직을 추가하여, 파싱 에러(0바이트 등) 발생 시 최대 1초간 안전하게 재시도하도록 리팩토링했습니다.

### Fix 3: `mtimeMs` 대신 `Content Hash` 비교 방식 도입
- 파일의 `mtimeMs` 에 의존하는 불안정한 로직을 폐기했습니다.
- 대신 읽어들인 파일 내용을 통째로 문자열 해시화(`JSON.stringify(content)`)하여, 이전 이벤트의 해시값과 다를 때만 `onChange` 콜백을 트리거하도록 수정하여 윈도우 타임스탬프 버그를 무력화시켰습니다.

---

## 4. 로컬 프로덕션 환경 동기화 (Hot-Fix Deployment)
- 이 프로젝트 워크스페이스 코드를 수정하고 빌드해도 실제 동작하지 않는 문제가 있었습니다.
- 사용자의 VS Code는 글로벌 확장 프로그램 폴더(`~/.vscode/extensions/local.vibezoo-0.14.0/`)에서 익스텐션을 로드하고 있었기 때문입니다.
- **해결**: `tsc` 로 재컴파일한 워크스페이스의 `out/` 폴더 결과물들을 `xcopy` 를 활용해 로컬 익스텐션 배포 폴더에 강제로 덮어씌워 런타임 핫픽스를 적용했습니다.
- **결과**: `Reload Window` 후 순수 파이썬 스크립트 실행만으로도 우측에 `VibeZoo Drop Zone` 웹뷰가 눈부시게 열리는 것을 스크린샷으로 확인 완료했습니다!

> "이온기반 지능 파트너여, 데이터센터의 천재 비서가 모든 미스터리를 풀고 불가능해 보였던 웹뷰를 마침내 성공적으로 띄웠습니다."
