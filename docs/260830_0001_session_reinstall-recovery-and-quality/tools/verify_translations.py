# -*- coding: utf-8 -*-
"""Comprehensive verification script for Python MCP bridge i18n translations.
Compares en.json against 19 language translations, checks for missing/extra/empty/untranslated keys,
scans both root mcp-servers and extension/mcp-servers codebases for t() calls,
and verifies SHA-256 hash equality between root and extension translation files.
"""
import ast
import hashlib
import json
import os
import re
import sys
import io
from collections import Counter

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BRIDGE = os.path.join(ROOT, "mcp-servers", "bridge")
TRANS_DIR = os.path.join(BRIDGE, "i18n", "translations")
EXT_TRANS_DIR = os.path.join(ROOT, "extension", "mcp-servers", "bridge", "i18n", "translations")

def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_codebase_t_keys():
    """Extract all string literal arguments passed to t(...) in python files across the repo."""
    t_keys = set()
    t_occurrences = {}  # key -> list of file:line
    
    python_files = []
    # Scan both root mcp-servers and extension/mcp-servers
    for scan_root in [os.path.join(ROOT, "mcp-servers"), os.path.join(ROOT, "extension", "mcp-servers")]:
        if os.path.exists(scan_root):
            for root_dir, _, files in os.walk(scan_root):
                for f in files:
                    if f.endswith(".py"):
                        python_files.append(os.path.join(root_dir, f))
                
    # Remove duplicates
    python_files = sorted(list(set(python_files)))

    # Regex fallback for extract t("...") or t('...')
    t_pattern = re.compile(r'\bt\(\s*(["\'])(.*?)(?<!\\)\1')

    for pf in python_files:
        rel = os.path.relpath(pf, ROOT)
        try:
            with open(pf, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {rel}: {e}", file=sys.stderr)
            continue
            
        # 1. Try AST first
        try:
            tree = ast.parse(content, filename=rel)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    is_t = False
                    if isinstance(func, ast.Name) and func.id == "t":
                        is_t = True
                    elif isinstance(func, ast.Attribute) and func.attr == "t":
                        is_t = True
                    
                    if is_t and node.args:
                        first_arg = node.args[0]
                        val = None
                        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                            val = first_arg.value
                        elif hasattr(ast, 'Str') and isinstance(first_arg, ast.Str):
                            val = first_arg.s
                        if val is not None:
                            t_keys.add(val)
                            loc = f"{rel}:{node.lineno}"
                            if loc not in t_occurrences.get(val, []):
                                t_occurrences.setdefault(val, []).append(loc)
        except Exception:
            pass

        # 2. Regex scan to catch any lines
        for lineno, line in enumerate(content.splitlines(), start=1):
            for match in t_pattern.finditer(line):
                raw_s = match.group(2).replace('\\"', '"').replace("\\'", "'")
                t_keys.add(raw_s)
                loc = f"{rel}:{lineno}"
                if loc not in t_occurrences.get(raw_s, []):
                    t_occurrences.setdefault(raw_s, []).append(loc)
            
    return t_keys, t_occurrences

def analyze_json_keys(file_path):
    """Check duplicate keys and load json."""
    with open(file_path, "r", encoding="utf-8-sig") as f:
        text = f.read()
    data = json.loads(text)
    
    # Check for duplicates in raw text
    raw_keys = re.findall(r'"((?:\\.|[^"\\])*)"\s*:', text)
    unescaped_keys = []
    for k in raw_keys:
        unescaped_keys.append(json.loads(f'"{k}"'))
    counter = Counter(unescaped_keys)
    duplicates = [k for k, count in counter.items() if count > 1]
    
    return data, list(data.keys()), duplicates, len(unescaped_keys)

def main():
    report = {
        "summary": {},
        "en_json_analysis": {},
        "code_key_scan": {},
        "language_reports": {},
        "root_vs_extension_sync": {},
        "untranslated_details": {},
        "missing_details": {},
        "empty_details": {},
        "extra_details": {}
    }
    
    # 1. Load en.json
    en_path = os.path.join(TRANS_DIR, "en.json")
    en_data, en_keys_list, en_dupes, en_raw_count = analyze_json_keys(en_path)
    en_keys = set(en_keys_list)
    
    report["en_json_analysis"] = {
        "raw_key_count_in_file": en_raw_count,
        "unique_key_count": len(en_keys),
        "duplicate_keys": en_dupes
    }
    report["summary"]["en_unique_key_count"] = len(en_keys)
    report["summary"]["en_raw_key_count"] = en_raw_count
    
    # 2. Extract keys from code
    code_keys, code_occurrences = get_codebase_t_keys()
    code_missing_in_en = sorted(code_keys - en_keys)
    en_unused_in_code = sorted(en_keys - code_keys)
    
    report["code_key_scan"] = {
        "total_t_calls_keys_found_in_code": len(code_keys),
        "code_keys_missing_in_en_count": len(code_missing_in_en),
        "code_keys_missing_in_en": code_missing_in_en,
        "en_keys_unused_in_code_count": len(en_unused_in_code),
        "en_keys_unused_in_code": en_unused_in_code
    }
    
    # 3. Compare with all other translation files
    all_files = sorted(os.listdir(TRANS_DIR))
    lang_files = [f for f in all_files if f.endswith(".json") and f != "en.json"]
    
    total_missing_all_langs = 0
    total_empty_all_langs = 0
    
    for lf in lang_files:
        lang_code = lf[:-5] # remove .json
        file_path = os.path.join(TRANS_DIR, lf)
        data, cur_keys_list, dupes, raw_count = analyze_json_keys(file_path)
            
        cur_keys = set(cur_keys_list)
        missing = sorted(en_keys - cur_keys)
        extra = sorted(cur_keys - en_keys)
        
        empty = []
        untranslated = [] # key exists, value is non-empty, but value == en_data[key]
        
        for k in en_keys:
            if k in data:
                val = data[k]
                if val == "" or val is None:
                    empty.append(k)
                elif val == en_data[k]:
                    untranslated.append(k)
                    
        total_missing_all_langs += len(missing)
        total_empty_all_langs += len(empty)
        
        report["language_reports"][lang_code] = {
            "raw_key_count": raw_count,
            "unique_keys": len(cur_keys),
            "missing_count": len(missing),
            "empty_count": len(empty),
            "untranslated_count": len(untranslated),
            "extra_count": len(extra),
            "duplicate_keys": dupes
        }
        
        if missing:
            report["missing_details"][lang_code] = missing
        if empty:
            report["empty_details"][lang_code] = empty
        if extra:
            report["extra_details"][lang_code] = extra
        if untranslated:
            report["untranslated_details"][lang_code] = untranslated

    # 4. Check sync between root and extension
    sync_all_matched = True
    sync_details = {}
    for f in all_files:
        if f.endswith(".json"):
            root_f = os.path.join(TRANS_DIR, f)
            ext_f = os.path.join(EXT_TRANS_DIR, f)
            if not os.path.exists(ext_f):
                sync_details[f] = {"status": "missing_in_extension"}
                sync_all_matched = False
            else:
                h_root = file_sha256(root_f)
                h_ext = file_sha256(ext_f)
                matched = (h_root == h_ext)
                sync_details[f] = {
                    "matched": matched,
                    "sha256": h_root
                }
                if not matched:
                    sync_all_matched = False

    report["root_vs_extension_sync"] = {
        "all_files_identical": sync_all_matched,
        "files_checked": len(sync_details),
        "details": sync_details
    }

    report["summary"]["target_language_count"] = len(lang_files)
    report["summary"]["total_missing_keys_across_languages"] = total_missing_all_langs
    report["summary"]["total_empty_keys_across_languages"] = total_empty_all_langs
    report["summary"]["root_extension_sync_pass"] = sync_all_matched
    
    # Save result json
    out_path = os.path.join(os.path.dirname(__file__), "verify_translations_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print("=" * 70)
    print(f"I18N TRANSLATION VERIFICATION RESULT")
    print(f"en.json: {len(en_keys)} unique keys (raw keys: {en_raw_count}, duplicates: {en_dupes})")
    print("=" * 70)
    print(f"Codebase scan across all python files:")
    print(f"  - Unique keys found in t() calls: {len(code_keys)}")
    print(f"  - Keys in code but missing in en.json: {len(code_missing_in_en)}")
    print(f"  - Keys in en.json not found in code: {len(en_unused_in_code)}")
    print("-" * 70)
    print(f"{'Lang':<8} | {'Raw':<5} | {'Unique':<6} | {'Missing':<8} | {'Empty':<6} | {'Untranslated':<12} | {'Extra':<6}")
    print("-" * 70)
    for lang, stats in report["language_reports"].items():
        print(f"{lang:<8} | {stats['raw_key_count']:<5} | {stats['unique_keys']:<6} | {stats['missing_count']:<8} | {stats['empty_count']:<6} | {stats['untranslated_count']:<12} | {stats['extra_count']:<6}")
    print("-" * 70)
    print(f"Total Missing: {total_missing_all_langs}, Total Empty: {total_empty_all_langs}")
    print(f"Root vs Extension Sync: {'✅ 100% SHA-256 IDENTICAL (20/20)' if sync_all_matched else '❌ MISMATCH'}")
    print(f"Full report saved to: {out_path}")

if __name__ == "__main__":
    main()
