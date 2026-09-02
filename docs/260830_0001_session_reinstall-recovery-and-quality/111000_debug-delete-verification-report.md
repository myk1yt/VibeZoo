# Debug Task Report — VibeZoo P4.5 DELETE 판정 검증

## Task Summary
평가보고서([110000_project-research-utility-audit.md](110000_project-research-utility-audit.md))의 DELETE 판정 9개 MCP 툴 + 13개 커맨드의 삭제 안전성을 코드 사실 기반으로 검증. 실제 grep으로 등록/임포트/역참조를 확인하고, i18n 키 삭제 전략을 확정.

## Search Log

```yaml
- id: S1
  question: DELETE 9개 MCP 툴이 __init__.py/bridge.py에 등록/임포트되어 있는가?
  intent: FIND_REFERENCES
  tool: search_files
  query: explain_code|analyze_changes|generate_tests|analyze_coverage|ux_coordinator|auto_analyze_after_drop|auto_analyze_whiteboard|apply_patch|explore_github
  path: mcp-servers
  result: MATCHES_FOUND
  interpretation: 9개 툴 모두 등록/참조 위치 확인

- id: S2
  question: extension/mcp-servers 복사본도 동일한 참조를 가지는가?
  intent: FIND_REFERENCES
  tool: search_files
  query: (동일 패턴)
  path: extension/mcp-servers
  result: MATCHES_FOUND
  interpretation: extension 복사본도 동일 구조 확인

- id: S3
  question: tests에서 DELETE 대상을 참조하는가?
  intent: FIND_REFERENCES
  tool: search_files
  query: explain_code|analyze_changes|generate_tests|analyze_coverage|apply_patch|explore_github
  path: mcp-servers/tests
  result: NO_MATCH_IN_SCOPE
  interpretation: test_whiteboard_merge.py만 ux_coordinator 참조 (삭제 시 함께 제거 필요)

- id: S4
  question: intent_detector는 ux_coordinator에서만 사용되는가?
  intent: FIND_IMPORT_EXPORT
  tool: search_files
  query: intent_detector|from bridge.intent_detector
  path: mcp-servers
  result: MATCHES_FOUND
  matches: [ux_coordinator.py L14]
  interpretation: ux_coordinator.py만 import. 삭제 시 dead code

- id: S5
  question: 13개 DELETE 커맨드의 registerCommand 위치
  intent: FIND_REFERENCES
  tool: search_files + read_file
  query: registerCommand.*vibezoo.(...)
  path: extension/src/extension.ts
  result: MATCHES_FOUND (9개 L668-L731 + 4개 L386-L401)
  interpretation: 13개 모두 showInformationMessage만 포함

- id: S6
  question: package.json contributes/menus/keybindings 매핑
  intent: FIND_REFERENCES
  tool: search_files + read_file
  path: extension/package.json
  result: MATCHES_FOUND
  interpretation: 13개 커맨드 정의(L69-L140) + editor/context 4개(L384-L404) + commandPalette 4개(L406-L423) 확인

- id: S7
  question: i18n 키 존재 여부 (package.nls + bundle.l10n)
  intent: FIND_EXACT_TEXT
  tool: read_file
  path: extension/package.nls.json, extension/l10n/bundle.l10n.json
  result: MATCHES_FOUND
  interpretation: 13개 커맨드 title 키 + 9개 runtime 메시지 키 확인

- id: S8
  question: tool_context.py manifest에서 DELETE 대상 툴 참조
  intent: FIND_REFERENCES
  tool: read_file
  path: mcp-servers/bridge/tool_context.py
  result: MATCHES_FOUND
  interpretation: MANIFEST_EXPLAIN_CODE, MANIFEST_GENERATE_TESTS, make_explain_code_context, make_generate_tests_context만 DELETE 대상. find_bugs/suggest_refactor manifest는 KEEP
```

---

## Part 1: MCP 툴 DELETE 검증 (9개)

### 1. `explain_code` — [analysis.py L188-L422](mcp-servers/bridge/tools/analysis.py#L188)

