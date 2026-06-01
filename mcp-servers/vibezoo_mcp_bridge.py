# VibeZoo MCP Bridge — 통합 MCP 서버 (v0.14.0)
# 모듈화된 bridge/ 패키지 기반, 진입점 70줄
# Scout(코드 검색) + Reviewer(리뷰) + Tester(테스트) + DeepAnalyzer(분석)
# Crow Memory(Python)와 동일한 FastMCP 기반
# 포트 9027에서 SSE transport로 실행
# VS Code Webview 드랍존만 사용 (브라우저 드랍존 제거됨)

import argparse
import time

from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.requests import Request

from bridge.config import VERSION, CROW_URL, CROW_TIMEOUT
from bridge.crow_client import crow_health_check
from bridge.tools import register_all_tools

mcp = FastMCP(name="vibezoo")
register_all_tools(mcp)


# ── Zoo Code MCP 호환: list_subagents ─────────────────────
# Zoo Code MCP 클라이언트가 연결 시 POST /tools/list_subagents를 호출함
# 이 엔드포인트가 없으면 404 → 세션 초기화 실패 → 모든 툴 호출 불가


@mcp.custom_route("/tools/list_subagents", methods=["POST"])
async def list_subagents_route(request: Request) -> JSONResponse:
    """Zoo Code MCP 호환 — 연결된 서브에이전트 목록 반환"""
    return JSONResponse({
        "agents": [
            {"name": "Scout", "status": "ready", "tools": ["search_codebase", "find_references", "summarize_architecture"]},
            {"name": "Reviewer", "status": "ready", "tools": ["review_code"]},
            {"name": "DeepAnalyzer", "status": "ready", "tools": ["analyze_call_graph", "map_dependencies", "extract_patterns", "reverse_engineer"]},
            {"name": "Tester", "status": "ready", "tools": ["generate_tests", "analyze_coverage"]},
            {"name": "Whiteboard", "status": "ready", "tools": ["draw_on_whiteboard", "get_whiteboard_state", "capture_screen"]},
            {"name": "FixLoop", "status": "ready", "tools": ["auto_fix_status", "retry_build", "check_intervention"]},
            {"name": "Integrated", "status": "ready", "tools": ["review_project", "find_bugs", "suggest_refactor", "generate_docs"]},
            {"name": "Analysis", "status": "ready", "tools": ["explain_code", "analyze_changes", "review_pr", "refactor_across_files"]},
            {"name": "Knowledge", "status": "ready", "tools": ["learn_project", "recall_project", "learn_preference", "get_preferences"]},
            {"name": "Web", "status": "ready", "tools": ["fetch_page", "web_search"]},
            {"name": "SSA", "status": "ready", "tools": ["aggregate_spatial_pixels"]},
            {"name": "Setup", "status": "ready", "tools": ["vibezoo_setup"]},
        ]
    })


# ── Health Check ──────────────────────────────────────────

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """헬스체크 엔드포인트 — Bridge 상태 및 Crow 연결 상태 반환"""
    crow_ok = crow_health_check()
    return JSONResponse({
        "status": "ok",
        "crow": crow_ok,
        "timestamp": time.time(),
        "version": VERSION,
    })


# ═══════════════════════════════════════════════════════════
# 메인 — SSE 서버 시작
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VibeZoo MCP Bridge Server")
    parser.add_argument("--port", type=int, default=9027, help="SSE server port")
    args = parser.parse_args()

    print(f"\U0001f680 VibeZoo MCP Bridge v{VERSION} starting on port {args.port}...")
    print(f"   Crow Memory: {CROW_URL} (timeout: {CROW_TIMEOUT}s)")
    print(f"   Dropzone: Webview only (browser dropzone removed)")

    mcp.run(transport="sse", host="127.0.0.1", port=args.port)
