# Debug Task Report — P5 기술 리뷰 (f40c1a8..6109781)

## Task Summary
세션 전체 10커밋(ef18b1f..HEAD, HEAD=6109781)을 정적 diff + 미러 SHA 전수 비교 + 런타임 스모크 + tsc compile + i18n + pytest 전수로 검증. 삭제 커밋(6109781)이 KEEP 기능을 깼는지, 미러 동기화가 깨졌는지, 세션 중 도입된 신규 결함이 있는지를 근본 원인 수준에서 확인.

## Actions Taken
1. `git log ef18b1f..HEAD` + `git diff --stat` 로 10커밋/139파일 스코프 확정
2. 회귀 정적 분석: 삭제된 5개 모듈(editor/tester/ux_coordinator/github_diver/intent_detector)의 잔여 참조를 `search_files`로 전수 검색
3. 미러 비교: `tools/p5_mirror_compare.py` 신규 작성 → extension/mcp-servers vs mcp-servers SHA-256 전수(67파일) 비교
4. 미러 차이 12파일 상세: `tools/p5_mirror_diff_details.py` 신규 작성 → unified diff 추출
5. start_vibezoo_bridge.bat 루트 생성 이유: `git log --diff-filter=A` + f40c1a8/6109781 커밋 메시지 + init_vibezoo.bat 본문 대조
6. 런타임 스모크: `tools/p5_smoke.py` 신규 작성 — 14개 bridge 모듈 import + MockMCP(2종 데코레이터 패턴) + requests MagicMock + register_all_tools 호출 → 등록 툴 수/삭제 툴 누출/중복 검사 (양 미러 각각)
7. TS 빌드: `cd extension && npm run compile` (= `tsc -p ./`)
8. i18n: `tools/verify_translations.py` 재실행
9. pytest 전수: `cd extension/mcp-servers && python -m pytest tests/ -q` (pytest/requests 시스템 python에 신규 설치)
10. pytest 실패 원인 분석: `read_command_output` + `git log -L` blame으로 신규 회귀 여부 확정

## Result — FAIL (BLOCKER 2 + MAJOR 2 + MINOR 2)

### 환경 이슈 (수정 후 보고)
- 시스템 python(3.11)에 `requests`, `pytest` 미설치 → 첫 스모크/테스트가 ImportError로 중단. **원래 상태**: 모듈 없음. **수정**: `python -m pip install requests pytest` 로 사용자 환경에 추가 후 재실행 정상. 설치는 검증 전용, 프로덕션 코드 무관.

---

## 결함 표

