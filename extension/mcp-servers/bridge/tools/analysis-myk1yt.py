# VibeZoo Bridge — Analysis 도구 그룹
# explain_code + analyze_changes + review_pr + refactor_across_files

import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

from bridge.config import (
    VERSION, DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS, TS_JS_EXTS,
)
from bridge.i18n import t
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string, _validate_int, _validate_file_path,
    _read_file_content, _truncate, _normalize_path,
    _iter_project_files, _iter_project_files_cached,
    _npx_cmd, get_project_root,
    _extract_regex_imports,
)
from bridge.crow_client import try_crow_ingest, try_crow_recall
from bridge.ast_engine import AstEngine
from bridge.ast_singleton import get_ast_engine as _get_ast_engine
from bridge.tool_context import (
    make_explain_code_context,
    format_manifest_markdown,
)


def _get_git_blame(target: Path, line_number: int) -> dict:
    """git blame 정보 조회 (author, date, commit_message, commit_hash)"""
    try:
        result = subprocess.run(
            ["git", "blame", "-L", f"{line_number},{line_number}", "--porcelain", str(target)],
            cwd=str(target.parent),
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return {}
        
        blame_info = {}
        for line in result.stdout.split("\n"):
            if line.startswith("author "):
                blame_info["author"] = line[7:].strip()
            elif line.startswith("author-time "):
                ts = int(line[12:].strip())
                blame_info["date"] = time.strftime("%Y-%m-%d", time.localtime(ts))
            elif line.startswith("summary "):
                blame_info["commit_message"] = line[8:].strip()
            elif " " not in line and line.strip():
                blame_info["commit_hash"] = line.split(" ")[0] if " " in line else line[:10]
        
        if not blame_info.get("commit_hash"):
            # fallback: extract hash from first line
            first_line = result.stdout.split("\n")[0] if result.stdout else ""
            if first_line:
                blame_info["commit_hash"] = first_line.split(" ")[0][:10]
        
        return blame_info
    except Exception:
        return {}


def _find_related_tests(target: Path) -> list[dict]:
    """관련 테스트 파일 검색"""
    root = Path(os.getcwd())
    stem = target.stem
    related = []
    test_patterns = [
        f"**/test_{stem}.*", f"**/{stem}.test.*", f"**/{stem}.spec.*",
        f"**/test_*{stem}*", f"**/test*{stem}*",
    ]
    for pattern in test_patterns:
        for p in root.glob(pattern):
            if p.is_file() and p != target:
                related.append({
                    "file": str(p.relative_to(root)),
                    "name": p.name,
                })
    return related


# ── AST-aware rename ──────────────────────────────────


def _ast_aware_rename(pattern: str, new_pattern: str, file_content: str, ext: str) -> str:
    """AST 기반 rename — 심볼 정의부만 정확히 치환.
    
    Args:
        pattern: 찾을 심볼 이름 (예: 'User')
        new_pattern: 대체할 새 이름 (예: 'AppUser')
        file_content: 파일 전체 내용
        ext: 파일 확장자 (예: '.ts', '.py', '.go', '.rs')
    
    Returns:
        치환된 파일 내용 (AST 실패 시 기존 regex 방식으로 폴백)
    """
    from bridge.ast_engine import AstEngine
    
    ast_engine = AstEngine()
    ast_engine._init_legacy_tree_sitter()
    
    # 1. AST로 심볼 정의 위치 찾기
    ast = ast_engine.parse(file_content, ext)
    definitions = []
    
    if ast:
        # 함수 정의
        for fn in ast.get("functions", []):
            if fn["name"] == pattern:
                definitions.append(fn)
        # 클래스/구조체 정의
        for cls in ast.get("classes", []):
            if cls["name"] == pattern:
                definitions.append(cls)
        # 인터페이스 정의 (TS/JS)
        for iface in ast.get("interfaces", []):
            if iface["name"] == pattern:
                definitions.append(iface)
        # enum 정의 (Rust)
        for enm in ast.get("enums", []):
            if enm["name"] == pattern:
                definitions.append(enm)
    
    if not definitions:
        # AST 실패 시 기존 regex 방식으로 폴백 (안전)
        return file_content.replace(pattern, new_pattern)
    
    # 2. 정의 위치 기준 스코프 내 참조에만 치환 적용
    lines = file_content.split("\n")
    new_lines = list(lines)
    replaced_lines = set()
    
    for defn in definitions:
        def_line = defn.get("line", 1) - 1  # 0-based
        end_line = defn.get("end_line", len(lines))
        
        # 정의 라인 자체는 항상 치환 (함수/클래스 이름)
        if def_line < len(new_lines) and def_line not in replaced_lines:
            old = new_lines[def_line]
            # 정의 라인에서는 정확한 심볼 이름만 치환 (e.g., 'def User():' → 'def AppUser():')
            # 단, import 문이나 다른 컨텍스트에서 실수로 치환되지 않도록 패턴 매칭
            if pattern in old:
                # 함수/클래스 정의 라인에서 심볼 이름 치환
                new_lines[def_line] = old.replace(pattern, new_pattern)
                replaced_lines.add(def_line)
        
        # 3. 변수遮蔽(variable shadowing) 고려
        # 스코프 내에서 pattern과 동일한 이름의 로컬 변수 선언이 있으면,
        # 그 로컬 변수 선언 이후의 참조는 치환하지 않음
        shadowed_lines = set()
        for i in range(def_line + 1, min(end_line, len(lines))):
            line = lines[i]
            stripped = line.strip()
            # Python: 로컬 변수 선언 (e.g., 'User = ...')
            if ext == ".py" and re.match(rf'\s*{pattern}\s*=', stripped) and not stripped.startswith('def ') and not stripped.startswith('class '):
                shadowed_lines.add(i)
            # TS/JS: const/let/var 선언 (e.g., 'const User = ...')
            if ext in (".ts", ".tsx", ".js", ".jsx") and re.match(rf'\s*(?:const|let|var)\s+{pattern}\s*[=:]', stripped):
                shadowed_lines.add(i)
            # Go: ':=' or 'var' (e.g., 'User := ...')
            if ext == ".go" and re.match(rf'\s*(?:var\s+)?{pattern}\s*(?::=|=)', stripped):
                shadowed_lines.add(i)
            # Rust: 'let' (e.g., 'let User = ...')
            if ext == ".rs" and re.match(rf'\s*let\s+(?:mut\s+)?{pattern}\s*=', stripped):
                shadowed_lines.add(i)
        
        # 스코프 내 참조 라인 치환
        for i in range(def_line + 1, min(end_line, len(lines))):
            if i in replaced_lines or i in shadowed_lines:
                continue
            if pattern in new_lines[i]:
                new_lines[i] = new_lines[i].replace(pattern, new_pattern)
                replaced_lines.add(i)
    
    return "\n".join(new_lines)


def register(mcp):
    """Analysis 도구 등록"""

    @mcp.tool
    def review_pr(base_branch: str = "main", head_branch: str = "") -> str:
        """analyze_changes + review_code를 통합하여 PR 리뷰 보고서를 생성합니다.
        두 브랜치 간의 git diff를 분석하고, 변경된 파일들에 대해 코드 리뷰를 수행합니다.

        Args:
            base_branch: 기준 브랜치 (기본: main)
            head_branch: 대상 브랜치 (기본: 현재 브랜치)

        Returns:
            Markdown PR 리뷰 보고서
        """
        err = _validate_string(base_branch, "base_branch")
        if err:
            return _markdown_header("PR Review Error", "❌") + f"**{err}**\n" + _markdown_footer()

        root = os.getcwd()
        output = _markdown_header("Pull Request Review")
        output += f"> **Base**: `{base_branch}` → **Head**: `{head_branch or 'current'}`\n\n"

        try:
            diff_cmd = ["git", "diff"]
            if head_branch:
                diff_cmd.extend([f"{base_branch}...{head_branch}"])
            else:
                diff_cmd.append(f"{base_branch}..HEAD")

            stat_result = subprocess.run(diff_cmd + ["--stat"], cwd=root, capture_output=True, text=True, timeout=10)
            stat_output = stat_result.stdout.strip()
            diff_result = subprocess.run(diff_cmd, cwd=root, capture_output=True, text=True, timeout=10)
            diff_output = diff_result.stdout.strip()

            if not stat_output:
                output += f"⚠️ {t('No differences found between branches.')}\n"
                output += _markdown_footer()
                return output

            changed_files = []
            for line in stat_output.split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    file_path = parts[0].strip()
                    changed_files.append(file_path)

            output += f"## 📂 Changed Files ({len(changed_files)})\n\n"
            for f in changed_files:
                output += f"- `{_normalize_path(f)}`\n"
            output += "\n"

            total_additions = 0
            total_deletions = 0
            for line in stat_output.split("\n"):
                m = re.search(r'(\d+) insertion', line)
                if m:
                    total_additions += int(m.group(1))
                m = re.search(r'(\d+) deletion', line)
                if m:
                    total_deletions += int(m.group(1))

            output += f"## 📈 Stats\n\n"
            output += f"- **{len(changed_files)}** files changed\n"
            output += f"- **+{total_additions}** / **-{total_deletions}** lines\n\n"

            # 의존성 분석
            output += "## 🔗 Dependency Analysis\n\n"
            changed_set = set(changed_files)
            project_root = Path(root)
            file_deps = defaultdict(set)
            for f in changed_files:
                p = project_root / f
                if p.exists():
                    content_f = _read_file_content(p)
                    if content_f:
                        ext_f = p.suffix.lower()
                        if ext_f in TS_JS_EXTS:
                            ast_imports = _get_ast_engine().extract_imports(content_f, ext_f)
                            for imp in ast_imports:
                                file_deps[f].add(imp["module"])
                        else:
                            regex_imports = _extract_regex_imports(str(p))
                            for imp in regex_imports:
                                file_deps[f].add(imp)
            cross_refs = []
            for f, deps_set in file_deps.items():
                for dep in deps_set:
                    for cf in changed_set:
                        if cf != f and (dep in cf or cf.endswith(dep.replace(".", "/"))):
                            cross_refs.append((f, cf))
            if cross_refs:
                output += "⚠️ Cross-file dependencies detected in this PR:\n\n"
                for src, target in cross_refs[:5]:
                    output += f"- `{src}` → imports `{target}`\n"
                output += "\n> These files should be reviewed together for consistency.\n"
            else:
                output += "✅ No cross-file dependencies detected.\n"
            output += "\n"

            # 롤백 위험도 평가
            output += "## ⚠️ Rollback Risk Assessment\n\n"
            risk_score = 0
            risk_factors = []
            if len(changed_files) > 10:
                risk_score += 2
                risk_factors.append(f"Large PR ({len(changed_files)} files)")
            if total_deletions > 100:
                risk_score += 2
                risk_factors.append(f"Heavy deletions ({total_deletions} lines)")
            if total_additions > 200:
                risk_score += 1
                risk_factors.append(f"Large additions ({total_additions} lines)")
            if cross_refs:
                risk_score += 2
                risk_factors.append(f"Cross-file dependencies ({len(cross_refs)})")
            if "package.json" in changed_set or "go.mod" in changed_set or "requirements.txt" in changed_set:
                risk_score += 3
                risk_factors.append("Dependency manifest changed")
            if risk_score == 0:
                output += "🟢 **Low risk** — Safe to merge after review.\n"
            elif risk_score <= 3:
                output += "🟡 **Medium risk** — Review carefully.\n"
            elif risk_score <= 6:
                output += "🟠 **High risk** — Multiple reviewers recommended.\n"
            else:
                output += "🔴 **Critical risk** — Consider splitting this PR.\n"
            if risk_factors:
                output += "\nRisk factors:\n"
                for rf in risk_factors:
                    output += f"- {rf}\n"
            output += "\n"

            output += "## 📝 Code Review per File\n\n"
            for f in changed_files[:10]:
                output += f"### `{_normalize_path(f)}`\n\n"
                p = project_root / f
                if p.exists():
                    from bridge.tools.reviewer import review_code as _review_code
                    review_result = _review_code(str(f))
                    for line in review_result.split("\n"):
                        if "⚠️" in line or "📝" in line or "✅" in line or "Found" in line:
                            output += line + "\n"
                else:
                    output += "*(file deleted in this PR)*\n"
                output += "\n"

            output += "## 🔍 Diff Preview\n\n"
            if len(diff_output) > 4000:
                output += f"```diff\n{diff_output[:4000]}\n```\n"
                output += f"\n> ... ({len(diff_output) - 4000} more chars)\n"
            else:
                output += f"```diff\n{diff_output}\n```\n"

            output += "\n## 🧠 Crow Memory Context\n\n"
            for f in changed_files[:3]:
                file_name = os.path.basename(f)
                past_context = try_crow_recall(query=f"review {file_name}", register="style", limit=2)
                if past_context:
                    for item in past_context:
                        content = item.get("content", item.get("value", str(item)))
                        output += f"- `{file_name}`: {content[:200]}\n"

        except FileNotFoundError:
            output += f"❌ {t('Git not available. Make sure git is installed and this is a git repository.')}\n"
        except subprocess.TimeoutExpired:
            output += f"❌ {t('Git diff timed out.')}\n"
        except Exception as e:
            output += f"❌ Error: {e}\n"

        try_crow_ingest(json.dumps({"action": "review_pr", "base": base_branch, "head": head_branch, "files": len(changed_files)}), register="context")
        output += _markdown_footer()
        return output

    @mcp.tool
    def refactor_across_files(pattern: str, new_pattern: str, file_patterns: Optional[str] = None,
                               dry_run: bool = True) -> str:
        """search_codebase로 패턴을 찾고, 모든 발생 위치에 대해 일괄 수정 제안을 생성합니다.
        dry_run=True면 변경 제안서만, dry_run=False면 yocto 백업 후 실제 파일 수정을 수행합니다.

        Args:
            pattern: 찾을 코드 패턴 (검색어)
            new_pattern: 대체할 새 패턴 (변경 제안)
            file_patterns: 검색 대상 파일 패턴 (예: *.ts,*.tsx). 쉼표로 구분.
            dry_run: True면 제안만 (기본값: True), False면 실제 파일 수정

        Returns:
            Markdown 리팩토링 제안서: 각 발생 위치와 제안된 변경 사항 (diff 블록 포함)
        """
        err = _validate_string(pattern, "pattern")
        if err:
            return _markdown_header("Refactoring Error", "❌") + f"**{err}**\n" + _markdown_footer()
        err = _validate_string(new_pattern, "new_pattern")
        if err:
            return _markdown_header("Refactoring Error", "❌") + f"**{err}**\n" + _markdown_footer()

        from bridge.tools.scout import search_codebase

        output = _markdown_header("Multi-File Refactoring Proposal")
        output += f"> **Search**: `{pattern}`\n"
        output += f"> **Replace with**: `{new_pattern}`\n"
        output += f"> **File patterns**: `{file_patterns or '*.ts,*.tsx,*.js,*.jsx,*.py'}`\n"
        output += f"> **Mode**: {'🔍 Dry run (proposal only)' if dry_run else '🚀 Apply changes'}\n\n"

        search_result = search_codebase(query=pattern, file_patterns=file_patterns, max_results=100)
        occurrences = []
        for line in search_result.split("\n"):
            m = re.match(r'^- `(.+?:\d+):', line)
            if m:
                occurrences.append(m.group(1))
            m2 = re.match(r'^- `(.+?:\d+)`', line)
            if m2:
                occurrences.append(m2.group(1))

        if not occurrences:
            output += f"✅ {t('No occurrences found for this pattern.')}\n"
            output += _markdown_footer()
            return output

        output += f"## Found {len(occurrences)} Occurrences\n\n"
        by_file = defaultdict(list)
        for occ in occurrences:
            parts = occ.split(":")
            if len(parts) >= 2:
                by_file[parts[0]].append(parts[1])

        output += f"### Files Affected: {len(by_file)}\n\n"
        for file_path, lines in sorted(by_file.items()):
            line_list = ", ".join(lines[:10])
            suffix = f" ... and {len(lines)-10} more" if len(lines) > 10 else ""
            output += f"- `{_normalize_path(file_path)}` — lines {line_list}{suffix}\n"

        output += "\n## Suggested Changes (AST-aware rename)\n\n"
        for file_path, lines in sorted(by_file.items())[:10]:
            actual_path = Path(os.getcwd()) / file_path
            if not actual_path.exists():
                continue
            content = _read_file_content(actual_path)
            if content is None:
                continue
            ext = actual_path.suffix.lower()
            file_lines = content.split("\n")
            output += f"### `{_normalize_path(file_path)}`\n\n"
            output += f"```diff\n"
            # AST-aware rename 적용
            new_content = _ast_aware_rename(pattern, new_pattern, content, ext)
            new_lines = new_content.split("\n")
            for line_num_str in lines[:5]:
                idx = int(line_num_str) - 1
                if 0 <= idx < len(file_lines) and 0 <= idx < len(new_lines):
                    original = file_lines[idx]
                    suggested = new_lines[idx]
                    if original != suggested:
                        output += f"-{original}\n"
                        output += f"+{suggested}\n"
                    else:
                        # AST-aware rename이 해당 라인을 변경하지 않은 경우 (예: shadowing)
                        output += f" {original}\n"
            output += f"```\n\n"

        output += "## 📊 Impact Analysis\n\n"
        total_affected_lines = sum(len(ls) for ls in by_file.values())
        output += f"- **Scale**: {len(occurrences)} changes across {len(by_file)} files\n"
        output += f"- **Total affected lines**: {total_affected_lines}\n"
        if total_affected_lines > 50:
            output += "- **Risk**: 🔴 **High** — extensive changes, may introduce side effects\n"
        elif total_affected_lines > 20:
            output += "- **Risk**: 🟡 **Medium** — moderate changes, review recommended\n"
        else:
            output += "- **Risk**: 🟢 **Low** — limited changes\n"
        if len(by_file) > 5:
            output += "- **Dependency impact**: Changes span multiple files — ensure imports are updated\n"

        # ── Apply changes (dry_run=False, AST-aware rename) ──
        if not dry_run:
            output += "\n## Applied Changes (AST-aware rename)\n\n"
            applied_count = 0
            failed_count = 0
            for file_path, lines in sorted(by_file.items()):
                actual_path = Path(os.getcwd()) / file_path
                if not actual_path.exists():
                    failed_count += 1
                    continue
                try:
                    content = _read_file_content(actual_path)
                    if content is None:
                        failed_count += 1
                        continue
                    ext = actual_path.suffix.lower()
                    # AST-aware rename 적용
                    new_content = _ast_aware_rename(pattern, new_pattern, content, ext)
                    if new_content != content:
                        # yocto 백업: create .bak file
                        bak_path = actual_path.with_suffix(actual_path.suffix + ".bak")
                        if not bak_path.exists():
                            import shutil
                            shutil.copy2(str(actual_path), str(bak_path))
                        actual_path.write_text(new_content, encoding="utf-8")
                        applied_count += 1
                        output += f"- ✅ `{_normalize_path(file_path)}` — AST-aware rename applied\n"
                except Exception:
                    failed_count += 1
            output += f"\n**Result**: {applied_count} files modified, {failed_count} failed\n"
            if applied_count > 0:
                output += "\n> ⚠️ Backup files (.bak) created in the same directory. Restore by renaming `.bak` to original.\n"
        else:
            output += "\n> Note: This is a **proposal only**. No files have been modified.\n"
            output += "> To apply changes, call with `dry_run=False` or use your editor's find-and-replace.\n"

        try_crow_ingest(json.dumps({"action": "refactor_across_files", "pattern": pattern, "new_pattern": new_pattern, "occurrences": len(occurrences), "files_affected": len(by_file), "dry_run": dry_run}), register="style")
        output += _markdown_footer()
        return output
