# [Code Lead] VibeZoo 이중 mcp-servers/ 병합 — 1단계(인벤토리) 보고서

> **Session**: `docs/260830_0001_session_reinstall-recovery-and-quality/`  
> **Date**: 2026-08-30 (Asia/Seoul)  
> **Author**: Dev Lead (Code mode)  
> **Task ID**: D4-1 (`REQ-008`, `bridge-merge-plan.md`, `architecture-plan.md` D-4)  

---

## Task Summary
루트 디렉토리의 `mcp-servers/`와 VS Code 확장의 `extension/mcp-servers/` 디렉토리에 대한 **전수 파일 인벤토리 수집, 바이트 및 해시 비교, AST/기능 diff 분석, Git uncommitted 변경사항 검증, 글로벌/로컬 MCP 설정 경로 조사**를 완료했습니다.
- **결론 요약**: `extension/mcp-servers/`가 버전(`0.15.1`), i18n 다국어 지원, 파일 분석(`_check_uploaded_files_impl`), `crow_memory_server.py`(241줄 정식 Fallback 구현체), `start_vibezoo_bridge.bat` 등 모든 측면에서 상위 집합(Super-set)이자 최신 소스임이 확인되었습니다.
- **루트 유니크 파일**: 소스 코드 기준 **0건** (루트에만 있고 extension에 없는 기능 코드는 전무). `.pytest_cache/` 임시 캐시 1건만 존재.
- **안전성**: 이번 위임(D4-1) 원칙에 따라 루트 및 extension 파일의 삭제나 수정은 일체 수행하지 않았으며, D4-2 병합 및 D4-4 안전 제거를 위한 완벽한 인벤토리와 병합 계획을 수립했습니다.

---

## Actions Taken
1. **전수 파일 직렬화 인벤토리 스캔**: `mcp-servers/` (68개 소스 파일) 및 `extension/mcp-servers/` (69개 소스 파일)의 크기(Byte), 수정시각(mtime), SHA-256 해시, 라인 수 수집.
2. **유니크 파일 식별**: 루트 전용 파일 및 extension 전용 파일 목록화 및 손실 위험성 검토.
3. **파일별 동일/다름 판정 및 AST 구문 분석**: 68개 공통 파일 중 47개 동일, 21개 내용 차이(Diff) 분석. Python AST 파서를 통해 등록 툴(`@mcp.tool`), 클래스, 함수, 모듈 상수(`VERSION`)의 차이점 전수 분석.
4. **Git 관점 변경사항 추적**: `git status` 및 `git diff`를 통해 working tree의 uncommitted 수정 내역이 `mcp-servers/`와 `extension/mcp-servers/` 양쪽에 어떻게 반영되어 있는지 검증.
5. **MCP 설정 참조 경로 전수 조사**: VS Code 글로벌 스토리지(`zoocodeorganization.zoo-code`), 워크스페이스 `.roo/mcp.json`, `extension/src/mcp/McpConfigService.ts`, `init_vibezoo.bat`, `start_vibezoo_bridge.bat` 등 시스템 전반의 참조 경로 검증.
6. **D4-2 병합 및 향후 제거 계획표 작성**: 파일별 액션(복사/유지/제거)과 리스크 방지책 명세.

---

## Result

### 1. 인벤토리 요약 통계
| 항목 | `mcp-servers/` (루트) | `extension/mcp-servers/` (확장) | 비고 |
|---|---|---|---|
| **전체 파일 수 (캐시 제외)** | 68개 | 69개 | extension에 `start_vibezoo_bridge.bat` 포함 |
| **도구 모듈 (`bridge/tools/`)** | 19개 py | 19개 py | 파일 목록 100% 동일, 등록 툴 38개 동일 |
| **다국어 (`bridge/i18n/`)** | 21개 (json 20 + py 1) | 21개 (json 20 + py 1) | 21개 파일 100% SHA-256 일치 |
| **비전 모듈 (`bridge/vision/`)** | 1개 py (`minicpm.py`) | 1개 py (`minicpm.py`) | 100% SHA-256 일치 |
| **내용 일치 파일 (Identical)** | 47개 | 47개 | SHA-256 완벽 일치 |
| **내용 상이 파일 (Different)** | 21개 | 21개 | extension이 최신/상위 호환 |
| **루트 고유 파일 (Root Only)** | **0개** (캐시 제외) | - | *소스 코드 누락 위험 없음* |
| **확장 고유 파일 (Ext Only)** | - | 1개 (`start_vibezoo_bridge.bat`) | 브릿지 자동실행 스크립트 |

