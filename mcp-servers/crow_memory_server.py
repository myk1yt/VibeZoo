#!/usr/bin/env python3
# Crow Memory Server - FastMCP based SSE MCP Server (v1.0.0)
# Port 9020, JSON file storage (~/.crow-memory/)

import argparse
import json
import os
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.requests import Request

HOME_DIR = Path.home()
DATA_DIR = HOME_DIR / '.crow-memory'
REGISTERS_DIR = DATA_DIR / 'registers'
BACKUPS_DIR = DATA_DIR / 'backups'
PREFERENCES_FILE = DATA_DIR / 'preferences.json'
PROJECTS_FILE = DATA_DIR / 'projects.json'
VERSION = '1.0.0'

DEFAULT_REGISTERS = {
    'context': {'description': 'General', 'entries': []},
    'arch': {'description': 'Architecture', 'entries': []},
    'style': {'description': 'Coding style', 'entries': []},
    'life_context': {'description': 'Life context', 'entries': []},
}
VALID_REGISTERS = set(DEFAULT_REGISTERS.keys()) | {'coding_style','naming','formatting','architecture','workflow'}
MAX_ENTRIES_PER_REGISTER = 500

def ensure_dirs():
    [d.mkdir(parents=True, exist_ok=True) for d in [DATA_DIR, REGISTERS_DIR, BACKUPS_DIR]]

def _rp(n): return REGISTERS_DIR / f'{n}.json'

def _lr(n):
    p = _rp(n)
    if p.exists():
        try: return json.loads(p.read_text("utf-8"))
        except: pass
    return dict(DEFAULT_REGISTERS[n]) if n in DEFAULT_REGISTERS else {"description": "", "entries": []}

def _sr(n, d): _rp(n).write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")

def _lj(p, d=None):
    if p.exists():
        try: return json.loads(p.read_text("utf-8"))
        except: pass
    return d if d is not None else {}

def _sj(p, d): p.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")

mcp = FastMCP(name='crow_memory')
ensure_dirs()


# ═══════════════════════════════════ MCP Tools ═══════════════════════════════════


@mcp.tool()
def crow_ingest(content: str, register: str = 'context', source: str = None, tags: list = None) -> str:
    if register not in VALID_REGISTERS: return f"Unknown register: {register}"
    data = _lr(register)
    e = {"id": str(uuid.uuid4()), "content": content, "source": source or "user",
         "tags": tags or [], "timestamp": datetime.now(timezone.utc).isoformat()} 
    data['entries'].append(e)
    if len(data['entries']) > MAX_ENTRIES_PER_REGISTER: data['entries'] = data['entries'][-MAX_ENTRIES_PER_REGISTER:]
    _sr(register, data)
    return f"Saved to [{register}] (id: {e[chr(105)+chr(100)]})"

@mcp.tool()
def crow_recall(query: str, register: str = None, limit: int = 5) -> str:
    return json.dumps({"results": _recall(query, register, limit), "count": 0}, ensure_ascii=False, indent=2)

def _recall(q, reg=None, limit=5):
    ql = q.lower(); res = []; regs = [reg] if reg else list(VALID_REGISTERS)
    for r in regs:
        for e in _lr(r).get("entries", []):
            c = e.get("content", "")
            if ql in c.lower():
                res.append({"register": r, "id": e.get("id"), "content": c,
                           "source": e.get("source"), "tags": e.get("tags", []),
                           "timestamp": e.get("timestamp"), "score": c.lower().count(ql)})
                if len(res) >= limit: break
        if len(res) >= limit: break
    res.sort(key=lambda x: x.get("score", 0), reverse=True)
    return res[:limit]

@mcp.tool()
def crow_evolve_propose(register: str = 'arch', insight: str = '') -> str:
    if register not in VALID_REGISTERS: return f"Unknown: {register}"
    data = _lr(register); entries = data.get("entries", [])
    if not entries: return f"[{register}] empty."
    seen = set(); deduped = []
    for e in entries:
        k = e.get("content", "")[:100]
        if k not in seen: seen.add(k); deduped.append(e)
    s = {"original": len(entries), "deduped": len(deduped), "removed": len(entries)-len(deduped),
         "insight": insight or "auto", "timestamp": datetime.now(timezone.utc).isoformat()}
    data['entries'] = deduped; _sr(register, data)
    return json.dumps(s, ensure_ascii=False, indent=2)

