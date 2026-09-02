# VibeZoo Bridge — Fix Loop 도구 그룹
# auto_fix_status + retry_build + check_intervention

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Optional

from bridge.config import (
    VERSION, FIX_REQUEST_FILE, WHITEBOARD_FILE, CHAT_PENDING_FILE,
)
from bridge.i18n import t
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _truncate, _atomic_write_json, _npx_cmd,
)
from bridge.crow_client import try_crow_ingest, try_crow_recall


def _extract_build_errors(build_output: str) -> list[dict]:
    """빌드 출력에서 에러/경고 부분만 추출.

    지원 패턴:
    - TS/JS: "error TS2322: ..."
    - Python: "SyntaxError:", "ImportError:", "  File ..., line N"
    - Go: "undefined:", "cannot use", "expected"
    - Generic: "Error:", "ERROR:", "Warning:", "WARNING:"

    Returns:
        list[{"type": "error"|"warning", "file": "...", "line": N, "message": "..."}]
    """
    results = []
    lines = build_output.split("\n")

    # TS/JS: "error TS2322: ..."
    ts_pattern = re.compile(
        r'^(?:.*?\.(?:ts|tsx|js|jsx))\(\s*(\d+)\s*,\s*\d+\s*\)\s*:\s*(error|warning)\s+(TS\d+)\s*:\s*(.+)$'
    )
    # Python: "  File ..., line N"
    py_file_pattern = re.compile(r'^\s*File\s+"([^"]+)",\s+line\s+(\d+)')
    # Go: "undefined:", "cannot use"
    go_pattern = re.compile(
        r'^(?:.*?\.go):(\d+):\s*(undefined|cannot use|expected|not used)\b(.+)$'
    )
    # Generic: "Error:", "ERROR:", "Warning:", "WARNING:"
    generic_error = re.compile(r'^(.*?):\s*(Error|ERROR|error)\s*:\s*(.+)$')
    generic_warning = re.compile(r'^(.*?):\s*(Warning|WARNING|warning)\s*:\s*(.+)$')

    i = 0
    while i < len(lines):
        line = lines[i]
        entry = None

        # TS/JS
        m = ts_pattern.match(line)
        if m:
            entry = {
                "type": "error" if m.group(2) == "error" else "warning",
                "file": m.group(1),
                "line": int(m.group(1)),
                "message": f"{m.group(3)}: {m.group(4).strip()}",
            }

        # Python syntax errors: "SyntaxError:", "ImportError:" on its own line
        if not entry:
            py_err_match = re.match(
                r'^\s*(SyntaxError|ImportError|IndentationError|NameError|TypeError|ValueError|KeyError|AttributeError|ModuleNotFoundError|FileNotFoundError|OSError|RuntimeError|ZeroDivisionError|StopIteration|FloatingPointError)(.*)$',
                line
            )
            if py_err_match:
                err_type = py_err_match.group(1)
                err_detail = py_err_match.group(2).strip()
                # Look backwards for File line
                file_info = ""
                line_num = 0
                for j in range(i - 1, max(-1, i - 3), -1):
                    fm = py_file_pattern.match(lines[j])
                    if fm:
                        file_info = fm.group(1)
                        line_num = int(fm.group(2))
                        break
                entry = {
                    "type": "error",
                    "file": file_info,
                    "line": line_num,
                    "message": f"{err_type}: {err_detail}",
                }

        # Go
        if not entry:
            m = go_pattern.match(line)
            if m:
                entry = {
                    "type": "error",
                    "file": m.group(1),
                    "line": int(m.group(2)),
                    "message": f"{m.group(3)}{m.group(4).strip()}",
                }

        # Generic
        if not entry:
            m = generic_error.match(line)
            if m:
                entry = {
                    "type": "error",
                    "file": m.group(1),
                    "line": 0,
                    "message": m.group(3).strip(),
                }
        if not entry:
            m = generic_warning.match(line)
            if m:
                entry = {
                    "type": "warning",
                    "file": m.group(1),
                    "line": 0,
                    "message": m.group(3).strip(),
                }

        if entry:
            results.append(entry)
        i += 1

    return results


