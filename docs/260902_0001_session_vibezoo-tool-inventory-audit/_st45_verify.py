# -*- coding: utf-8 -*-
"""ST-4/ST-5 verification v2: grep 0-hits, runtime registration check, mirror parity."""
import hashlib
import io
import os
import re
import sys

sys.dont_write_bytecode = True

FILES = {
    "integrated": ["mcp-servers/bridge/tools/integrated.py",
                   "extension/mcp-servers/bridge/tools/integrated.py"],
    "knowledge": ["mcp-servers/bridge/tools/knowledge.py",
                  "extension/mcp-servers/bridge/tools/knowledge.py"],
}
REMOVED = ["find_bugs", "suggest_refactor", "generate_docs", "learn_project"]
overall_ok = True

# ── 0. mirror parity FIRST (before os.chdir below) ──
print("=" * 60)
print("[0] Mirror parity (SHA-256)")
parity = {}
for kind, paths in FILES.items():
    hashes = []
    for p in paths:
        with open(p, "rb") as f:
            data = f.read()
        h = hashlib.sha256(data).hexdigest()
        hashes.append(h)
        print("  %s  %s" % (h[:16], p))
    parity[kind] = (hashes[0] == hashes[1])
    print("  %s -> %s" % (kind, "IDENTICAL" if parity[kind] else "DRIFT"))
print("  RESULT:", "PASS" if all(parity.values()) else "DRIFT (documented)")
if not all(parity.values()):
    overall_ok = False

# ── 1. grep 0-hits (word-level — must be 0 hits) ──
print("=" * 60)
print("[1] Removed-name grep in 4 edited files (must be 0 hits)")
all_clear = True
for kind, paths in FILES.items():
    for p in paths:
        with io.open(p, "r", encoding="utf-8") as f:
            text = f.read()
        hits = []
        for name in REMOVED:
            for m in re.finditer(r"\b%s\b" % name, text):
                line_no = text.count("\n", 0, m.start()) + 1
                hits.append((name, line_no))
        status = "OK (0 hits)" if not hits else "FAIL: %s" % hits
        if hits:
            all_clear = False
        print("  %s -> %s" % (p, status))
print("  RESULT:", "PASS" if all_clear else "FAIL")
if not all_clear:
    overall_ok = False

# ── 2. runtime registration check with stub mcp ──
print("=" * 60)
print("[2] Runtime registration check (stub mcp, both trees)")

class StubMCP:
    def __init__(self):
        self.registered = []
    def tool(self, fn=None, **kw):
        def deco(f):
            self.registered.append(f.__name__)
            return f
        return deco(fn) if fn is not None else deco

def check_tree(root):
    print("  --- %s ---" % root)
    int_mod = __import__("bridge.tools.integrated", fromlist=["register"])
    kno_mod = __import__("bridge.tools.knowledge", fromlist=["register"])

    mcp = StubMCP()
    int_mod.register(mcp)
    int_tools = sorted(mcp.registered)
    print("    integrated.register -> %s" % int_tools)

    mcp2 = StubMCP()
    kno_mod.register(mcp2)
    kno_tools = sorted(mcp2.registered)
    print("    knowledge.register  -> %s" % kno_tools)

    ok = True
    if int_tools != ["review_project"]:
        print("    FAIL: integrated expected ['review_project']")
        ok = False
    if kno_tools != ["get_preferences", "learn_preference", "recall_project"]:
        print("    FAIL: knowledge expected ['get_preferences','learn_preference','recall_project']")
        ok = False
    # shared helpers survived
    import bridge.tools.integrated as I
    for attr in ("_run_tool", "_tool_registry", "truncate_to_tokens", "register"):
        if not hasattr(I, attr):
            print("    FAIL: integrated missing %s" % attr)
            ok = False
    from bridge.utils import truncate_to_tokens as utt
    if getattr(I, "truncate_to_tokens", None) is not utt:
        print("    FAIL: integrated truncate_to_tokens is not bridge.utils.truncate_to_tokens")
        ok = False
    import bridge.tools.knowledge as K
    # recall_project/learn_preference/get_preferences are register() closures —
    # their presence is proven by the registration list above.
    if not hasattr(K, "_auto_learn_project"):
        print("    FAIL: knowledge missing _auto_learn_project")
        ok = False
    if not callable(getattr(K, "_auto_learn_project", None)):
        print("    FAIL: _auto_learn_project not callable")
        ok = False
    print("    RESULT:", "PASS" if ok else "FAIL")
    return ok

sys.path.insert(0, os.path.abspath("mcp-servers"))
ok1 = check_tree("mcp-servers (root)")

# purge bridge modules, reload from extension tree
for name in list(sys.modules):
    if name == "bridge" or name.startswith("bridge."):
        sys.modules.pop(name, None)
sys.path.pop(0)
os.chdir("extension/mcp-servers")
sys.path.insert(0, os.path.abspath("."))
ok2 = check_tree("extension/mcp-servers (extension)")

# ── 3. summary ──
print("=" * 60)
parity_note = "IDENTICAL" if all(parity.values()) else \
    "integrated=%s knowledge=%s" % ("identical" if parity["integrated"] else "DRIFT",
                                    "identical" if parity["knowledge"] else "drift")
print("OVERALL:", "PASS" if (ok1 and ok2 and all(parity.values())) else "FAIL",
      "| parity:", parity_note)