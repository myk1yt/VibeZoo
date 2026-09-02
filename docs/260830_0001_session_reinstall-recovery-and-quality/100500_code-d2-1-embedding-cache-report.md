# Code Task Report: D2-1 embedding_client.py 가용성 캐시 및 백오프 개선

## Status
COMPLETE: [`EmbeddingClient`](extension/mcp-servers/bridge/embedding_client.py:28) 가용성 캐시에 60초 TTL, probe 실패 시 지수 백오프(1s -> 2s -> 4s -> ... 최대 30s), [`reset_availability()`](extension/mcp-servers/bridge/embedding_client.py:64) 공개 함수, 모듈 싱글톤 팩토리 [`get_embedding_client()`](extension/mcp-servers/bridge/embedding_client.py:169) 및 i18n 로깅 래핑 적용 완료.

---

## Objective and Scope
- **Objective**: 임베딩 서버(포트 8089) 미실행 또는 재시작 시 최초 1회 probe 결과를 프로세스 수명 동안 영구 캐시하던 결함을 제거하고, 60초 TTL 양의 캐시와 지수 백오프 음의 캐시, 강제 재probe 기능을 구현하여 임베딩 서버 재시작 시 자동 복구를 지원.
- **Acceptance Criteria**:
  1. [`EmbeddingClient.is_available()`](extension/mcp-servers/bridge/embedding_client.py:43)에 60초 TTL 도입
  2. probe 실패 시 지수 백오프 (1s -> 2s -> 4s -> 최대 30s)로 반복 타임아웃 지연 제거
  3. [`reset_availability()`](extension/mcp-servers/bridge/embedding_client.py:179) 공개 함수 추가 (D2-4 rebuild 커맨드 및 외부 연동용)
  4. 성공 probe 시 백오프/타이머 초기화 및 복구 로그 출력
  5. 기존 호출부([`scout.py`](extension/mcp-servers/bridge/tools/scout.py:110), [`result_ranker.py`](extension/mcp-servers/bridge/result_ranker.py:8) 등) 시그니처 100% 호환 유지
  6. 모듈 싱글톤 팩토리 [`get_embedding_client()`](extension/mcp-servers/bridge/embedding_client.py:169) / [`_get_embed_client()`](extension/mcp-servers/bridge/embedding_client.py:175) 제공
  7. AST 문법 검사 및 단위/모의 시나리오 검증 100% 통과
- **Problem Scope**: [`extension/mcp-servers/bridge/embedding_client.py`](extension/mcp-servers/bridge/embedding_client.py) 및 미러 [`mcp-servers/bridge/embedding_client.py`](mcp-servers/bridge/embedding_client.py)
- **Expected Edit Scope**: [`extension/mcp-servers/bridge/embedding_client.py`](extension/mcp-servers/bridge/embedding_client.py), [`mcp-servers/bridge/embedding_client.py`](mcp-servers/bridge/embedding_client.py)
- **Actual Edit Scope**: 예상 범위와 일치
- **Scope Expansions**: None
- **Risk Level**: 🟢 LOW

---

## Root Cause & Rationale
- **Symptom**: 임베딩 서버(LM Studio nomic-embed-text, 8089)가 꺼진 상태에서 브릿지가 기동되면 `_available=False`가 한 번 설정된 후 영구히 캐시되어, 사용자가 나중에 임베딩 서버를 켜도 시맨틱 검색이 영구히 BM25 폴백 모드로 고정됨.
- **Root Cause**: [`EmbeddingClient.is_available()`](extension/mcp-servers/bridge/embedding_client.py:21) 구현에서 `if self._available is not None: return self._available`로 무기한 캐싱하며 재시도/만료 타이머 로직이 전무했음.
- **Mechanism**:
  - `_last_probe_time`과 `_current_backoff`, `_consecutive_failures` 상태를 추가.
  - 서버 가용(`_available == True`) 시 60초 TTL 동안만 캐시를 신뢰하고 만료 후 백그라운드/다음 호출 시 재probe.
  - 서버 다운(`_available == False`) 시 probe 완료 시점부터 1초 -> 2초 -> 4초 -> ... 최대 30초까지 지수 백오프 윈도우 동안 즉시 `False`를 반환하여 검색 지연을 방지하고, 윈도우 만료 후 다음 요청 시 1회 재probe 시도.
  - 프로브 완료 시점(`time.monotonic()`)에 타이머를 갱신하여 긴 TCP 타임아웃에 의한 백오프 윈도우 조기 소진 방지.
  - [`EmbeddingClient.reset_availability()`](extension/mcp-servers/bridge/embedding_client.py:64) 및 모듈 레벨 [`reset_availability()`](extension/mcp-servers/bridge/embedding_client.py:179)로 즉시 캐시 무효화 및 재probe 유도 지원.

---

## Changes Summary

### 1. [`extension/mcp-servers/bridge/embedding_client.py`](extension/mcp-servers/bridge/embedding_client.py) & [`mcp-servers/bridge/embedding_client.py`](mcp-servers/bridge/embedding_client.py)

