import shutil
from pathlib import Path

def main():
    src_base = Path("extension/mcp-servers")
    dst_base = Path("mcp-servers")
    
    # Files to copy
    diff_rel_paths = [
        "bridge/tools/_base.py",
        "bridge/tools/deep_analyzer.py",
        "bridge/tools/feedback.py",
        "bridge/tools/file_analyzer.py",
        "bridge/tools/fix_loop.py",
        "bridge/tools/knowledge.py",
        "bridge/tools/reviewer.py",
        "bridge/tools/scout.py",
        "bridge/tools/setup.py",
        "bridge/tools/ssa.py",
        "bridge/tools/web.py",
        "bridge/tools/whiteboard.py",
        "tests/test_whiteboard_merge.py",
    ]
    
    for rel in diff_rel_paths:
        src = src_base / rel
        dst = dst_base / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"Copied {src} -> {dst}")

if __name__ == "__main__":
    main()