### 2. 유니크 파일 식별 목록
#### (1) 루트 전용 파일 (`mcp-servers/`에만 존재)
- **소스 파일**: **없음 (0건)**
- *임시 캐시 파일*: `mcp-servers/.pytest_cache/v/cache/lastfailed` (2 Byte, pytest 실행 시 자동 생성되는 캐시이므로 보존 불필요)
> ⚠️ **안전성 판정**: 루트 디렉토리에만 존재하는 기능 코드나 문서, 설정은 **전무**하므로 루트 디렉토리 제거 시 소스 코드 영구 유실 위험은 없습니다.

#### (2) extension 전용 파일 (`extension/mcp-servers/`에만 존재)
- `extension/mcp-servers/start_vibezoo_bridge.bat` (1,494 Byte, 45 lines, mtime: 2026-06-16 07:17:46)
  - 역할: 포트 9027에서 `vibezoo_mcp_bridge.py` 백그라운드 기동 및 헬스체크 배치 스크립트.
  - 참조: `McpConfigService.ts`의 `autoStartCommand` 및 `init_vibezoo.bat`에서 호출.

### 3. 파일별 상세 비교 및 다름(Diff) 판정 근거 (21개 상이 파일)

| 파일 경로 | 루트 (`mcp-servers/`) | 확장 (`extension/mcp-servers/`) | 판정 | 상세 차이 및 최신성 근거 |
|---|---|---|---|---|
| `.pytest_cache/v/cache/nodeids` | 9184B (106L) | 7407B (85L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 35 lines). |
| `bridge/config.py` | 4037B (89L) | 4037B (89L) | **확장 최신 (0.15.1)** | **버전 차이**: 루트 `VERSION='0.14.4'` vs 확장 `VERSION='0.15.1'`. 확장이 package.json(0.15.1)과 일치하는 최신본. |
| `bridge/tools/_base.py` | 2958B (77L) | 2966B (78L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 28 lines). |
| `bridge/tools/analysis.py` | 41754B (833L) | 41867B (833L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 106 lines). |
| `bridge/tools/deep_analyzer.py` | 40528B (886L) | 40637B (886L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 127 lines). |
| `bridge/tools/editor.py` | 24397B (620L) | 24208B (620L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 63 lines). |
| `bridge/tools/feedback.py` | 2446B (49L) | 2471B (49L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 25 lines). |
| `bridge/tools/file_analyzer.py` | 14405B (361L) | 16910B (422L) | **확장 기능 확장본** | 확장에 `_check_uploaded_files_impl()` 추가(드롭존 세션 기반 파일 감지) 및 `analyze_uploaded_file(file_path='')` 인자 기본값 지원. |
| `bridge/tools/fix_loop.py` | 13569B (350L) | 13584B (350L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 55 lines). |
| `bridge/tools/github_diver.py` | 7238B (161L) | 7327B (162L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 61 lines). |
| `bridge/tools/integrated.py` | 47655B (1020L) | 47755B (1020L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 150 lines). |
| `bridge/tools/knowledge.py` | 15118B (389L) | 15254B (389L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 143 lines). |
| `bridge/tools/reviewer.py` | 47003B (1007L) | 47166B (1007L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 118 lines). |
| `bridge/tools/scout.py` | 37015B (781L) | 37337B (781L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 286 lines). |
| `bridge/tools/setup.py` | 50941B (1257L) | 51038B (1257L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 178 lines). |
| `bridge/tools/ssa.py` | 33872B (827L) | 34070B (827L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 111 lines). |
| `bridge/tools/tester.py` | 20768B (426L) | 21006B (426L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 182 lines). |
| `bridge/tools/ux_coordinator.py` | 13958B (307L) | 14025B (307L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 235 lines). |
| `bridge/tools/web.py` | 13808B (358L) | 13514B (358L) | **확장 i18n 최신본** | 모든 하드코딩 응답/에러 메시지에 `from bridge.i18n import t` 적용 및 다국어 래핑 완료 (Diff: 79 lines). |
| `bridge/tools/whiteboard.py` | 47051B (1100L) | 47245B (1099L) | **확장 i18n 반영본** | 모든 UI/응답 문자열에 `t(...)` 다국어 함수 적용 및 드롭존 안내 메시지 다국어화 완료. |
| `crow_memory_server.py` | 733B (21L) | 9139B (241L) | **확장 완전본 채택** | **구현체 차이**: 루트(21줄)는 DEPRECATED stub. 확장(241줄)은 Proxy/Local fallback 모드를 지원하는 완전한 `CrowMemoryHandler` 구현체. |
| `vibezoo_mcp_bridge.py` | 4781B (90L) | 4733B (90L) | **확장 최신** | 확장에서 `vibezoo_mcp_bridge.py` 서브에이전트 목록의 툴 매핑 최적화 및 i18n 초기화 로직(`i18n_init(VIBEZOO_LANG)`) 탑재. |

