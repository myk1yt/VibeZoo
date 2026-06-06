# VibeZoo 자동 에러 수집 및 대응 시스템 (Error Collection & Auto-Response System) 설계

> **Version**: 1.0.0 | **Date**: 2026-06-06 | **Author**: Architect Mode  
> **Target**: VibeZoo v0.15.0 | **Priority**: P1 (Foundation)

---

## 목차

1. [개요](#1-개요)
2. [기존 코드 분석](#2-기존-코드-분석)
3. [전체 아키텍처](#3-전체-아키텍처)
4. [컴포넌트 상세 설계](#4-컴포넌트-상세-설계)
   - [4.1 Python Bridge — Global Error Handler](#41-python-bridge--global-error-handler)
   - [4.2 Error Registry (저장소)](#42-error-registry-저장소)
   - [4.3 Crow Memory 동기화](#43-crow-memory-동기화)
   - [4.4 Error Dashboard (VS Code Webview)](#44-error-dashboard-vs-code-webview)
   - [4.5 Auto-Fix with Crow Pattern Matching](#45-auto-fix-with-crow-pattern-matching)
   - [4.6 Extension Notification (StatusBar + Message)](#46-extension-notification-statusbar--message)
5. [데이터 흐름](#5-데이터-흐름)
6. [변경 대상 파일 목록](#6-변경-대상-파일-목록)
7. [구현 우선순위 (P1~P5)](#7-구현-우선순위-p1p5)
8. [에러 분류 체계](#8-에러-분류-체계)
9. [설계 원칙 검증](#9-설계-원칙-검증)
10. [테스트 시나리오](#10-테스트-시나리오)

---

## 1. 개요

현재 VibeZoo는 MCP 도구 호출 중 발생하는 예외(예: [`search_files`](mcp-servers/bridge/tools/scout.py)에 `regex` 파라미터 누락 등)를 사용자에게 즉시 노출하지만, 이를 **자동으로 수집·분석·대응**하는 체계가 없습니다.

이 설계는 VibeZoo가 **LLM의 개입 없이도** 자동으로 에러를 감지·수집·집계하고, **과거 유사 패턴과 매칭하여 자동 복구**를 시도하는 End-to-End 시스템을 정의합니다.

---

## 2. 기존 코드 분석

### 2.1 Python Bridge — 현재 에러 처리

| 파일 | 현재 상태 | 한계 |
|------|----------|------|
| [`_base.py`](mcp-servers/bridge/tools/_base.py:34) `report_error()` | JSON 포맷의 수동 에러 보고 유틸 | 도구 함수 내에서 명시적 호출 필요, 자동 캡처 없음 |
| [`_base.py`](mcp-servers/bridge/tools/_base.py:7) `validate_file_path()` | 파일 경로 검증 → 에러 마크다운 반환 | 검증 실패 시 예외 대신 문자열 반환 (catch 불가) |
| 각 도구 함수 | `try/except` 없이 raw call | 예외 발생 시 MCP 클라이언트가 받아서 LLM에게 노출 |

**핵심 발견**: Python Bridge에는 **전역 에러 캡처 레이어가 전혀 없습니다**. 모든 예외는 MCP 프로토콜 수준에서 처리되어 LLM에게 그대로 전달됩니다.

### 2.2 Extension — 기존 에러 관련 인프라

| 파일 | 담당 | 재사용 가능 요소 |
|------|------|------------------|
| [`SelfCheck.ts`](extension/src/safety/SelfCheck.ts:28) `AlarmMonitor` | 60초 슬라이딩 윈도우 알람 추적, 분당 30회 초과 시 throttle | 알람 카운팅 패턴을 에러 빈도 집계로 확장 가능 |
| [`SelfCheck.ts`](extension/src/safety/SelfCheck.ts:106) `SelfChecker` | 시스템 자가진단, `autoRecover()` 로 복구 시도 | `autoRecover()` 패턴을 에러 자동복구로 확장 가능 |
| [`BuildFeedback.ts`](extension/src/flow/BuildFeedback.ts:9) `activateBuildFeedback()` | `onDidEndTaskProcess` 구독 → 빌드 실패 감지 → FixLoopManager 호출 | **에러 이벤트 구독 패턴**을 MCP 에러 감지로 확장 |
| [`FixLoopManager.ts`](extension/src/orchestra/FixLoopManager.ts:92) `FixLoopManager` | 상태 머신(idle→pending→in_progress→building→resolved/abandoned), I_instability 계산, oscillation 감지 | **자동 수정 루프 상태 머신**을 MCP 에러 자동복구로 확장 |
| [`FixLoopManager.ts`](extension/src/orchestra/FixLoopManager.ts:75) `calculateInstability()` | α=0.35, β=0.45, γ=0.20 가중치로 불안정성 지표 계산 | **불안정성 임계값 로직**을 MCP 에러에도 적용 |
| [`StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts:100) | StatusBar 통합 관리, `NotificationThrottle` | StatusBar에 에러 카운트 표시 추가 |
| [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts:85) | Webview 패널(Whiteboard, Diagram, Dropzone) | **`fs.watchFile` 패턴**을 Dashboard 자동 갱신에 재사용 |

### 2.3 Crow Memory — 기존 저장소

| 파일 | 기능 | 확장 가능성 |
|------|------|-------------|
| [`crow_memory_server.py`](mcp-servers/crow_memory_server.py:66) `crow_ingest()` | 레지스터에 엔트리 저장 | `"error"` 레지스터 추가하여 에러 패턴 저장 |
| [`crow_memory_server.py`](mcp-servers/crow_memory_server.py:77) `crow_recall()` | 키워드 기반 검색 (substring match) | 에러 시그니처로 유사 패턴 검색 |
| [`crow_memory_server.py`](mcp-servers/crow_memory_server.py:129) `crow_ingest_from_build()` | 빌드 로그를 Crow에 저장 | MCP 에러도 동일 패턴으로 저장 가능 |

**핵심 발견**: Crow Memory는 이미 에러 저장·검색 인프라를 갖추고 있습니다. `crow_ingest_from_build()`의 패턴을 MCP 도구 에러로 확장하면 됩니다.

### 2.4 도구 등록 구조

```
register_all_tools(mcp)  ← __init__.py
    ├── reg_setup(mcp)
    ├── reg_scout(mcp)
    ├── reg_reviewer(mcp)
    ├── reg_deep(mcp)
    ├── reg_tester(mcp)
    ├── reg_wb(mcp)
    ├── reg_fix(mcp)
    └── ... (14개 +)
```

각 `register()` 함수는 `@mcp.tool()` 데코레이터로 개별 함수를 등록합니다. **에러 캡처 삽입 지점**은 이 `register_all_tools()` 함수입니다.

---

## 3. 전체 아키텍처

```
┌──────────────────────────────────────────────────────────────────────┐
│                        MCP Tool Call (Zoo Code → LLM)                 │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Python Bridge (vibezoo_mcp_bridge.py :9027)                         │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  ErrorCaptureMiddleware (mcp-servers/bridge/error_handler.py)│     │
│  │  ┌───────────────────────────────────────────────────────┐  │     │
│  │  │  @capture_tool_errors(tool_name)                      │  │     │
│  │  │  def tool_function(*args, **kwargs):                  │  │     │
│  │  │      try:                                              │  │     │
│  │  │          return original_func(*args, **kwargs)        │  │     │
│  │  │      except Exception as e:                            │  │     │
│  │  │          ErrorRegistry.record(tool_name, e, kwargs)   │  │     │
│  │  │          raise  # 원본 예외 유지                       │  │     │
│  │  └───────────────────────────────────────────────────────┘  │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                 │                                      │
└─────────────────────────────────┼──────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
          ┌──────────────┐ ┌───────────┐ ┌────────────────┐
          │ registry.json│ │ Crow      │ │ VS Code        │
          │ (~/.vibezoo- │ │ Memory    │ │ Notification   │
          │  errors/)     │ │ /ingest   │ │ (StatusBar +   │
          │              │ │           │ │  showErrorMsg) │
          └──────┬───────┘ └─────┬─────┘ └───────┬────────┘
                 │               │               │
                 │      ┌────────┘               │
                 ▼      ▼                        ▼
          ┌──────────────────────┐  ┌─────────────────────────┐
          │ Error Dashboard      │  │ ErrorAutoFix             │
          │ (VS Code Webview)    │◄─┤ - Crow Pattern Match    │
          │ - Top 5 빈도         │  │ - Known Pattern Retry   │
          │ - 최근 에러          │  │ - FixLoopManager 연동   │
          │ - 복구 성공률        │  │ - User Hint 제공         │
          │                      │  │                          │
          │ ▲ fs.watchFile       │  └─────────────────────────┘
          │   (registry.json)    │
          └──────────────────────┘
```

### 핵심 설계 결정

| 결정 | 선택 | 근거 |
|------|------|------|
| 에러 캡처 위치 | `__init__.py` → `register_all_tools()` 에서 일괄 래핑 | 16개 도구 파일 개별 수정 불필요, 단일 변경 지점 |
| 래핑 방식 | `mcp.tool()` 반환값을 래퍼로 감싸기 | FastMCP의 `@mcp.tool()` 데코레이터와 호환 |
| 저장소 형식 | JSON 파일 (1차) + Crow Memory (2차) | JSON: 빠른 읽기·쓰기, Crow: 장기 패턴 분석 |
| 대시보드 갱신 | `fs.watchFile` | 기존 VisualVibePanels와 일관된 패턴 |
| 자동복구 연동 | FixLoopManager 상태 머신 확장 | 기존 인프라 재사용, oscillation 감지 등 혜택 |

---

## 4. 컴포넌트 상세 설계

### 4.1 Python Bridge — Global Error Handler

#### 파일: `mcp-servers/bridge/error_handler.py` (신규)

```python
# VibeZoo Bridge — 전역 에러 캡처 및 레지스트리
# 모든 MCP 도구 호출을 투명하게 감싸 예외를 자동 수집한다.
# 설계 원칙: Zero-overhead on success, Graceful degradation

import functools
import json
import os
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

HOME_DIR = Path.home()
ERROR_DIR = HOME_DIR / ".vibezoo-errors"
REGISTRY_PATH = ERROR_DIR / "registry.json"
MAX_ENTRIES = 100
FREQUENCY_THRESHOLD = 5  # 동일 에러 N회 → "주의" 플래그

_lock = threading.Lock()

# ── 익명화 ──────────────────────────────────────────────
def _anonymize_path(p: str) -> str:
    """사용자 홈 디렉토리 경로를 ~로 익명화"""
    home = str(HOME_DIR)
    if p.startswith(home):
        return "~" + p[len(home):]
    return p

# ── 에러 시그니처 생성 ─────────────────────────────────
def _error_signature(tool_name: str, exception_type: str) -> str:
    """동일 에러 패턴 식별용 시그니처"""
    return f"{tool_name}:{exception_type}"

# ── ErrorRegistry 클래스 ─────────────────────────────────
class ErrorRegistry:
    """스레드 안전한 에러 레지스트리 (JSON 파일 + 메모리 캐시)"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self._cache: list = []
        self._frequency: dict = {}  # signature → count
        self._loaded = False
    
    def _ensure_loaded(self):
        if self._loaded:
            return
        try:
            ERROR_DIR.mkdir(parents=True, exist_ok=True)
            if REGISTRY_PATH.exists():
                raw = REGISTRY_PATH.read_text("utf-8")
                self._cache = json.loads(raw) if raw.strip() else []
            # 빈도 복원
            for entry in self._cache:
                sig = _error_signature(entry.get("tool", ""), entry.get("exception_type", ""))
                self._frequency[sig] = self._frequency.get(sig, 0) + 1
        except Exception:
            self._cache = []
        self._loaded = True
    
    def record(self, tool_name: str, exception: Exception, params: dict = None) -> str:
        """에러 기록. 예외 발생 시 silently fail (도구 호출에 영향 없음)."""
        entry_id = str(uuid.uuid4())[:8]
        tb = traceback.format_exc()
        
        # 파일:라인 추출
        file_line = "unknown"
        try:
            tb_lines = tb.strip().split("\n")
            for line in reversed(tb_lines):
                if 'File "' in line:
                    parts = line.strip().split('File "')
                    if len(parts) > 1:
                        rest = parts[1].split('"')
                        if len(rest) > 1:
                            file_path = _anonymize_path(rest[0])
                            line_no = rest[1].strip().replace(", line ", "")
                            file_line = f"{file_path}:{line_no}"
                            break
        except Exception:
            pass
        
        entry = {
            "id": entry_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "parameters": params or {},
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": tb,
            "file_line": file_line,
            "auto_fix_attempted": False,
            "auto_fix_success": None,
        }
        
        try:
            with _lock:
                self._ensure_loaded()
                self._cache.insert(0, entry)
                if len(self._cache) > MAX_ENTRIES:
                    removed = self._cache[MAX_ENTRIES:]
                    self._cache = self._cache[:MAX_ENTRIES]
                    # 제거된 항목의 빈도 감소
                    for r in removed:
                        sig = _error_signature(r.get("tool", ""), r.get("exception_type", ""))
                        self._frequency[sig] = max(0, self._frequency.get(sig, 0) - 1)
                
                # 빈도 집계
                sig = _error_signature(tool_name, type(exception).__name__)
                self._frequency[sig] = self._frequency.get(sig, 0) + 1
                
                # 디스크 쓰기 (best-effort)
                try:
                    REGISTRY_PATH.write_text(
                        json.dumps(self._cache, ensure_ascii=False, indent=2),
                        "utf-8"
                    )
                except OSError:
                    pass  # Graceful degradation
        except Exception:
            pass  # Graceful degradation
        
        return entry_id
    
    def get_recent(self, limit: int = 20) -> list:
        """최근 에러 조회"""
        self._ensure_loaded()
        return self._cache[:limit]
    
    def get_top_frequency(self, limit: int = 5) -> list:
        """빈도 Top N"""
        self._ensure_loaded()
        sorted_freq = sorted(self._frequency.items(), key=lambda x: x[1], reverse=True)
        return [{"signature": sig, "count": cnt, "is_critical": cnt >= FREQUENCY_THRESHOLD}
                for sig, cnt in sorted_freq[:limit]]
    
    def get_stats(self) -> dict:
        """통계 요약"""
        self._ensure_loaded()
        total = len(self._cache)
        auto_fix_attempted = sum(1 for e in self._cache if e.get("auto_fix_attempted"))
        auto_fix_success = sum(1 for e in self._cache if e.get("auto_fix_success") is True)
        auto_fix_fail = sum(1 for e in self._cache if e.get("auto_fix_success") is False)
        return {
            "total_errors": total,
            "unique_signatures": len(self._frequency),
            "auto_fix_attempted": auto_fix_attempted,
            "auto_fix_success": auto_fix_success,
            "auto_fix_fail": auto_fix_fail,
            "auto_fix_success_rate": round(auto_fix_success / max(auto_fix_attempted, 1), 2),
        }
    
    def mark_auto_fix(self, entry_id: str, success: bool):
        """자동 복구 결과 마킹"""
        try:
            with _lock:
                self._ensure_loaded()
                for entry in self._cache:
                    if entry.get("id") == entry_id:
                        entry["auto_fix_attempted"] = True
                        entry["auto_fix_success"] = success
                        break
                try:
                    REGISTRY_PATH.write_text(
                        json.dumps(self._cache, ensure_ascii=False, indent=2),
                        "utf-8"
                    )
                except OSError:
                    pass
        except Exception:
            pass
    
    def clear(self):
        """레지스트리 초기화"""
        with _lock:
            self._cache = []
            self._frequency = {}
            try:
                REGISTRY_PATH.write_text("[]", "utf-8")
            except OSError:
                pass


# ── 데코레이터: capture_tool_errors ────────────────────
def capture_tool_errors(tool_name: str):
    """MCP 도구 함수를 에러 캡처로 감싸는 데코레이터.
    
    Zero-overhead on success: 예외가 없으면 레지스트리 접근 없이 원본 함수만 호출.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 비동기로 에러 기록 (threading, non-blocking)
                def _record():
                    try:
                        registry = ErrorRegistry()
                        registry.record(tool_name, e, kwargs)
                        # Crow Memory에 비동기 저장 시도
                        _try_crow_ingest(tool_name, e, kwargs)
                    except Exception:
                        pass  # Graceful degradation
                
                t = threading.Thread(target=_record, daemon=True)
                t.start()
                
                raise  # 원본 예외 재발생 (MCP 클라이언트로 전파)
        return wrapper
    return decorator


def _try_crow_ingest(tool_name: str, exception: Exception, params: dict = None):
    """Crow Memory에 에러 정보 저장 (best-effort)"""
    try:
        import urllib.request
        import urllib.error
        
        content = (
            f"## MCP Tool Error\n"
            f"- **Tool**: {tool_name}\n"
            f"- **Exception**: {type(exception).__name__}: {str(exception)}\n"
            f"- **Time**: {datetime.now(timezone.utc).isoformat()}\n"
        )
        if params:
            content += f"- **Parameters**: {json.dumps(params, ensure_ascii=False)}\n"
        
        payload = json.dumps({
            "content": content,
            "register": "context",
            "source": "error_handler",
            "tags": ["error", "mcp_tool", tool_name, type(exception).__name__],
        }).encode("utf-8")
        
        req = urllib.request.Request(
            "http://localhost:9020/ingest",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass  # Crow 없어도 정상 동작


# ── 싱글톤 접근자 ───────────────────────────────────────
error_registry = ErrorRegistry()
```

#### 통합 지점: `mcp-servers/bridge/tools/__init__.py` (수정)

```python
# 기존:
from bridge.tools.scout import register as reg_scout
# ...

# 수정: 각 register 함수를 래핑하여 등록된 모든 도구에 에러 캡처 적용
from bridge.error_handler import capture_tool_errors

def register_all_tools(mcp):
    """모든 tools/*.py의 register(mcp) 함수를 호출하여 도구 등록
    
    ★ 에러 캡처: 각 도구 등록 전에 mcp.tool()을 래핑하여
       모든 MCP 도구 호출이 자동으로 try/except로 감싸지도록 함.
    """
    # 원본 mcp.tool 참조 저장
    _original_tool = mcp.tool
    
    def _wrapped_tool(*targs, **tkwargs):
        """mcp.tool()을 래핑하여 자동 에러 캡처 적용"""
        name = tkwargs.get("name") or (targs[0].__name__ if targs else "unknown")
        
        def decorator(func):
            # 에러 캡처로 감싼 후 원본 mcp.tool()에 전달
            wrapped = capture_tool_errors(name)(func)
            return _original_tool(*targs, **tkwargs)(wrapped)
        return decorator
    
    # mcp.tool을 래핑된 버전으로 교체
    mcp.tool = _wrapped_tool
    
    try:
        from bridge.tools.setup import register as reg_setup
        from bridge.tools.scout import register as reg_scout
        from bridge.tools.reviewer import register as reg_reviewer
        from bridge.tools.deep_analyzer import register as reg_deep
        from bridge.tools.tester import register as reg_tester
        from bridge.tools.file_analyzer import register as register_file_analyzer
        from bridge.tools.whiteboard import register as reg_wb
        from bridge.tools.fix_loop import register as reg_fix
        from bridge.tools.integrated import register as reg_integrated
        from bridge.tools.analysis import register as reg_analysis
        from bridge.tools.knowledge import register as reg_knowledge
        from bridge.tools.web import register as reg_web
        from bridge.tools.ssa import register as reg_ssa
        from bridge.tools.editor import register as reg_editor
        from bridge.tools.ux_coordinator import register as reg_ux
        from bridge.tools.feedback import register as reg_feedback
        
        for reg in [reg_setup, reg_scout, reg_reviewer, reg_deep, reg_tester,
                    register_file_analyzer, reg_wb, reg_fix, reg_integrated,
                    reg_analysis, reg_knowledge, reg_web, reg_ssa, reg_editor,
                    reg_ux, reg_feedback]:
            reg(mcp)
    finally:
        # 원본 mcp.tool 복원 (다른 코드와의 호환성)
        mcp.tool = _original_tool
```

**설계 노트**: `mcp.tool`을 임시로 래핑하는 방식은 모든 개별 도구 파일을 수정하지 않고도 일괄 적용할 수 있습니다. `try/finally`로 원본을 복원하여 부작용을 방지합니다.

---

### 4.2 Error Registry (저장소)

#### 저장소 위치

```
~/.vibezoo-errors/
├── registry.json          ← 최근 100개 에러 (빠른 읽기·쓰기)
└── .lock                  ← (미사용, threading.Lock으로 대체)
```

#### `registry.json` 스키마

```json
[
  {
    "id": "a1b2c3d4",
    "timestamp": "2026-06-06T19:30:00.000Z",
    "tool": "search_codebase",
    "parameters": {"query": "something", "max_results": 10},
    "exception_type": "TypeError",
    "exception_message": "search_files() missing 1 required positional argument: 'regex'",
    "traceback": "Traceback (most recent call last):\n  File ...",
    "file_line": "~/mcp-servers/bridge/tools/scout.py:142",
    "auto_fix_attempted": false,
    "auto_fix_success": null
  }
]
```

#### 빈도 집계 알고리즘

```python
FREQUENCY_THRESHOLD = 5  # 동일 (tool, exception_type) 5회 → "주의"

def _check_critical(signature: str) -> bool:
    return error_registry._frequency.get(signature, 0) >= FREQUENCY_THRESHOLD
```

"주의" 플래그가 설정되면:
1. StatusBar에 경고 아이콘 표시
2. Dashboard에서 해당 항목 강조
3. Crow Memory에 "critical" 태그로 저장

#### Graceful Degradation

- 디스크 I/O 실패 → 에러는 메모리 캐시에만 저장, 도구 호출 정상 진행
- `registry.json` 파싱 실패 → 빈 캐시로 초기화
- Crow Memory 연결 실패 → 로컬 JSON만 사용, 3초 타임아웃

---

### 4.3 Crow Memory 동기화

#### 신규 레지스터 제안

```python
# crow_memory_server.py의 VALID_REGISTERS에 추가 (선택적)
VALID_REGISTERS = set(DEFAULT_REGISTERS.keys()) | {
    'coding_style', 'naming', 'formatting', 'architecture', 'workflow',
    'error',  # ← 신규: MCP 도구 에러 패턴 저장
}
```

또는 기존 `context` 레지스터를 활용 (기존 코드 변경 최소화):
- `source="error_handler"`, `tags=["error", "mcp_tool", tool_name, exception_type]`

#### 자동 저장 흐름

```
Error Occurs
    │
    ├──→ ErrorRegistry.record() → registry.json (동기, 빠름)
    │
    └──→ _try_crow_ingest()      → Crow Memory /ingest (비동기, best-effort)
            │
            └── source="error_handler"
                tags=["error", "mcp_tool", tool_name, exception_type]
                register="context"
```

---

### 4.4 Error Dashboard (VS Code Webview)

#### 파일: `extension/src/visual/ErrorDashboard.ts` (신규)

```typescript
// VibeZoo Wave 7: Error Dashboard
// registry.json을 감시하여 실시간 에러 현황판 표시
// VisualVibePanels의 fs.watchFile 패턴 재사용

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const REGISTRY_PATH = path.join(os.homedir(), '.vibezoo-errors', 'registry.json');

export class ErrorDashboard {
  private panel: vscode.WebviewPanel | null = null;
  private _watching = false;
  private lastMtime = { current: 0 };

  open(): vscode.WebviewPanel {
    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.Two);
      return this.panel;
    }

    this.panel = vscode.window.createWebviewPanel(
      'vibezoo-error-dashboard',
      '🐞 VibeZoo Error Dashboard',
      vscode.ViewColumn.Two,
      { enableScripts: true, retainContextWhenHidden: true }
    );

    this.panel.webview.html = this.getHtml();
    this.startWatching();
    
    this.panel.onDidDispose(() => {
      this.panel = null;
      this.stopWatching();
    });

    // 초기 데이터 로드
    this.sendData();

    return this.panel;
  }

  private startWatching(): void {
    if (this._watching) return;
    this._watching = true;
    this.lastMtime.current = this.getCurrentMtime();
    
    fs.watchFile(REGISTRY_PATH, { interval: 500 }, () => {
      const newMtime = this.getCurrentMtime();
      if (newMtime > this.lastMtime.current) {
        this.lastMtime.current = newMtime;
        this.sendData();
      }
    });
  }

  private stopWatching(): void {
    if (!this._watching) return;
    try { fs.unwatchFile(REGISTRY_PATH); } catch {}
    this._watching = false;
  }

  private getCurrentMtime(): number {
    try { return fs.statSync(REGISTRY_PATH).mtimeMs; }
    catch { return 0; }
  }

  private sendData(): void {
    try {
      if (!fs.existsSync(REGISTRY_PATH)) return;
      const raw = fs.readFileSync(REGISTRY_PATH, 'utf-8');
      const data = JSON.parse(raw);
      this.panel?.webview.postMessage({ type: 'update', data });
    } catch { /* ignore */ }
  }

  private getHtml(): string {
    return `<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--vscode-editor-background, #1e1e1e); color: var(--vscode-foreground, #ccc); font-family: var(--vscode-font-family, sans-serif); padding: 20px; overflow-y: auto; }
  h1 { font-size: 1.5em; margin-bottom: 20px; color: #f44747; }
  .section { margin-bottom: 24px; }
  .section h2 { font-size: 1.1em; margin-bottom: 8px; border-bottom: 1px solid #444; padding-bottom: 4px; }
  .stat-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 12px; }
  .stat { background: #2d2d2d; padding: 10px 16px; border-radius: 8px; min-width: 120px; }
  .stat .label { font-size: 0.75em; color: #888; }
  .stat .value { font-size: 1.5em; font-weight: bold; }
  .stat .value.success { color: #6acb6a; }
  .stat .value.warning { color: #ffd700; }
  .stat .value.error { color: #f44747; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #333; }
  th { color: #888; font-weight: normal; }
  .critical { color: #f44747; font-weight: bold; }
  .error-row:hover { background: #2a2a2a; }
  .badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 0.7em; }
  .badge.critical { background: #f44747; color: #fff; }
  .badge.warning { background: #ffd700; color: #000; }
  .empty { color: #888; text-align: center; padding: 40px; }
  .auto-refresh { font-size: 0.7em; color: #666; margin-top: 20px; text-align: right; }
</style>
</head><body>
<h1>🐞 Error Dashboard</h1>

<div class="section">
  <h2>📊 요약</h2>
  <div class="stat-row" id="summary"></div>
</div>

<div class="section">
  <h2>🔥 빈도 Top 5</h2>
  <div id="top-freq"></div>
</div>

<div class="section">
  <h2>📋 최근 에러</h2>
  <div id="recent-errors"></div>
</div>

<div class="auto-refresh">🔄 auto-refresh via FileSystemWatcher</div>

<script>
  const vscode = acquireVsCodeApi();
  
  function render(data) {
    if (!data || data.length === 0) {
      document.getElementById('recent-errors').innerHTML = '<div class="empty">✅ No errors recorded</div>';
      document.getElementById('summary').innerHTML = '<div class="stat"><div class="label">Total Errors</div><div class="value success">0</div></div>';
      document.getElementById('top-freq').innerHTML = '';
      return;
    }

    // 빈도 집계
    const freq = {};
    let autoFixTotal = 0, autoFixSuccess = 0;
    data.forEach(e => {
      const sig = e.tool + ':' + e.exception_type;
      freq[sig] = (freq[sig] || 0) + 1;
      if (e.auto_fix_attempted) {
        autoFixTotal++;
        if (e.auto_fix_success) autoFixSuccess++;
      }
    });

    // Top 5
    const sorted = Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 5);
    const topHtml = sorted.length > 0 
      ? '<table><tr><th>Signature</th><th>Count</th><th>Status</th></tr>' +
        sorted.map(([sig, cnt]) => {
          const isCrit = cnt >= 5;
          return '<tr class="' + (isCrit ? 'critical' : '') + '"><td>' + sig + '</td><td>' + cnt + '</td><td>' + (isCrit ? '<span class="badge critical">⚠️ CRITICAL</span>' : '<span class="badge warning">⚠️</span>') + '</td></tr>';
        }).join('') + '</table>'
      : '<div class="empty">-</div>';
    document.getElementById('top-freq').innerHTML = topHtml;

    // 요약
    const successRate = autoFixTotal > 0 ? Math.round(autoFixSuccess / autoFixTotal * 100) : 0;
    document.getElementById('summary').innerHTML = 
      '<div class="stat"><div class="label">Total Errors</div><div class="value error">' + data.length + '</div></div>' +
      '<div class="stat"><div class="label">Unique Types</div><div class="value warning">' + Object.keys(freq).length + '</div></div>' +
      '<div class="stat"><div class="label">Auto-Fix Rate</div><div class="value ' + (successRate >= 50 ? 'success' : 'warning') + '">' + successRate + '%</div></div>' +
      '<div class="stat"><div class="label">Auto-Fix Total</div><div class="value">' + autoFixTotal + '</div></div>';

    // 최근 에러
    const recent = data.slice(0, 20);
    const recentHtml = recent.length > 0
      ? '<table><tr><th>Time</th><th>Tool</th><th>Exception</th><th>File</th></tr>' +
        recent.map(e => {
          const time = new Date(e.timestamp).toLocaleTimeString();
          const isCrit = (freq[e.tool + ':' + e.exception_type] || 0) >= 5;
          return '<tr class="error-row ' + (isCrit ? 'critical' : '') + '"><td>' + time + '</td><td>' + e.tool + '</td><td>' + e.exception_type + ': ' + (e.exception_message || '').substring(0, 60) + '</td><td>' + (e.file_line || '') + '</td></tr>';
        }).join('') + '</table>'
      : '<div class="empty">-</div>';
    document.getElementById('recent-errors').innerHTML = recentHtml;
  }

  window.addEventListener('message', event => {
    if (event.data.type === 'update') {
      render(event.data.data);
    }
  });
</script>
</body></html>`;
  }

  dispose(): void {
    this.stopWatching();
    this.panel?.dispose();
  }
}
```

#### VS Code 통합: [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) 수정

```typescript
// VisualVibePanels에 ErrorDashboard 멤버 추가
import { ErrorDashboard } from './ErrorDashboard';

export class VisualVibePanels {
  // ... 기존 멤버 ...
  private errorDashboard: ErrorDashboard;

  constructor() {
    // ...
    this.errorDashboard = new ErrorDashboard();
  }

  openErrorDashboard(): vscode.WebviewPanel {
    return this.errorDashboard.open();
  }

  // dispose()에 추가:
  dispose(): void {
    // ...
    this.errorDashboard?.dispose();
  }
}
```

#### 명령어 등록: [`extension.ts`](extension/src/extension.ts)에 추가

```typescript
// Open Error Dashboard
context.subscriptions.push(
  vscode.commands.registerCommand('vibezoo.openErrorDashboard', () => {
    visualPanels.openErrorDashboard();
  })
);
```

#### [`package.json`](extension/package.json)에 커맨드 추가

```json
{
  "command": "vibezoo.openErrorDashboard",
  "title": "%vibezoo.openErrorDashboard.title%"
}
```

---

### 4.5 Auto-Fix with Crow Pattern Matching

#### 파일: `mcp-servers/bridge/auto_fixer.py` (신규)

```python
# VibeZoo Bridge — MCP 도구 에러 자동 복구기
# Crow Memory에서 과거 유사 에러를 검색하고 알려진 패턴에 대해 자동 재시도

import json
import urllib.request
import urllib.error
from typing import Optional

from bridge.error_handler import ErrorRegistry, error_registry

# ── 알려진 에러 패턴 → 자동 수정 액션 ─────────────────
KNOWN_PATTERNS = {
    # (tool_name, exception_type) → (fix_action, hint_message)
    ("search_codebase", "TypeError"): {
        "action": "retry_with_fix",
        "fix_params": lambda p: {**p, "regex": p.get("query", p.get("regex", ""))},
        "hint": "`regex` 파라미터가 누락되었습니다. `query` 값을 `regex`로 자동 변환합니다.",
    },
    ("search_files", "TypeError"): {
        "action": "hint_only",
        "hint": "`search_files`는 `regex` 파라미터가 필수입니다. `search_codebase`를 대신 사용하세요.",
    },
    ("review_code", "FileNotFoundError"): {
        "action": "hint_only",
        "hint": "파일을 찾을 수 없습니다. 경로가 현재 워크스페이스 기준인지 확인하세요.",
    },
    ("analyze_uploaded_file", "FileNotFoundError"): {
        "action": "hint_only",
        "hint": "업로드된 파일을 찾을 수 없습니다. `check_uploaded_files`로 업로드 상태를 확인하세요.",
    },
}


def find_known_pattern(tool_name: str, exception_type: str) -> Optional[dict]:
    """알려진 에러 패턴 검색"""
    return KNOWN_PATTERNS.get((tool_name, exception_type))


def search_crow_for_similar(tool_name: str, exception_message: str) -> list:
    """Crow Memory에서 유사 에러 검색"""
    try:
        query = f"{tool_name} {exception_message[:100]}"
        url = f"http://localhost:9020/recall?query={urllib.parse.quote(query)}&limit=3"
        resp = urllib.request.urlopen(url, timeout=2)
        data = json.loads(resp.read())
        return data.get("results", [])
    except Exception:
        return []


def generate_fix_suggestion(tool_name: str, exception: Exception, params: dict = None) -> dict:
    """에러에 대한 자동 수정 제안 생성
    
    Returns:
        {
            "can_auto_fix": bool,
            "action": "retry_with_fix" | "hint_only" | "unknown",
            "suggested_params": dict | None,
            "hint": str,
            "similar_past_errors": list,
        }
    """
    exception_type = type(exception).__name__
    
    # 1. 알려진 패턴 검색
    known = find_known_pattern(tool_name, exception_type)
    if known:
        result = {
            "can_auto_fix": known["action"] == "retry_with_fix",
            "action": known["action"],
            "suggested_params": known.get("fix_params", lambda p: None)(params) if known["action"] == "retry_with_fix" else None,
            "hint": known["hint"],
            "similar_past_errors": [],
        }
        return result
    
    # 2. Crow Memory에서 유사 에러 검색
    similar = search_crow_for_similar(tool_name, str(exception))
    if similar:
        return {
            "can_auto_fix": False,
            "action": "hint_only",
            "suggested_params": None,
            "hint": f"과거 유사 에러 {len(similar)}건 발견: {similar[0].get('content', '')[:200]}",
            "similar_past_errors": similar,
        }
    
    # 3. 알 수 없는 에러
    return {
        "can_auto_fix": False,
        "action": "unknown",
        "suggested_params": None,
        "hint": "알려지지 않은 에러 패턴입니다. Crow Memory에 기록되었습니다.",
        "similar_past_errors": [],
    }


# ── Global AutoFixer ───────────────────────────────────
class GlobalAutoFixer:
    """전역 자동 복구 관리자"""
    
    @staticmethod
    def attempt_fix(tool_name: str, exception: Exception, params: dict = None) -> dict:
        """자동 복구 시도"""
        suggestion = generate_fix_suggestion(tool_name, exception, params)
        
        if suggestion["can_auto_fix"] and suggestion["suggested_params"]:
            # 수정된 파라미터로 재시도는 LLM이 수행
            # 여기서는 제안만 생성
            pass
        
        return suggestion
```

#### FixLoopManager 연동 (Extension 측)

[`FixLoopManager.ts`](extension/src/orchestra/FixLoopManager.ts)에 MCP 에러 자동복구 모드 추가:

```typescript
// FixLoopManager에 MCP 에러 대응 모드 추가
export type FixLoopSource = 'build' | 'mcp_error';

export interface McpErrorInfo {
  toolName: string;
  exceptionType: string;
  exceptionMessage: string;
  parameters: Record<string, any>;
  entryId: string;
}

class FixLoopManager {
  // ... 기존 코드 ...
  
  /** MCP 도구 에러 발생 시 호출 */
  onMcpError(errorInfo: McpErrorInfo): void {
    // build 에러와 동일한 FixLoop 상태 머신으로 처리
    const diagnostics: Diagnostic[] = [{
      file: `mcp:${errorInfo.toolName}`,
      line: 1,
      column: 1,
      severity: 'error',
      message: `[${errorInfo.exceptionType}] ${errorInfo.exceptionMessage}`,
      code: errorInfo.exceptionType,
      source: 'vibezoo-mcp',
    }];
    
    this.onBuildFailure(diagnostics, JSON.stringify(errorInfo.parameters), `mcp:${errorInfo.toolName}`);
  }
}
```

---

### 4.6 Extension Notification (StatusBar + Message)

#### StatusBarManager 확장

[`StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts) 수정:

```typescript
// StatusBarManager에 에러 카운트 추가
export class StatusBarManager {
  // ... 기존 멤버 ...
  private _errorCount: number = 0;
  private _criticalErrorCount: number = 0;

  /** 에러 카운트 업데이트 */
  setErrorCount(total: number, critical: number): void {
    this._errorCount = total;
    this._criticalErrorCount = critical;
    this._refreshDisplay();
  }

  private _refreshDisplay(): void {
    let text = this._composeText();
    
    // 에러 카운트 표시 (0이면 숨김)
    if (this._errorCount > 0) {
      const icon = this._criticalErrorCount > 0 ? '$(error)' : '$(warning)';
      text += ` ${icon} ${this._errorCount}`;
    }
    
    this.item.text = text;
    this.item.tooltip = this._composeTooltip() + 
      (this._errorCount > 0 ? ` | Errors: ${this._errorCount} (Critical: ${this._criticalErrorCount})` : '');
  }

  // setActive, setCrowStatus, setYoloStatus, setCimStatus, setGuardMode 호출 시
  // this.item.show() 대신 this._refreshDisplay() 호출로 통일
}
```

#### 에러 감지 → 알림 흐름

```typescript
// extension.ts에 에러 감지 구독 추가
function activateErrorCollection(context: vscode.ExtensionContext): void {
  const errorPath = path.join(os.homedir(), '.vibezoo-errors', 'registry.json');
  
  // registry.json 변경 감지
  fs.watchFile(errorPath, { interval: 1000 }, () => {
    try {
      if (!fs.existsSync(errorPath)) return;
      const raw = fs.readFileSync(errorPath, 'utf-8');
      const errors = JSON.parse(raw);
      const total = errors.length;
      
      // Critical 에러 카운트 (동일 시그니처 5회 이상)
      const freq: Record<string, number> = {};
      errors.forEach((e: any) => {
        const sig = `${e.tool}:${e.exception_type}`;
        freq[sig] = (freq[sig] || 0) + 1;
      });
      const critical = Object.values(freq).filter(c => c >= 5).length;
      
      statusBar.setErrorCount(total, critical);
      
      // Critical 에러 발생 시 showErrorMessage
      if (critical > 0 && critical > lastCriticalCount) {
        NotificationThrottle.showError(
          `🐞 VibeZoo: ${critical}개 Critical 에러 감지! Error Dashboard를 확인하세요.`,
          'Open Dashboard'
        ).then(choice => {
          if (choice === 'Open Dashboard') {
            vscode.commands.executeCommand('vibezoo.openErrorDashboard');
          }
        });
      }
      
      lastCriticalCount = critical;
    } catch { /* ignore */ }
  });
}
```

#### "자동 복구됨" 알림

```typescript
// ErrorAutoFix가 성공적으로 복구했을 때
function notifyAutoFixSuccess(toolName: string, attemptCount: number): void {
  NotificationThrottle.showInfo(
    `✅ VibeZoo: ${toolName} 에러 자동 복구 완료 (${attemptCount}회 시도)`
  );
}
```

---

## 5. 데이터 흐름

### 5.1 정상 흐름 (에러 없음)

```
MCP Tool Call → @capture_tool_errors → original_func() → 정상 반환
                                            ↓
                                    (Zero overhead: 래퍼만 통과, 레지스트리 접근 없음)
```

### 5.2 에러 발생 흐름

```
MCP Tool Call → @capture_tool_errors → original_func() → Exception 발생!
                                            ↓
                              ┌─ try/except ──────────────────────────┐
                              │  1. ErrorRegistry.record()             │
                              │     → registry.json 쓰기 (동기)       │
                              │  2. _try_crow_ingest()                 │
                              │     → Crow Memory /ingest (비동기)     │
                              │  3. generate_fix_suggestion()          │
                              │     → 알려진 패턴? 힌트 생성           │
                              │  4. raise (원본 예외 재발생)           │
                              └────────────────────────────────────────┘
                                            ↓
                              MCP Client가 예외 수신 → LLM에게 표시
                                            ↓
                              registry.json 변경 감지 (fs.watchFile)
                                            ↓
                              ┌─ VS Code 측 반응 ─────────────────────┐
                              │  • ErrorDashboard Webview 갱신         │
                              │  • StatusBar 에러 카운트 업데이트      │
                              │  • Critical 여부 판단 → 알림 표시      │
                              │  • Auto-Fix 제안 (FixLoopManager 연동)  │
                              └────────────────────────────────────────┘
```

### 5.3 자동 복구 흐름

```
Error Registry 기록됨
    │
    ├──→ Crow Memory recall (유사 에러 검색)
    │       │
    │       ├── 알려진 패턴 매칭 → 자동 파라미터 수정 제안
    │       │       │
    │       │       └── FixLoopManager로 전달 → LLM에게 힌트 제공
    │       │
    │       └── 미확인 패턴 → Crow에 새 패턴으로 저장
    │
    └──→ FixLoopManager.onMcpError() → 상태 머신 진입
            │
            ├── LLM이 auto_fix_status() 호출 → in_progress
            ├── LLM이 수정 적용 → retry_build() 호출
            └── resolved / abandoned
```

---

## 6. 변경 대상 파일 목록

### 신규 파일 (5개)

| # | 파일 | 설명 | 우선순위 |
|---|------|------|----------|
| 1 | `mcp-servers/bridge/error_handler.py` | ErrorRegistry + `@capture_tool_errors` 데코레이터 + Crow 동기화 | P1 |
| 2 | `mcp-servers/bridge/auto_fixer.py` | 알려진 패턴 DB + Crow 유사 검색 + 수정 제안 생성 | P2 |
| 3 | `extension/src/visual/ErrorDashboard.ts` | VS Code Webview 에러 대시보드 | P3 |
| 4 | `extension/src/flow/ErrorCollection.ts` | Extension 측 에러 수집 구독 + 알림 관리 | P3 |
| 5 | `plans/error-collection-system.md` | 이 설계 문서 | P1 |

### 수정 파일 (7개)

| # | 파일 | 변경 내용 | 우선순위 |
|---|------|----------|----------|
| 1 | [`mcp-servers/bridge/tools/__init__.py`](mcp-servers/bridge/tools/__init__.py) | `register_all_tools()`에 `mcp.tool()` 래핑 추가 | P1 |
| 2 | [`mcp-servers/bridge/tools/_base.py`](mcp-servers/bridge/tools/_base.py) | `report_error()`에 ErrorRegistry 연동 추가 (선택적) | P2 |
| 3 | [`extension/src/extension.ts`](extension/src/extension.ts) | `activateErrorCollection()` 호출 + `openErrorDashboard` 커맨드 등록 | P3 |
| 4 | [`extension/src/ui/StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts) | `setErrorCount()` 메서드 + `_refreshDisplay()` 통합 | P4 |
| 5 | [`extension/src/visual/VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | `ErrorDashboard` 멤버 추가 + `openErrorDashboard()` | P3 |
| 6 | [`extension/src/orchestra/FixLoopManager.ts`](extension/src/orchestra/FixLoopManager.ts) | `onMcpError()` 메서드 + MCP 에러 소스 타입 추가 | P4 |
| 7 | [`extension/package.json`](extension/package.json) | `vibezoo.openErrorDashboard` 커맨드 + 설정 추가 | P3 |

### 선택적 수정 (Crow Memory 확장)

| # | 파일 | 변경 내용 | 우선순위 |
|---|------|----------|----------|
| 8 | [`mcp-servers/crow_memory_server.py`](mcp-servers/crow_memory_server.py) | `VALID_REGISTERS`에 `"error"` 추가 (기존 `context`로도 충분) | P5 |

---

## 7. 구현 우선순위 (P1~P5)

### P1: Core Error Capture (Foundation)
- [ ] [`error_handler.py`](mcp-servers/bridge/error_handler.py) — `ErrorRegistry` + `@capture_tool_errors` + Crow 동기화
- [ ] [`__init__.py`](mcp-servers/bridge/tools/__init__.py) — `mcp.tool()` 래핑
- [ ] 이 설계 문서

**검증**: 의도적으로 잘못된 파라미터로 MCP 도구 호출 → `~/.vibezoo-errors/registry.json`에 에러 기록 확인

### P2: Known Pattern Auto-Fix
- [ ] [`auto_fixer.py`](mcp-servers/bridge/auto_fixer.py) — 알려진 패턴 DB + Crow 유사 검색
- [ ] [`_base.py`](mcp-servers/bridge/tools/_base.py) — `report_error()` 연동 (선택적)

**검증**: `search_files`를 `regex` 없이 호출 → 자동 힌트 생성 확인

### P3: Dashboard + Extension Integration
- [ ] [`ErrorDashboard.ts`](extension/src/visual/ErrorDashboard.ts) — Webview 대시보드
- [ ] [`ErrorCollection.ts`](extension/src/flow/ErrorCollection.ts) — Extension 측 구독
- [ ] [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) — 통합
- [ ] [`extension.ts`](extension/src/extension.ts) — 커맨드 등록
- [ ] [`package.json`](extension/package.json) — 커맨드 + 설정

**검증**: 대시보드 열기 → 에러 발생 시 자동 갱신 확인

### P4: StatusBar + Notification
- [ ] [`StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts) — 에러 카운트 표시
- [ ] [`FixLoopManager.ts`](extension/src/orchestra/FixLoopManager.ts) — MCP 에러 연동

**검증**: Critical 에러 발생 → StatusBar 카운트 + `showErrorMessage` 확인

### P5: Crow Memory 전용 레지스터
- [ ] [`crow_memory_server.py`](mcp-servers/crow_memory_server.py) — `"error"` 레지스터 추가

**검증**: Crow diagnostics에서 error 레지스터 항목 확인

---

## 8. 에러 분류 체계

### 심각도 (Severity)

| 레벨 | 조건 | 대응 |
|------|------|------|
| **Critical** | 동일 시그니처 5회 이상 / Crow Memory 확인 불가 / Bridge crash | `showErrorMessage` + StatusBar error icon + Dashboard 강조 |
| **Warning** | 동일 시그니처 2~4회 / 파라미터 검증 실패 | StatusBar warning icon + Dashboard 표시 |
| **Info** | 최초 발생 / 알려진 패턴에 매칭됨 | Dashboard에만 기록, 사용자 알림 없음 |

### 에러 타입 (Exception Type)

| 타입 | 예시 | 자동복구 가능성 |
|------|------|----------------|
| `TypeError` | 필수 파라미터 누락 | ✅ 높음 (파라미터 자동 보정) |
| `FileNotFoundError` | 파일 경로 오류 | ⚠️ 중간 (경로 제안) |
| `ValueError` | 잘못된 값 | ⚠️ 중간 (값 범위 제안) |
| `ConnectionError` | Crow/Bridge 연결 실패 | ❌ 낮음 (인프라 문제) |
| `OSError` | 디스크 I/O 실패 | ❌ 낮음 (시스템 문제) |
| `RuntimeError` | 예상치 못한 런타임 오류 | ❌ 낮음 (수동 확인 필요) |

---

## 9. 설계 원칙 검증

| 원칙 | 구현 방식 | 검증 |
|------|----------|------|
| **Zero-overhead on success** | `@capture_tool_errors`는 예외 발생 시에만 ErrorRegistry 접근 | 정상 경로: 래퍼 1회 함수 호출만 추가 (오버헤드 < 1μs) |
| **Graceful degradation** | 모든 I/O (JSON 쓰기, Crow HTTP)는 `try/except`로 감싸고 실패 시 silently continue | 디스크 full 상태에서도 도구 호출 정상 작동 |
| **Privacy** | [`_anonymize_path()`](mcp-servers/bridge/error_handler.py:24)로 홈 디렉토리 경로를 `~`로 대체 | 스택트레이스에 `C:\Users\...` 대신 `~` 표시 |
| **최소 의존성** | 표준 라이브러리만 사용 (`json`, `threading`, `traceback`, `urllib`) | 신규 Python 패키지 0개 |

---

## 10. 테스트 시나리오

### TS-1: 기본 에러 캡처
```
Given: Bridge 실행 중
When: search_codebase() 호출 시 regex 파라미터 누락
Then: 
  - registry.json에 에러 엔트리 추가됨
  - tool="search_codebase", exception_type="TypeError"
  - 원본 예외가 MCP 클라이언트에 정상 전파됨
```

### TS-2: Crow Memory 동기화
```
Given: Crow Memory :9020 실행 중
When: MCP 도구 예외 발생
Then:
  - Crow /ingest에 source="error_handler"로 저장됨
  - tags에 ["error", "mcp_tool", "search_codebase", "TypeError"] 포함
```

### TS-3: Dashboard 자동 갱신
```
Given: Error Dashboard Webview 열림
When: 새 에러 발생 → registry.json 변경
Then:
  - Webview가 500ms 이내에 자동 갱신됨
  - 새 에러가 최근 에러 목록 상단에 표시됨
```

### TS-4: Critical 알림
```
Given: 동일 에러가 이미 4회 기록됨
When: 5번째 동일 에러 발생
Then:
  - StatusBar에 error icon + 카운트 표시
  - showErrorMessage로 Critical 알림 표시
  - Dashboard에서 해당 시그니처가 강조 표시됨
```

### TS-5: 알려진 패턴 자동 제안
```
Given: search_files를 regex 없이 호출
When: TypeError 발생 → auto_fixer.generate_fix_suggestion()
Then:
  - can_auto_fix=false, action="hint_only"
  - hint="search_files는 regex 파라미터가 필수입니다..."
```

### TS-6: Graceful degradation
```
Given: 디스크 공간 부족으로 registry.json 쓰기 실패
When: MCP 도구 예외 발생
Then:
  - 도구 호출은 정상적으로 예외를 반환
  - 콘솔에 경고 로그만 출력
  - 메모리 캐시에는 에러 기록 유지
```

---

## 부록 A: 설정 스키마 (package.json)

```json
{
  "vibezoo.errorCollection.enabled": {
    "type": "boolean",
    "default": true,
    "description": "Enable automatic MCP tool error collection"
  },
  "vibezoo.errorCollection.maxEntries": {
    "type": "number",
    "default": 100,
    "minimum": 10,
    "maximum": 500,
    "description": "Maximum error entries in registry.json"
  },
  "vibezoo.errorCollection.criticalThreshold": {
    "type": "number",
    "default": 5,
    "minimum": 2,
    "maximum": 20,
    "description": "Number of same errors to trigger critical alert"
  },
  "vibezoo.errorCollection.autoFixEnabled": {
    "type": "boolean",
    "default": true,
    "description": "Enable automatic fix suggestions for known error patterns"
  },
  "vibezoo.errorCollection.privacy.anonymizePaths": {
    "type": "boolean",
    "default": true,
    "description": "Anonymize home directory paths in error traces"
  }
}
```

## 부록 B: Crow Memory 쿼리 예시

```bash
# 유사 에러 검색
curl "http://localhost:9020/recall?query=search_codebase+TypeError&limit=3"

# 에러 통계 확인
curl "http://localhost:9020/health"

# 수동 에러 ingest (디버깅용)
curl -X POST http://localhost:9020/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "search_codebase TypeError: missing regex", "register": "context", "source": "debug", "tags": ["error", "test"]}'
```

---

> **문서 상태**: ✅ 설계 완료  
> **다음 단계**: P1 구현 → [`error_handler.py`](mcp-servers/bridge/error_handler.py) 작성 및 [`__init__.py`](mcp-servers/bridge/tools/__init__.py) 통합
