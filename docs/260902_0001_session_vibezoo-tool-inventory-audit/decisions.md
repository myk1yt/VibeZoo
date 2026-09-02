# User Decisions
## 2026-09-02 15:54

- "전면 정리 (A1-B3): 집계형 도구(find_bugs, suggest_refactor, generate_docs, learn_project)도 제거하고 프롬프트 조합으로 대체" → [ACTION: APPROVED — full cleanup scope]

## Approved Scope
1. **A1**: Remove deprecated `auto_analyze_whiteboard` tool (ux_coordinator.py)
2. **A2**: Delete dead code `github_diver.py` (both mcp-servers/ and extension/mcp-servers/ copies)
3. **A3**: Remove ghost entry `read_project_file` from vibezoo_mcp_bridge.py list_subagents + McpConfigService.ts alwaysAllow
4. **B1**: Merge `auto_analyze_after_drop` into `analyze_uploaded_file` (dropzone session tracking as parameter)
5. **B2**: Remove aggregate tools `find_bugs`, `suggest_refactor`, `generate_docs`, `learn_project` — replace with prompt-level composition

## Noted Asymmetry (VP flag)
`learn_project` (storage path) is removed while `recall_project` (retrieval path) stays. Defensible: recall is needed by agents/VP for context restoration; storage happens via auto-learn on startup. If user objects, restore learn_project.

## Out of Scope (kept)
- `recall_project`, `review_project`, `review_pr`, `apply_patch`, `fetch_page`/`web_search` — differentiated value per audit report
- B4 (extension/mcp-servers full sync audit) — separate future session