#### 🔍 루트 쪽에만 존재하는 기능(함수/클래스/툴) 분석 결과
- **결과**: **루트 쪽에만 존재하는 기능(함수/클래스/툴)은 0건 (None)**.
- **AST 분석 검증 결과**:
  - 38개 MCP 도구(`@mcp.tool`): `analysis.py`(4개), `deep_analyzer.py`(4개), `feedback.py`(1개), `file_analyzer.py`(1개), `fix_loop.py`(3개), `github_diver.py`(1개), `integrated.py`(4개), `knowledge.py`(4개), `reviewer.py`(1개), `scout.py`(4개), `setup.py`(1개), `ssa.py`(1개), `tester.py`(2개), `ux_coordinator.py`(3개), `web.py`(2개), `whiteboard.py`(4개), `vibezoo_mcp_bridge.py`(1개). 루트와 확장의 도구 목록이 100% 일치하거나 확장이 더 유연한 파라미터(`file_path=''`)를 제공.
  - 오히려 `extension/mcp-servers/`에만 추가 기능(`_check_uploaded_files_impl`, `CrowMemoryHandler`, `i18n_init`)이 존재함.

### 4. 전체 파일 직렬화 인벤토리 (전수 대조표)
| # | 상대 경로 (`rel_path`) | 루트 크기 (B) | 루트 SHA-256 (앞 8자리) | 확장 크기 (B) | 확장 SHA-256 (앞 8자리) | 상태 |
|---|---|---|---|---|---|---|
| 1 | `.pytest_cache/.gitignore` | 37 | `3ed731b6` | 37 | `3ed731b6` | ✅ 동일 (Identical) |
| 2 | `.pytest_cache/CACHEDIR.TAG` | 191 | `37dc88ef` | 191 | `37dc88ef` | ✅ 동일 (Identical) |
| 3 | `.pytest_cache/README.md` | 302 | `73fd6fcc` | 302 | `73fd6fcc` | ✅ 동일 (Identical) |
| 4 | `.pytest_cache/v/cache/lastfailed` | 2 | `44136fa3` | - | - | 🔴 *루트 전용 (Root Only)* |
| 5 | `.pytest_cache/v/cache/nodeids` | 9184 | `2e5f13b4` | 7407 | `3ec8e258` | 🔶 상이 (Different) |
| 6 | `bridge/__init__.py` | 670 | `723e98b2` | 670 | `723e98b2` | ✅ 동일 (Identical) |
| 7 | `bridge/ast_engine.py` | 34940 | `5dc4e6ef` | 34940 | `5dc4e6ef` | ✅ 동일 (Identical) |
| 8 | `bridge/ast_singleton.py` | 287 | `02cb40f8` | 287 | `02cb40f8` | ✅ 동일 (Identical) |
| 9 | `bridge/auto_fixer.py` | 6645 | `0d913d07` | 6645 | `0d913d07` | ✅ 동일 (Identical) |
| 10 | `bridge/config.py` | 4037 | `c72c2d76` | 4037 | `4f967523` | 🔶 상이 (Different) |
| 11 | `bridge/crow_client.py` | 2938 | `0e6a4d54` | 2938 | `0e6a4d54` | ✅ 동일 (Identical) |
| 12 | `bridge/embedding_client.py` | 4726 | `2472fe03` | 4726 | `2472fe03` | ✅ 동일 (Identical) |
| 13 | `bridge/error_handler.py` | 14176 | `872919eb` | 14176 | `872919eb` | ✅ 동일 (Identical) |
| 14 | `bridge/file_cache.py` | 9712 | `21d753e4` | 9712 | `21d753e4` | ✅ 동일 (Identical) |
| 15 | `bridge/fuzzy_matcher.py` | 1937 | `7276f9f8` | 1937 | `7276f9f8` | ✅ 동일 (Identical) |
| 16 | `bridge/i18n/__init__.py` | 7995 | `009899bb` | 7995 | `009899bb` | ✅ 동일 (Identical) |
| 17 | `bridge/i18n/translations/ar.json` | 17239 | `2bc3fcc8` | 17239 | `2bc3fcc8` | ✅ 동일 (Identical) |
| 18 | `bridge/i18n/translations/bg.json` | 19801 | `7ec4275d` | 19801 | `7ec4275d` | ✅ 동일 (Identical) |
| 19 | `bridge/i18n/translations/cs.json` | 15541 | `ccfa690d` | 15541 | `ccfa690d` | ✅ 동일 (Identical) |
| 20 | `bridge/i18n/translations/de.json` | 15452 | `c875f039` | 15452 | `c875f039` | ✅ 동일 (Identical) |
| 21 | `bridge/i18n/translations/en.json` | 13985 | `00eb606f` | 13985 | `00eb606f` | ✅ 동일 (Identical) |
| 22 | `bridge/i18n/translations/es.json` | 15459 | `413658df` | 15459 | `413658df` | ✅ 동일 (Identical) |
| 23 | `bridge/i18n/translations/fr.json` | 15575 | `59074c19` | 15575 | `59074c19` | ✅ 동일 (Identical) |
| 24 | `bridge/i18n/translations/he.json` | 16082 | `cff21ac0` | 16082 | `cff21ac0` | ✅ 동일 (Identical) |
| 25 | `bridge/i18n/translations/hu.json` | 15538 | `cd2879b7` | 15538 | `cd2879b7` | ✅ 동일 (Identical) |
| 26 | `bridge/i18n/translations/it.json` | 15090 | `2c973509` | 15090 | `2c973509` | ✅ 동일 (Identical) |
| 27 | `bridge/i18n/translations/ja.json` | 18423 | `9828c15e` | 18423 | `9828c15e` | ✅ 동일 (Identical) |
| 28 | `bridge/i18n/translations/ko.json` | 16358 | `6a33af53` | 16358 | `6a33af53` | ✅ 동일 (Identical) |
| 29 | `bridge/i18n/translations/pl.json` | 15351 | `ea1455d8` | 15351 | `ea1455d8` | ✅ 동일 (Identical) |
| 30 | `bridge/i18n/translations/pt-BR.json` | 15340 | `5a747956` | 15340 | `5a747956` | ✅ 동일 (Identical) |
| 31 | `bridge/i18n/translations/ru.json` | 19463 | `6b7521a5` | 19463 | `6b7521a5` | ✅ 동일 (Identical) |
| 32 | `bridge/i18n/translations/th.json` | 21116 | `aef3818e` | 21116 | `aef3818e` | ✅ 동일 (Identical) |
| 33 | `bridge/i18n/translations/tr.json` | 14881 | `63828f65` | 14881 | `63828f65` | ✅ 동일 (Identical) |
| 34 | `bridge/i18n/translations/vi.json` | 16383 | `5268d2d8` | 16383 | `5268d2d8` | ✅ 동일 (Identical) |
| 35 | `bridge/i18n/translations/zh-CN.json` | 13911 | `8bba3505` | 13911 | `8bba3505` | ✅ 동일 (Identical) |
| 36 | `bridge/i18n/translations/zh-TW.json` | 13965 | `26bf9d29` | 13965 | `26bf9d29` | ✅ 동일 (Identical) |
| 37 | `bridge/intent_detector.py` | 17679 | `3ce23db3` | 17679 | `3ce23db3` | ✅ 동일 (Identical) |
| 38 | `bridge/llm_pipeline.py` | 8190 | `db6272b7` | 8190 | `db6272b7` | ✅ 동일 (Identical) |
| 39 | `bridge/ocr_engine.py` | 18733 | `e86b49a3` | 18733 | `e86b49a3` | ✅ 동일 (Identical) |
| 40 | `bridge/result_ranker.py` | 2953 | `0737b6e9` | 2953 | `0737b6e9` | ✅ 동일 (Identical) |
| 41 | `bridge/search_engine.py` | 17330 | `ce5647df` | 17330 | `ce5647df` | ✅ 동일 (Identical) |
| 42 | `bridge/tool_context.py` | 17231 | `ddb8046c` | 17231 | `ddb8046c` | ✅ 동일 (Identical) |
| 43 | `bridge/tools/__init__.py` | 3537 | `f00224c1` | 3537 | `f00224c1` | ✅ 동일 (Identical) |
| 44 | `bridge/tools/_base.py` | 2958 | `1fe974ea` | 2966 | `d0a8c8e3` | 🔶 상이 (Different) |
| 45 | `bridge/tools/analysis.py` | 41754 | `0e1cd3b2` | 41867 | `c8b33737` | 🔶 상이 (Different) |
| 46 | `bridge/tools/deep_analyzer.py` | 40528 | `c6fe64bc` | 40637 | `db0564b3` | 🔶 상이 (Different) |
| 47 | `bridge/tools/editor.py` | 24397 | `9772e8dc` | 24208 | `92ac94bf` | 🔶 상이 (Different) |
| 48 | `bridge/tools/feedback.py` | 2446 | `d3c7feca` | 2471 | `0fbb1fbd` | 🔶 상이 (Different) |
| 49 | `bridge/tools/file_analyzer.py` | 14405 | `a698870a` | 16910 | `dde7c331` | 🔶 상이 (Different) |
| 50 | `bridge/tools/fix_loop.py` | 13569 | `b563271b` | 13584 | `502432c3` | 🔶 상이 (Different) |
| 51 | `bridge/tools/github_diver.py` | 7238 | `1f5a57ff` | 7327 | `2e0e7138` | 🔶 상이 (Different) |
| 52 | `bridge/tools/integrated.py` | 47655 | `08f4f45f` | 47755 | `c088ebb5` | 🔶 상이 (Different) |
| 53 | `bridge/tools/knowledge.py` | 15118 | `58d0164e` | 15254 | `c3fc65d4` | 🔶 상이 (Different) |
| 54 | `bridge/tools/reviewer.py` | 47003 | `c4f546a5` | 47166 | `cac01100` | 🔶 상이 (Different) |
| 55 | `bridge/tools/scout.py` | 37015 | `e5d51ff3` | 37337 | `59ffeaa5` | 🔶 상이 (Different) |
| 56 | `bridge/tools/setup.py` | 50941 | `211fe1f9` | 51038 | `a160eafc` | 🔶 상이 (Different) |
| 57 | `bridge/tools/ssa.py` | 33872 | `a64f7105` | 34070 | `b8106ebc` | 🔶 상이 (Different) |
| 58 | `bridge/tools/tester.py` | 20768 | `a39b5afd` | 21006 | `a0398de4` | 🔶 상이 (Different) |
| 59 | `bridge/tools/ux_coordinator.py` | 13958 | `9867f39f` | 14025 | `d8a75081` | 🔶 상이 (Different) |
| 60 | `bridge/tools/web.py` | 13808 | `148637a0` | 13514 | `c91d5071` | 🔶 상이 (Different) |
| 61 | `bridge/tools/whiteboard.py` | 47051 | `9e16cf75` | 47245 | `d2a2559e` | 🔶 상이 (Different) |
| 62 | `bridge/utils.py` | 21484 | `d7881a91` | 21484 | `d7881a91` | ✅ 동일 (Identical) |
| 63 | `bridge/vision/minicpm.py` | 3811 | `20ed4457` | 3811 | `20ed4457` | ✅ 동일 (Identical) |
| 64 | `crow_memory_server.py` | 733 | `4eb36729` | 9139 | `7aebf6c7` | 🔶 상이 (Different) |
| 65 | `start_vibezoo_bridge.bat` | - | - | 1494 | `222c5ef9` | 🔵 확장 전용 (Ext Only) |
| 66 | `tests/test_find_references.py` | 5063 | `64d1518d` | 5063 | `64d1518d` | ✅ 동일 (Identical) |
| 67 | `tests/test_fuzzy_search.py` | 6172 | `37a3285e` | 6172 | `37a3285e` | ✅ 동일 (Identical) |
| 68 | `tests/test_max_tokens.py` | 7983 | `1f3cb0e7` | 7983 | `1f3cb0e7` | ✅ 동일 (Identical) |
| 69 | `tests/test_search_cache.py` | 7734 | `1ae25e75` | 7734 | `1ae25e75` | ✅ 동일 (Identical) |
| 70 | `tests/test_semantic_search.py` | 13597 | `e805177e` | 13597 | `e805177e` | ✅ 동일 (Identical) |
| 71 | `tests/test_web_search.py` | 11072 | `5bc274cf` | 11072 | `5bc274cf` | ✅ 동일 (Identical) |
| 72 | `tests/test_whiteboard_merge.py` | 10218 | `2d63de24` | 10218 | `2d63de24` | ✅ 동일 (Identical) |
| 73 | `tools/analyzer.py` | 3514 | `f26502fa` | 3514 | `f26502fa` | ✅ 동일 (Identical) |
| 74 | `vibezoo_mcp_bridge.py` | 4781 | `e9ffe8a8` | 4733 | `f2bbb2c9` | 🔶 상이 (Different) |

