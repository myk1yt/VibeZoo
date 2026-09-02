# -*- coding: utf-8 -*-
"""ST-4/ST-5 surgical edit script: remove aggregate MCP tools from integrated.py + knowledge.py (both trees)."""
import io
import sys

REPORT = []

def log(msg):
    REPORT.append(msg)
    print(msg)

def read_lines(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return f.readlines()

def write_lines(path, lines):
    # normalize: strip trailing blank lines, end with single newline
    while lines and lines[-1].strip() == "":
        lines.pop()
    if lines and not lines[-1].endswith("\n"):
        lines[-1] = lines[-1] + "\n"
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)

def find_tool_start(lines, fn_name):
    """Return index of the '@mcp.tool' line immediately preceding 'def <fn_name>('."""
    for i, ln in enumerate(lines):
        if ln.strip() == "@mcp.tool" and i + 1 < len(lines) and \
           lines[i + 1].strip().startswith("def %s(" % fn_name):
            return i
    return -1

def find_closure_start(lines, closure_name):
    for i, ln in enumerate(lines):
        if ln.strip().startswith("def %s():" % closure_name):
            return i
    return -1

def find_closure_end(lines, start):
    """End index (exclusive) = next line at same indent level starting a def or the section marker."""
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith("def _get_") or s.startswith("# ── 도구 등록"):
            return j
    return len(lines)

def replace_once(lines, old, new, path, must=True):
    joined = "".join(lines)
    if old not in joined:
        if must:
            raise RuntimeError("ANCHOR NOT FOUND in %s: %r" % (path, old))
        return lines
    joined = joined.replace(old, new, 1)
    return joined.splitlines(keepends=True)

# ─────────────────────────────────────────────────────────
# ST-4: integrated.py
# ─────────────────────────────────────────────────────────
HEADER_NEW = "# review_project (find_bugs/suggest_refactor/generate_docs 제거 — 프롬프트 조합으로 대체, plan §4)\n"

CLOSURES_TO_DELETE = [
    "_get_search_codebase",
    "_get_map_dependencies",
    "_get_analyze_call_graph",
    "_get_reverse_engineer",
    "_get_summarize_architecture",
    "_get_draw_on_whiteboard",
    "_get_analyze_changes",
]

def edit_integrated(path):
    lines = read_lines(path)
    orig_count = len(lines)

    # 1. module docstring comment (line 2)
    lines = replace_once(
        lines,
        "# review_project + find_bugs + suggest_refactor + generate_docs\n",
        HEADER_NEW, path)

    # 2. delete module-level ESLint/tsc/native-linter helpers (used ONLY by find_bugs)
    es = next(i for i, ln in enumerate(lines) if ln.startswith("# ── ESLint / tsc 헬퍼"))
    rg = next(i for i, ln in enumerate(lines) if ln.startswith("def register(mcp):"))
    del lines[es:rg]
    # trim extra blank lines so exactly 2 blank lines precede def register
    while True:
        # find def register index again
        rg = next(i for i, ln in enumerate(lines) if ln.startswith("def register(mcp):"))
        blanks = 0
        k = rg - 1
        while k >= 0 and lines[k].strip() == "":
            blanks += 1
            k -= 1
        if blanks > 2:
            del lines[rg - (blanks - 2):rg]
        else:
            break

    # 3. delete register()-local lazy-import closures used only by removed tools
    for name in CLOSURES_TO_DELETE:
        st = find_closure_start(lines, name)
        if st == -1:
            raise RuntimeError("closure not found: %s in %s" % (name, path))
        en = find_closure_end(lines, st)
        del lines[st:en]

    # 4. delete find_bugs + suggest_refactor (contiguous) and generate_docs (to EOF)
    sf = find_tool_start(lines, "find_bugs")
    sg = find_tool_start(lines, "suggest_refactor")
    sgd = find_tool_start(lines, "generate_docs")
    if not (0 < sf < sg < sgd):
        raise RuntimeError("unexpected tool ordering in %s: %d %d %d" % (path, sf, sg, sgd))
    # sanity: find_bugs..suggest_refactor are adjacent blocks
    del lines[sgd:]          # generate_docs to EOF
    del lines[sf:sgd]        # find_bugs + suggest_refactor blocks (incl. separating blank)

    # 5. remove now-unused 'import subprocess' (only user was deleted helper block)
    idx = next(i for i, ln in enumerate(lines) if ln.strip() == "import subprocess")
    del lines[idx]

    write_lines(path, lines)
    log("[ST-4] %s: %d -> %d lines" % (path, orig_count, len(lines)))

