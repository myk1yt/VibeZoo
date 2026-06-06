# 🪲 위협 분석 보고서 — Error Collection System

> **대상**: [`plans/error-collection-system.md`](plans/error-collection-system.md) v1.0.0  
> **분석일**: 2026-06-06  
> **분석 모드**: Debug (Threat Analysis)  
> **심각도 범례**: 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low | ⚪ Info

---

## 1. 총평 (Executive Summary)

설계는 전반적으로 **방향성은 올바르나**, 실제 구현에 들어가기 전에 반드시 해결해야 할 **🔴 Critical 버그 2건**과 **🟠 High 위험 4건**이 발견되었습니다. 특히 `mcp.tool()` 래핑 메커니즘은 **현재 설계대로 구현 시 모든 MCP 도구 등록이 실패**하는 치명적 결함이 있습니다. 아래 상세 분석을 참고하여 설계 보완이 필요합니다.

---

## 2. 🔴 Critical — `mcp.tool()` 래핑 메커니즘 근본적 결함

### 2.1 문제 설명

설계서 4.1절의 `register_all_tools()` 래핑 코드([`plans/error-collection-system.md:435-473`](plans/error-collection-system.md:435))는 FastMCP의 `mcp.tool` 동작 방식을 오해하고 있습니다.

**현재 모든 도구 모듈의 `register()` 함수** (예: [`scout.py:717-720`](mcp-servers/bridge/tools/scout.py:717))는 다음과 같은 패턴을 사용합니다:

```python
# scout.py, reviewer.py 등 14개 모듈 — @mcp.tool (괄호 없음)
@mcp.tool
def search_codebase(...): ...

# feedback.py ONLY — @mcp.tool() (괄호 있음)
@mcp.tool()
def vibezoo_feedback(...): ...
```

### 2.2 결함 추적 (Trace)

설계서의 `_wrapped_tool`이 `mcp.tool`을 대체했을 때의 실행 흐름:

```
[Case A] @mcp.tool (괄호 없음, 14개 도구)
─────────────────────────────────────────
1. Python: _wrapped_tool(search_codebase_func) 호출
2. targs = (search_codebase_func,), tkwargs = {}
3. name = search_codebase_func.__name__  → "search_codebase"
4. decorator(func) 반환 ← 여기서 끝!
5. Python: search_codebase = decorator (함수)
6. ❌ decorator는 호출되지 않음 — func 인자를 받지 못함
7. ❌ _original_tool()에 전달되지 않음 → MCP 도구 등록 안 됨
```

```
[Case B] @mcp.tool() (괄호 있음, feedback.py)
─────────────────────────────────────────
1. Python: _wrapped_tool() 호출
2. targs = (), tkwargs = {}
3. name = "unknown"  ← targs가 비어있어 함수 이름 추출 불가
4. decorator(func) 반환
5. Python: decorator(vibezoo_feedback_func) 호출
6. wrapped = capture_tool_errors("unknown")(func)  ← 이름이 "unknown"
7. _original_tool()(wrapped) 호출 → 등록은 되지만 이름 오류
```

### 2.3 영향도

| 시나리오 | 결과 |
|----------|------|
| `register_all_tools()` 호출 | **14개 도구 중 14개가 등록되지 않음** (`@mcp.tool` 패턴) |
| `feedback.py` | 등록되지만 도구 이름이 `"unknown"`으로 기록됨 |
| 전체 시스템 | MCP 클라이언트가 모든 도구를 찾지 못함 → **Bridge 무용지물** |

### 2.4 수정 제안

```python
def _wrapped_tool(*targs, **tkwargs):
    # Case 1: @mcp.tool (no parens) — first arg is the function
    if targs and callable(targs[0]) and not tkwargs:
        func = targs[0]
        name = func.__name__
        wrapped = capture_tool_errors(name)(func)
        return _original_tool(wrapped)

    # Case 2: @mcp.tool() or @mcp.tool(name="...")
    name = tkwargs.get("name") or (targs[0].__name__ if targs and callable(targs[0]) else "unknown")
    def decorator(func):
        wrapped = capture_tool_errors(name if name != "unknown" else func.__name__)(func)
        return _original_tool(*targs, **tkwargs)(wrapped)
    return decorator
```

