# Code Task Report: D2-3 Server Down Guidance Standardization

## Status
COMPLETE — [`extension/mcp-servers/bridge/tools/scout.py:110`](extension/mcp-servers/bridge/tools/scout.py:110) 및 관련 모듈에 임베딩 서버 다운 시 통일된 복구 안내 메시지 적용, 20개 언어 i18n 번역 동기화, `embedding_health_check` / `rebuild_code_index` 도구 추가 및 미러링 검증 완료.

## Objective and Scope
- **Objective**: 8089 포트 임베딩 서버(nomic-embed-text) 다운 시 AI 에이전트 및 사용자에게 원인과 복구 절차를 명확히 제시하는 통일된 안내 메시지 체계 구축 및 scout 툴 연동.
- **Acceptance criteria**:
  1. [`bridge.tools.scout._search_codebase_impl()`](extension/mcp-servers/bridge/tools/scout.py:63), [`bridge.tools.scout._embedding_health_check_impl()`](extension/mcp-servers/bridge/tools/scout.py:736), [`bridge.tools.scout._rebuild_code_index_impl()`](extension/mcp-servers/bridge/tools/scout.py:756)에서 `is_available() == False` 시 통일된 복구 안내 반환.
  2. 통일 안내 문구:
     - 한국어 (ko): "Embedding 서버(localhost:8089, nomic-embed-text)에 연결할 수 없습니다. 복구: [1] LM Studio/Ollama에서 nomic-embed-text 모델 로드 및 8089 포트 구동 [2] 서버 구동 후 동일 요청 재시도(자동 재probe). 코드 인덱스 수동 리빌드: VS Code 커맨드 'VibeZoo: Rebuild Code Index'."
     - 영어 (en): "Cannot connect to embedding server (localhost:8089, nomic-embed-text). Recovery: [1] Load nomic-embed-text model in LM Studio/Ollama and run on port 8089. [2] Retry the same request after server starts (auto-reprobes). Manual code index rebuild: VS Code command 'VibeZoo: Rebuild Code Index'."
  3. `en.json`/`ko.json` 실번역 및 18개 타 언어 en 폴백으로 20개 언어 번역 사전 누락 0건 유지.
  4. [`extension/mcp-servers/`](extension/mcp-servers)와 [`mcp-servers/`](mcp-servers) 양방향 100% SHA-256 일치.
  5. AST 구문 검증 및 mock 기반 시나리오 테스트 전체 통과.
- **Problem scope**: 임베딩 의존 툴의 오류 메시지 분산 및 불명확한 에러 문자열을 i18n 기반의 명확한 사용자 복구 가이드로 통일.
- **Expected edit scope**: [`extension/mcp-servers/bridge/tools/scout.py`](extension/mcp-servers/bridge/tools/scout.py), [`extension/mcp-servers/bridge/embedding_client.py`](extension/mcp-servers/bridge/embedding_client.py), [`extension/mcp-servers/bridge/i18n/translations/`](extension/mcp-servers/bridge/i18n/translations), [`mcp-servers/`](mcp-servers) 미러.
- **Actual edit scope**: 계획과 100% 일치.
- **Risk level**: LOW (하위 호환성 유지, graceful fallback 유지).

## Implementation Details

### 1. i18n 키 추가 및 20개 언어 사전 동기화
- 번역 파일: [`extension/mcp-servers/bridge/i18n/translations/*.json`](extension/mcp-servers/bridge/i18n/translations/en.json:1) 및 [`mcp-servers/bridge/i18n/translations/*.json`](mcp-servers/bridge/i18n/translations/en.json:1) (20개 언어)
- 추가 키:
  - `"Cannot connect to embedding server (localhost:8089, nomic-embed-text). Recovery: [1] Load nomic-embed-text model in LM Studio/Ollama and run on port 8089. [2] Retry the same request after server starts (auto-reprobes). Manual code index rebuild: VS Code command 'VibeZoo: Rebuild Code Index'."`
  - `"Code Index Rebuild"`
  - `"Code index rebuilt successfully ({0} files indexed)."`
  - `"Embedding Health Check"`

