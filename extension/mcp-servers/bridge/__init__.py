# VibeZoo Bridge — 패키지 초기화
# 모듈화된 구조, 지연 임포트로 순환 참조 방지

import sys
from pathlib import Path

# Pylance: 패키지 루트(mcp-servers/)를 Python 경로에 추가
# 이 파일을 import하는 모든 bridge 모듈에 적용됨
_PKG_ROOT = str(Path(__file__).resolve().parent)
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from bridge.config import VERSION, CROW_URL, CROW_TIMEOUT
from bridge.crow_client import try_crow_ingest, try_crow_recall, crow_health_check

__all__ = [
    "VERSION", "CROW_URL", "CROW_TIMEOUT",
    "try_crow_ingest", "try_crow_recall", "crow_health_check",
]
