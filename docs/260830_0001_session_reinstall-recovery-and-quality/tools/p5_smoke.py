# P5 Runtime smoke: extension/mcp-servers bridge import + Mock MCP registration
# Also verifies the root mirror copy.
import sys
import io
import traceback
from pathlib import Path
from unittest.mock import MagicMock

# requests is not installed in system python — inject a MagicMock so import-only
# smoke works (per P5 spec: "requests mock 활용"). Network calls are never made.
sys.modules.setdefault("requests", MagicMock())

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXPECTED_DELETED_TOOLS = {
    "explain_code", "analyze_changes", "generate_tests", "analyze_coverage",
    "ux_coordinator", "auto_analyze_after_drop", "auto_analyze_whiteboard",
    "apply_patch", "explore_github",
}


class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, *args, **kwargs):
        # Pattern 1: @mcp.tool (bare)
        if args and callable(args[0]) and not kwargs:
            fn = args[0]
            self.tools[fn.__name__] = fn
            return fn

        # Pattern 2: @mcp.tool() / @mcp.tool(name=...)
        def decorator(fn):
            name = kwargs.get("name") or fn.__name__
            self.tools[name] = fn
            return fn
        return decorator


def run_smoke(servers_dir: Path, label: str):
    print("=" * 60)
    print("SMOKE: %s (%s)" % (label, servers_dir))
    # Fresh module state per run
    for mod in list(sys.modules):
        if mod == "bridge" or mod.startswith("bridge."):
            del sys.modules[mod]
    sys.path.insert(0, str(servers_dir))
    try:
        results = {}
        modules = [
            "bridge.config", "bridge.utils", "bridge.i18n", "bridge.tool_context",
            "bridge.index_cache", "bridge.embedding_client", "bridge.crow_client",
            "bridge.error_handler", "bridge.file_cache", "bridge.ast_engine",
            "bridge.ast_singleton", "bridge.search_engine", "bridge.llm_pipeline",
            "bridge.tools",
        ]
        for m in modules:
            try:
                __import__(m)
                results[m] = "OK"
            except Exception as e:
                results[m] = "FAIL: %s: %s" % (type(e).__name__, e)
        ok = sum(1 for v in results.values() if v == "OK")
        print("module imports: %d/%d OK" % (ok, len(modules)))
        for m, v in results.items():
            if v != "OK":
                print("  FAIL %s -> %s" % (m, v))

        # Mock registration via register_all_tools
        import bridge.tools as bt
        mcp = MockMCP()
        try:
            bt.register_all_tools(mcp)
            names = sorted(mcp.tools.keys())
            print("registered tools: %d" % len(names))
            leaked = EXPECTED_DELETED_TOOLS & set(names)
            print("deleted-tool leakage: %s" % (sorted(leaked) if leaked else "none"))
            dup = [n for n in names if names.count(n) > 1]
            print("duplicate names: %s" % (sorted(set(dup)) if dup else "none"))
            for n in names:
                print("  - %s" % n)
            return len(names), leaked
        except Exception as e:
            print("register_all_tools FAILED: %s: %s" % (type(e).__name__, e))
            traceback.print_exc()
            return -1, EXPECTED_DELETED_TOOLS
    finally:
        try:
            sys.path.remove(str(servers_dir))
        except ValueError:
            pass


def main():
    ext_n, ext_leak = run_smoke(ROOT / "extension" / "mcp-servers", "extension/mcp-servers")
    mir_n, mir_leak = run_smoke(ROOT / "mcp-servers", "mcp-servers (root mirror)")
    print("=" * 60)
    print("SUMMARY ext=%d tools (leak=%s), mir=%d tools (leak=%s)" % (
        ext_n, bool(ext_leak), mir_n, bool(mir_leak)))


if __name__ == "__main__":
    main()
