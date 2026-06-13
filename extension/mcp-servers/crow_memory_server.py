#!/usr/bin/env python3
"""
VibeZoo Crow Memory Server — 최소 in-memory Fallback 서버.
===========================================================

목적:
  - 실제 Crow Memory 서버가 없을 때 graceful degradation으로 동작하는 최소 서버
  - 외부 Crow 서버 (http://localhost:9020) 가 존재하면 Proxy 모드로 전환
  - 외부 Crow 서버가 없으면 자체 in-memory 저장소로 /ingest, /recall, /health 제공
  - **절대 sys.exit(0) 금지** — 서버는 항상 listen 상태를 유지

포트:
  기본 9020 (--port 인자로 변경 가능)

엔드포인트:
  GET  /health        → {"status": "ok", "mode": "proxy|local", "memory_count": N}
  POST /ingest        → {"status": "ok", "id": "..."}
  GET  /recall        → {"results": [...]}
"""

import argparse
import json
import logging
import sys
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen, URLError

logging.basicConfig(
    level=logging.INFO,
    format="[CrowMemory] %(levelname)s %(message)s",
)
logger = logging.getLogger("crow_memory")

# ── In-memory 저장소 ────────────────────────────────────────

_memory_store: List[Dict] = []
_external_crow_url: Optional[str] = None


def _detect_external_crow(timeout: float = 1.0) -> Optional[str]:
    """외부 Crow 서버 존재 여부 확인.

    Returns:
        외부 Crow URL (예: "http://localhost:9020") 또는 None
    """
    candidates = [
        "http://localhost:9020",
        "http://127.0.0.1:9020",
    ]
    for url in candidates:
        try:
            req = Request(f"{url}/health")
            resp = urlopen(req, timeout=timeout)
            if resp.status == 200:
                logger.info("✅ 외부 Crow 서버 발견: %s", url)
                return url
        except (URLError, OSError, ValueError):
            continue
    return None


def _proxy_request(method: str, path: str, body: Optional[bytes] = None,
                   timeout: float = 5.0) -> Optional[Dict]:
    """외부 Crow 서버로 요청 프록시."""
    if not _external_crow_url:
        return None
    url = f"{_external_crow_url}{path}"
    try:
        req = Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        resp = urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError, ValueError) as exc:
        logger.debug("Proxy 요청 실패 (%s %s): %s", method, path, exc)
        return None


# ── HTTP Request Handler ─────────────────────────────────────

class CrowMemoryHandler(BaseHTTPRequestHandler):
    """최소 in-memory Crow Memory HTTP 서버."""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/health":
            self._handle_health()
        elif path == "/recall":
            params = parse_qs(parsed.query)
            self._handle_recall(params)
        else:
            self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        if path == "/ingest":
            self._handle_ingest(body)
        elif path == "/store":
            self._handle_ingest(body)
        else:
            self._send_json(404, {"error": "Not Found"})

    # ── 내부 핸들러 ────────────────────────────────────────

    def _handle_health(self):
        """헬스체크: 외부 Crow → Proxy 모드, 없으면 Local 모드."""
        if _external_crow_url:
            proxy_result = _proxy_request("GET", "/health")
            if proxy_result:
                proxy_result["mode"] = "proxy"
                proxy_result["status"] = "ok"
                self._send_json(200, proxy_result)
                return

        self._send_json(200, {
            "status": "ok",
            "mode": "local",
            "memory_count": len(_memory_store),
            "version": "0.1.0-fallback",
        })

    def _handle_ingest(self, body: bytes):
        """메모리 저장: 외부 Crow → Proxy, 없으면 Local 저장."""
        if _external_crow_url:
            proxy_result = _proxy_request("POST", "/ingest", body)
            if proxy_result:
                self._send_json(200, proxy_result)
                return

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        entry = {
            "id": str(uuid.uuid4()),
            "content": data.get("content", ""),
            "register": data.get("register", "context"),
            "source": data.get("source", "vibezoo-fallback"),
            "tags": data.get("tags", []),
            "timestamp": time.time(),
        }
        _memory_store.append(entry)
        logger.info("📝 메모리 저장 (local): id=%s, register=%s, content_len=%d",
                     entry["id"], entry["register"], len(entry["content"]))
        self._send_json(200, {"status": "ok", "id": entry["id"]})

    def _handle_recall(self, params: Dict):
        """메모리 회상: 외부 Crow → Proxy, 없으면 Local 검색."""
        if _external_crow_url:
            query_string = self.path.split("?")[1] if "?" in self.path else ""
            proxy_result = _proxy_request("GET", f"/recall?{query_string}")
            if proxy_result:
                self._send_json(200, proxy_result)
                return

        query = params.get("query", [""])[0].lower()
        register = params.get("register", ["context"])[0]
        limit_str = params.get("limit", ["5"])[0]
        try:
            limit = max(1, min(int(limit_str), 100))
        except ValueError:
            limit = 5

        # 간단한 키워드 매칭 검색
        results = []
        for entry in reversed(_memory_store):
            if entry["register"] != register:
                continue
            if query and query not in entry["content"].lower():
                continue
            results.append(entry)
            if len(results) >= limit:
                break

        logger.info("🔍 메모리 회상 (local): query=%s, register=%s, results=%d",
                     query or "(all)", register, len(results))
        self._send_json(200, {"results": results, "count": len(results)})

    # ── 응답 유틸 ──────────────────────────────────────────

    def _send_json(self, status: int, data: Dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """표준 출력 대신 logger 사용."""
        logger.debug("HTTP %s", format % args)


# ── Server Runner ────────────────────────────────────────────

def run_server(port: int = 9020, bind: str = "127.0.0.1"):
    """Crow Memory Fallback 서버 실행."""
    global _external_crow_url

    # 외부 Crow 서버 탐색 (시작 시 1회 + 2초 타임아웃)
    logger.info("🔍 외부 Crow 서버 탐색 중...")
    _external_crow_url = _detect_external_crow(timeout=2.0)

    if _external_crow_url:
        logger.info("🚀 Crow Memory 서버 시작 (Proxy 모드 → %s)", _external_crow_url)
    else:
        logger.info("🚀 Crow Memory 서버 시작 (Local Fallback 모드, 포트 %d)", port)

    server = HTTPServer((bind, port), CrowMemoryHandler)
    logger.info("✅ Crow Memory 서버 listen: http://%s:%d", bind, port)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Crow Memory 서버 종료 (KeyboardInterrupt)")
    except Exception as exc:
        logger.error("💥 Crow Memory 서버 예외: %s", exc)
    finally:
        server.server_close()
        logger.info("✅ Crow Memory 서버 정상 종료")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VibeZoo Crow Memory Fallback Server")
    parser.add_argument("--port", type=int, default=9020, help="Listen port (default: 9020)")
    parser.add_argument("--bind", type=str, default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    args = parser.parse_args()

    run_server(port=args.port, bind=args.bind)