@mcp.tool()
def crow_diagnostics() -> str:
    total = 0; stats = {}
    for reg in sorted(VALID_REGISTERS):
        d = _lr(reg); c = len(d.get("entries", [])); total += c
        stats[reg] = {"count": c, "description": d.get("description", "")}
    size = sum(f.stat().st_size for f in REGISTERS_DIR.glob("*.json"))
    return json.dumps({"version": VERSION, "status": "healthy", "total_entries": total,
                       "storage_bytes": size, "registers": stats}, ensure_ascii=False, indent=2)

@mcp.tool()
def crow_check_drift() -> str:
    issues = []
    for reg in sorted(VALID_REGISTERS):
        for e in _lr(reg).get("entries", []):
            c = e.get("content", "").strip()
            if not c: issues.append({"register": reg, "type": "empty"})
            elif len(c) < 10: issues.append({"register": reg, "type": "too_short", "len": len(c)})
    return json.dumps({"drift_detected": len(issues) > 0, "issues": issues}, ensure_ascii=False, indent=2)

@mcp.tool()
def crow_ingest_from_build(build_log: str, errors: list = None, project_name: str = None) -> str:
    parts = []
    if project_name: parts.append(f"## Build: {project_name}")
    parts.append(f"### Log\n```\n{build_log}\n```")
    sep = chr(32)
    if errors: parts.append("### Errors\n" + sep.join(errors))
    return crow_ingest(content="\n\n".join(parts), register="context", source="build", tags=["build"])

@mcp.tool()
def crow_get_user_bias() -> str:
    prefs = _lj(PREFERENCES_FILE, {})
    return json.dumps({"bias": prefs}, ensure_ascii=False, indent=2)

@mcp.tool()
def crow_manage_prompt(action='list', prompt_id=None, content=None, title=None) -> str:
    pf = DATA_DIR / "prompts.json"; prompts = _lj(pf, {})
    if action == "list": return json.dumps({"prompts": [{"id":k,"title":v.get("title","")} for k,v in prompts.items()], "count": len(prompts)}, ensure_ascii=False, indent=2)
    elif action == "get":
        if not prompt_id or prompt_id not in prompts: return json.dumps({"error": f"Not found: {prompt_id}"}, ensure_ascii=False, indent=2)
        return json.dumps(prompts[prompt_id], ensure_ascii=False, indent=2)
    elif action == "save":
        pid = prompt_id or str(uuid.uuid4()); prompts[pid] = {"id": pid, "title": title or "Untitled", "content": content or ""}
        _sj(pf, prompts); return json.dumps({"status": "saved", "id": pid}, ensure_ascii=False, indent=2)
    elif action == "delete":
        if prompt_id and prompt_id in prompts: del prompts[prompt_id]; _sj(pf, prompts); return json.dumps({"status": "deleted", "id": prompt_id}, ensure_ascii=False, indent=2)
        return json.dumps({"error": f"Not found: {prompt_id}"}, ensure_ascii=False, indent=2)
    return json.dumps({"error": f"Unknown action: {action}"}, ensure_ascii=False, indent=2)

