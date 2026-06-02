# VibeZoo MCP Bridge — 통합 MCP 서버 (v0.14.1)
# 모듈화된 bridge/ 패키지 기반, 진입점 90줄
# Scout(코드 검색) + Reviewer(리뷰) + Tester(테스트) + DeepAnalyzer(분석)
# Crow Memory(Python)와 동일한 FastMCP 기반
# 포트 9027에서 SSE transport로 실행

import argparse
import json
import os
import time
from pathlib import Path

from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.requests import Request

from bridge.config import VERSION, CROW_URL, CROW_TIMEOUT, IMAGE_CACHE_DIR, UPLOADED_IMAGE_PATH
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


# ── Image Upload ─────────────────────────────────────────

os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)


@mcp.custom_route("/upload", methods=["GET", "POST"])
async def image_upload_handler(request: Request) -> JSONResponse:
    """이미지 드래그앤드롭 업로드 엔드포인트"""
    if request.method == "GET":
        html = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>VibeZoo Image Upload</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1e1e1e;color:#ccc;font-family:-apple-system,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
#dropzone{width:600px;height:400px;border:3px dashed #555;border-radius:16px;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:20px;cursor:pointer;transition:all .3s;text-align:center;padding:20px}
#dropzone:hover,#dropzone.dragover{border-color:#4ec9ff;background:rgba(78,201,255,.1)}
#dropzone.dragover{border-color:#6acb6a;background:rgba(106,203,106,.1)}
#dropzone img{max-width:90%;max-height:70%;border-radius:8px;display:none}
#dropzone.has-image img{display:block}
#dropzone.has-image .placeholder{display:none}
.icon{font-size:64px;opacity:.5}
.hint{font-size:14px;color:#888}
.status{font-size:16px;color:#6acb6a;margin-top:12px}
input[type=file]{display:none}
</style></head><body>
<div id=dropzone onclick="document.getElementById('f').click()">
<div class=icon>&#128247;</div>
<div class=placeholder><h2>Drag & Drop Image Here</h2><p style="color:#888;margin-top:8px">or click to browse</p></div>
<img id=prev><div class=status id=sta></div></div>
<input type=file id=f accept=image/* onchange="u(this.files[0])">
<script>
function u(f){if(!f)return;var fd=new FormData();fd.append('image',f);document.getElementById('sta').textContent='Uploading...';var x=new XMLHttpRequest();x.open('POST','/upload',true);x.onload=function(){if(x.status==200){var d=JSON.parse(x.responseText);document.getElementById('sta').innerHTML='&#x2705; Uploaded! Path: <code>'+d.path+'</code>';var r=new FileReader();r.onload=function(e){document.getElementById('prev').src=e.target.result;document.getElementById('dropzone').classList.add('has-image')};r.readAsDataURL(f)}else{document.getElementById('sta').textContent='&#x274c; Upload failed'}};x.onerror=function(){document.getElementById('sta').textContent='&#x274c; Network error'};x.send(fd)}
document.getElementById('dropzone').addEventListener('dragover',function(e){e.preventDefault();this.classList.add('dragover')});
document.getElementById('dropzone').addEventListener('dragleave',function(e){this.classList.remove('dragover')});
document.getElementById('dropzone').addEventListener('drop',function(e){e.preventDefault();this.classList.remove('dragover');var f=e.dataTransfer.files[0];if(f&&f.type.startsWith('image/'))u(f)});
</script></body></html>"""
        return JSONResponse({"html": html})
    elif request.method == "POST":
        try:
            form = await request.form()
            file = form.get("image")
            if not file:
                return JSONResponse({"error": "No file"}, status_code=400)
            content_bytes = await file.read()
            with open(UPLOADED_IMAGE_PATH, "wb") as f:
                f.write(content_bytes)
            return JSONResponse({"status": "ok", "path": UPLOADED_IMAGE_PATH, "size": len(content_bytes)})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)


# ═══════════════════════════════════════════════════════════
# 메인 — SSE 서버 시작
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VibeZoo MCP Bridge Server")
    parser.add_argument("--port", type=int, default=9027, help="SSE server port")
    args = parser.parse_args()

    print(f"\U0001f680 VibeZoo MCP Bridge v{VERSION} starting on port {args.port}...")
    print(f"   Crow Memory: {CROW_URL} (timeout: {CROW_TIMEOUT}s)")

    mcp.run(transport="sse", host="127.0.0.1", port=args.port)
