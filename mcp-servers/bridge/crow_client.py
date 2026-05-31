# VibeZoo Bridge — Crow Memory HTTP 클라이언트
# 선택적 Crow Memory 연동 (실패해도 무시)

import json
import time
from typing import Optional, List

from bridge.config import CROW_URL, CROW_TIMEOUT


def try_crow_ingest(content: str, register: str = "context", **kwargs):
    """선택적으로 Crow Memory에 저장 (실패해도 무시, 3초 타임아웃)"""
    try:
        import requests
        payload = {"content": content, "register": register, **kwargs}
        requests.post(f"{CROW_URL}/ingest", json=payload, timeout=CROW_TIMEOUT)
    except Exception:
        pass


def try_crow_recall(query: str, register: str = "context", limit: int = 5) -> list:
    """선택적으로 Crow Memory에서 회상 (3초 타임아웃)"""
    try:
        import requests
        resp = requests.get(
            f"{CROW_URL}/recall",
            params={"query": query, "register": register, "limit": limit},
            timeout=CROW_TIMEOUT
        )
        if resp.ok:
            return resp.json().get("results", [])
    except Exception:
        pass
    return []


def crow_health_check() -> bool:
    """Crow Memory 헬스체크"""
    try:
        import requests
        resp = requests.get(f"{CROW_URL}/health", timeout=CROW_TIMEOUT)
        return resp.ok
    except Exception:
        return False