# ─────────────────────────────────────────────────────────
# ST-5: knowledge.py
# ─────────────────────────────────────────────────────────
KNOWLEDGE_EDITS = [
    # header
    ("# learn_project + recall_project + learn_preference + get_preferences\n",
     "# recall_project + learn_preference + get_preferences\n"),
    ("# 자동 learn_project (register 시 지연 초기화, 1회만)\n",
     "# 프로젝트 지식 자동 수집 (_auto_learn_project, register 시 지연 초기화, 1회만)\n"),
    # section comment
    ("# ── 자동 learn_project 관리 ──────────────────────────\n",
     "# ── 자동 프로젝트 지식 수집 관리 ──────────────────────\n"),
    # _auto_learn_project docstring
    ("    \"\"\"등록 시 자동 learn_project (지연 초기화, 최초 1회만).",
     "    \"\"\"등록 시 프로젝트 지식을 자동 수집 (지연 초기화, 최초 1회만)."),
    ("    learn_project 실패 시에도 예외를 삼키고 조용히 진행합니다.",
     "    자동 수집 실패 시에도 예외를 삼키고 조용히 진행합니다."),
    ("        # learn_project 내부 로직을 직접 호출 (async-safe)",
     "        # 자동 수집 로직 직접 호출 (async-safe)"),
    # register docstring + comments
    ("    \"\"\"Knowledge 도구 등록 (자동 learn_project 스케줄 포함)\"\"\"",
     "    \"\"\"Knowledge 도구 등록 (자동 프로젝트 지식 수집 스케줄 포함)\"\"\""),
    ("    # ── 자동 learn_project 스케줄 (지연 초기화, 1회만) ──",
     "    # ── 자동 프로젝트 지식 수집 스케줄 (지연 초기화, 1회만) ──"),
    ("            \"\"\"서버 시작 후 3초 지연 → 자동 learn_project 실행\"\"\"",
     "            \"\"\"서버 시작 후 3초 지연 → 자동 프로젝트 지식 수집 실행\"\"\""),
    # recall_project docstring
    ("        \"\"\"Crow Memory에서 learn_project로 저장된 프로젝트 지식을 회상합니다.",
     "        \"\"\"Crow Memory에 자동 수집된 프로젝트 지식을 회상합니다."),
    # recall_project hint text (plan §4 learn_project guidance)
    ("            output += \"  → Run `learn_project()` first to store project knowledge.\\n\"",
     "            output += \"  → Project knowledge is auto-captured at bridge startup (_auto_learn_project); force-refresh via summarize_architecture/extract_patterns/map_dependencies and recall again.\\n\""),
]

def edit_knowledge(path):
    lines = read_lines(path)
    orig_count = len(lines)

    # 1. delete @mcp.tool learn_project block [start, recall_start)
    sl = find_tool_start(lines, "learn_project")
    rl = find_tool_start(lines, "recall_project")
    if not (0 < sl < rl):
        raise RuntimeError("learn_project/recall_project ordering broken in %s: %d %d" % (path, sl, rl))
    del lines[sl:rl]

    # 2. text replacements (docstrings/comments/hint)
    for old, new in KNOWLEDGE_EDITS:
        lines = replace_once(lines, old, new, path)

    write_lines(path, lines)
    log("[ST-5] %s: %d -> %d lines" % (path, orig_count, len(lines)))

ROOTS = ["mcp-servers", os.path.join("extension", "mcp-servers")] if False else ["mcp-servers", "extension/mcp-servers"]

import os
for root in ROOTS:
    edit_integrated(os.path.join(root, "bridge", "tools", "integrated.py"))
    edit_knowledge(os.path.join(root, "bridge", "tools", "knowledge.py"))

log("ALL EDITS APPLIED")