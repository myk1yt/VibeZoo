# P5: byte-level diff details for mirror mismatch files
import difflib
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent.parent.parent
FILES = [
    "bridge/tools/_base.py",
    "bridge/tools/deep_analyzer.py",
    "bridge/tools/feedback.py",
    "bridge/tools/file_analyzer.py",
    "bridge/tools/fix_loop.py",
    "bridge/tools/knowledge.py",
    "bridge/tools/reviewer.py",
    "bridge/tools/setup.py",
    "bridge/tools/ssa.py",
    "bridge/tools/web.py",
    "bridge/tools/whiteboard.py",
    "crow_memory_server.py",
]


def main():
    for f in FILES:
        ext_path = ROOT / "extension" / "mcp-servers" / f
        mir_path = ROOT / "mcp-servers" / f
        a = ext_path.read_text(encoding="utf-8", errors="replace").splitlines()
        b = mir_path.read_text(encoding="utf-8", errors="replace").splitlines()
        print("=" * 70)
        print("FILE: %s  ext=%d lines  mir=%d lines" % (f, len(a), len(b)))
        d = list(difflib.unified_diff(b, a, fromfile="mcp-servers/" + f,
                                       tofile="extension/mcp-servers/" + f,
                                       lineterm="", n=1))
        # Limit printed diff lines per file to keep output manageable
        for line in d[:80]:
            print(line)
        if len(d) > 80:
            print("... (%d more diff lines)" % (len(d) - 80))


if __name__ == "__main__":
    main()