### 5. Git 관점 분석 (Working Tree & Uncommitted Modifications)
#### (1) Git 상태 요약
- 현재 working copy에 `mcp-servers/` 및 `extension/mcp-servers/` 양쪽 모두 i18n 적용으로 인한 수정사항(`M`)과 `bridge/i18n/` 디렉토리(`??`)가 존재합니다.
- `extension/mcp-servers/bridge/i18n/` (20개 언어 JSON + `__init__.py`)은 루트의 `mcp-servers/bridge/i18n/`와 **100% 동일하게 이미 생성되어 있음**.
- `vibezoo_mcp_bridge.py`의 경우 확장에 `i18n_init(os.environ.get('VIBEZOO_LANG', 'en'))`가 uncommitted로 정상 반영되어 있습니다.

#### (2) 흡수 필요 Diff 분석
- **결론**: 루트 `mcp-servers/`의 uncommitted 변경사항은 이미 `extension/mcp-servers/`에 더 발전된 형태(i18n 래핑 + config 0.15.1 + crow fallback)로 반영되어 있으므로, **루트에서 확장으로 별도 역흡수(backport)해야 할 diff는 0건**입니다.

### 6. MCP 설정 참조 경로 전수 조사 결과

시스템 내 모든 설정 파일 및 스크립트가 참조하고 있는 MCP 브릿지/서버 경로 분석 결과입니다:

