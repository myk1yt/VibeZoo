import os
import py_compile
import sys

def main():
    count = 0
    errors = []
    for r, d, files in os.walk('.'):
        if any(x in r for x in ['.git', 'venv', 'node_modules', '.pytest_cache']):
            continue
        for f in files:
            if f.endswith('.py'):
                p = os.path.join(r, f)
                try:
                    py_compile.compile(p, doraise=True)
                    count += 1
                except Exception as e:
                    errors.append((p, str(e)))
                    
    print(f"py_compile checked {count} files.")
    if errors:
        print(f"FAILED on {len(errors)} files:")
        for p, err in errors:
            print(f"  {p}: {err}")
        sys.exit(1)
    else:
        print("ALL py files compiled successfully (0 errors).")
        sys.exit(0)

if __name__ == "__main__":
    main()
