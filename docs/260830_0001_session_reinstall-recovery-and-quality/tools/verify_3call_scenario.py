"""
Verification of 3 consecutive is_available() calls in real down environment (port 8089 down).
Measures latency of each call to prove backoff cache eliminates redundant network timeout delays.
"""
import sys
import time
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

from bridge.embedding_client import EmbeddingClient, get_embedding_client, reset_availability

def test_real_scenario():
    print("=== Testing 3-call scenario in current environment (8089 down) ===")
    client = EmbeddingClient()
    
    # Call 1 (first probe)
    t0 = time.perf_counter()
    res1 = client.is_available()
    t1 = time.perf_counter()
    dur1 = (t1 - t0) * 1000
    print(f"Call 1: result={res1}, duration={dur1:.2f}ms (initial network probe)")
    
    # Call 2 (immediate second call - should hit backoff cache)
    t0 = time.perf_counter()
    res2 = client.is_available()
    t1 = time.perf_counter()
    dur2 = (t1 - t0) * 1000
    print(f"Call 2: result={res2}, duration={dur2:.4f}ms (cached via backoff)")
    
    # Call 3 (immediate third call - should hit backoff cache)
    t0 = time.perf_counter()
    res3 = client.is_available()
    t1 = time.perf_counter()
    dur3 = (t1 - t0) * 1000
    print(f"Call 3: result={res3}, duration={dur3:.4f}ms (cached via backoff)")
    
    assert res1 is False
    assert res2 is False
    assert res3 is False
    assert dur2 < 5.0, f"Call 2 should be < 5ms, took {dur2}ms"
    assert dur3 < 5.0, f"Call 3 should be < 5ms, took {dur3}ms"
    print("SUCCESS: Consecutive calls returned instant cached False without network delay!")

if __name__ == "__main__":
    test_real_scenario()
