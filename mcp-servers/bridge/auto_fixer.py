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
        "fix_params": lambda p: {**p, "regex": p.get("query", p.get("regex", ""))},
        "hint": (
            "`regex` 파라미터가 누락되었습니다. "
            "`query` 값을 `regex`로 자동 변환하여 재시도할 수 있습니다."
        ),
    },
    ("search_files", "TypeError"): {
        "action": "hint_only",
        "hint": (
            "`search_files`는 `regex` 파라미터가 필수입니다. "
            "`search_codebase`를 대신 사용하거나 `regex` 값을 제공하세요."
        ),
    },
    ("review_code", "FileNotFoundError"): {
        "action": "hint_only",
        "hint": (
            "파일을 찾을 수 없습니다. 경로가 현재 워크스페이스 기준인지 확인하고, "
            "파일이 존재하는지 검토하세요."
        ),
    },
    ("analyze_uploaded_file", "FileNotFoundError"): {
        "action": "hint_only",
        "hint": (
            "업로드된 파일을 찾을 수 없습니다. "
            "`check_uploaded_files`로 업로드 상태를 먼저 확인하세요."
        ),
    },
    ("fetch_page", "ConnectionError"): {
        "action": "hint_only",
        "hint": (
            "URL에 연결할 수 없습니다. URL이 올바른지, "
            "인터넷 연결이 정상인지 확인하세요."
        ),
    },
    ("web_search", "ConnectionError"): {
        "action": "hint_only",
        "hint": (
            "검색 엔진에 연결할 수 없습니다. "
            "인터넷 연결을 확인하거나 다른 검색 엔진(engine 파라미터)을 시도하세요."
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

    # 2. Crow Memory에서 유사 에러 검색
    error_sig = _error_signature(tool_name, exception_type)
    similar = search_crow_for_similar(error_sig)
    if similar:
        first_content = similar[0].get("content", "")[:200]
        return {
            "can_auto_fix": False,
            "action": "hint_only",
            "suggested_params": None,
            "hint": f"과거 유사 에러 {len(similar)}건 발견: {first_content}",
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
    def attempt_fix(
        tool_name: str,
        exception_type: str,
        params: Optional[dict] = None,
        error_msg: Optional[str] = None,
    ) -> dict:
        """자동 복구 시도 및 제안 생성
        
        Args:
            tool_name: 에러가 발생한 도구 이름
            exception_type: 예외 타입명
            params: 도구 호출 파라미터
            error_msg: 원본 에러 메시지 (선택)
        
        Returns:
            수정 제안 딕셔너리 (generate_fix_suggestion 반환값과 동일)
        """
        suggestion = generate_fix_suggestion(tool_name, exception_type, params)
        
        # 자동 복구 가능한 경우 → 레지스트리에 기록
        if suggestion.get("can_auto_fix") and suggestion.get("suggested_params"):
            logger.debug(
                "Auto-fix available for %s/%s: %s",
                tool_name, exception_type, suggestion["hint"]
            )
        
        return suggestion