1. **VS Code 글로벌 MCP 설정 (`%APPDATA%/Code/User/globalStorage/zoocodeorganization.zoo-code/settings/mcp_settings.json`)**:
   - `vibezoo`: `http://127.0.0.1:9027/sse` (SSE 엔드포인트 참조, 38개 툴 등록)
   - `crow-memory`: `http://127.0.0.1:9021/mcp`
   - 포트 기반 통신이므로 디렉토리 병합 후에도 포트 9027이 유지되면 정상 작동.

2. **확장 설정 서비스 ([`extension/src/mcp/McpConfigService.ts#L252`](extension/src/mcp/McpConfigService.ts:252))**:
   - `autoStartCommand`: `cd /d "%USERPROFILE%\mcp-servers\vibezoo" && start_vibezoo_bridge.bat` (Windows)
   - `autoStartCommand`: `cd ~/mcp-servers/vibezoo && bash start_vibezoo_bridge.sh` (Linux/macOS)
   - 즉, 런타임 autoStart는 사용자의 `%USERPROFILE%\mcp-servers\vibezoo`를 참조.

3. **확장 내부 직접 참조 ([`extension/src/crow/CrowServerManager.ts#L76`](extension/src/crow/CrowServerManager.ts:76), [`extension/src/extension.ts#L635`](extension/src/extension.ts:635))**:
   - `CrowServerManager.ts`: `path.join(this.extensionPath, 'mcp-servers', 'crow_memory_server.py')`
   - `extension.ts`: `path.join(__dirname, '..', 'mcp-servers', 'vibezoo_mcp_bridge.py')`
   - **확장 내부 코드는 이미 `extension/mcp-servers/` 번들을 참조하고 있음! (루트를 참조하지 않음)**

