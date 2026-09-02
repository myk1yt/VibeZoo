import json

with open('docs/260830_0001_session_reinstall-recovery-and-quality/tools/detailed_diff_analysis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print('================ SUMMARY ================')
print(f"Root files: {d['summary']['root_total_files']}")
print(f"Ext files : {d['summary']['ext_total_files']}")
print(f"Root only : {d['summary']['root_only_files']}")
print(f"Ext only  : {d['summary']['ext_only_files']}")
print(f"Identical : {d['summary']['identical_count']}")
print(f"Different : {d['summary']['different_count']}")

print('\n================ ROOT ONLY DETAILS ================')
for k, v in d['root_only_details'].items():
    print(f"{k}: size={v['size']}, lines={v['line_count']}, mtime={v['mtime']}")

print('\n================ EXT ONLY DETAILS ================')
for k, v in d['ext_only_details'].items():
    print(f"{k}: size={v['size']}, lines={v['line_count']}, mtime={v['mtime']}")

print('\n================ DIFFERENT FILES (22 files) ================')
for k, v in d['different_analyses'].items():
    print(f"\n--- {k} ---")
    print(f"  Root: size={v['root_size']}, lines={v['root_lines']}, mtime={v['root_mtime']}, ver={v['root_version']}")
    print(f"  Ext : size={v['ext_size']}, lines={v['ext_lines']}, mtime={v['ext_mtime']}, ver={v['ext_version']}")
    print(f"  Git Root: {v['root_git']}")
    print(f"  Git Ext : {v['ext_git']}")
    if v['root_only_tools'] or v['ext_only_tools']:
        print(f"  * TOOLS DIFF -> Root only: {v['root_only_tools']}, Ext only: {v['ext_only_tools']}")
    if v['root_only_funcs'] or v['ext_only_funcs']:
        print(f"  * FUNCS DIFF -> Root only: {v['root_only_funcs']}, Ext only: {v['ext_only_funcs']}")
    if v['root_only_classes'] or v['ext_only_classes']:
        print(f"  * CLASSES DIFF -> Root only: {v['root_only_classes']}, Ext only: {v['ext_only_classes']}")
    print(f"  Diff line count: {v['diff_line_count']}")

print('\n================ GIT STATUS MCP ================')
for l in d['git_status_mcp']:
    print(l)

print('\n================ CONFIG REFERENCES ================')
for cr in d['config_references']:
    print(cr)

print('\n================ GLOBAL MCP FINDINGS ================')
for gf in d['global_mcp_findings']:
    print(gf['path'], "exists:", gf['exists'], "has_vibezoo:", gf.get('has_vibezoo'))
