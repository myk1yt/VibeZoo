# VibeZoo Bridge — 전역 에러 캡처 및 레지스트리
# 모든 MCP 도구 호출을 투명하게 감싸 예외를 자동 수집한다.
# 설계 원칙: Zero-overhead on success, Graceful degradation

import functools
import json
import logging
import os
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import urllib.parse  # module-level import (명세 요구사항)

logger = logging.getLogger(__name__)

HOME_DIR = Path.home()
ERROR_DIR = HOME_DIR / ".vibezoo-errors"
REGISTRY_PATH = ERROR_DIR / "registry.json"
MAX_ENTRIES = 100
FREQUENCY_THRESHOLD = 5  # 동일 에러 N회 → "주의" 플래그

_lock = threading.Lock()
_thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="vibezoo-err")


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


# ── ErrorRegistry 클래스 (DCLP singleton) ──────────────

class ErrorRegistry:
    """스레드 안전한 에러 레지스트리 (JSON 파일 + 메모리 캐시)
    
    Thread-safe singleton with Double-Checked Locking Pattern (DCLP).
    모든 I/O 메서드에 threading.Lock 적용.
    """
    
    _instance = None
    _lock = threading.Lock()  # DCLP용 클래스 레벨 락
    
    def __new__(cls):
        if cls._instance is None:  # First check (no lock)
            with cls._lock:
                if cls._instance is None:  # Second check (with lock)
                    instance = super().__new__(cls)
                    instance._init()
                    cls._instance = instance
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
        except Exception as exc:
            logger.debug("ErrorRegistry._ensure_loaded failed: %s", exc)
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
                except OSError as exc:
                    logger.debug("ErrorRegistry disk write failed: %s", exc)
        except Exception:
            pass  # Graceful degradation
        
        return entry_id
    
    def get_recent(self, limit: int = 20) -> list:
        """최근 에러 조회"""
        with _lock:
            self._ensure_loaded()
            return list(self._cache[:limit])
    
    def get_top_frequency(self, n: int = 5) -> list:
        """빈도 Top N"""
        with _lock:
            self._ensure_loaded()
            sorted_freq = sorted(self._frequency.items(), key=lambda x: x[1], reverse=True)
            return [
                {
                    "signature": sig,
                    "count": cnt,
                    "is_critical": cnt >= FREQUENCY_THRESHOLD,
                }
                for sig, cnt in sorted_freq[:n]
            ]
    
    def get_stats(self) -> dict:
        """통계 요약"""
        with _lock:
            self._ensure_loaded()
            total = len(self._cache)
            unique = len(self._frequency)
            auto_fix_attempted = sum(1 for e in self._cache if e.get("auto_fix_attempted"))
            auto_fix_success = sum(1 for e in self._cache if e.get("auto_fix_success") is True)
            auto_fix_fail = sum(1 for e in self._cache if e.get("auto_fix_success") is False)
            return {
                "total_errors": total,
                "unique_signatures": unique,
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

def capture_tool_errors(name: Optional[str] = None):
    """MCP 도구 함수를 에러 캡처로 감싸는 데코레이터.
    
    Zero-overhead on success: 예외가 없으면 레지스트리 접근 없이 원본 함수만 호출.
    
    Args:
        name: 도구 이름 (None이면 func.__name__ 사용)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                tool_name = name or func.__name__
                # 비동기로 에러 기록 (ThreadPoolExecutor, non-blocking)
                def _record():
                    try:
                        registry = ErrorRegistry()
                        registry.record(tool_name, e, kwargs)
                        # Crow Memory에 비동기 저장 시도
                        _try_crow_ingest(tool_name, e, kwargs)
                        # Auto-fix 제안 생성 시도
                        _try_auto_fix(tool_name, e, kwargs)
                    except Exception:
                        pass  # Graceful degradation
                
                _thread_pool.submit(_record)
                
                raise  # 원본 예외 재발생 (MCP 클라이언트로 전파)
        return wrapper
    return decorator


# ── Crow Memory 동기화 ──────────────────────────────────

def _try_crow_ingest(tool_name: str, exception: Exception, params: dict = None):
    """Crow Memory에 에러 정보 저장 (best-effort, 비동기)"""
    try:
        content = (
            f"## MCP Tool Error\n"
            f"- **Tool**: {tool_name}\n"
            f"- **Exception**: {type(exception).__name__}: {str(exception)}\n"
            f"- **Time**: {datetime.now(timezone.utc).isoformat()}\n"
        )
        if params:
            # 파라미터에서 민감 정보 마스킹 (home 경로 등)
            safe_params = {}
            for k, v in params.items():
                if isinstance(v, str):
                    safe_params[k] = _anonymize_path(v)
                else:
                    safe_params[k] = v
            content += f"- **Parameters**: {json.dumps(safe_params, ensure_ascii=False)}\n"
        
        payload = json.dumps({
            "content": content,
            "register": "context",
            "source": "error_handler",
            "tags": ["error", "mcp_tool", tool_name, type(exception).__name__],
        }).encode("utf-8")
        
        import urllib.request
        import urllib.error
        
        req = urllib.request.Request(
            "http://localhost:9020/ingest",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass  # Crow 없어도 정상 동작


# ── Auto-Fix 연동 ───────────────────────────────────────

def _try_auto_fix(tool_name: str, exception: Exception, params: dict = None):
    """Auto-fix 제안 생성 시도 (best-effort)"""
    try:
        from bridge.auto_fixer import generate_fix_suggestion
        suggestion = generate_fix_suggestion(tool_name, type(exception).__name__, params)
        if suggestion and suggestion.get("can_auto_fix"):
            # 자동 복구 가능한 패턴 → entry에 마킹 (향후 확장)
            pass
    except Exception:
        pass


# ── 싱글톤 접근자 ───────────────────────────────────────

error_registry = ErrorRegistry()