**⚠️ 추가 검증 필요**: FastMCP의 `mcp.tool` 구현체가 `mcp.tool(func)` 호출을 지원하는지 확인해야 합니다. FastMCP 내부에서 `ToolManager.__call__`이 callable을 직접 받을 수 있는지 검증이 필요합니다.

---

## 3. 🟠 High — `fs.watchFile` 이중 감시 및 메모리 누수

### 3.1 문제 설명

설계서는 **동일한 `registry.json` 파일**에 대해 **두 개의 독립적인 `fs.watchFile`** 감시자를 생성합니다:

| 위치 | 인터벌 | 파일 |
|------|--------|------|
| [`ErrorDashboard.ts:615`](plans/error-collection-system.md:615) | 500ms | `~/.vibezoo-errors/registry.json` |
| [`extension.ts` `activateErrorCollection()`:1017](plans/error-collection-system.md:1017) | 1000ms | `~/.vibezoo-errors/registry.json` |

### 3.2 메모리 누수 경로

1. **`ErrorDashboard`**: `onDidDispose`에서 `stopWatching()` 호출 → `fs.unwatchFile()` → 정상 해제 ✅
2. **`activateErrorCollection()`**: `fs.watchFile()` 호출 후 **반환된 `fs.StatWatcher` 객체를 저장하지 않음** → `unwatchFile()`을 호출할 방법이 없음 ❌

```typescript
// 설계서 1017행 — StatWatcher가 가비지 컬렉션되지 않음
fs.watchFile(errorPath, { interval: 1000 }, () => { ... });
// ↑ 반환값 미저장 → 영구 리스너 누수
```

`fs.watchFile`은 내부적으로 `StatWatcher` 객체를 생성하고, 이 객체는 `process` 종료 시까지 이벤트 루프에 바인딩됩니다. Extension이 deactivate 되어도 리스너는 해제되지 않습니다.

### 3.3 기존 코드의 동일한 버그

[`VisualVibePanels.ts:233-239`](extension/src/visual/VisualVibePanels.ts:233)의 `stopWatching()` 메서드는 **`DZ_ACTION_FILE()`을 `unwatchFile`하지 않습니다**:

```typescript
// startWatching()에서 4개 파일 감시 시작
fs.watchFile(wbAction, ...)    // ← unwatch 됨 (235행)
fs.watchFile(uiAction, ...)    // ← unwatch 됨 (236행)
fs.watchFile(dzAction, ...)    // ← unwatch 됨 (237행)
fs.watchFile(wbFile, ...)      // ← ❌ unwatch 누락!

// stopWatching()에서는 3개만 해제
fs.unwatchFile(WB_FILE());       // 235행
fs.unwatchFile(WB_ACTION_FILE());// 236행
fs.unwatchFile(UI_ACTION_FILE());// 237행
// ❌ DZ_ACTION_FILE() 누락!
```

### 3.4 수정 제안

1. `activateErrorCollection()`에서 `StatWatcher` 참조를 저장하고, `context.subscriptions`에 `{ dispose: () => fs.unwatchFile(path) }` 형태로 등록
2. 단일 watcher로 통합: `ErrorDashboard`만 감시하고, Extension은 `ErrorDashboard`를 통해 데이터를 수신
3. `VisualVibePanels.stopWatching()`에 `DZ_ACTION_FILE()` unwatch 추가

---

## 4. 🟠 High — `ErrorRegistry` 읽기/쓰기 경합 (Race Condition)

### 4.1 문제 설명

`ErrorRegistry`는 `threading.Lock`을 사용하지만, **읽기 메서드(`get_recent`, `get_top_frequency`, `get_stats`)는 락을 획득하지 않습니다**.