### 2. EmbeddingClient 프로퍼티 보강
- [`bridge.embedding_client.EmbeddingClient`](extension/mcp-servers/bridge/embedding_client.py:29):
  - [`base_url`](extension/mcp-servers/bridge/embedding_client.py:47) 프로퍼티 제공
  - [`model_name`](extension/mcp-servers/bridge/embedding_client.py:52) 프로퍼티 제공
  - [`api_style`](extension/mcp-servers/bridge/embedding_client.py:57) 프로퍼티 제공

### 3. Scout 도구 확장 및 메시지 통일
- [`bridge.tools.scout._search_codebase_impl()`](extension/mcp-servers/bridge/tools/scout.py:63):
  - `EmbeddingClient()` 직접 인스턴스화 대신 싱글톤 [`_get_embed_client()`](extension/mcp-servers/bridge/tools/scout.py:110) 사용.
  - `mode == "semantic"` 및 서버 다운 시 BM25 키워드 랭킹 폴백 유지 + 통일된 복구 안내 문구(`down_guidance`) 첨부.
- [`bridge.tools.scout._embedding_health_check_impl()`](extension/mcp-servers/bridge/tools/scout.py:736):
  - `available`, `api_style`, `url`, `model`, `hint`를 포함하는 JSON 문자열 반환.
  - 다운 시 `hint`에 i18n 통일 복구 안내 포함.
- [`bridge.tools.scout._rebuild_code_index_impl()`](extension/mcp-servers/bridge/tools/scout.py:756):
  - [`bridge.index_cache.CodeIndexCache`](extension/mcp-servers/bridge/index_cache.py:74) 인스턴스를 통해 인덱스 리빌드 수행.
  - 다운 시 마크다운 경고 헤더와 함께 복구 안내 반환.
- [`bridge.tools.scout.register()`](extension/mcp-servers/bridge/tools/scout.py:788):
  - `@mcp.tool embedding_health_check()` 등록.
  - `@mcp.tool rebuild_code_index(target_path)` 등록.

## Changes

| File | Change | Reason |
|------|--------|--------|
| [`extension/mcp-servers/bridge/embedding_client.py:47-60`](extension/mcp-servers/bridge/embedding_client.py:47-60) | `base_url`, `model_name`, `api_style` 프로퍼티 추가 | scout 툴에서 안전하게 클라이언트 메타데이터에 접근 |
| [`extension/mcp-servers/bridge/tools/scout.py:36`](extension/mcp-servers/bridge/tools/scout.py:36) | `_get_embed_client` import 추가 | 싱글톤 인스턴스 사용 |
| [`extension/mcp-servers/bridge/tools/scout.py:110-131`](extension/mcp-servers/bridge/tools/scout.py:110-131) | `_search_codebase_impl` semantic 모드 다운 안내 통일 | BM25 폴백 유지 및 복구 가이드 제공 |
| [`extension/mcp-servers/bridge/tools/scout.py:736-782`](extension/mcp-servers/bridge/tools/scout.py:736-782) | `_embedding_health_check_impl`, `_rebuild_code_index_impl` 구현 및 툴 등록 | D2-3 명세 도구 제공 |
| [`extension/mcp-servers/bridge/i18n/translations/*.json`](extension/mcp-servers/bridge/i18n/translations/en.json:1) | 20개 언어 번역 키 추가 (172개 키) | 다국어 지원 및 i18n 검증 100% 충족 |
| [`mcp-servers/bridge/embedding_client.py:47-60`](mcp-servers/bridge/embedding_client.py:47-60) | root mirror 동기화 | extension과 100% SHA-256 일치 |
| [`mcp-servers/bridge/tools/scout.py:1-850`](mcp-servers/bridge/tools/scout.py:1) | root mirror 동기화 | extension과 100% SHA-256 일치 |
| [`mcp-servers/bridge/i18n/translations/*.json`](mcp-servers/bridge/i18n/translations/en.json:1) | root mirror 동기화 | extension과 100% SHA-256 일치 |
| [`extension/mcp-servers/tests/test_scout_health.py:1-75`](extension/mcp-servers/tests/test_scout_health.py:1) | 신규 테스트 파일 생성 | `embedding_health_check`, `rebuild_code_index` 단위 테스트 |
| [`mcp-servers/tests/test_scout_health.py:1-75`](mcp-servers/tests/test_scout_health.py:1) | root mirror 동기화 | 단위 테스트 미러링 |
| [`extension/mcp-servers/tests/test_semantic_search.py:330-360`](extension/mcp-servers/tests/test_semantic_search.py:330-360) | `_get_embed_client` 패치 반영 및 안내 문구 검증 | 싱글톤 팩토리 변경 반영 |
| [`mcp-servers/tests/test_semantic_search.py:330-360`](mcp-servers/tests/test_semantic_search.py:330-360) | root mirror 동기화 | semantic 검색 테스트 미러링 |
| [`docs/.../tools/test_d2_3_serverdown_guidance.py`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/test_d2_3_serverdown_guidance.py:1) | 세션 검증 스크립트 작성 | AST 파싱, SHA-256 일치, 다국어 시나리오 검증 |

