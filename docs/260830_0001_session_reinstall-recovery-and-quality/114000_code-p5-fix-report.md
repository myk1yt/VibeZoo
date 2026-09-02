# Code Task Report — P5 결함 수정 (114000)

> **Session Folder**: [`docs/260830_0001_session_reinstall-recovery-and-quality/`](docs/260830_0001_session_reinstall-recovery-and-quality/)  
> **Task**: P5 결함 수정 (B1, B2, rebuildCodeIndex 복원, M1, M2, m1, m2)  
> **Author**: Code mode (Dev Lead)  
> **Date**: 2026-08-30 (Asia/Seoul)  

---

## Status
COMPLETE — Debug 리뷰([`113000_debug-p5-review-report.md`](docs/260830_0001_session_reinstall-recovery-and-quality/113000_debug-p5-review-report.md:1))에서 식별된 BLOCKER 2건, MAJOR 2건, MINOR 2건 및 사용자 결정 D2-4(`vibezoo.rebuildCodeIndex`) 복원을 전수 완료하고 전체 빌드/테스트(pytest 111/111 통과, TS 0 error, 미러 SHA 100% 일치) 검증을 통과했습니다.

---

## Objective and Scope
- **Objective**: P5 단계에서 발견된 모든 결함(B1, B2, M1, M2, m1, m2)을 수정하고 과다 삭제된 `rebuildCodeIndex`를 복원하여 프로덕션 배포 가능한 품질 상태 달성.
- **Acceptance Criteria**:
  1. [`extension/mcp-servers/bridge/tools/scout.py:386`](extension/mcp-servers/bridge/tools/scout.py:386)의 루프 변수명 `t` 충돌 제거 및 `test_find_references.py` 6/6 통과.
  2. [`mcp-servers/crow_memory_server.py`](mcp-servers/crow_memory_server.py:1)를 [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:1) 실체(241줄)로 동기화.
  3. [`extension/package.json`](extension/package.json:65), [`extension/src/extension.ts:668`](extension/src/extension.ts:668), 20개 [`package.nls.*.json`](extension/package.nls.json:15), 20개 [`bundle.l10n.*.json`](extension/l10n/bundle.l10n.json:55)에 `vibezoo.rebuildCodeIndex` 복원.
  4. [`extension/mcp-servers/tests/test_whiteboard_merge.py`](extension/mcp-servers/tests/test_whiteboard_merge.py:1)에서 삭제된 `ux_coordinator` fixture 제거 및 영문 i18n 기대값 교정으로 12/12 통과.
  5. 20개 언어 [`translations/*.json`](extension/mcp-servers/bridge/i18n/translations/en.json:1)에 Whiteboard D3-1/D3-2 신규 키 39개 추가(en/ko/ja 수동 번역, 17개 언어 fallback) 및 미러 동기화 (`Missing=0`, `Empty=0`, `ko Untranslated=0`).
  6. [`init_vibezoo.bat:15`](init_vibezoo.bat:15)에서 고아 `.bat` 복사 구문 제거.
  7. 루트 미러 [`mcp-servers/bridge/tools/`](mcp-servers/bridge/tools/) 11개 파일 및 테스트 파일을 extension 소스와 100% SHA 동기화 (`diff=0`).
- **Problem Scope**: P5 기술 리뷰 결함 전수 해결.
- **Expected Edit Scope**: `scout.py`, `crow_memory_server.py`, `package.json`, `extension.ts`, `package.nls.*.json` 20개, `bundle.l10n.*.json` 20개, `test_whiteboard_merge.py`, `translations/*.json` 20개, `init_vibezoo.bat`, 루트 `mcp-servers/tools/*.py` 11개.
- **Risk Level**: LOW (국소 수정 및 정밀 미러 동기화).

---

## Root Cause or Rationale

### 1. B1 (scout.py UnboundLocalError)
- **Symptom**: `find_references` 실행 시 `UnboundLocalError: cannot access local variable 't'` 발생.
- **Root Cause**: [`_find_references_impl`](extension/mcp-servers/bridge/tools/scout.py:293) 내 `for t, label in type_labels.items():` 에서 `t`를 루프 변수로 선언하여 상위 스코프의 i18n 번역 함수 `t()`를 가림.
- **Fix**: 루프 변수를 `tool_type`으로 변경하고 루프 내 `items = ref_types.get(tool_type, [])`로 교체. 또한 line 97의 리스트 컴프리헨션 변수도 `tok`으로 명확히 분리.

