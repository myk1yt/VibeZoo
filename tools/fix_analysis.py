import ast

for path in ['mcp-servers/bridge/tools/analysis.py', 'extension/mcp-servers/bridge/tools/analysis.py']:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if explain_code is in content
    if 'def explain_code' in content:
        print('Found explain_code in', path)
        reg_str = 'def register(mcp):\n    """Analysis 도구 등록"""'
        review_str = '    @mcp.tool\n    def review_pr('
        reg_idx = content.find(reg_str)
        review_idx = content.find(review_str)
        if reg_idx != -1 and review_idx != -1:
            new_content = content[:reg_idx] + reg_str + '\n\n' + content[review_idx:]
            ast.parse(new_content)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print('Successfully cleaned explain_code and analyze_changes from', path)
        else:
            print('Indices:', reg_idx, review_idx)
    else:
        print('explain_code not found in', path)
