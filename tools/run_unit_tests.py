import sys, os, glob, importlib.util

sys.path.insert(0, os.path.abspath('mcp-servers'))
test_files = sorted(glob.glob('mcp-servers/tests/test_*.py'))
print(f"Discovered {len(test_files)} test files: {[os.path.basename(f) for f in test_files]}")

from unittest.mock import MagicMock
sys.modules['requests'] = MagicMock()

passed = 0
failed = 0
for tf in test_files:
    mod_name = os.path.splitext(os.path.basename(tf))[0]
    spec = importlib.util.spec_from_file_location(mod_name, tf)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        print(f"[PASS] {mod_name} imported successfully")
        passed += 1
    except Exception as e:
        print(f"[FAIL] {mod_name} import failed: {e}")
        failed += 1

print(f"\nResults: {passed} passed, {failed} failed")