## Preserved Invariants
- 기존 `exact`, `fuzzy`, `ast`, `auto` 검색 모드의 동작에 영향 없음.
- `semantic` 모드에서 임베딩 서버가 가용할 때는 정상적인 벡터 코사인 유사도 랭킹 수행.
- 임베딩 서버가 다운되었을 때 크래시 없이 BM25 랭킹으로 graceful fallback 유지.
- 한국어 사용자(`ko`)와 영문/타 언어 사용자 간 일관된 i18n 번역 시스템 작동.

## Verification

| Level | Command/Check | Result | Evidence |
|-------|--------------|--------|----------|
| Level 1 | AST Syntax Parse ([`test_d2_3_serverdown_guidance.py:46`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/test_d2_3_serverdown_guidance.py:46)) | PASS | 8개 대상 파이썬 파일 모두 AST 파싱 성공 |
| Level 1 | Root vs Extension Mirroring ([`test_d2_3_serverdown_guidance.py:66`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/test_d2_3_serverdown_guidance.py:66)) | PASS | 4개 핵심 파일 100% SHA-256 일치 |
| Level 2 | i18n Translation Coverage ([`verify_translations.py`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_translations.py:1)) | PASS | 20개 언어 모두 172개 키 일치 (Missing 0, Empty 0, 20/20 SHA-256 일치) |
| Level 2 | Health Check Unit Tests ([`test_scout_health.py`](extension/mcp-servers/tests/test_scout_health.py:1)) | PASS | `test_embedding_health_check_available`, `test_embedding_health_check_down`, `test_embedding_health_check_ko`, `test_rebuild_code_index_*` 통과 |
| Level 2 | Semantic Search Tests ([`run_semantic_tests.py`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/run_semantic_tests.py:1)) | PASS | 21/21 passed (0 failed, 0 skipped) |
| Level 3 | Scenario Simulations ([`test_d2_3_serverdown_guidance.py:77`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/test_d2_3_serverdown_guidance.py:77)) | PASS | Scenario A, B, C (KO/EN), D (KO/EN), E (Rebuild OK) 100% 검증 성공 |

## Next Step Recommendations
- D2-4 단계 진행: [`extension/src/extension.ts`](extension/src/extension.ts) 및 [`extension/package.json`](extension/package.json)에 `vibezoo.rebuildCodeIndex` 커맨드 등록.
- D2-5 단계 진행: `vibezoo.rebuildCodeIndex.title` 커맨드 타이틀을 20개 `package.nls.*.json`에 동기화.

## Final Statement
COMPLETE — D2-3 요구사항(통일된 임베딩 다운 복구 안내 메시지, i18n 20개 언어 동기화, scout 툴 확장 및 테스트)이 완벽히 구현 및 검증되었습니다.
