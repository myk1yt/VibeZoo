# -*- coding: utf-8 -*-
"""i18n Technical Review Verification Script.
Runs all static checks and emits a structured JSON report.
"""
import json
import os
import py_compile
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXT = os.path.join(ROOT, "extension")
MCP = os.path.join(EXT, "mcp-servers")
BRIDGE = os.path.join(MCP, "bridge")
TOOLS = os.path.join(BRIDGE, "tools")
I18N = os.path.join(BRIDGE, "i18n")
TRANS = os.path.join(I18N, "translations")
L10N = os.path.join(EXT, "l10n")

report = {
    "root": ".",
    "python_compile": {"pass": [], "fail": []},
    "json_validation": {"pass": [], "fail": []},
    "key_consistency": {},
    "import_check": {"pass": [], "fail": [], "no_t_usage": []},
}

# ---------- 1. Python compilation ----------
python_targets = [
    os.path.join(I18N, "__init__.py"),
    os.path.join(MCP, "vibezoo_mcp_bridge.py"),
]
tool_files = [
    "analysis.py", "deep_analyzer.py", "editor.py", "feedback.py",
    "file_analyzer.py", "fix_loop.py", "github_diver.py", "integrated.py",
    "knowledge.py", "reviewer.py", "scout.py", "setup.py", "ssa.py",
    "tester.py", "ux_coordinator.py", "web.py", "whiteboard.py", "_base.py",
]
for tf in tool_files:
    python_targets.append(os.path.join(TOOLS, tf))

for path in python_targets:
    rel = os.path.relpath(path, ROOT)
    if not os.path.isfile(path):
        report["python_compile"]["fail"].append({"file": rel, "error": "FILE NOT FOUND"})
        continue
    try:
        py_compile.compile(path, doraise=True)
        report["python_compile"]["pass"].append(rel)
    except py_compile.PyCompileError as e:
        report["python_compile"]["fail"].append({"file": rel, "error": str(e)})

# ---------- 2. JSON validation ----------
json_targets = []
for f in sorted(os.listdir(TRANS)):
    if f.endswith(".json"):
        json_targets.append(os.path.join(TRANS, f))
for f in sorted(os.listdir(EXT)):
    if f.startswith("package.nls") and f.endswith(".json"):
        json_targets.append(os.path.join(EXT, f))
for f in sorted(os.listdir(L10N)):
    if f.startswith("bundle.l10n") and f.endswith(".json"):
        json_targets.append(os.path.join(L10N, f))

for path in json_targets:
    rel = os.path.relpath(path, ROOT)
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            json.load(fh)
        report["json_validation"]["pass"].append(rel)
    except Exception as e:
        report["json_validation"]["fail"].append({"file": rel, "error": str(e)})

# ---------- 3. Key consistency vs en.json ----------
def flatten(d, prefix=""):
    keys = set()
    if isinstance(d, dict):
        for k, v in d.items():
            nk = f"{prefix}.{k}" if prefix else k
            keys.add(nk)
            keys |= flatten(v, nk)
    return keys

en_path = os.path.join(TRANS, "en.json")
with open(en_path, "r", encoding="utf-8-sig") as fh:
    en_data = json.load(fh)
en_keys = flatten(en_data)
report["key_consistency"]["en_key_count_top_level"] = len(en_data)
report["key_consistency"]["en_key_count_flattened"] = len(en_keys)
report["key_consistency"]["files"] = {}

for f in sorted(os.listdir(TRANS)):
    if not f.endswith(".json") or f == "en.json":
        continue
    p = os.path.join(TRANS, f)
    with open(p, "r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    keys = flatten(data)
    missing = sorted(en_keys - keys)
    extra = sorted(keys - en_keys)
    report["key_consistency"]["files"][f] = {
        "top_level": len(data),
        "flattened": len(keys),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "missing_sample": missing[:5],
        "extra_sample": extra[:5],
    }

# ---------- 4. Import check ----------
for tf in tool_files:
    if tf == "_base.py":
        # _base may or may not use t(); check separately
        pass
    path = os.path.join(TOOLS, tf)
    rel = os.path.relpath(path, ROOT)
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    has_import = ("from bridge.i18n import" in src) or ("from ..i18n import" in src) or ("from .i18n import" in src)
    uses_t = "t(" in src
    if uses_t and has_import:
        report["import_check"]["pass"].append(rel)
    elif uses_t and not has_import:
        report["import_check"]["fail"].append({"file": rel, "error": "uses t() but no i18n import"})
    elif not uses_t:
        report["import_check"]["no_t_usage"].append(rel)
    else:
        report["import_check"]["pass"].append(rel)

# ---------- Summary ----------
report["summary"] = {
    "python_total": len(python_targets),
    "python_pass": len(report["python_compile"]["pass"]),
    "python_fail": len(report["python_compile"]["fail"]),
    "json_total": len(json_targets),
    "json_pass": len(report["json_validation"]["pass"]),
    "json_fail": len(report["json_validation"]["fail"]),
    "i18n_files_with_key_drift": sum(
        1 for v in report["key_consistency"]["files"].values()
        if v["missing_count"] > 0 or v["extra_count"] > 0
    ),
    "import_pass": len(report["import_check"]["pass"]),
    "import_fail": len(report["import_check"]["fail"]),
    "import_no_t_usage": len(report["import_check"]["no_t_usage"]),
}

out = json.dumps(report, indent=2, ensure_ascii=False)
print(out)

with open(os.path.join(os.path.dirname(__file__), "i18n_verify_result.json"), "w", encoding="utf-8") as fh:
    fh.write(out)