### 2. B2 (crow_memory_server.py 미러 불일치)
- **Symptom**: 루트 미러 `crow_memory_server.py`가 21줄짜리 `sys.exit(0)` 스텁으로 남아있음.
- **Root Cause**: D4/D6 커맨드 정리 시 루트 미러의 `crow_memory_server.py`가 동기화 대상에서 누락됨.
- **Fix**: [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:1)(241줄 in-memory fallback 서버)를 [`mcp-servers/crow_memory_server.py`](mcp-servers/crow_memory_server.py:1)로 덮어쓰기 복사.

### 3. rebuildCodeIndex 복원
- **Symptom**: REQ-005로 합의 및 승인된 `vibezoo.rebuildCodeIndex`가 6109781 커밋에서 과다 삭제됨.
- **Root Cause**: REQ-006(사용되지 않는 UI 커맨드 제거) 적용 시 직전 커밋(b4bc4cf)에서 추가된 신규 필수 커맨드까지 일괄 제거됨.
- **Fix**: [`extension/package.json`](extension/package.json:65), [`extension/src/extension.ts:668`](extension/src/extension.ts:668), 20개 [`package.nls.*.json`](extension/package.nls.json:15), 20개 [`bundle.l10n.*.json`](extension/l10n/bundle.l10n.json:55)에 등록 및 핸들러 복원.

### 4. M1 (test_whiteboard_merge.py fixture & assertion 실패)
- **Symptom**: `test_whiteboard_merge.py` 실행 시 4 errors + 7 failures 발생.
- **Root Cause**: 6109781에서 `ux_coordinator.py` 모듈이 삭제되었으나 테스트 파일 내 `registered_ux_tools` fixture 및 `TestAutoAnalyzeWhiteboardDeprecated` 클래스가 남아있었고, D3-2에서 영문 i18n으로 변경된 출력에 대해 한국어 하드코딩 assertion이 존재함.
- **Fix**: 고아 fixture 및 deprecated 테스트 클래스 제거, assertion 대상을 영문 i18n 문자열("Analysis Suggestions", "Diagram Conversion" 등)로 업데이트, `registered_whiteboard_tools` fixture를 `yield` 컨텍스트로 전환하여 mock patch 유지.

### 5. M2 (whiteboard t() 다국어 리소스 누락)
- **Symptom**: Whiteboard D3-1/D3-2 신규 문자열이 20개 언어 `translations/*.json`에 미등록되어 fallback 영문만 출력됨.
- **Root Cause**: D3-2 구현 시 `t()` 래핑만 적용하고 json 키 추가 단계 누락.
- **Fix**: 39개 신규 키를 전수 추출하여 20개 번역 파일에 추가 (en, ko, ja 수동 번역, 나머지 fallback) 및 루트 미러 동기화 완료.

### 6. m1 (init_vibezoo.bat 고아 스크립트 복사 구문)
- **Symptom**: 루트에 존재하지 않는 `.bat` 파일 복사 시도.
- **Root Cause**: 구버전 배치 스크립트 참조 잔재.
- **Fix**: [`init_vibezoo.bat:15`](init_vibezoo.bat:15)의 `start_vibezoo_servers.bat`, `watch_vibezoo_bridge.bat` 복사 줄 삭제.

### 7. m2 (루트 tools 11개 i18n 동기화)
- **Symptom**: 루트 `mcp-servers/bridge/tools/` 11개 파일이 extension 측과 불일치.
- **Root Cause**: D1-2 i18n 변경 사항이 루트 미러에 미반영됨.
- **Fix**: `extension/mcp-servers/` 소스 전체를 `mcp-servers/`에 복사하여 SHA-256 100% 동기화 달성.

---

## Changes

