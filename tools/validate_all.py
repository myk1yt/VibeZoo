import py_compile, glob, sys, os, subprocess

print("=== 1. py_compile validation ===")
py_files = glob.glob('mcp-servers/**/*.py', recursive=True) + glob.glob('extension/mcp-servers/**/*.py', recursive=True)
for f in py_files:
    py_compile.compile(f, doraise=True)
print(f"PASS: Compiled {len(py_files)} Python files without syntax errors.")

print("\n=== 2. Tool registration validation ===")
from unittest.mock import MagicMock
sys.modules['requests'] = MagicMock()

class MockMCP:
    def __init__(self):
        self.tools = {}
    def tool(self, *args, **kwargs):
        if args and callable(args[0]):
            fn = args[0]
            self.tools[fn.__name__] = fn
            return fn
        def dec(fn):
            name = kwargs.get('name', fn.__name__)
            self.tools[name] = fn
            return fn
        return dec

deleted_tools = [
    'explain_code', 'analyze_changes', 'generate_tests', 'analyze_coverage',
    'ux_coordinator', 'auto_analyze_after_drop', 'auto_analyze_whiteboard',
    'apply_patch', 'explore_github'
]

for p in ['mcp-servers', 'extension/mcp-servers']:
    sys.path.insert(0, os.path.abspath(p))
    from bridge.tools import register_all_tools
    m = MockMCP()
    register_all_tools(m)
    print(f"[{p}] Registered {len(m.tools)} tools.")
    for d in deleted_tools:
        if d in m.tools:
            raise AssertionError(f"Tool '{d}' is still registered in {p}!")
    print(f"[{p}] PASS: Verified 0/{len(deleted_tools)} deleted tools present.")
    sys.path.pop(0)

print("\n=== 3. i18n Translation validation ===")
res = subprocess.run([sys.executable, "docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_translations.py"], capture_output=True, text=True)
print(res.stdout)
if res.returncode != 0:
    print(res.stderr)
    sys.exit(res.returncode)

print("=== All Validations Passed Successfully! ===")
