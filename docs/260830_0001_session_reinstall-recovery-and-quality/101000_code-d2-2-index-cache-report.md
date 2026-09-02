# Code Task Report: D2-2 VibeZoo 검색 영속화 — 디스크 기반 인덱스 캐시 신설

## Task Summary
시맨틱 검색 및 코드 인덱싱 결과 벡터를 디스크에 영속화하여 확장 재설치나 프로세스 재시작 후에도 재색인 없이 즉시 로드하고 원큐 리빌드가 가능하도록 하는 디스크 기반 벡터/메타데이터 캐시 모듈 [`CodeIndexCache`](extension/mcp-servers/bridge/index_cache.py:74)를 신설하고 미러 동기화 및 검증을 완료하였습니다.

## Actions Taken
1. **[`CodeIndexCache`](extension/mcp-servers/bridge/index_cache.py:74) 신규 구현**:
   - 캐시 경로: `<workspace>/.zoo-code/index-cache/` (`meta.json` + `vectors.npz`).
   - 무결성/신선도 검사: [`compute_file_hash()`](extension/mcp-servers/bridge/index_cache.py:55) (64KB 스트리밍 sha256 해시) 기반으로 [`is_stale()`](extension/mcp-servers/bridge/index_cache.py:137) 및 [`is_file_stale()`](extension/mcp-servers/bridge/index_cache.py:190) 구현.
   - 벡터 영속화 및 복원: [`save()`](extension/mcp-servers/bridge/index_cache.py:211) (원자적 임시파일 교체 + 5000개 파일 LRU 트리밍), [`load()`](extension/mcp-servers/bridge/index_cache.py:349) (손상 감지 시 자동 [`clear()`](extension/mcp-servers/bridge/index_cache.py:389) 및 안전 복구).
   - 단일 파일/리빌드 API: [`get_embedding()`](extension/mcp-servers/bridge/index_cache.py:411), [`store_embedding()`](extension/mcp-servers/bridge/index_cache.py:434), [`invalidate()`](extension/mcp-servers/bridge/index_cache.py:466), [`rebuild()`](extension/mcp-servers/bridge/index_cache.py:494) 구현.
   - Graceful Fallback: `numpy` 미설치 환경에서도 크래시 없이 메모리 전용 모드로 1회 경고 로그 후 정상 작동.
   - 동시성 제어: 재진입 락 [`threading.RLock()`](extension/mcp-servers/bridge/index_cache.py:90) 적용으로 다중 메서드 호출 시 데드락 방지.
   - 싱글톤 팩토리: [`get_index_cache()`](extension/mcp-servers/bridge/index_cache.py:546) 및 alias [`_get_index_cache()`](extension/mcp-servers/bridge/index_cache.py:554) 제공.
2. **미러 복사 동기화**:
   - 루트의 [`mcp-servers/bridge/index_cache.py`](mcp-servers/bridge/index_cache.py)에 동일 파일 복사하여 D4-4 전까지 동기화 유지.
3. **단위 및 통합 검증 테스트 작성**:
   - [`tools/test_d2_2_index_cache.py`](tools/test_d2_2_index_cache.py): 6개 시나리오(AST 문법 검사, 저장-로드 라운드트립, 파일 변경 시 stale 감지, clear 초기화, numpy 미설치 mock graceful fallback, 손상 복구 & rebuild) 전체 통과.
   - [`extension/mcp-servers/tests/test_index_cache.py`](extension/mcp-servers/tests/test_index_cache.py): 표준 `unittest.TestCase` 스위트 6개 테스트 통과.

## Result
- **AST 문법 검사**: [`extension/mcp-servers/bridge/index_cache.py`](extension/mcp-servers/bridge/index_cache.py), [`mcp-servers/bridge/index_cache.py`](mcp-servers/bridge/index_cache.py) 양쪽 모두 정상 구문 분석 완료 (`ast.parse` PASS).
- **테스트 결과**:
  - `tools/test_d2_2_index_cache.py`: 6개 항목 ALL PASS.
  - `python -m unittest extension/mcp-servers/tests/test_index_cache.py`: 6 tests in 0.062s OK.

## Issues Discovered
- 초기 lock 구현 시 단순 `threading.Lock()` 사용으로 `load()` 내부에서 `is_stale()` / `load_manifest()` 호출 시 재진입 데드락이 발생할 가능성을 발견하여, 즉시 [`threading.RLock()`](extension/mcp-servers/bridge/index_cache.py:90)으로 교체하고 안전성을 입증하였습니다.

## Next Step Recommendations
- D2-3 단계로 진행: [`extension/mcp-servers/bridge/tools/scout.py`](extension/mcp-servers/bridge/tools/scout.py)에 `@mcp.tool embedding_health_check()` 및 `@mcp.tool rebuild_code_index(target_path)` 툴 추가 및 `_search_codebase_impl` 싱글톤 연동.

## Affected File List
- [`extension/mcp-servers/bridge/index_cache.py`](extension/mcp-servers/bridge/index_cache.py) (신규 생성)
- [`mcp-servers/bridge/index_cache.py`](mcp-servers/bridge/index_cache.py) (미러 생성)
- [`tools/test_d2_2_index_cache.py`](tools/test_d2_2_index_cache.py) (신규 생성)
- [`extension/mcp-servers/tests/test_index_cache.py`](extension/mcp-servers/tests/test_index_cache.py) (신규 생성)