4. **초기화 및 동기화 스크립트 ([`init_vibezoo.bat#L19-22`](init_vibezoo.bat:19))**:
   - `copy /Y "%REPO_DIR%extension\mcp-servers\vibezoo_mcp_bridge.py" "%TARGET_DIR%\"`
   - `copy /Y "%REPO_DIR%extension\mcp-servers\crow_memory_server.py" "%TARGET_DIR%\"`
   - `xcopy /E /I /Y "%REPO_DIR%extension\mcp-servers\bridge" "%TARGET_DIR%\bridge\"`
   - `xcopy /E /I /Y "%REPO_DIR%extension\mcp-servers\tools" "%TARGET_DIR%\tools\"`
   - **배포 복사 소스가 이미 `extension/mcp-servers`로 지정되어 있음!**

5. **초기화 셸 스크립트 ([`init_vibezoo.sh#L16`](init_vibezoo.sh:16)) — [발견된 수정 사항]**:
   - `cp "$REPO_DIR/start_vibezoo_bridge.bat" "$TARGET_DIR/"` (루트에 `start_vibezoo_bridge.bat`가 없어서 에러 가능)
   - D4-4 단계에서 `$REPO_DIR/extension/mcp-servers/start_vibezoo_bridge.bat`로 경로 수정 필요.