```python
# record() — 락 사용
def record(self, tool_name, exception, params=None):
    with _lock:           # ✅ 쓰기 보호
        self._ensure_loaded()
        self._cache.insert(0, entry)
        ...

# get_recent() — 락 없음
def get_recent(self, limit=20):
    self._ensure_loaded()  # ❌ 락 없이 캐시 읽기
    return self._cache[:limit]  # ❌ 동시 record() 중이면 슬라이싱 도중 캐시 변경
```

### 4.2 구체적 시나리오

```
Thread A (record)              Thread B (get_recent)
─────────────────────          ─────────────────────
with _lock:
  self._cache.insert(0, e)
  if len > MAX_ENTRIES:
    self._cache = self._cache[:MAX_ENTRIES]  
                                self._cache[:limit]  
                                ↑ 슬라이싱 도중 A가 self._cache를 재할당
                                → inconsistent slice or RuntimeError
```

### 4.3 `_ensure_loaded()`의 추가 문제

```python
def _ensure_loaded(self):
    if self._loaded:       # ❌ 락 없이 flag 확인
        return
    # ... 파일 읽기 ...
    self._loaded = True    # ❌ 락 없이 flag 설정
```

두 스레드가 동시에 `_ensure_loaded()`에 진입하면 **파일을 중복해서 읽고**, `_frequency` 집계가 **두 배로 누적**됩니다.

### 4.4 수정 제안

```python
def get_recent(self, limit=20):
    with _lock:                    # 읽기에도 락 사용
        self._ensure_loaded()
        return list(self._cache[:limit])  # 복사본 반환
```

또는 `threading.RLock` + `copy.deepcopy` 패턴, 혹은 읽기 전용에는 `copy` 모듈로 스냅샷 반환.

---

## 5. 🟠 High — Thread Explosion (Error Storm)

### 5.1 문제 설명

에러 발생 시마다 새로운 daemon thread가 생성됩니다:

```python
# @capture_tool_errors — 371행
t = threading.Thread(target=_record, daemon=True)
t.start()
```

### 5.2 시나리오 분석

| 시나리오 | 초당 Thread 생성 | 결과 |
|----------|-----------------|------|
| Crow Memory 서버 다운 → 모든 `crow_recall()` 실패 | 10~50 | 50개 thread 순간 생성 |
| 파일 시스템 권한 오류로 모든 도구 실패 | 20~100 | 100개 thread, 각 2초 Crow timeout |
| MCP 클라이언트 재시도 루프 | 100+ | Thread 폭발, 메모리 고갈 가능성 |

각 thread는 `_try_crow_ingest()`에서 `urllib.request.urlopen(url, timeout=2)`로 최대 2초 블로킹됩니다. 100개 thread × 2초 = 200 thread-seconds 소비.

### 5.3 수정 제안

1. **ThreadPoolExecutor** 사용: 최대 4~8개 worker로 제한
2. **Queue + 단일 consumer thread**: 에러 이벤트를 큐에 넣고, consumer가 순차 처리
3. **Token bucket rate limiter**: 초당 N개 이상 에러는 기록만 하고 Crow 전송 스킵

---

## 6. 🟡 Medium — `KNOWN_PATTERNS`의 `fix_params` 람다 `None` 참조 오류

### 6.1 문제

```python
# auto_fixer.py:832
("search_codebase", "TypeError"): {
    "fix_params": lambda p: {**p, "regex": p.get("query", ...)},
}
```

`generate_fix_suggestion()`에서 호출 시:

```python
# 887행
"fix_params": known.get("fix_params", lambda p: None)(params)
```

`params`의 기본값은 `None`입니다 ([`error_handler.py:226`](plans/error-collection-system.md:226) `record(tool_name, exception, params=None)`). `{**None, ...}` → **`TypeError` 발생**.

### 6.2 추가: `urllib.parse` 지역 임포트

```python
# 382행, 859행
import urllib.request
import urllib.error
import urllib.parse  # search_crow_for_similar 내에서만 임포트
```