| # | Severity | File:Line | Defect | Root Cause | Evidence |
|---|----------|-----------|--------|------------|----------|
| B1 | 🔴 BLOCKER | [`extension/mcp-servers/bridge/tools/scout.py:386`](extension/mcp-servers/bridge/tools/scout.py#L386) | `for t, label in type_labels.items():` 가 모듈 import `t`(i18n)를 함수 로컬 변수로 가려버림 → `_find_references_impl` L297 첫 t() 호출부터 `UnboundLocalError` | a88c63b(D2-3, 102500)가 기존 `_find_references_impl` 에 t() i18n을 추가하면서 L386 기존 루프 변수명 `t`와 충돌. base(ef18b1f)에는 이 함수에 t() 호출이 없어 충돌이 없었음 → **이번 세션 신규 회귀** | pytest: `test_find_references.py` 6건 전부 `UnboundLocalError: cannot access local variable 't'` (라인 494/602/710/818/926/1034). git log -L 293,300 으로 t() 추가 커밋이 a88c63b임을 확인 |
| B2 | 🔴 BLOCKER | [`mcp-servers/crow_memory_server.py:1`](mcp-servers/crow_memory_server.py#L1) vs [`extension/mcp-servers/crow_memory_server.py:1`](extension/mcp-servers/crow_memory_server.py#L1) | 루트 미러가 21줄 deprecated 스텁, extension 쪽은 241줄 실제 fallback 서버(프록시/in-memory). 미러 동기화 완전 붕괴 | 어느 커밋에서도 루트 crow_memory_server.py를 갱신하지 않음. init_vibezoo.bat L20이 extension 쪽을 복사하므로 설치 경로는 안전하지만, 루트 미러를 직접 쓰는 실행 경로가 있으면 깨짐 | p5_mirror_compare.py CONTENT_DIFF 목록, p5_mirror_diff_details.py (mir=21 lines, ext=241 lines, 본문 전체 불일치) |
| M1 | 🟠 MAJOR | [`extension/mcp-servers/tests/test_whiteboard_merge.py:106`](extension/mcp-servers/tests/test_whiteboard_merge.py#L106) | fixture `registered_ux_tools` 가 삭제된 `bridge.tools.ux_coordinator` 를 patch → `AttributeError: module 'bridge.tools' has no attribute 'ux_coordinator'` (4 errors). 동일 파일 7건 FAILED 추가 | 6109781(112000)이 ux_coordinator.py를 삭제하면서 테스트 파일의 참조를 함께 정리하지 않음. whiteboard 한국어 하드코딩 테스트는 D3-2(105000)가 영어 i18n으로 바꾸면서 이미 무효화됨 | pytest 결과: 4 errors + 7 failed in test_whiteboard_merge.py. 총 13 failed / 98 passed / 4 errors |
| M2 | 🟠 MAJOR | [`extension/mcp-servers/bridge/tools/whiteboard.py:875`](extension/mcp-servers/bridge/tools/whiteboard.py#L875) 일대 | D3-2가 whiteboard 사용자 노출 문자열을 영어 i18n t()로 전환하면서, ko.json 등 20개 locale에 신규 키("Analysis Suggestions", "Diagram Conversion" 등)를 추가하지 않음 → t() fallback으로 모든 로케일에서 영문 출력 | D3-2(105000, b42470d/287ee6b 계열)가 코드만 바꾸고 번역 키 추가를 누락. verify_translations는 en.json 기준 Missing/Empty만 검사하고 "ko locale에 신규 키가 있는가"는 별도 지표로만 보고(untranslated 5)하여 BLOCKER로 잡지 못함 | ko.json에 "Analysis Suggestions" 검색 결과 0건. verify_translations 결과표: ko Untranslated=0 이지만 그 외 18개 locale Untranslated=5 (신규 whiteboard 키가 비-ko locale에만 존재) |
| m1 | 🟡 MINOR | [`init_vibezoo.bat:15`](init_vibezoo.bat#L15), [`init_vibezoo.bat:16`](init_vibezoo.bat#L16) | `start_vibezoo_servers.bat`, `watch_vibezoo_bridge.bat` 는 루트에 실재하지만 `git log` 상 마지막 갱신이 ebf0cd6(구 버전). f40c1a8이 canonical 소스를 extension/mcp-servers로 바꾸면서 이 2개 .bat은 여전히 루트에서 복사 → extension 쪽과 내용 불일치 가능성 | f40c1a8은 start_vibezoo_bridge.bat만 canonical 교체 대상으로 삼았고 나머지 2개는 그대로 둠. 세션 범위 밖이지만 같은 "orphaned root .bat" 문제의 연장 | init_vibezoo.bat L14-16 대조 |
| m2 | 🟡 MINOR | [`mcp-servers/bridge/tools/_base.py:3`](mcp-servers/bridge/tools/_base.py#L3) 등 11개 tools 파일 | 루트 미러의 tools/*.py 11개 파일이 extension 쪽과 내용 불일치 — 대부분 i18n `t()` 적용이 루트에만 안 되어 있거나 import 1줄만 있는 상태 | 6109781이 "mirrors SHA-synced"라고 커밋 메시지에 썼으나 실제로는 11개 파일이 미동기. D1-2(i18n) 변경이 extension에만 적용되고 루트에 부분 반영 | p5_mirror_compare.py: CONTENT_DIFF 11개( _base, deep_analyzer, feedback, file_analyzer, fix_loop, knowledge, reviewer, setup, ssa, web, whiteboard ). diff 본문은 t() 호출 유무 차이 |

---

## 체크리스트별 검증 결과

### 1. 회귀 탐색 (삭제 → KEEP 의존성)
- ✅ 삭제된 5개 모듈을 import하는 KEEP 소스: **없음** (bridge/, tools/ 내 `search_files` 전수)
- ✅ [`tools/__init__.py`](extension/mcp-servers/bridge/tools/__init__.py:57) 등록 리스트에 삭제 모듈 register 없음
- ✅ [`vibezoo_mcp_bridge.py`](extension/mcp-servers/vibezoo_mcp_bridge.py:40) list_subagents는 whiteboard 포함 33개 툴 경로와 무관하게 독립 구현
- ✅ tool_context.py는 explain_code/generate_tests manifest를 보유하지만 이는 삭제된 MCP 툴이 아니라 LLM 파이프라인 매니페스트 — analysis.py L29가 `make_explain_code_context` 를 계속 import하며 해당 팩토리는 tool_context.py에 존재 → 일관성 OK
- ❌ extension.ts에서 제거된 registerCommand 9개 + rebuildCodeIndex: 다른 TS 모듈 참조 없음(executeCommand 검색 0건) → 참조 일관성은 OK. **단, rebuildCodeIndex는 b4bc4cf(D2-4)가 추가한 지 3커밋 만에 6109781이 삭제** — package.json contributes.commands + 20개 locale nls/l10n 문자열을 추가한 D2-4 작업이 사실상 무효화됨 (기획 의도 충돌, REQ-005 vs REQ-006)
- ❌ test_whiteboard_merge.py가 삭제된 ux_coordinator를 참조 → M1

### 2. 미러 동기화
- 전수 67파일, only_ext 0 / only_mir 0 (파일 목록 일치)
- 내용 불일치 12파일 (B2 crow_memory_server + m2 tools 11개)
- start_vibezoo_bridge.bat 루트 생성 이유: 6109781 커밋이 `create mode` 로 추가. init_vibezoo.bat L14는 canonical인 extension 쪽을 복사하므로 설치 경로는 정상. 루트 생성은 D4 미러 유지 관례에 따른 것이나 crow_memory_server/tools 11개와 달리 이 파일만 유독 동기화됨 → 동기화 작업이 선택적/불완전

### 3. 런타임 스모크
- extension/mcp-servers: 14/14 모듈 import OK, 33 tools 등록, 삭제 툴 누출 없음, 중복 없음 ✅
- mcp-servers (root): 14/14 OK, 33 tools, 누출/중복 없음 ✅ (import는 되나 B1처럼 런타임 호출 시 깨지는 경로는 스모크로 못 잡음)

### 4. TS 빌드
- `cd extension && npm run compile` → exit 0, 0 errors, out/extension.js 생성 ✅

### 5. i18n
- Missing=0, Empty=0, Root↔Extension SHA 20/20 ✅
- ⚠️ ko 제외 18개 locale Untranslated=5 (M2의 whiteboard 신규 키) — verify 스크립트가 이를 BLOCKER로 승격하지 않음

### 6. pytest 전수 (extension/mcp-servers/tests/)
- **13 failed, 98 passed, 4 errors** (17.09s)
- test_find_references.py 6 failed → B1
- test_whiteboard_merge.py 7 failed + 4 errors → M1/M2
- 나머지 8개 파일 98건 모두 PASS (test_scout_health, test_index_cache, test_max_tokens 등 D2 시리즈 신규 테스트는 정상)

---

## Issues Discovered
- B1/B2는 BLOCKER. M1/M2는 MAJOR. m1/m2는 MINOR.
- 커밋 메시지(6109781)의 "Verification: tsc 0 errors; py_compile 92 files; mock MCP registration 33 tools / 0 deleted" 는 사실이나, **pytest 전수를 돌리지 않아 B1/M1 회귀를 놓침**. py_compile은 UnboundLocalError를 잡지 못하고, mock registration은 함수 본문을 실행하지 않아 L297을 타지 않음.
- D2-4(b4bc4cf)로 추가된 vibezoo.rebuildCodeIndex가 D6(6109781)에서 삭제됨 — REQ-005(인덱스 워밍 진입점)와 REQ-006(무용 삭제) 간 의사결정 충돌. decisions.md에 사용자 승인 기록이 있는지 VP가 확인 필요.

## Next Step Recommendations (BLOCKER만 즉시 수정 요청 가능)
- **B1 (즉시 수정 가능, Path A)**: scout.py L386 루프 변수 `t` → `rtype` 등으로 rename 1줄. reverse-dependency: `_find_references_impl` 호출부는 scout.register의 find_references 래퍼 1곳 + test 6건. 수정 후 test_find_references 6건 재실행으로 검증 가능.
- **B2 (즉시 수정 가능, Path A)**: `extension/mcp-servers/crow_memory_server.py` 를 `mcp-servers/crow_memory_server.py` 로 복사(241줄). reverse-dependency: crow_client.py는 URL로만 통신하므로 파일 내용만 동기화하면 되고, 영향 파일은 미러 1개 + init 복사 경로 무관.
- M1: test_whiteboard_merge.py의 ux_coordinator fixture 4건 + 한국어 하드코딩 assertion 7건을 삭제 커밋 의도에 맞게 정리 (ux_coordinator 관련 TestAutoAnalyzeWhiteboardDeprecated 클래스 제거 + i18n 문자열 기대값 갱신). BLOCKER는 아니므로 VP 판단.
- M2: whiteboard 신규 t() 키 5~6개를 20개 locale json에 추가 (en/ko/ja 수동, 나머지 fallback). D3-2 후속.
- m2: 루트 tools 11개 파일을 extension 쪽으로 재동기 (m1과 함께 미러 정책을 "extension → root 전체 덮어쓰기"로 통일 권장).

## Affected File List
- extension/mcp-servers/bridge/tools/scout.py (B1, 수정 대상)
- mcp-servers/crow_memory_server.py (B2, 덮어쓰기 대상)
- extension/mcp-servers/tests/test_whiteboard_merge.py (M1)
- extension/mcp-servers/bridge/i18n/translations/*.json (M2, 20파일)
- mcp-servers/bridge/tools/*.py 11개 (m2)
- init_vibezoo.bat (m1, 검토만)

## 부록: 재현 명령
- 미러 비교: `python -u docs/260830_0001_session_reinstall-recovery-and-quality/tools/p5_mirror_compare.py`
- 미러 상세 diff: `python -u docs/260830_0001_session_reinstall-recovery-and-quality/tools/p5_mirror_diff_details.py`
- 스모크: `python -u docs/260830_0001_session_reinstall-recovery-and-quality/tools/p5_smoke.py`
- tsc: `cd extension && npm run compile`
- i18n: `python -u docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_translations.py`
- pytest: `cd extension/mcp-servers && python -m pytest tests/ -q`

## 최종 판정
**FAIL** — BLOCKER 2건(B1 find_references 런타임 크래시, B2 crow_memory_server 미러 붕괴)으로 인해 현재 HEAD를 출시 상태로 승인할 수 없음. 두 BLOCKER 모두 원인 특정 완료, Path A(국소 수정) 가능.