@mcp.tool()
def crow_manage_backup(action='list', backup_id=None) -> str:
    if action == 'create':
        bn = 'backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'); bd = BACKUPS_DIR / bn; bd.mkdir(parents=True, exist_ok=True)
        c = 0
        for reg in VALID_REGISTERS:
            d = _lr(reg)
            if d.get("entries"): _sj(bd / f"{reg}.json", d); c += len(d["entries"])
        _sj(bd / "meta.json", {"name": bn, "entries": c})
        return json.dumps({"status": "created", "backup": bn, "entries": c}, ensure_ascii=False, indent=2)
    elif action == 'list':
        bl = [];
        for d in sorted(BACKUPS_DIR.iterdir()):
            if d.is_dir(): m = _lj(d / "meta.json", {}); bl.append({"id": d.name, "entries": m.get("entries", 0)})
        return json.dumps({"backups": bl, "count": len(bl)}, ensure_ascii=False, indent=2)
    elif action == 'restore':
        if not backup_id: return json.dumps({"error": "backup_id required"}, ensure_ascii=False, indent=2)
        bd = BACKUPS_DIR / backup_id
        if not bd.exists(): return json.dumps({"error": f"Not found: {backup_id}"}, ensure_ascii=False, indent=2)
        r = 0
        for reg in VALID_REGISTERS:
            bp = bd / f"{reg}.json"
            if bp.exists(): d = _lj(bp, {}); _sr(reg, d); r += len(d.get("entries", []))
        return json.dumps({"status": "restored", "backup": backup_id, "entries": r}, ensure_ascii=False, indent=2)
    elif action == 'delete':
        if not backup_id: return json.dumps({"error": "backup_id required"}, ensure_ascii=False, indent=2)
        bd = BACKUPS_DIR / backup_id
        if not bd.exists(): return json.dumps({"error": f"Not found: {backup_id}"}, ensure_ascii=False, indent=2)
        shutil.rmtree(bd); return json.dumps({"status": "deleted", "backup": backup_id}, ensure_ascii=False, indent=2)
    return json.dumps({"error": f"Unknown action: {action}"}, ensure_ascii=False, indent=2)

@mcp.tool()
def crow_project_info(action='get', project_name=None, description=None) -> str:
    projects = _lj(PROJECTS_FILE, {})
    if action == 'list': return json.dumps({"projects": [{"name":k,"description":v.get("description","")} for k,v in projects.items()], "count": len(projects)}, ensure_ascii=False, indent=2)
    elif action == 'get':
        if not project_name: return json.dumps({"error": "project_name required"}, ensure_ascii=False, indent=2)
        if project_name in projects: return json.dumps(projects[project_name], ensure_ascii=False, indent=2)
        return json.dumps({"error": f"Not found: {project_name}"}, ensure_ascii=False, indent=2)
    elif action == 'save':
        if not project_name: return json.dumps({"error": "project_name required"}, ensure_ascii=False, indent=2)
        projects[project_name] = {"name": project_name, "description": description or ""}
        _sj(PROJECTS_FILE, projects); return json.dumps({"status": "saved", "name": project_name}, ensure_ascii=False, indent=2)
    elif action == 'delete':
        if not project_name: return json.dumps({"error": "project_name required"}, ensure_ascii=False, indent=2)
        if project_name in projects: del projects[project_name]; _sj(PROJECTS_FILE, projects); return json.dumps({"status": "deleted", "name": project_name}, ensure_ascii=False, indent=2)
        return json.dumps({"error": f"Not found: {project_name}"}, ensure_ascii=False, indent=2)
    return json.dumps({"error": f"Unknown action: {action}"}, ensure_ascii=False, indent=2)


# ═══════════════════════════════════ HTTP Endpoints ═══════════════════════════════════

@mcp.custom_route("/health", methods=["GET"])
async def health_endpoint(request: Request) -> JSONResponse:
    try:
        d = json.loads(crow_diagnostics())
        return JSONResponse({"status": "ok", "version": VERSION, "entries": d.get("total_entries", 0), "timestamp": time.time()})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)

@mcp.custom_route("/ingest", methods=["POST"])
async def ingest_endpoint(request: Request) -> JSONResponse:
    try:
        b = await request.json()
        r = crow_ingest(content=b.get("content",""), register=b.get("register","context"), source=b.get("source","bridge"), tags=b.get("tags",[]))
        return JSONResponse({"status": "ok", "message": r})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=400)

@mcp.custom_route("/recall", methods=["GET"])
async def recall_endpoint(request: Request) -> JSONResponse:
    try:
        q = request.query_params
        results = _recall(q.get("query",""), reg=q.get("register",None), limit=int(q.get("limit","5")))
        return JSONResponse({"results": results, "count": len(results)})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=400)


# ═══════════════════════════════════ Main ═══════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crow Memory Server")
    parser.add_argument("--port", type=int, default=9020, help="Port (default: 9020)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Bind address")
    args = parser.parse_args()
    print(f"Crow Memory Server v{VERSION} starting on port {args.port}...")
    mcp.run(transport="sse", host=args.host, port=args.port)
