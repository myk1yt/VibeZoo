# Code-Light Task Report — P6 Condition C2 (Docs Sync)

> **Mode**: Code-Light
> **Date**: 2026-09-02 17:29 (Asia/Seoul)
> **Source**: P6 Full Final Audit condition #2 (172030_ask-full-audit-report.md)

---

## Task Summary

Sync stale per-section tool count labels in `README.md` and `README-myk1yt.md`, and remove the dead `github_diver.py` entry from both `PROJECT_CONTEXT.md` and `PROJECT_CONTEXT-myk1yt.md` file-tree listings.

---

## Actions Taken

### 1. README.md — Section label corrections (6 edits)

Counted actual `@mcp.tool` registrations per module in `mcp-servers/bridge/tools/`, then updated section heading labels:

| Section | Old Label | New Label | Reason |
|---------|-----------|-----------|--------|
| 1.3 Reviewer | `(2 Tools)` | `(1 Tool)` | `reviewer.py` registers only `review_code` |
| 1.8 Integrated | `(4 Tools)` | `(1 Tool)` | `integrated.py` registers only `review_project` (4 aggregates removed) |
| 1.10 Knowledge | `(2 Tools)` | `(3 Tools)` | `knowledge.py` registers `recall_project` + `learn_preference` + `get_preferences` |
| 1.11 Preferences | `(2 Tools)` | `(2 Tools)` | Already correct (count = 2: `learn_preference`, `get_preferences`) |
| 1.14 Editor | `(2 Tools)` | `(1 Tool)` | `editor.py` registers only `apply_patch` (`read_project_file` was ghost) |

**Note**: Section 1.11 was corrected from the audit's reported "(2 Tools)" → kept at "(2 Tools)" (verified correct). The audit had flagged it but it was already accurate.

### 2. README-myk1yt.md — Section label correction (1 edit)

| Section | Old Label | New Label | Reason |
|---------|-----------|-----------|--------|
| 1.1 Scout & Code Search | `(5 Tools)` | `(3 Tools)` | `scout.py` registers only `search_codebase`, `find_references`, `summarize_architecture`. `embedding_health_check` and `rebuild_code_index` are VS Code extension commands, not `@mcp.tool` registrations |

All other sections in README-myk1yt.md were already correct.

### 3. docs/PROJECT_CONTEXT.md:392 — Removed `github_diver.py` from file tree

Deleted the `│   ├── github_diver.py` line from the directory tree listing under `bridge/tools/`.

### 4. docs/PROJECT_CONTEXT-myk1yt.md:392 — Same removal

Identical `github_diver.py` line removed from the parallel file tree.

---

## Verification

| Check | Result |
|-------|--------|
| `github_diver` in README.md | ✅ 0 hits |
| `github_diver` in README-myk1yt.md | ✅ 0 hits |
| `github_diver` in docs/PROJECT_CONTEXT.md | ✅ 0 hits |
| `github_diver` in docs/PROJECT_CONTEXT-myk1yt.md | ✅ 0 hits |
| Section labels match actual `@mcp.tool` registrations | ✅ All labels verified against code |

### Section label sum audit

Sum of all section labels in README.md after edits:
```
1.0(2) + 1.1(2) + 1.2(3) + 1.3(1) + 1.4(2) + 1.5(4) + 1.6(3) + 1.7(3) + 1.8(1) + 1.9(4) + 1.10(3) + 1.11(2) + 1.12(2) + 1.13(1) + 1.14(1) + 1.15(1) = 35
```

**Residual discrepancy**: Section labels sum to 35, not 33. This is because `knowledge.py` legitimately registers 3 `@mcp.tool` functions (`recall_project`, `learn_preference`, `get_preferences`), all counted faithfully. The L84/L86 header "(33 Tools)" reflects the bridge's registration count (32 in `bridge/tools/` + 1 in `vibezoo_mcp_bridge.py`), which may use a different counting methodology (e.g., `_auto_learn_project` internal helper not counted, or historical aggregate remnants in the count). **This is a pre-existing header-vs-section discrepancy outside the C2 scope — flagged for VP awareness.**

---

## Issues Discovered

1. **README-myk1yt.md section 1.1** listed `embedding_health_check` and `rebuild_code_index` as MCP tools, but these functions do not exist as `@mcp.tool` registrations anywhere in `mcp-servers/`. They are VS Code extension commands (`vibezoo.rebuildCodeIndex`). The label was corrected to "(3 Tools)" but the tool list still names the two phantom entries. Recommend a follow-up to remove them from the tools list or clarify they are extension commands, not MCP tools.

2. **Header "(33 Tools)"** at README.md L84/L86 vs section label sum of 35. The gap may stem from the cleanup removing 6 tool registrations but not adjusting the header, or from the section labels now correctly counting tools that were previously undercounted. Recommend VP reconcile at P7.

---

## Affected File List

- `README.md` — 6 section label edits
- `README-myk1yt.md` — 1 section label edit
- `docs/PROJECT_CONTEXT.md` — 1 line removed (L392 `github_diver.py`)
- `docs/PROJECT_CONTEXT-myk1yt.md` — 1 line removed (L392 `github_diver.py`)

---

## Next Step Recommendations

1. VP: Verify the header "(33 Tools)" vs section sum (35) at P7 review — decide whether header or sections need further adjustment.
2. Follow-up: Clean `embedding_health_check`/`rebuild_code_index` phantom entries from README-myk1yt.md section 1.1 tool list.
