# Code Task Report — VibeZoo P4.5 쓸모없는 기능 및 도구 삭제 실행

## Task Summary
[`111000_debug-delete-verification-report.md`](docs/260830_0001_session_reinstall-recovery-and-quality/111000_debug-delete-verification-report.md)의 최종 삭제 매니페스트 및 [`110000_project-research-utility-audit.md`](docs/260830_0001_session_reinstall-recovery-and-quality/110000_project-research-report.md) 평가 결과에 따라, VibeZoo 코드베이스 전반에서 쓸모없는 9개 MCP 툴, 13개 VS Code 커맨드, 4개 Editor Context 메뉴, 5개 미사용 설정 및 관련 다국어 i18n 리소스를 완전 삭제하고 양방향 미러 동기화와 전수 컴파일/번역 무결성 검증을 완료했습니다.

---

## Actions Taken

### 1. MCP 툴 9개 완전 삭제 및 레지스트리/브릿지 정리
- **툴 파일 5종 영구 삭제 (Recycle Bin 보관 및 동기화)**:
  - [`mcp-servers/bridge/tools/github_diver.py`](mcp-servers/bridge/tools/github_diver.py) & [`extension/mcp-servers/bridge/tools/github_diver.py`](extension/mcp-servers/bridge/tools/github_diver.py) (`explore_github`)
  - [`mcp-servers/bridge/tools/editor.py`](mcp-servers/bridge/tools/editor.py) & [`extension/mcp-servers/bridge/tools/editor.py`](extension/mcp-servers/bridge/tools/editor.py) (`apply_patch`)
  - [`mcp-servers/bridge/tools/tester.py`](mcp-servers/bridge/tools/tester.py) & [`extension/mcp-servers/bridge/tools/tester.py`](extension/mcp-servers/bridge/tools/tester.py) (`generate_tests`, `analyze_coverage`)
  - [`mcp-servers/bridge/tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) & [`extension/mcp-servers/bridge/tools/ux_coordinator.py`](extension/mcp-servers/bridge/tools/ux_coordinator.py) (`ux_coordinator`, `auto_analyze_after_drop`, `auto_analyze_whiteboard`)
  - [`mcp-servers/bridge/intent_detector.py`](mcp-servers/bridge/intent_detector.py) & [`extension/mcp-servers/bridge/intent_detector.py`](extension/mcp-servers/bridge/intent_detector.py) (`ux_coordinator` 연계 데드 코드)
- **등록부 및 관련 코드 정리**:
  - [`mcp-servers/bridge/tools/__init__.py:57`](mcp-servers/bridge/tools/__init__.py:57): `tester`, `editor`, `ux_coordinator` 모듈 임포트 및 등록 목록 제거.
  - [`mcp-servers/bridge/tools/analysis.py:1`](mcp-servers/bridge/tools/analysis.py:1): `explain_code` 및 `analyze_changes` 툴 본문 제거, 전용 헬퍼 `_get_git_blame()`, `_find_related_tests()` 및 `tool_context` 미사용 임포트 제거. `review_pr` 및 `refactor_across_files` 유지.
  - [`mcp-servers/bridge/tools/integrated.py:369`](mcp-servers/bridge/tools/integrated.py:369): `_get_analyze_changes()` 데드 lazy getter 함수 제거.
  - [`mcp-servers/bridge/tool_context.py:10`](mcp-servers/bridge/tool_context.py:10): `MANIFEST_EXPLAIN_CODE`, `MANIFEST_GENERATE_TESTS`, `make_explain_code_context()`, `make_generate_tests_context()` 및 `_MANIFEST_REGISTRY`, `__all__` 엔트리 제거.
  - [`mcp-servers/vibezoo_mcp_bridge.py:40`](mcp-servers/vibezoo_mcp_bridge.py:40): `list_subagents` 라우트에서 `Tester`, `Editor` 에이전트 그룹 삭제 및 `Analysis` 툴 목록에서 `explain_code`, `analyze_changes` 제거 (`review_pr`, `refactor_across_files` 유지).
  - [`mcp-servers/tests/test_whiteboard_merge.py:100`](mcp-servers/tests/test_whiteboard_merge.py:100): `registered_ux_tools` 픽스처 및 `TestAutoAnalyzeWhiteboardDeprecated` 테스트 클래스 삭제.

### 2. VS Code 커맨드 13개 + UI 메뉴 8개 제거
- **확장 진입점 정리 ([`extension/src/extension.ts:660`](extension/src/extension.ts:660))**:
  - 단순 안내 팝업만 띄우던 9개 `registerCommand` 블록 (`vibezoo.explainCode`, `analyzeChanges`, `reviewPR`, `refactorAcrossFiles`, `learnProject`, `recallProject`, `learnPreference`, `getPreferences`, `rebuildCodeIndex`) 제거.
- **매니페스트 정리 ([`extension/package.json:65`](extension/package.json:65))**:
  - `contributes.commands`에서 13개 커맨드 정의 제거 (`reviewProject`, `findBugs`, `suggestRefactor`, `generateDocs`, `explainCode`, `analyzeChanges`, `reviewPR`, `refactorAcrossFiles`, `learnProject`, `recallProject`, `learnPreference`, `getPreferences`, `rebuildCodeIndex`).
  - `contributes.menus.editor/context` 4개 메뉴 항목 완전 삭제.
  - `contributes.menus.commandPalette` 4개 `when: never` 메뉴 항목 완전 삭제.
  - `contributes.configuration.properties`에서 미사용 설정 5개 제거 (`vibezoo.scout.port`, `vibezoo.reviewer.port`, `vibezoo.tester.port`, `vibezoo.deepAnalyzer.port`, `vibezoo.emotion.detectionEnabled`).

### 3. 다국어 i18n 리소스 20개 언어 전수 키 정리
- **`extension/package.nls.*.json` (20개 파일)**:
  - 13개 커맨드 title 키 + 5개 설정 description 키 = 총 18개 키 전수 삭제 (ar, bg, cs, de, es, fr, he, hu, it, ja, ko, pl, pt-BR, ru, th, tr, vi, zh-CN, zh-TW, en(기본)).
- **`extension/l10n/bundle.l10n.*.json` (20개 파일)**:
  - 9개 런타임 안내 메시지 키 전수 삭제 (20개 언어 전체).
- **`mcp-servers/bridge/i18n/translations/*.json` (20개 파일)**:
  - 삭제 대상 툴 고유 키가 없으므로 불변 유지 확인.

### 4. 루트와 확장 `mcp-servers` 미러 정합성 동기화
- `extension/mcp-servers/`와 `mcp-servers/` 간 변경/삭제된 모든 파일(6종 수정, 5종 삭제)을 100% SHA-256 일치하도록 동기화.

---

## Result

### 매니페스트 대비 삭제 완료 체크리스트

| 범주 | 항목 | 대상 파일/위치 | 상태 | 검증 결과 |
|---|---|---|---|---|
| **MCP 툴** | `explore_github` | `github_diver.py` | ✅ 삭제 완료 | 파일 삭제됨, 등록 없음 |
| **MCP 툴** | `apply_patch` | `editor.py` | ✅ 삭제 완료 | 파일 삭제됨, 등록 없음 |
| **MCP 툴** | `generate_tests` | `tester.py` | ✅ 삭제 완료 | 파일 삭제됨, 등록 없음 |
| **MCP 툴** | `analyze_coverage` | `tester.py` | ✅ 삭제 완료 | 파일 삭제됨, 등록 없음 |
| **MCP 툴** | `ux_coordinator` | `ux_coordinator.py` | ✅ 삭제 완료 | 파일 삭제됨, 등록 없음 |
| **MCP 툴** | `auto_analyze_after_drop` | `ux_coordinator.py` | ✅ 삭제 완료 | 파일 삭제됨, 등록 없음 |
| **MCP 툴** | `auto_analyze_whiteboard` | `ux_coordinator.py` | ✅ 삭제 완료 | 파일 삭제됨, 등록 없음 |
| **MCP 툴** | `explain_code` | `analysis.py` | ✅ 삭제 완료 | 함수/헬퍼/Manifest 삭제됨 |
| **MCP 툴** | `analyze_changes` | `analysis.py`, `integrated.py` | ✅ 삭제 완료 | 함수/lazy getter 삭제됨 |
| **데드 모듈** | `intent_detector.py` | `bridge/intent_detector.py` | ✅ 삭제 완료 | 파일 삭제됨, 미사용 |
| **VSCode 커맨드** | 13개 커맨드 등록 | `extension.ts`, `package.json` | ✅ 삭제 완료 | 커맨드/메뉴 정의 완전 제거 |
| **UI 메뉴** | Editor context 4개 | `package.json` (`editor/context`) | ✅ 삭제 완료 | 메뉴 항목 제거 |
| **UI 메뉴** | Palette hidden 4개 | `package.json` (`commandPalette`) | ✅ 삭제 완료 | 메뉴 항목 제거 |
| **설정** | Port 4개 + Emotion 1개 | `package.json` (`configuration`) | ✅ 삭제 완료 | 미사용 프로퍼티 5개 제거 |
| **i18n nls** | 18개 키 × 20개 언어 | `package.nls.*.json` | ✅ 삭제 완료 | 20개 파일 각 18개 키 제거 |
| **i18n l10n** | 9개 키 × 20개 언어 | `bundle.l10n.*.json` | ✅ 삭제 완료 | 20개 파일 각 9개 키 제거 |
| **미러 정합** | 루트 ↔ 확장 동기화 | `mcp-servers/` ↔ `extension/` | ✅ 동기화 완료 | 100% SHA-256 일치 |

### 전수 검증 결과표

| 검증 단계 | 명령어 / 검증기 | 결과 | 상세 근거 |
|---|---|---|---|
| **TypeScript 빌드** | `npm run compile` (`tsc -p ./`) | ✅ **PASS** | 에러 0건, 컴파일 성공 |
| **Python 문법** | `py_compile` (전체 92개 파일) | ✅ **PASS** | 문법 에러 0건 |
| **MCP 툴 등록 검증** | `register_all_tools(MockMCP)` | ✅ **PASS** | 유지 툴 33개 정상 등록, 삭제 툴 9개 중 0개 등록 확인 |
| **브릿지 i18n 무결성** | [`verify_translations.py`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_translations.py:1) | ✅ **PASS** | `Total Missing: 0, Total Empty: 0, Sync: 20/20 SHA-256 IDENTICAL` |
| **단위 테스트 스위트** | `test_d2_2_index_cache.py` (6/6) | ✅ **PASS** | 6개 시나리오 전원 통과 |

---

## Issues Discovered
- 특이사항 없음. 모든 삭제 및 리팩토링이 기존 기능(Scout, Reviewer, DeepAnalyzer, Whiteboard, FixLoop, Integrated, Knowledge, Web, SSA, FileAnalyzer 등 33개 툴 및 Extension 메인 기능)에 영향 없이 안전하게 적용되었습니다.

---

## Next Step Recommendations
1. **D4-4 (루트 `mcp-servers` 단일화 준비)**: 현재 `extension/mcp-servers`와 `mcp-servers`가 완벽하게 동기화되었으므로, 다음 계획에 따라 루트 복사본 제거 또는 패키징 파이프라인 정리 진행.
2. **P5 (검증 및 사용자 승인)**: VP 및 CPO 최종 리뷰 진행.

---

## Affected File List

### 1. Deleted Files (10 files)
- [`mcp-servers/bridge/tools/github_diver.py`](mcp-servers/bridge/tools/github_diver.py)
- [`mcp-servers/bridge/tools/editor.py`](mcp-servers/bridge/tools/editor.py)
- [`mcp-servers/bridge/tools/tester.py`](mcp-servers/bridge/tools/tester.py)
- [`mcp-servers/bridge/tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py)
- [`mcp-servers/bridge/intent_detector.py`](mcp-servers/bridge/intent_detector.py)
- [`extension/mcp-servers/bridge/tools/github_diver.py`](extension/mcp-servers/bridge/tools/github_diver.py)
- [`extension/mcp-servers/bridge/tools/editor.py`](extension/mcp-servers/bridge/tools/editor.py)
- [`extension/mcp-servers/bridge/tools/tester.py`](extension/mcp-servers/bridge/tools/tester.py)
- [`extension/mcp-servers/bridge/tools/ux_coordinator.py`](extension/mcp-servers/bridge/tools/ux_coordinator.py)
- [`extension/mcp-servers/bridge/intent_detector.py`](extension/mcp-servers/bridge/intent_detector.py)

### 2. Modified Python Files (6 files × 2 locations = 12 files)
- [`mcp-servers/bridge/tools/__init__.py`](mcp-servers/bridge/tools/__init__.py:57) & [`extension/mcp-servers/bridge/tools/__init__.py`](extension/mcp-servers/bridge/tools/__init__.py:57)
- [`mcp-servers/bridge/tools/analysis.py`](mcp-servers/bridge/tools/analysis.py:1) & [`extension/mcp-servers/bridge/tools/analysis.py`](extension/mcp-servers/bridge/tools/analysis.py:1)
- [`mcp-servers/bridge/tools/integrated.py`](mcp-servers/bridge/tools/integrated.py:369) & [`extension/mcp-servers/bridge/tools/integrated.py`](extension/mcp-servers/bridge/tools/integrated.py:369)
- [`mcp-servers/bridge/tool_context.py`](mcp-servers/bridge/tool_context.py:10) & [`extension/mcp-servers/bridge/tool_context.py`](extension/mcp-servers/bridge/tool_context.py:10)
- [`mcp-servers/vibezoo_mcp_bridge.py`](mcp-servers/vibezoo_mcp_bridge.py:40) & [`extension/mcp-servers/vibezoo_mcp_bridge.py`](extension/mcp-servers/vibezoo_mcp_bridge.py:40)
- [`mcp-servers/tests/test_whiteboard_merge.py`](mcp-servers/tests/test_whiteboard_merge.py:100) & [`extension/mcp-servers/tests/test_whiteboard_merge.py`](extension/mcp-servers/tests/test_whiteboard_merge.py:100)

### 3. Modified TypeScript & Manifest Files (2 files)
- [`extension/src/extension.ts`](extension/src/extension.ts:660)
- [`extension/package.json`](extension/package.json:65)

### 4. Modified Localization Files (40 files)
- 20 files in `extension/package.nls.*.json`
- 20 files in `extension/l10n/bundle.l10n.*.json`