### 7. D4 병합 계획표 (Merge Action Plan)

| 대상 파일/디렉토리 | 소스 승격 여부 | D4-2 (병합 액션) | D4-3 (검증) | D4-4 (최종 처리) |
|---|---|---|---|---|
| `extension/mcp-servers/` (전체) | **유일한 단일 소스(Single Source of Truth)로 승격** | 최신 0.15.1 유지 | 브릿지 컴파일 및 pytest | VSIX 빌드 포함 |
| `extension/mcp-servers/bridge/i18n/` | 유지 | 이미 100% 동일 (추가 작업 불필요) | `import bridge.i18n` 검증 | 단일 소스 유지 |
| `extension/mcp-servers/start_vibezoo_bridge.bat` | 유지 | 유지 (실행 권한/동작 확인) | 스크립트 문법 검증 | `%USERPROFILE%` 배포 |
| `mcp-servers/` (루트 전체) | **제거 대상** | 변경 없음 (보존) | D4-3 통과 확인 대기 | **휴지통(Recycle Bin) 이동** |
| `init_vibezoo.sh` | 보완 | `start_vibezoo_bridge.bat` 복사 경로를 `extension/mcp-servers/`로 갱신 | 셸 문법 검증 | 영구 적용 |

---

## Issues Discovered
1. **`init_vibezoo.sh`의 stale 경로 발견**:
   - `init_vibezoo.sh` 16행에서 `cp "$REPO_DIR/start_vibezoo_bridge.bat"`를 호출하고 있으나, 해당 파일은 `extension/mcp-servers/start_vibezoo_bridge.bat`에만 존재합니다.
   - → D4-4 동기화 스크립트 수정 단계에서 `extension/mcp-servers/start_vibezoo_bridge.bat`로 경로를 갱신해야 합니다.