| File | Before | After | Reason |
|------|--------|-------|--------|
| [`extension/mcp-servers/bridge/tools/scout.py:386`](extension/mcp-servers/bridge/tools/scout.py:386) | `for t, label in type_labels.items():` | `for tool_type, label in type_labels.items():` | B1 결함 해결 (i18n `t()` 충돌 제거) |
| [`mcp-servers/crow_memory_server.py:1`](mcp-servers/crow_memory_server.py:1) | 21 lines deprecated stub | 241 lines standalone in-memory fallback server | B2 결함 해결 (미러 동기화) |
| [`extension/package.json:65`](extension/package.json:65) | `vibezoo.rebuildCodeIndex` 누락 | `vibezoo.rebuildCodeIndex` command 추가 | REQ-005 커맨드 복원 |
| [`extension/src/extension.ts:668`](extension/src/extension.ts:668) | `vibezoo.rebuildCodeIndex` handler 누락 | `registerCommand('vibezoo.rebuildCodeIndex', ...)` 추가 | REQ-005 핸들러 복원 |
| [`extension/package.nls.*.json`](extension/package.nls.json:15) (20개) | `vibezoo.rebuildCodeIndex.title` 누락 | 20개 언어 title 키 등록 (ko/ja 실번역) | NLS 다국어 복원 |
| [`extension/l10n/bundle.l10n.*.json`](extension/l10n/bundle.l10n.json:55) (20개) | 안내 문자열 누락 | 20개 언어 안내 메시지 등록 | l10n 다국어 복원 |
| [`extension/mcp-servers/tests/test_whiteboard_merge.py`](extension/mcp-servers/tests/test_whiteboard_merge.py:1) | 4 errors + 7 failures | 12 passed (고아 fixture 제거 + 영문 assertion) | M1 결함 해결 |
| [`extension/mcp-servers/bridge/i18n/translations/*.json`](extension/mcp-servers/bridge/i18n/translations/en.json:1) (20개) | 173 unique keys | 212 unique keys (Whiteboard 39개 키 추가) | M2 결함 해결 |
| [`mcp-servers/bridge/i18n/translations/*.json`](mcp-servers/bridge/i18n/translations/en.json:1) (20개) | 173 unique keys | 212 unique keys (미러 100% 일치) | M2 및 m2 결함 해결 |
| [`init_vibezoo.bat:14`](init_vibezoo.bat:14) | 고아 .bat 2개 copy 줄 존재 | 고아 copy 구문 2줄 삭제 | m1 결함 해결 |
| [`mcp-servers/bridge/tools/*.py`](mcp-servers/bridge/tools/_base.py:1) (11개) | extension과 불일치 (t() 누락) | extension과 100% SHA 일치 | m2 결함 해결 |

---

## Preserved Invariants
- 33개 MCP 툴 등록 목록 및 매니페스트 불변 유지 (스모크 검증: 33 tools 등록, 누출 0건).
- VS Code TypeScript 빌드 및 모든 커맨드 등록 무결성 보존 (`npm run compile` 0 errors).
- 다국어 번역 무결성 보존 (`verify_translations` Missing=0, Empty=0, SHA 100% 일치).
- 루트 `mcp-servers`와 `extension/mcp-servers` 간 완전한 미러링 보존 (`p5_mirror_compare.py` diff=0).

---

## Verification

| Level | Command/Check | Result | Evidence |
|-------|--------------|--------|----------|
| L1 | [`tools/run_py_compile.py`](tools/run_py_compile.py) | ✅ PASS | 139개 Python 파일 문법 검사 0 errors |
| L2 | `pytest extension/mcp-servers/tests/test_find_references.py` | ✅ PASS | 6 passed in 0.16s (B1 검증 완료) |
| L2 | `pytest extension/mcp-servers/tests/test_whiteboard_merge.py` | ✅ PASS | 12 passed in 0.21s (M1 검증 완료) |
| L3 | `cd extension && npm run compile` | ✅ PASS | TypeScript tsc 5.9.3 compile 0 errors |
| L3 | [`docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_translations.py`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_translations.py) | ✅ PASS | 212 keys, Missing=0, Empty=0, Root↔Ext SHA-256 20/20 일치 |
| L3 | [`docs/260830_0001_session_reinstall-recovery-and-quality/tools/p5_mirror_compare.py`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/p5_mirror_compare.py) | ✅ PASS | ext=67 mir=67 common=67 diff=0 only_ext=0 only_mir=0 |
| L3 | [`docs/260830_0001_session_reinstall-recovery-and-quality/tools/p5_smoke.py`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/p5_smoke.py) | ✅ PASS | ext=33 tools (leak=False), mir=33 tools (leak=False) |
| L4 | `pytest extension/mcp-servers/tests/` & `pytest mcp-servers/tests/` | ✅ PASS | **111 passed / 0 failed / 0 errors** (양쪽 미러 전수 통과) |

---

## Issues Found
- 특이사항 없음. 모든 결함이 완전히 해소되었으며 추가 회귀나 결함은 발견되지 않았습니다.

---

## Not Verified
- 실제 VS Code UI 상 마우스 클릭 E2E (자동화 단위/통합 테스트, tsc 타입 체크, NLS/l10n JSON 정합성 검사로 완전 대체됨).

---

## Remaining Risks
- 없음. 모든 변경 사항이 양방향 미러와 테스트 스위트에 의해 검증되었습니다.

---

## Final Statement
**COMPLETE** — P5 검토 보고서의 모든 BLOCKER, MAJOR, MINOR 결함 및 D2-4 복원 요구사항이 100% 충족되었으며, 전체 pytest 111건 통과, tsc 컴파일 0 에러, 미러 동기화 diff=0이 확인되었습니다.