`_try_crow_ingest()`에서는 `urllib.parse`를 임포트하지 않고 `urllib.request.Request()`에 URL 인코딩 없는 raw string을 전달합니다. Crow Memory `/recall?query=...` 호출 시 특수문자(`&`, `#`, `+`)가 있으면 URL 파싱 오류 발생 가능.

### 6.3 수정 제안

```python
# fix_params 람다
"fix_params": lambda p: {**(p or {}), "regex": (p or {}).get("query", ...)}

# urllib.parse 모듈 레벨로 이동
from urllib import parse as urlparse
```

---

## 7. 🟡 Medium — `ErrorRegistry` 싱글톤 `__new__` Thread Safety

### 7.1 문제

```python
class ErrorRegistry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:       # ❌ 락 없음
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
```

두 스레드가 동시에 첫 `ErrorRegistry()` 호출 시:
- Thread A: `_instance is None` → `super().__new__()` → `_init()`
- Thread B: `_instance is None` → `super().__new__()` → `_init()` (A가 할당하기 전)
- 결과: **두 개의 독립적인 ErrorRegistry 인스턴스**, 서로 다른 `_cache`와 `_frequency` 사용

### 7.2 수정 제안

```python
_instance_lock = threading.Lock()

def __new__(cls):
    if cls._instance is None:
        with _instance_lock:
            if cls._instance is None:  # Double-checked locking
                cls._instance = super().__new__(cls)
                cls._instance._init()
    return cls._instance
```

---

## 8. 🟡 Medium — `_frequency` 불일치 (Cache Eviction)

### 8.1 문제

`_ensure_loaded()`는 디스크에서 로드된 모든 entry를 기반으로 `_frequency`를 구축합니다. 이후 `record()`에서 MAX_ENTRIES 초과 시 오래된 entry 제거 + frequency 감소를 수행합니다.

```python
# _ensure_loaded() — 219-221행
for entry in self._cache:
    sig = _error_signature(...)
    self._frequency[sig] = self._frequency.get(sig, 0) + 1

# record() eviction — 265-271행  
if len(self._cache) > MAX_ENTRIES:
    removed = self._cache[MAX_ENTRIES:]
    self._cache = self._cache[:MAX_ENTRIES]
    for r in removed:
        sig = ...
        self._frequency[sig] = max(0, self._frequency.get(sig, 0) - 1)
```

**결함**: `_frequency`가 최초 `_ensure_loaded()`에서 한 번만 빌드되고, 이후 eviction 시에만 감소됩니다. 만약 `_ensure_loaded()`가 모든 100개 entry를 집계한 후, eviction으로 5개가 제거되고 frequency가 5 감소하면 정합성은 유지됩니다. **그러나** 프로세스 재시작 없이 장기 실행될 경우, `_ensure_loaded()`가 다시 호출되지 않으므로( `_loaded = True`), eviction된 항목들의 frequency는 영구히 감소된 상태로 남습니다. 디스크에는 더 이상 존재하지 않는 entry의 frequency 정보가 메모리에 남아 **고스트 시그니처**가 생성됩니다.

### 8.2 수정 제안

`_frequency`를 매번 `_cache`로부터 재계산하거나, `clear()` 호출 시에만 리셋하는 전략 채택.

---

## 9. 🟡 Medium — `FixLoopManager.onMcpError()` 타입 호환성

### 9.1 문제

설계서의 `McpErrorInfo` 인터페이스([`plans/error-collection-system.md:939-945`](plans/error-collection-system.md:939))가 제안되었지만, 실제 [`types/index.ts:67-75`](extension/src/types/index.ts:67)의 `Diagnostic` 인터페이스와 필드 구조가 일치하는지 확인이 필요합니다.

현재 `Diagnostic` 정의:
```typescript
export interface Diagnostic {
  file: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  code: string;
  source: string;
}
```