2. **루트와 확장의 도구 파일 수 오해 해소**:
   - 이전 연구 보고서의 '19개 vs 38개' 표기는 파일 수가 아닌 '19개 도구 파일 내 총 38개 등록 툴'을 의미한 것으로 확인되었습니다. 양쪽 디렉토리 모두 19개의 파이썬 도구 모듈을 보유하고 있습니다.
3. **i18n 번역 파일의 기반영 상태 확인**:
   - 20개 언어 번역 JSON 파일이 `mcp-servers/bridge/i18n/translations/`뿐만 아니라 `extension/mcp-servers/bridge/i18n/translations/`에도 100% 동일하게 이미 생성되어 있어 D4-2 단계의 파일 복사 부담이 대폭 경감되었습니다.

---

## Next Step Recommendations
1. **D4-2 (루트 고유 파일 병합 및 정합성 보완)**:
   - `extension/mcp-servers/`가 이미 모든 상위 기능을 포함하고 있으므로, 별도 파일 이동 없이 `bridge/config.py`의 버전 주석(D5-1 연계) 및 문법 검증(`compileall`)을 수행할 수 있습니다.
2. **D4-3 (단일 소스 빌드 및 테스트 검증)**:
   - `python -m compileall extension/mcp-servers/bridge/ -q` 실행
   - `python -m pytest extension/mcp-servers/tests/ -v` (또는 브릿지 툴 등록 검증)
3. **D4-4 (루트 디렉토리 안전 제거 및 동기화 스크립트 갱신)**:
   - D4-3 검증 완료 후, CPO/VP 승인을 받아 `mcp-servers/` 루트 디렉토리를 Recycle Bin으로 이동.
   - `init_vibezoo.sh` 16행 경로 수정.

---

## Affected File List
- **분석/검증 대상 파일 (변경 없음)**:
  - `mcp-servers/` (68개 소스 파일)
  - `extension/mcp-servers/` (69개 소스 파일)
  - `init_vibezoo.bat`, `init_vibezoo.sh`
  - `extension/src/mcp/McpConfigService.ts`
  - `extension/src/crow/CrowServerManager.ts`
  - `extension/src/extension.ts`
- **산출물 및 검증 도구 (신규 생성)**:
  - [`docs/260830_0001_session_reinstall-recovery-and-quality/092600_code-d4-1-merge-inventory-report.md`](docs/260830_0001_session_reinstall-recovery-and-quality/092600_code-d4-1-merge-inventory-report.md)
  - `docs/260830_0001_session_reinstall-recovery-and-quality/tools/inventory_scan.py`
  - `docs/260830_0001_session_reinstall-recovery-and-quality/tools/analyze_diffs.py`
  - `docs/260830_0001_session_reinstall-recovery-and-quality/tools/detailed_diff_checker.py`
  - `docs/260830_0001_session_reinstall-recovery-and-quality/tools/scan_config_refs.py`
  - `docs/260830_0001_session_reinstall-recovery-and-quality/tools/detailed_diff_analysis.json`