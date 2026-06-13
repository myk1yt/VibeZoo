# VibeZoo Bridge — Crow Memory HTTP 클라이언트
# 선택적 Crow Memory 연동 (Bridge-compatible REST API 사용)

import json
import logging
from typing import Optional, List

import requests
from bridge.config import CROW_URL, CROW_TIMEOUT

logger = logging.getLogger(__name__)


def try_crow_ingest(content: str, register: str = "context", **kwargs):
    """선택적으로 Crow Memory에 저장 (Bridge REST API /ingest)

    Args:
        content: 저장할 내용
        register: 레지스터 이름 (기본: "context")
        **kwargs: 추가 필드 (source, tags 등)

    Note:
        실패해도 Bridge 작동에 영향을 주지 않음.
    """
    try:
        payload = {"content": content, "register": register, **kwargs}
        requests.post(f"{CROW_URL}/ingest", json=payload, timeout=CROW_TIMEOUT)
    except requests.exceptions.ConnectionError:
        logger.debug("Crow Memory ingest failed: connection refused")
    except requests.exceptions.Timeout:
        logger.debug("Crow Memory ingest timed out after %ss", CROW_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        logger.debug("Crow Memory ingest failed: %s", exc)


def try_crow_recall(query: str, register: str = "context", limit: int = 5) -> list:
    """선택적으로 Crow Memory에서 회상 (Bridge REST API /recall)

    Args:
        query: 검색어
        register: 레지스터 이름 (기본: "context")
        limit: 최대 결과 수 (기본: 5)

    Returns:
        결과 리스트 (실패 시 빈 리스트)
    """
    try:
        resp = requests.get(
            f"{CROW_URL}/recall",
            params={"query": query, "register": register, "limit": limit},
            timeout=CROW_TIMEOUT
        )
        if resp.ok:
            return resp.json().get("results", [])
    except requests.exceptions.ConnectionError:
        logger.debug("Crow Memory recall failed: connection refused")
    except requests.exceptions.Timeout:
        logger.debug("Crow Memory recall timed out after %ss", CROW_TIMEOUT)
    except (requests.exceptions.RequestException, json.JSONDecodeError) as exc:
        logger.debug("Crow Memory recall failed: %s", exc)
    return []


def crow_health_check() -> bool:
    """Crow Memory 헬스체크 (Bridge REST API /health)

    Returns:
        True if Crow Memory is healthy, False otherwise
    """
    try:
        resp = requests.get(f"{CROW_URL}/health", timeout=CROW_TIMEOUT)
        return resp.ok
    except requests.exceptions.ConnectionError:
        logger.debug("Crow Memory health check failed: connection refused")
    except requests.exceptions.Timeout:
        logger.debug("Crow Memory health check timed out after %ss", CROW_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        logger.debug("Crow Memory health check failed: %s", exc)
    return False