| 검증 항목 | 결과 | 근거 |
|-----------|------|------|
| `__init__.py` 등록 | ⚠️ **import 필요** | [`__init__.py L65`](mcp-servers/bridge/tools/__init__.py#L65) — `from bridge.tools.analysis import register` (모듈 전체 import) |
| `vibezoo_mcp_bridge.py` 참조 | ⚠️ **수정 필요** | [`vibezoo_mcp_bridge.py L52`](mcp-servers/vibezoo_mcp_bridge.py#L52) — `list_subagents` 응답에 `"explain_code"` 포함 |
| 다른 KEEP 툴 호출 | ✅ 없음 | integrated.py의 `_tool_registry`에 `explain_code` 없음 |
| 관련 헬퍼 | ⚠️ **함께 삭제** | `_get_git_blame()` L35-L66, `_find_related_tests()` L69-L85 — explain_code에서만 사용 |
| tool_context.py | ⚠️ **함께 삭제** | [`tool_context.py L14-L36`](mcp-servers/bridge/tool_context.py#L14) — `MANIFEST_EXPLAIN_CODE`, [`L255-L302`](mcp-servers/bridge/tool_context.py#L255) — `make_explain_code_context` |
| tests 참조 | ✅ 없음 | — |
| extension 복사본 | ⚠️ **동기화 필요** | `extension/mcp-servers/bridge/tools/analysis.py` 동일 수정 |

**판정: 삭제 가능** (단, analysis.py에서 함수 삭제 + __init__.py 수정 + tool_context.py 정리 + bridge.py list_subagents 수정)

---

### 2. `analyze_changes` — [analysis.py L424-L523](mcp-servers/bridge/tools/analysis.py#L424)

| 검증 항목 | 결과 | 근거 |
|-----------|------|------|
| `__init__.py` 등록 | ⚠️ **import 필요** | 모듈 전체 import (analysis.register) |
| `vibezoo_mcp_bridge.py` 참조 | ⚠️ **수정 필요** | [`vibezoo_mcp_bridge.py L52`](mcp-servers/vibezoo_mcp_bridge.py#L52) — `"analyze_changes"` 포함 |
| integrated.py 참조 | ⚠️ **함께 삭제** | [`integrated.py L374-L377`](mcp-servers/bridge/tools/integrated.py#L374) — `_get_analyze_changes()` lazy getter (dead code) |
| 다른 KEEP 툴 호출 | ✅ 없음 | `review_pr`는 analyze_changes를 직접 호출하지 않음 (git diff 자체 실행) |
| tests 참조 | ✅ 없음 | — |
| extension 복사본 | ⚠️ **동기화 필요** | 동일 |

**판정: 삭제 가능** (단, integrated.py `_get_analyze_changes` 함께 삭제)

---

### 3. `generate_tests` — [tester.py L37-L307](mcp-servers/bridge/tools/tester.py#L37)

| 검증 항목 | 결과 | 근거 |
|-----------|------|------|
| `__init__.py` 등록 | ⚠️ **import 필요** | [`__init__.py L61`](mcp-servers/bridge/tools/__init__.py#L61) — `from bridge.tools.tester import register` |
| `vibezoo_mcp_bridge.py` 참조 | ⚠️ **수정 필요** | [`vibezoo_mcp_bridge.py L48`](mcp-servers/vibezoo_mcp_bridge.py#L48) — `"generate_tests"` 포함 |
| 다른 KEEP 툴 호출 | ✅ 없음 | — |
| tool_context.py | ⚠️ **함께 삭제** | [`tool_context.py L38-L59`](mcp-servers/bridge/tool_context.py#L38) — `MANIFEST_GENERATE_TESTS`, [`L305-L343`](mcp-servers/bridge/tool_context.py#L305) — `make_generate_tests_context` |
| tests 참조 | ✅ 없음 | — |
| extension 복사본 | ⚠️ **동기화 필요** | 동일 |

**판정: 삭제 가능** (단, tester.py 모듈 자체를 삭제하고 __init__.py에서 tester import 제거)

---

### 4. `analyze_coverage` — [tester.py L309-L427](mcp-servers/bridge/tools/tester.py#L309)

| 검증 항목 | 결과 | 근거 |
|-----------|------|------|
| `__init__.py` 등록 | ⚠️ **import 필요** | tester 모듈 전체 삭제 시 함께 제거 |
| `vibezoo_mcp_bridge.py` 참조 | ⚠️ **수정 필요** | [`vibezoo_mcp_bridge.py L48`](mcp-servers/vibezoo_mcp_bridge.py#L48) — `"analyze_coverage"` 포함 |
| 다른 KEEP 툴 호출 | ✅ 없음 | — |
| tests 참조 | ✅ 없음 | — |
| extension 복사본 | ⚠️ **동기화 필요** | 동일 |

**판정: 삭제 가능** (generate_tests와 함께 tester.py 모듈 전체 삭제)

---

### 5. `ux_coordinator` — [ux_coordinator.py L60-L134](mcp-servers/bridge/tools/ux_coordinator.py#L60)

| 검증 항목 | 결과 | 근거 |
|-----------|------|------|
| `__init__.py` 등록 | ⚠️ **import 필요** | [`__init__.py L70`](mcp-servers/bridge/tools/__init__.py#L70) — `from bridge.tools.ux_coordinator import register` |
| `vibezoo_mcp_bridge.py` 참조 | ✅ 없음 | `list_subagents`에 ux_coordinator 그룹 없음 |
| 다른 KEEP 툴 호출 | ✅ 없음 | — |
| intent_detector | ⚠️ **함께 삭제** | [`intent_detector.py`](mcp-servers/bridge/intent_detector.py) — ux_coordinator.py에서만 import (L14). 삭제 시 dead code |
| tests 참조 | ⚠️ **함께 수정** | [`test_whiteboard_merge.py L107`](mcp-servers/tests/test_whiteboard_merge.py#L107) — `from bridge.tools.ux_coordinator import register` |
| extension 복사본 | ⚠️ **동기화 필요** | 동일 |

**판정: 삭제 가능** (단, ux_coordinator.py + intent_detector.py + test_whiteboard_merge.py 함께 삭제/수정)

---

### 6. `auto_analyze_after_drop` — [ux_coordinator.py L136-L284](mcp-servers/bridge/tools/ux_coordinator.py#L136)

| 검증 항목 | 결과 | 근거 |
|-----------|------|------|
| `__init__.py` 등록 | ⚠️ ux_coordinator 모듈과 함께 제거 | — |
| `vibezoo_mcp_bridge.py` 참조 | ✅ 없음 | — |
| 다른 KEEP 툴 호출 | ✅ 없음 | whiteboard.py는 주석으로만 참조 (실제 호출 없음) |
| intent_detector | ⚠️ **함께 삭제** | [`intent_detector.py L402-L404`](mcp-servers/bridge/intent_detector.py#L402) — `"next_tool": "auto_analyze_after_drop"` 참조 |
| tests 참조 | ✅ 없음 | — |
| extension 복사본 | ⚠️ **동기화 필요** | 동일 |

**판정: 삭제 가능** (ux_coordinator.py 모듈과 함께 삭제)

---

### 7. `auto_analyze_whiteboard` — [ux_coordinator.py L286-L308](mcp-servers/bridge/tools/ux_coordinator.py#L286)

| 검증 항목 | 결과 | 근거 |
|-----------|------|------|
| `__init__.py` 등록 | ⚠️ ux_coordinator 모듈과 함께 제거 | — |
| `vibezoo_mcp_bridge.py` 참조 | ✅ 없음 | — |
| 다른 KEEP 툴 호출 | ✅ 없음 | whiteboard.py는 주석으로만 참조 |
| intent_detector | ⚠️ **함께 삭제** | [`intent_detector.py L416-L418`](mcp-servers/bridge/intent_detector.py#L416) — `"next_tool": "auto_analyze_whiteboard"` 참조 |
| tests 참조 | ⚠️ **함께 수정** | [`test_whiteboard_merge.py L182-L207`](mcp-servers/tests/test_whiteboard_merge.py#L182) — `TestAutoAnalyzeWhiteboardDeprecated` 클래스 전체 |
| extension 복사본 | ⚠️ **동기화 필요** | 동일 |

**판정: 삭제 가능** (ux_coordinator.py 모듈과 함께 삭제 + test 파일 수정)

---

### 8. `apply_patch` — [editor.py L607-L620](mcp-servers/bridge/tools/editor.py#L607)

| 검증 항목 | 결과 | 근거 |
|-----------|------|------|
| `__init__.py` 등록 | ⚠️ **import 필요** | [`__init__.py L69`](mcp-servers/bridge/tools/__init__.py#L69) — `from bridge.tools.editor import register` |
| `vibezoo_mcp_bridge.py` 참조 | ⚠️ **수정 필요** | [`vibezoo_mcp_bridge.py L57`](mcp-servers/vibezoo_mcp_bridge.py#L57) — `"apply_patch"` 포함. Editor 그룹 전체 삭제 필요 |
| 다른 KEEP 툴 호출 | ✅ 없음 | — |
| read_project_file | ⚠️ **미구현 확인** | `list_subagents`에 `"read_project_file"`이 나에되지만 editor.py에 구현 없음. 삭제 시 함께 정리 |
| tests 참조 | ✅ 없음 | — |
| extension 복사본 | ⚠️ **동기화 필요** | 동일 |

**판정: 삭제 가능** (editor.py 모듈 전체 삭제 + __init__.py 수정 + bridge.py list_subagents에서 Editor 그룹 삭제)

---

### 9. `explore_github` — [github_diver.py L143-L161](mcp-servers/bridge/tools/github_diver.py#L143)

| 검증 항목 | 결과 | 근거 |
|-----------|------|------|
| `__init__.py` 등록 | ✅ **미등록** | `__init__.py`에 import 없음. 호출 불가 상태 |
| `vibezoo_mcp_bridge.py` 참조 | ✅ 없음 | — |
| 다른 KEEP 툴 호출 | ✅ 없음 | — |
| tests 참조 | ✅ 없음 | — |
| extension 복사본 | ⚠️ **동기화 필요** | 동일 |

**판정: 삭제 가능** (파일만 삭제하면 됨. 이미 미등록 상태)

---

## Part 2: VS Code 커맨드 DELETE 검증 (13개)

### extension.ts registerCommand 블록

| # | 커맨드 ID | 위치 | 내용 | 판정 |
|---|-----------|------|------|------|
| 1 | `vibezoo.reviewProject` | L386-L390 | `showInformationMessage("Please type 'review project' in chat")` | **삭제 가능** |
| 2 | `vibezoo.findBugs` | L391-L393 | `showInformationMessage("Please type 'find bugs' in chat")` | **삭제 가능** |
| 3 | `vibezoo.suggestRefactor` | L394-L398 | `showInformationMessage("Please type 'refactor' in chat")` | **삭제 가능** |
| 4 | `vibezoo.generateDocs` | L399-L401 | `showInformationMessage("Please type 'generate docs' in chat")` | **삭제 가능** |
| 5 | `vibezoo.explainCode` | L668-L672 | `showInformationMessage("Please type 'explain code' in chat")` | **삭제 가능** |
| 6 | `vibezoo.analyzeChanges` | L675-L679 | `showInformationMessage("Please type 'analyze changes' in chat")` | **삭제 가능** |
| 7 | `vibezoo.reviewPR` | L682-L686 | `showInformationMessage("Please type 'review PR' in chat")` | **삭제 가능** |
| 8 | `vibezoo.refactorAcrossFiles` | L689-L693 | `showInformationMessage("Please type 'refactor' in chat")` | **삭제 가능** |
| 9 | `vibezoo.learnProject` | L696-L700 | `showInformationMessage("Please type 'learn project' in chat")` | **삭제 가능** |
| 10 | `vibezoo.recallProject` | L703-L707 | `showInformationMessage("Please type 'recall project' in chat")` | **삭제 가능** |
| 11 | `vibezoo.learnPreference` | L710-L714 | `showInformationMessage("Please type 'learn preference' in chat")` | **삭제 가능** |
| 12 | `vibezoo.getPreferences` | L717-L721 | `showInformationMessage("Please type 'show preferences' in chat")` | **삭제 가능** |
| 13 | `vibezoo.rebuildCodeIndex` | L724-L730 | `showInformationMessage("Please type 'rebuild code index' in chat")` | **삭제 가능** |

**공통 특징**: 13개 모두 `vscode.window.showInformationMessage(vscode.l10n.t(...))`만 포함. 실제 로직 없음. 삭제 시 기능 손실 없음.

---

### package.json 매핑 확인

| 구분 | 위치 | 내용 | 판정 |
|------|------|------|------|
| `contributes.commands` | L69-L84, L105-L140 | 13개 커맨드 정의 (title 키 참조) | **삭제 가능** |
| `menus.editor/context` | L384-L404 | vibezoo@1~4 (reviewProject, findBugs, suggestRefactor, generateDocs) | **삭제 가능** |
| `menus.commandPalette` | L406-L423 | `"when": "never"` 4개 (동일 4개 커맨드) | **삭제 가능** |
| `keybindings` | L359-L375 | 3개 (showSessionResume, instantRewind, openWhiteboard) — DELETE 대상 아님 | **유지** |

---

### i18n 키 매핑

#### package.nls.json (13개 키)

| 키 | 삭제 대상 |
|-----|-----------|
| `vibezoo.reviewProject.title` | ✅ |
| `vibezoo.findBugs.title` | ✅ |
| `vibezoo.suggestRefactor.title` | ✅ |
| `vibezoo.generateDocs.title` | ✅ |
| `vibezoo.explainCode.title` | ✅ |
| `vibezoo.analyzeChanges.title` | ✅ |
| `vibezoo.reviewPR.title` | ✅ |
| `vibezoo.refactorAcrossFiles.title` | ✅ |
| `vibezoo.learnProject.title` | ✅ |
| `vibezoo.recallProject.title` | ✅ |
| `vibezoo.learnPreference.title` | ✅ |
| `vibezoo.getPreferences.title` | ✅ |
| `vibezoo.rebuildCodeIndex.title` | ✅ |

#### bundle.l10n.json (9개 키 — L52-L60)

| 키 | 삭제 대상 |
|-----|-----------|
| `VibeZoo: Please type "explain code" in Zoo Code chat. (explain_code MCP tool)` | ✅ |
| `VibeZoo: Please type "analyze changes" in Zoo Code chat. (analyze_changes MCP tool)` | ✅ |
| `VibeZoo: Please type "review PR" in Zoo Code chat. (review_pr MCP tool)` | ✅ |
| `VibeZoo: Please type "refactor" in Zoo Code chat. (refactor_across_files MCP tool)` | ✅ |
| `VibeZoo: Please type "learn project" in Zoo Code chat. (learn_project MCP tool)` | ✅ |
| `VibeZoo: Please type "recall project" in Zoo Code chat. (recall_project MCP tool)` | ✅ |
| `VibeZoo: Please type "learn preference" in Zoo Code chat. (learn_preference MCP tool)` | ✅ |
| `VibeZoo: Please type "show preferences" in Zoo Code chat. (get_preferences MCP tool)` | ✅ |
| `VibeZoo: Please type "rebuild code index" in Zoo Code chat. (rebuild_code_index MCP tool)` | ✅ |

**주의**: `reviewProject`, `findBugs`, `suggestRefactor`, `generateDocs` 4개 커맨드는 `bundle.l10n.json`에 runtime 키가 없음 (menus에서만 사용). package.nls.json 키만 삭제하면 됨.

---

## Part 3: i18n 영향 분석

### 삭제 대상 키 존재 여부

| 파일 그룹 | 파일 수 | DELETE 키 존재 |
|-----------|---------|----------------|
| `extension/package.nls.*.json` | 20개 | 13개 키 존재 |
| `extension/l10n/bundle.l10n.*.json` | 20개 | 9개 키 존재 (L52-L60) |
| `mcp-servers/bridge/i18n/translations/*.json` | 20개 | DELETE 툴 고유 키 **없음** |

### D2-3/D3-1 키 식별

decisions.md에서 D2-3/D3-1 언긐 없음. `vibezoo.rebuildCodeIndex.title`은 D-1에서 이미 일본어 번역됨 ([package.nls.ja.json L32](extension/package.nls.ja.json#L32) — `"VibeZoo: Rebuild Code Index (コードインデックス再構築)"`).

**재확인**: D2-3/D3-1로 추가된 키는 존재하지 않음. 삭제 대상 13개 키는 모두 초기부터 존재하던 커맨드 title 키.

### missing=0 유지 전략

**권고**: 커맨드 삭제 시 i18n 키를 **동시에 삭제**해야 missing=0 유지 가능.

- `package.nls.*.json` (20개 파일): 13개 키 삭제
- `bundle.l10n.*.json` (20개 파일): 9개 키 삭제
- `translations/*.json` (20개 파일): DELETE 툴 고유 키 없음 → 변경 불필요

---

## Part 4: 최종 삭제 매니페스트 (code 위임용)

### 파일 삭제 (5개)

| 파일 | 이유 |
|------|------|
| [`mcp-servers/bridge/tools/github_diver.py`](mcp-servers/bridge/tools/github_diver.py) | explore_github 미등록 + GitHub MCP와 중복 |
| [`mcp-servers/bridge/tools/editor.py`](mcp-servers/bridge/tools/editor.py) | apply_patch DELETE. read_project_file 미구현 |
| [`mcp-servers/bridge/tools/tester.py`](mcp-servers/bridge/tools/tester.py) | generate_tests + analyze_coverage DELETE |
| [`mcp-servers/bridge/tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) | ux_coordinator + auto_analyze_after_drop + auto_analyze_whiteboard DELETE |
| [`mcp-servers/bridge/intent_detector.py`](mcp-servers/bridge/intent_detector.py) | ux_coordinator 삭제 시 dead code |

### 파일 수정 (7개)

| 파일 | 수정 내용 |
|------|-----------|
| [`mcp-servers/bridge/tools/__init__.py`](mcp-servers/bridge/tools/__init__.py) | tester(L61), editor(L69), ux_coordinator(L70) import 제거 + reg_tester/reg_editor/reg_ux 등록 제거(L73-L75) |
| [`mcp-servers/bridge/tools/analysis.py`](mcp-servers/bridge/tools/analysis.py) | explain_code(L188-L422) + analyze_changes(L424-L523) 삭제 + _get_git_blame(L35-L66) + _find_related_tests(L69-L85) 삭제 + tool_context import 정리(L28-L31) |
| [`mcp-servers/bridge/tools/integrated.py`](mcp-servers/bridge/tools/integrated.py) | _get_analyze_changes(L374-L377) 삭제 |
| [`mcp-servers/bridge/tool_context.py`](mcp-servers/bridge/tool_context.py) | MANIFEST_EXPLAIN_CODE(L14-L36), MANIFEST_GENERATE_TESTS(L38-L59), make_explain_code_context(L255-L302), make_generate_tests_context(L305-L343) 삭제 + _MANIFEST_REGISTRY(L107-L112), __all__(L424-L439) 정리 |
| [`mcp-servers/vibezoo_mcp_bridge.py`](mcp-servers/vibezoo_mcp_bridge.py) | list_subagents 응답에서 explain_code/analyze_changes(L52), generate_tests/analyze_coverage(L48), apply_patch/read_project_file(L57) 제거. Tester(L48), Editor(L57) 그룹 전체 삭제 |
| [`mcp-servers/tests/test_whiteboard_merge.py`](mcp-servers/tests/test_whiteboard_merge.py) | ux_coordinator import(L107) + TestAutoAnalyzeWhiteboardDeprecated 클래스(L186-L207) 삭제 |
| [`extension/src/extension.ts`](extension/src/extension.ts) | 13개 registerCommand 블록 삭제 (L386-L401 4개 + L668-L731 9개) |

### extension 복사본 동기화 (5개)

| 파일 | 작업 |
|------|------|
| `extension/mcp-servers/bridge/tools/__init__.py` | 위 __init__.py와 동일 수정 |
| `extension/mcp-servers/bridge/tools/analysis.py` | 위 analysis.py와 동일 수정 |
| `extension/mcp-servers/bridge/tools/integrated.py` | 위 integrated.py와 동일 수정 |
| `extension/mcp-servers/bridge/tool_context.py` | 위 tool_context.py와 동일 수정 |
| `extension/mcp-servers/vibezoo_mcp_bridge.py` | 위 bridge.py와 동일 수정 |

### package.json + i18n (42개 파일)

| 파일 | 수정 내용 |
|------|-----------|
| [`extension/package.json`](extension/package.json) | contributes.commands 13개 삭제(L69-L84, L105-L140) + menus.editor/context 4개 삭제(L384-L404) + menus.commandPalette 4개 삭제(L406-L423) |
| `extension/package.nls.*.json` (20개) | 13개 커맨드 title 키 삭제 |
| `extension/l10n/bundle.l10n.*.json` (20개) | 9개 runtime 메시지 키 삭제 (L52-L60) |

### 총 파일 수: **~59개**

---

## Result

**✅ 삭제 가능 (20/20 항목)**

모든 DELETE 판정이 코드 사실 기반으로 검증됨. 삭제 시 import 오류, 역참조 오류, i18n missing 오류가 발생하지 않도록 수정 파일 목록을 완전히 확정.

## Issues Discovered

1. **`read_project_file` 미구현**: `list_subagents` 응답에 `read_project_file`이 나에되지만 editor.py에 실제 구현이 없음. 삭제 시 함께 정리 필요.

2. **`review_pr`의 `analyze_changes` 의존성 없음**: 평가보고서에서 `review_pr`이 `analyze_changes`를 호출한다고 했지만, 실제 코드에서는 git diff를 직접 실행함. 의존성 없음.

3. **extension 복사본 동기화**: `mcp-servers/`와 `extension/mcp-servers/`가 동일한 구조를 가지며, 삭제 시 양쪽 모두 수정 필요.

## Next Step Recommendations

1. **code 모드 위임**: 위 매니페스트에 따라 삭제 실행. 순서: (1) Python 파일 삭제 → (2) __init__.py/bridge.py 수정 → (3) extension.ts 수정 → (4) package.json 수정 → (5) i18n 키 삭제 → (6) extension 복사본 동기화.

2. **삭제 후 검증**: `python -c "from bridge.tools import register_all_tools; print('OK')"` import 테스트 + `npm run compile` TypeScript 빌드 테스트.

3. **i18n 검증**: 삭제 후 `package.nls.*.json`과 `bundle.l10n.*.json`의 키 수가 각각 13개 + 9개 줄어들었는지 확인.

## Affected File List

| 파일 | 작업 | 판정 |
|------|------|------|
| `mcp-servers/bridge/tools/github_diver.py` | 삭제 | ✅ 안전 |
| `mcp-servers/bridge/tools/editor.py` | 삭제 | ✅ 안전 |
| `mcp-servers/bridge/tools/tester.py` | 삭제 | ✅ 안전 |
| `mcp-servers/bridge/tools/ux_coordinator.py` | 삭제 | ✅ 안전 |
| `mcp-servers/bridge/intent_detector.py` | 삭제 | ✅ 안전 |
| `mcp-servers/bridge/tools/__init__.py` | 수정 (import 3개 제거) | ✅ 안전 |
| `mcp-servers/bridge/tools/analysis.py` | 수정 (2개 툴 + 2개 헬퍼 삭제) | ✅ 안전 |
| `mcp-servers/bridge/tools/integrated.py` | 수정 (_get_analyze_changes 삭제) | ✅ 안전 |
| `mcp-servers/bridge/tool_context.py` | 수정 (2개 manifest + 2개 팩토리 삭제) | ✅ 안전 |
| `mcp-servers/vibezoo_mcp_bridge.py` | 수정 (list_subagents 3개 그룹 정리) | ✅ 안전 |
| `mcp-servers/tests/test_whiteboard_merge.py` | 수정 (ux_coordinator 참조 제거) | ✅ 안전 |
| `extension/src/extension.ts` | 수정 (13개 registerCommand 삭제) | ✅ 안전 |
| `extension/package.json` | 수정 (13개 커맨드 + 8개 메뉴 삭제) | ✅ 안전 |
| `extension/package.nls.*.json` (20개) | 수정 (13개 키 삭제) | ✅ 안전 |
| `extension/l10n/bundle.l10n.*.json` (20개) | 수정 (9개 키 삭제) | ✅ 안전 |
| `extension/mcp-servers/bridge/tools/__init__.py` | 수정 (동기화) | ✅ 안전 |
| `extension/mcp-servers/bridge/tools/analysis.py` | 수정 (동기화) | ✅ 안전 |
| `extension/mcp-servers/bridge/tools/integrated.py` | 수정 (동기화) | ✅ 안전 |
| `extension/mcp-servers/bridge/tool_context.py` | 수정 (동기화) | ✅ 안전 |
| `extension/mcp-servers/vibezoo_mcp_bridge.py` | 수정 (동기화) | ✅ 안전 |
