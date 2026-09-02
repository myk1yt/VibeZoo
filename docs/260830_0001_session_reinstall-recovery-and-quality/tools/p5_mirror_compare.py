# P5: extension/mcp-servers vs mcp-servers SHA-256 full comparison
import hashlib
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent.parent
ext = root / "extension" / "mcp-servers"
mir = root / "mcp-servers"

SKIP_DIRS = {"__pycache__", ".pytest_cache"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def collect(base: Path):
    out = {}
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        parts = set(p.relative_to(base).parts)
        if parts & SKIP_DIRS:
            continue
        rel = str(p.relative_to(base)).replace("\\", "/")
        out[rel] = sha(p)
    return out


def main():
    ext_files = collect(ext)
    mir_files = collect(mir)
    only_ext = sorted(set(ext_files) - set(mir_files))
    only_mir = sorted(set(mir_files) - set(ext_files))
    diff = sorted(k for k in (set(ext_files) & set(mir_files)) if ext_files[k] != mir_files[k])

    print("== ONLY_IN_extension/mcp-servers ==")
    for k in only_ext:
        print("  " + k)
    print("== ONLY_IN_mcp-servers ==")
    for k in only_mir:
        print("  " + k)
    print("== CONTENT_DIFF ==")
    for k in diff:
        print("  " + k)
    print("== COUNTS ==")
    print("ext=%d mir=%d common=%d diff=%d only_ext=%d only_mir=%d" % (
        len(ext_files), len(mir_files), len(set(ext_files) & set(mir_files)),
        len(diff), len(only_ext), len(only_mir)))


if __name__ == "__main__":
    main()
