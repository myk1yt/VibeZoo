"""
Run all test classes in extension/mcp-servers/tests/test_semantic_search.py using standard library unittest.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Mock requests if not installed
try:
    import requests
except ImportError:
    import types
    mock_req = types.ModuleType("requests")
    mock_req.exceptions = types.SimpleNamespace(ConnectionError=Exception, Timeout=Exception)
    mock_req.post = MagicMock()
    mock_req.get = MagicMock()
    sys.modules["requests"] = mock_req

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
EXT_MCP = REPO_ROOT / "extension" / "mcp-servers"
if str(EXT_MCP) not in sys.path:
    sys.path.insert(0, str(EXT_MCP))

"""
Run all test classes in extension/mcp-servers/tests/test_semantic_search.py.
Executes pytest-style test methods directly using introspection.
"""
import inspect
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock requests if not installed
try:
    import requests
except ImportError:
    import types
    mock_req = types.ModuleType("requests")
    mock_req.exceptions = types.SimpleNamespace(ConnectionError=Exception, Timeout=Exception)
    mock_req.post = MagicMock()
    mock_req.get = MagicMock()
    sys.modules["requests"] = mock_req

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
EXT_MCP = REPO_ROOT / "extension" / "mcp-servers"
if str(EXT_MCP) not in sys.path:
    sys.path.insert(0, str(EXT_MCP))

import tests.test_semantic_search as tss

def main():
    test_classes = [
        tss.TestCosineSimilarity,
        tss.TestEmbeddingClientAvailability,
        tss.TestEmbeddingClientEmbed,
        tss.TestRankByEmbedding,
        tss.TestResultRankerContextLines,
    ]

    total = 0
    passed = 0
    failed = 0

    print("=== Running test_semantic_search.py unit tests ===")

    for cls in test_classes:
        instance = cls()
        for attr_name in dir(instance):
            if attr_name.startswith("test_"):
                method = getattr(instance, attr_name)
                if callable(method):
                    total += 1
                    try:
                        # Check signature for fixtures
                        sig = inspect.signature(method)
                        if len(sig.parameters) == 0:
                            method()
                            passed += 1
                            print(f"[PASS] {cls.__name__}.{attr_name}")
                        else:
                            # Skip parameterized/fixture tests in this standalone runner
                            print(f"[SKIP] {cls.__name__}.{attr_name} (requires fixture)")
                    except Exception as e:
                        failed += 1
                        print(f"[FAIL] {cls.__name__}.{attr_name}: {e}")

    print(f"=== Results: {passed} passed, {failed} failed, {total - passed - failed} skipped / {total} total ===")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