#### 변경 전 (Before)
```python
class EmbeddingClient:
    def __init__(self):
        self._base_url = os.environ.get("VIBEZOO_EMBED_URL", "http://localhost:8089")
        self._model = os.environ.get("VIBEZOO_EMBED_MODEL", "nomic-embed-text")
        self._api_style: Optional[str] = None
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        # probe logic (무기한 캐시)
        ...
        self._available = False
        return False
```

#### 변경 후 (After)
```python
DEFAULT_AVAILABILITY_TTL: float = 60.0  # Seconds to cache successful probe
INITIAL_BACKOFF: float = 1.0            # Initial backoff on failure (seconds)
MAX_BACKOFF: float = 30.0               # Maximum backoff interval (seconds)
BACKOFF_FACTOR: float = 2.0             # Multiplier for exponential backoff
PROBE_TIMEOUT: float = 2.0              # HTTP timeout for health check probe (seconds)
EMBED_TIMEOUT: float = 5.0              # HTTP timeout for embedding batch request (seconds)

class EmbeddingClient:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None,
                 ttl: float = DEFAULT_AVAILABILITY_TTL):
        self._base_url = base_url or os.environ.get("VIBEZOO_EMBED_URL", "http://localhost:8089")
        self._model = model or os.environ.get("VIBEZOO_EMBED_MODEL", "nomic-embed-text")
        self._ttl: float = ttl
        self._api_style: Optional[str] = None
        self._available: Optional[bool] = None
        self._last_probe_time: float = 0.0
        self._current_backoff: float = INITIAL_BACKOFF
        self._consecutive_failures: int = 0

    def is_available(self, force: bool = False) -> bool:
        now = time.monotonic()
        if not force and self._available is not None and self._last_probe_time > 0.0:
            if self._available:
                if (now - self._last_probe_time) < self._ttl:
                    return True
            else:
                if (now - self._last_probe_time) < self._current_backoff:
                    return False
        if not force and self._available is not None and self._last_probe_time == 0.0:
            return self._available
        return self._probe(now)

    def reset_availability(self) -> None:
        self._available = None
        self._last_probe_time = 0.0
        self._consecutive_failures = 0
        self._current_backoff = INITIAL_BACKOFF
        self._api_style = None

    def _probe(self, now: float) -> bool:
        # probe logic with i18n logging, timer update at probe completion, exponential backoff
        ...

_client_instance: Optional[EmbeddingClient] = None

def get_embedding_client() -> EmbeddingClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = EmbeddingClient()
    return _client_instance

def _get_embed_client() -> EmbeddingClient:
    return get_embedding_client()

def reset_availability() -> None:
    global _client_instance
    if _client_instance is not None:
        _client_instance.reset_availability()
```

---

## Verification Results

| 검증 항목 | 실행 명령 / 스크립트 | 결과 | 비고 |
|---|---|---|---|
| **문법 검사 (AST Parse)** | `python -c "import ast; ast.parse(open('extension/mcp-servers/bridge/embedding_client.py', encoding='utf-8').read())"` | ✅ PASS | Syntax Error 0 |
| **미러 파일 문법 검사** | `python -c "import ast; ast.parse(open('mcp-servers/bridge/embedding_client.py', encoding='utf-8').read())"` | ✅ PASS | Syntax Error 0 |
| **D2-1 통합 캐시/백오프 테스트** | `python docs/.../tools/test_d2_1_embedding_cache.py` | ✅ 7/7 PASS | 백오프 1s→2s→4s→8s→16s→30s, 복구, TTL 60s, reset, 싱글톤 전수 검증 |
| **실서버 다운 환경 3회 연속 호출** | `python docs/.../tools/verify_3call_scenario.py` | ✅ PASS | Call 1 (8024ms) → Call 2 (0.0015ms 캐시) → Call 3 (0.0005ms 캐시) |
| **기존 시맨틱 검색 회귀 테스트** | `python docs/.../tools/run_semantic_tests.py` | ✅ 21/21 PASS | 기존 `test_semantic_search.py` 21개 테스트 100% 통과 (0 회귀) |

---

## Preserved Invariants
1. [`EmbeddingClient()`](extension/mcp-servers/bridge/embedding_client.py:28) 생성자 기본 파라미터 및 인스턴스 메서드 시그니처 유지 (`is_available`, `embed`, `_embed_ollama`, `_embed_openai`).
2. [`cosine_similarity()`](extension/mcp-servers/bridge/embedding_client.py:151) 및 [`rank_by_embedding()`](extension/mcp-servers/bridge/embedding_client.py:160) 함수 시그니처 및 랭킹 정렬 로직 100% 동일 유지.
3. [`scout.py`](extension/mcp-servers/bridge/tools/scout.py:110)의 기존 호출부 수정 없이 완벽 호환.

---

## Next Step Recommendations
- D2-2: [`extension/mcp-servers/bridge/index_cache.py`](extension/mcp-servers/bridge/index_cache.py) 신규 생성 (디스크 인덱스 영속화 `IndexCache` 클래스 구현)
- D2-3: [`extension/mcp-servers/bridge/tools/scout.py`](extension/mcp-servers/bridge/tools/scout.py:110)에서 `_get_embed_client()` 싱글톤 팩토리 사용 및 `embedding_health_check` / `rebuild_code_index` 툴 등록
