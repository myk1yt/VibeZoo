# VibeZoo Bridge — MCP 도구 에러 자동 복구기
# Crow Memory에서 과거 유사 에러를 검색하고 알려진 패턴에 대해 자동 재시도 제안

import json
import logging
from typing import Optional

import urllib.parse

from bridge.error_handler import _error_signature

logger = logging.getLogger(__name__)

# ── 알려진 에러 패턴 → 자동 수정 액션 ─────────────────
# 키: (tool_name, exception_type)
# 값: fix_action + hint
KNOWN_PATTERNS = {
    ("search_codebase", "TypeError"): {
        "action": "retry_with_fix",
        "fix_params": lambda p: {
            k: v for k, v in
            ({**p, "query": p.get("query", p.get("regex", ""))}).items()
            if k != "regex"
        },
        "hint": (
            "Missing required 'query' parameter (was passed as 'regex'). "
            "Automatically converting 'regex' value to 'query' for retry."
        ),
    },
    ("search_files", "TypeError"): {
        "action": "hint_only",
        "hint": (
            "Missing required 'regex' parameter. "
            "Use 'search_codebase' instead, or provide a 'regex' value."
        ),
    },
    ("review_code", "FileNotFoundError"): {
        "action": "hint_only",
        "hint": (
            "File not found. Verify the path is relative to the current "
            "workspace and the file exists."
        ),
    },
    ("analyze_uploaded_file", "FileNotFoundError"): {
        "action": "hint_only",
        "hint": (
            "Uploaded file not found. "
            "Use 'check_uploaded_files' to verify upload status first."
        ),
    },
    ("fetch_page", "ConnectionError"): {
        "action": "hint_only",
        "hint": (
            "Cannot connect to URL. "
            "Verify the URL is correct and internet connection is working."
        ),
    },
    ("web_search", "ConnectionError"): {
        "action": "hint_only",
        "hint": (
            "Cannot connect to search engine. "
            "Check internet connection or try a different engine parameter."
        ),
    },
}


def find_known_pattern(tool_name: str, exception_type: str) -> Optional[dict]:
    """알려진 에러 패턴 검색"""
    return KNOWN_PATTERNS.get((tool_name, exception_type))


def search_crow_for_similar(error_signature: str) -> list:
    """Crow Memory에서 유사 에러 패턴 검색
    
    Args:
        error_signature: "{tool_name}:{exception_type}" 형식의 시그니처
    
    Returns:
        과거 유사 에러 리스트 (최대 3개)
    """
    try:
        query = error_signature.replace(":", " ")
        url = (
            f"http://localhost:9020/recall"
            f"?query={urllib.parse.quote(query)}"
            f"&limit=3"
        )
        import urllib.request
        resp = urllib.request.urlopen(url, timeout=2)
        data = json.loads(resp.read())
        return data.get("results", [])
    except Exception:
        return []


def generate_fix_suggestion(
    tool_name: str,
    exception_type: str,
    params: Optional[dict] = None,
) -> dict:
    """에러에 대한 자동 수정 제안 생성
    
    Args:
        tool_name: 에러가 발생한 도구 이름
        exception_type: 예외 타입명 (e.g. "TypeError")
        params: 도구 호출 시 사용된 파라미터
    
    Returns:
        {
            "can_auto_fix": bool,
            "action": "retry_with_fix" | "hint_only" | "unknown",
            "suggested_params": dict | None,
            "hint": str,
            "similar_past_errors": list,
        }
    """
    # 1. 알려진 패턴 검색
    known = find_known_pattern(tool_name, exception_type)
    if known:
        result = {
            "can_auto_fix": known["action"] == "retry_with_fix",
            "action": known["action"],
            "suggested_params": (
                known.get("fix_params", lambda p: None)(params or {})
                if known["action"] == "retry_with_fix"
                else None
            ),
            "hint": known["hint"],
            "similar_past_errors": [],
        }
        return result

    # 2. Search Crow Memory for similar past errors
    error_sig = _error_signature(tool_name, exception_type)
    similar = search_crow_for_similar(error_sig)
    if similar:
        first_content = similar[0].get("content", "")[:200]
        return {
            "can_auto_fix": False,
            "action": "hint_only",
            "suggested_params": None,
            "hint": f"Found {len(similar)} similar past error(s): {first_content}",
            "similar_past_errors": similar,
        }

    # 3. Unknown error
    return {
        "can_auto_fix": False,
        "action": "unknown",
        "suggested_params": None,
        "hint": "Unknown error pattern. The error has been recorded in Crow Memory for future reference.",
        "similar_past_errors": [],
    }


# ── Global AutoFixer ───────────────────────────────────

class GlobalAutoFixer:
    """Global automatic fix manager"""
    
    @staticmethod
    def attempt_fix(
        tool_name: str,
        exception_type: str,
        params: Optional[dict] = None,
        error_msg: Optional[str] = None,
    ) -> dict:
        """Attempt auto-fix and generate suggestion
        
        Args:
            tool_name: Tool name where the error occurred
            exception_type: Exception type name
            params: Tool call parameters
            error_msg: Original error message (optional)
        
        Returns:
            Fix suggestion dict (same as generate_fix_suggestion return value)
        """
        suggestion = generate_fix_suggestion(tool_name, exception_type, params)
        
        # 자동 복구 가능한 경우 → 레지스트리에 기록
        if suggestion.get("can_auto_fix") and suggestion.get("suggested_params"):
            logger.debug(
                "Auto-fix available for %s/%s: %s",
                tool_name, exception_type, suggestion["hint"]
            )
        
        return suggestion
