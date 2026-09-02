# -*- coding: utf-8 -*-
"""ST-5 follow-up: extension/mcp-servers/bridge/tools/knowledge.py (uses i18n t() wrapper)."""
import io

path = "extension/mcp-servers/bridge/tools/knowledge.py"

with io.open(path, "r", encoding="utf-8") as f:
    text = f.read()

EDITS = [
    ("# learn_project + recall_project + learn_preference + get_preferences\n",
     "# recall_project + learn_preference + get_preferences\n"),
    ("# 자동 learn_project (register 시 지연 초기화, 1회만)\n",
     "# 프로젝트 지식 자동 수집 (_auto_learn_project, register 시 지연 초기화, 1회만)\n"),
    ("# ── 자동 learn_project 관리 ──────────────────────────\n",
     "# ── 자동 프로젝트 지식 수집 관리 ──────────────────────\n"),
    ("    \"\"\"등록 시 자동 learn_project (지연 초기화, 최초 1회만).",
     "    \"\"\"등록 시 프로젝트 지식을 자동 수집 (지연 초기화, 최초 1회만)."),
    ("    learn_project 실패 시에도 예외를 삼키고 조용히 진행합니다.",
     "    자동 수집 실패 시에도 예외를 삼키고 조용히 진행합니다."),
    ("        # learn_project 내부 로직을 직접 호출 (async-safe)",
     "        # 자동 수집 로직 직접 호출 (async-safe)"),
    ("    \"\"\"Knowledge 도구 등록 (자동 learn_project 스케줄 포함)\"\"\"",
     "    \"\"\"Knowledge 도구 등록 (자동 프로젝트 지식 수집 스케줄 포함)\"\"\""),
    ("    # ── 자동 learn_project 스케줄 (지연 초기화, 1회만) ──",
     "    # ── 자동 프로젝트 지식 수집 스케줄 (지연 초기화, 1회만) ──"),
    ("            \"\"\"서버 시작 후 3초 지연 → 자동 learn_project 실행\"\"\"",
     "            \"\"\"서버 시작 후 3초 지연 → 자동 프로젝트 지식 수집 실행\"\"\""),
    ("        \"\"\"Crow Memory에서 learn_project로 저장된 프로젝트 지식을 회상합니다.",
     "        \"\"\"Crow Memory에 자동 수집된 프로젝트 지식을 회상합니다."),
    # i18n t()-wrapped hint (extension drift)
    ("f\"  → {t('Run `learn_project()` first to store project knowledge.')}\\n\"",
     "f\"  → {t('Project knowledge is auto-captured at bridge startup (_auto_learn_project); force-refresh via summarize_architecture/extract_patterns/map_dependencies and recall again.')}\\n\""),
]

# 1. delete @mcp.tool learn_project block [start, recall_start)
lines = text.splitlines(keepends=True)
sl = rl = -1
for i, ln in enumerate(lines):
    if ln.strip() == "@mcp.tool" and i + 1 < len(lines) and \
       lines[i + 1].strip().startswith("def learn_project("):
        sl = i
    if ln.strip() == "@mcp.tool" and i + 1 < len(lines) and \
       lines[i + 1].strip().startswith("def recall_project("):
        rl = i
assert 0 < sl < rl, (sl, rl)
orig = len(lines)
del lines[sl:rl]
text = "".join(lines)

# 2. replacements
for old, new in EDITS:
    if old not in text:
        raise RuntimeError("ANCHOR NOT FOUND: %r" % old)
    text = text.replace(old, new, 1)

# normalize trailing newline
while text.endswith("\n\n"):
    text = text[:-1]
if not text.endswith("\n"):
    text += "\n"

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print("extension knowledge.py: %d -> %d lines" % (orig, text.count("\n")))