설계서의 `diagnostics` 구성(959행):
```typescript
const diagnostics: Diagnostic[] = [{
  file: `mcp:${errorInfo.toolName}`,
  line: 1,
  column: 1,
  severity: 'error',
  message: `[${errorInfo.exceptionType}] ${errorInfo.exceptionMessage}`,
  code: errorInfo.exceptionType,
  source: 'vibezoo-mcp',
}];
```

필드 구조는 일치하나, `file`에 `mcp:search_codebase` 같은 가상 경로를 사용하는 것은 `FixLoopManager`의 `parseTscDiagnostics()`가 실제 파일 경로를 기대하는 다른 로직과 충돌할 수 있습니다.

---

## 10. 🟢 Low — 부수적 이슈

### 10.1 `_anonymize_path`: Windows 대소문자 구분

```python
def _anonymize_path(p: str) -> str:
    home = str(HOME_DIR)  # Path.home() → "C:\\Users\\k1yt"
    if p.startswith(home):
        return "~" + p[len(home):]
    return p
```

Windows traceback은 때때로 소문자 드라이브 문자(`c:\\users\\...`)를 사용합니다. `startswith`는 대소문자 구분하므로 익명화가 누락될 수 있습니다.

### 10.2 `fs.watchFile` interval 500ms

`ErrorDashboard`의 500ms 폴링은 파일 변경 후 최대 500ms 지연이 발생합니다. [`VisualVibePanels`](extension/src/visual/VisualVibePanels.ts:40)도 동일한 500ms 상수를 사용하므로 일관성은 있습니다. `fs.watch` (FSWatcher)로 전환하면 더 빠른 응답이 가능합니다.

### 10.3 `urllib.request.urlopen` 예외 처리

```python
# 407행
urllib.request.urlopen(req, timeout=2)
```

`urlopen`은 `URLError`, `HTTPError`, `socket.timeout` 등 다양한 예외를 발생시킵니다. 현재는 `except Exception`으로 모두 삼키므로 디버깅이 어렵습니다. 최소한 `logger.debug()` 출력이 권장됩니다.

### 10.4 Dashboard Webview: `retainContextWhenHidden: true`

이 옵션은 Webview의 수명을 연장하지만, VS Code의 메모리 사용량 증가 요인이 됩니다. 수십 개의 에러 항목을 가진 대시보드가 백그라운드에 오래 머무르면 누적 부하가 발생할 수 있습니다.

---

## 11. ⚪ 호환성 검증

### 11.1 기존 코드와의 충돌