def register(mcp):
    """Fix Loop 도구 등록"""

    @mcp.tool
    def auto_fix_status() -> str:
        """현재 진행 중인 Auto-Fix 세션의 상태와 에러 정보를 조회합니다.
        LLM이 빌드 에러를 분석하고 수정을 시작할 때 호출합니다.
        과거 유사 에러 패턴을 Crow Memory에서 조회하여 함께 반환합니다.

        Returns:
            JSON: { status, attempt, maxAttempts, diagnostics, history, pastFixes }
        """
        if not os.path.exists(FIX_REQUEST_FILE):
            return json.dumps({"status": "idle", "message": t("No active fix request"), "timestamp": time.time()})

        try:
            with open(FIX_REQUEST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["status"] = "in_progress"
            data["lastReadAt"] = time.time()

            _atomic_write_json(FIX_REQUEST_FILE, data, indent=2)

            error_code = ""
            if data.get("history"):
                last = data["history"][-1]
                if last.get("diagnostics"):
                    error_code = last["diagnostics"][0].get("code", "")
            if error_code:
                past_fixes = try_crow_recall(
                    query=f"build error {error_code}",
                    register="bug",
                    limit=3
                )
                if past_fixes:
                    data["pastFixes"] = past_fixes

            data["version"] = VERSION
            data["timestamp"] = time.time()
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "status": "error", "message": str(e),
                "timestamp": time.time(), "version": VERSION
            })

    @mcp.tool
    def retry_build(build_command: Optional[str] = None) -> str:
        """빌드를 재실행하고 결과를 반환합니다.
        LLM이 수정 코드를 적용한 후 빌드 성공 여부를 확인할 때 호출합니다.

        Args:
            build_command: 빌드 명령어 (지정 시 우선, 없으면 자동 감지)

        Returns:
            JSON: { exitCode, stdout, stderr, success, diagnostics }
        """
        root = os.getcwd()

        if build_command:
            cmd = build_command.split()
        else:
            pkg_json = Path(root) / "package.json"
            if pkg_json.exists():
                cmd = [_npx_cmd(), "tsc", "--noEmit"]
            else:
                return json.dumps({
                    "exitCode": -1,
                    "diagnostics": [],
                    "success": False,
                    "error": t("No build command detected (package.json not found)"),
                    "timestamp": time.time(),
                })

        try:
            result = subprocess.run(
                cmd,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=60
            )

            if os.path.exists(FIX_REQUEST_FILE):
                try:
                    with open(FIX_REQUEST_FILE) as f:
                        fix_data = json.load(f)
                    attempt_num = len(fix_data.get("history", [])) + 1
                    if "history" not in fix_data:
                        fix_data["history"] = []
                    fix_data["history"].append({
                        "attempt": attempt_num,
                        "exitCode": result.returncode,
                        "stderr": result.stderr[-500:],
                        "stdout": result.stdout[-500:],
                        "fixApplied": None,
                        "timestamp": time.time()
                    })
                    fix_data["attempt"] = attempt_num
                    if result.returncode == 0:
                        fix_data["status"] = "resolved"
                    else:
                        fix_data["status"] = "pending" if attempt_num < fix_data.get("maxAttempts", 3) else "abandoned"
                    _atomic_write_json(FIX_REQUEST_FILE, fix_data, indent=2)

                    if result.returncode != 0:
                        try_crow_ingest(
                            json.dumps({
                                "error": result.stderr[-500:],
                                "exitCode": result.returncode,
                                "attempt": attempt_num,
                            }),
                            register="bug"
                        )
                except Exception:
                    pass

            # ── 에러/경고 추출 ──
            combined = result.stdout + "\n" + result.stderr
            errors = _extract_build_errors(combined)
            error_items = [e for e in errors if e["type"] == "error"]
            warning_items = [e for e in errors if e["type"] == "warning"]

            # 출력에 에러/경고 섹션 추가
            extracted_section = ""
            if error_items:
                extracted_section += "### Errors\n\n"
                for e in error_items[:15]:
                    file_part = f" `{e['file']}:{e['line']}`" if e.get("file") else ""
                    extracted_section += f"-{file_part}: {e['message'][:200]}\n"
                if len(error_items) > 15:
                    extracted_section += f"- ... +{len(error_items)-15} more\n"

            if warning_items:
                extracted_section += "\n### Warnings\n\n"
                for w in warning_items[:10]:
                    file_part = f" `{w['file']}:{w['line']}`" if w.get("file") else ""
                    extracted_section += f"-{file_part}: {w['message'][:200]}\n"
                if len(warning_items) > 10:
                    extracted_section += f"- ... +{len(warning_items)-10} more\n"

            return json.dumps({
                "exitCode": result.returncode,
                "stdout": _truncate(result.stdout, 2000),
                "stderr": _truncate(result.stderr, 2000),
                "success": result.returncode == 0,
                "errors": error_items[:20],
                "warnings": warning_items[:20],
                "extracted": extracted_section.strip(),
                "error_count": len(error_items),
                "warning_count": len(warning_items),
                "timestamp": time.time(),
            }, indent=2, ensure_ascii=False)

        except subprocess.TimeoutExpired:
            return json.dumps({
                "exitCode": -1,
                "success": False,
                "error": t("Build timed out after 60s"),
                "timestamp": time.time(),
            })
        except Exception as e:
            return json.dumps({
                "exitCode": -1,
                "success": False,
                "error": str(e),
                "timestamp": time.time(),
            })

    @mcp.tool
    def check_intervention() -> str:
        """Auto-Fix Loop 진행 전 사용자 개입 여부를 확인합니다.
        Whiteboard 상태와 대기 중인 채팅 메시지를 조회합니다.

        Returns:
            JSON: { whiteboard_annotations, pending_messages, user_guidance, should_pause }
        """
        result = {
            "whiteboard_annotations": [],
            "pending_messages": [],
            "user_guidance": None,
            "should_pause": False,
            "timestamp": time.time(),
        }

        if os.path.exists(WHITEBOARD_FILE):
            try:
                with open(WHITEBOARD_FILE) as f:
                    wb_data = json.load(f)
                for cmd in wb_data.get("commands", []):
                    if cmd.get("type") == "text":
                        result["whiteboard_annotations"].append({
                            "text": cmd.get("props", {}).get("text", ""),
                            "position": {
                                "left": cmd.get("props", {}).get("left", 0),
                                "top": cmd.get("props", {}).get("top", 0)
                            }
                        })
            except Exception:
                pass

        if os.path.exists(CHAT_PENDING_FILE):
            try:
                with open(CHAT_PENDING_FILE) as f:
                    pending = json.load(f)
                result["pending_messages"] = pending.get("messages", [])
                os.remove(CHAT_PENDING_FILE)
            except Exception:
                pass

        if result["whiteboard_annotations"] or result["pending_messages"]:
            guidance_parts = []
            if result["whiteboard_annotations"]:
                guidance_parts.append(t("Whiteboard annotations found"))
            if result["pending_messages"]:
                guidance_parts.append(t("Pending chat messages found"))
            result["user_guidance"] = "; ".join(guidance_parts)
            result["should_pause"] = bool(result["pending_messages"])

        return json.dumps(result, indent=2, ensure_ascii=False)