| 영역 | 상태 | 비고 |
|------|------|------|
| [`tools/__init__.py`](mcp-servers/bridge/tools/__init__.py) | ⚠️ 수정 필요 | `register_all_tools()`에 `mcp.tool` 래핑 추가 → Critical 버그 해결 필요 |
| [`vibezoo_mcp_bridge.py`](mcp-servers/vibezoo_mcp_bridge.py:27) | ✅ 호환 | `register_all_tools(mcp)` 호출만 존재, 내부 변경에 투명 |
| [`_base.py`](mcp-servers/bridge/tools/_base.py:34) | ✅ 호환 | `report_error()` 연동은 선택적, 기존 시그니처 변경 없음 |
| [`crow_memory_server.py`](mcp-servers/crow_memory_server.py) | ✅ 호환 | `"error"` register 추가는 선택적, 기존 `context`로 충분 |
| [`FixLoopManager.ts`](extension/src/orchestra/FixLoopManager.ts) | ⚠️ 주의 | `FixLoopSource` type union 추가, `onMcpError()` 신규 메서드 |
| [`StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts) | ⚠️ 주의 | `setErrorCount()` 추가, `_refreshDisplay()` 통합 시 기존 호출부(`setActive`, `setCrowStatus` 등) 모두 검증 필요 |
| [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | ⚠️ 주의 | `ErrorDashboard` 멤버 추가, `dispose()` 체인 확장 |
| [`extension.ts`](extension/src/extension.ts) | ⚠️ 주의 | `activateErrorCollection()` 추가, `openErrorDashboard` 커맨드 등록 |
| `extension/package.json` | ✅ 호환 | 명령어/설정 추가만 필요, 기존 항목과 중복 없음 |

### 11.2 orphaned 코드 검출

설계서에는 **참조되지 않는 코드 경로**가 발견되지 않았습니다. 모든 신규 모듈은 호출 체인이 명확합니다:
- `error_handler.py` → `__init__.py` → `vibezoo_mcp_bridge.py`
- `auto_fixer.py` → `error_handler.py` (간접) → `FixLoopManager.ts`
- `ErrorDashboard.ts` → `VisualVibePanels.ts` → `extension.ts`
- `ErrorCollection.ts` → `extension.ts`

### 11.3 Dead Code 경고

`auto_fixer.py`의 `GlobalAutoFixer.attempt_fix()` ([`plans/error-collection-system.md:919-928`](plans/error-collection-system.md:919))는 구현이 비어 있습니다:
```python
if suggestion["can_auto_fix"] and suggestion["suggested_params"]:
    # 수정된 파라미터로 재시도는 LLM이 수행
    # 여기서는 제안만 생성
    pass
```
`pass`로 남겨둔 것은 의도적이지만, 실제 재시도 로직 없이 배포되면 자동 복구 기능이 명목상으로만 존재하게 됩니다.

---

## 12. 결론 및 권고사항

### 구현 전 필수 조치사항

| # | 항목 | 심각도 | 조치 |
|---|------|--------|------|
| 1 | `mcp.tool()` 래핑 로직 | 🔴 Critical | 2.4절의 수정안 적용 + FastMCP 호환성 검증 |
| 2 | `fs.watchFile` 누수 | 🟠 High | `StatWatcher` 반환값 저장 및 dispose 체인 등록 |
| 3 | `ErrorRegistry` 읽기 경합 | 🟠 High | 읽기 메서드에도 `_lock` 적용 |
| 4 | Thread explosion | 🟠 High | `ThreadPoolExecutor(max_workers=4)` 도입 |
| 5 | `fix_params` None 처리 | 🟡 Medium | `(p or {})` 방어 코드 추가 |
| 6 | Singleton thread safety | 🟡 Medium | Double-checked locking 적용 |
| 7 | `_frequency` 정합성 | 🟡 Medium | 주기적 재계산 또는 eviction 로직 재설계 |

### 설계 품질 평가

| 측면 | 점수 | 비고 |
|------|------|------|
| 아키텍처 방향성 | 8/10 | 기존 인프라(SelfCheck, FixLoopManager) 재사용 우수 |
| 구현 가능성 | 4/10 | `mcp.tool()` 래핑 결함으로 즉시 구현 불가 |
| 성능 (정상 경로) | 9/10 | Zero-overhead 설계 원칙 충실 |
| 성능 (에러 경로) | 5/10 | Thread explosion 위험 |
| 보안 (Privacy) | 8/10 | `_anonymize_path`는 Windows 대소문자 edge case 존재 |
| Graceful degradation | 7/10 | Crow/Cache 실패 시에도 도구 호출 정상 작동 |
| 코드 품질 | 6/10 | `pass` 블록, 지역 임포트, 락 누락 등 품질 이슈 산재 |

### 최종 권고

**현재 설계서 상태로는 구현에 들어가면 안 됩니다.** 위 Critical/High 항목을 먼저 해결한 후, `mcp.tool()` 래핑 메커니즘을 FastMCP 테스트 환경에서 검증한 다음에 구현을 시작해야 합니다. 특히 `_wrapped_tool`의 경우 FastMCP의 `ToolManager` 구현을 직접 확인하고 단위 테스트를 먼저 작성할 것을 강력히 권고합니다.

---

> **분석자**: Debug Mode (Threat Analysis)  
> **다음 단계**: 설계 보완 → P1 구현 전 Critical 항목 해결 → 단위 테스트 → P1 구현
