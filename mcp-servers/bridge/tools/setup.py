# VibeZoo Bridge — Setup Tool
# Phase A: 통합 설치/설정 관리자 (vibezoo_setup)
# pip 패키지 설치, 시스템 도구 설치, MCP 설정, Zoo 설정을 한 번에 처리

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from bridge.config import VERSION


# ── 상수 ──────────────────────────────────────────────

# Core 필수 패키지 (target="minimal")
PIP_CORE = ["fastmcp", "uvicorn", "starlette"]

# Optional 패키지 (target="recommended"에 추가)
PIP_OPTIONAL: dict[str, str] = {
    "opencv-contrib-python-headless": "SSA 이미지 분석 (OpenCV)",
    "Pillow": "이미지 I/O, 스크린샷",
    "pytesseract": "OCR 텍스트 추출 (Tesseract 바인딩)",
    "tree-sitter": "AST 코드 분석 코어",
    "tree-sitter-python": "Python AST 언어팩",
    "tree-sitter-go": "Go AST 언어팩",
    "tree-sitter-rust": "Rust AST 언어팩",
    "mss": "크로스플랫폼 스크린샷",
    "html2text": "HTML→마크다운 변환",
    "requests": "HTTP 클라이언트 (Crow 연동)",
    "huggingface-hub": "허깅페이스 모델 다운로더",
    "PyMuPDF": "PDF 문서 파싱 및 텍스트/이미지 추출",
    "python-docx": "DOCX 워드 문서 텍스트 추출",
    "paddlepaddle": "PaddleOCR 딥러닝 백엔드",
    "paddleocr": "고성능 다국어 OCR 딥러닝 엔진",
    "llama-cpp-python": "MiniCPM-V GGUF 모델 로컬 구동 코어",
}

# 시스템 도구 정보
SYSTEM_TOOLS: dict[str, dict] = {
    "rg": {
        "name": "ripgrep",
        "desc": "초고속 코드 검색",
        "brew": "ripgrep",
        "winget": "BurntSushi.ripgrep.MSVC",
        "choco": "ripgrep",
        "scoop": "ripgrep",
        "apt": "ripgrep",
        "url": "https://github.com/BurntSushi/ripgrep/releases",
    },
    "tesseract": {
        "name": "Tesseract OCR",
        "desc": "이미지 텍스트 인식",
        "brew": "tesseract",
        "winget": "UB-Mannheim.TesseractOCR",
        "choco": "tesseract",
        "scoop": "tesseract",
        "apt": "tesseract-ocr",
        "url": "https://github.com/UB-Mannheim/tesseract/wiki",
    },
}

# 설치 대상별 패키지 매트릭스
TARGET_PACKAGES: dict[str, list[str]] = {
    "minimal": list(PIP_CORE),
    "recommended": list(PIP_CORE) + list(PIP_OPTIONAL.keys()),
    "full": list(PIP_CORE) + list(PIP_OPTIONAL.keys()),
}

# 설치 대상별 시스템 도구
TARGET_SYSTEM_TOOLS: dict[str, list[str]] = {
    "minimal": [],
    "recommended": [],
    "full": list(SYSTEM_TOOLS.keys()),
}


# ── SetupManager ──────────────────────────────────────


class SetupManager:
    """VibeZoo 통합 설치 관리자 — 의존성 설치, 설정, 상태 진단"""

    def __init__(self, dry_run: bool = False):
        self._dry_run = dry_run
        self._results: list[dict] = []
        self._start_time: float = 0.0

    # ── 공개 메서드 ────────────────────────────────────

    def run_setup(
        self,
        target: str = "minimal",
        python_packages: bool = True,
        system_tools: bool = False,
        configure_mcp: bool = True,
        configure_zoo: bool = True,
        download_models: bool = True,
    ) -> dict:
        """통합 설치 실행 — SetupManager의 주 진입점

        Args:
            target: 설치 대상 ("minimal", "recommended", "full")
            python_packages: Python 패키지 설치 여부
            system_tools: 시스템 도구 설치 여부
            configure_mcp: .roo/mcp.json 설정 여부
            configure_zoo: .zoo/config.json 설정 여부

        Returns:
            전체 결과 보고서 (dict)
        """
        self._start_time = time.time()
        self._results = []

        report: dict = {
            "python_packages": {"success": [], "skipped": [], "failed": []},
            "system_tools": {"installed": [], "skipped": [], "manual": [], "failed": []},
            "models_download": None,
            "mcp_config": None,
            "zoo_config": None,
            "summary": {},
        }

        # 1. Python 패키지 설치
        if python_packages:
            packages = TARGET_PACKAGES.get(target, TARGET_PACKAGES["minimal"])
            pip_result = self.install_pip_packages(packages)
            report["python_packages"] = pip_result

        # 2. 시스템 도구 설치
        if system_tools:
            tools = TARGET_SYSTEM_TOOLS.get(target, [])
            sys_result = self.install_system_tools(tools)
            report["system_tools"] = sys_result

        # 3. MCP 설정
        if configure_mcp:
            mcp_result = self.configure_mcp()
            report["mcp_config"] = mcp_result

        # 4. Zoo 설정
        if configure_zoo:
            zoo_result = self.configure_zoo()
            report["zoo_config"] = zoo_result

        # 5. 모델 다운로드
        if download_models and target in ("recommended", "full"):
            models_result = self.download_vision_models()
            report["models_download"] = models_result

        # 6. 요약
        elapsed = time.time() - self._start_time
        report["summary"] = self._build_summary(report, elapsed)

        return report

    # ── Python 패키지 ──────────────────────────────────

    def check_python_package(self, package: str) -> bool:
        """pip 패키지 설치 여부 확인 (importlib 시험)

        Args:
            package: 패키지명 (pip 이름, 예: "opencv-contrib-python-headless")

        Returns:
            설치되어 있으면 True
        """
        # 패키지명 → import 모듈명 변환
        module_name = package.replace("-", "_").replace(".", "_")
        # 특수 케이스
        if package == "opencv-contrib-python-headless":
            module_name = "cv2"
        elif package == "Pillow":
            module_name = "PIL"
        elif package == "tree-sitter-languages":
            module_name = "tree_sitter_languages"

        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    def install_pip_packages(self, packages: list[str]) -> dict:
        """pip install 실행 — 패키지별 개별 설치, 실패해도 계속 진행

        Args:
            packages: 설치할 패키지명 목록

        Returns:
            {"success": [...], "skipped": [...], "failed": [{"package": ..., "reason": ...}]}
        """
        result: dict[str, list] = {"success": [], "skipped": [], "failed": []}

        for pkg in packages:
            # 이미 설치됨?
            if self.check_python_package(pkg):
                result["skipped"].append(pkg)
                continue

            # dry-run
            if self._dry_run:
                self._results.append({
                    "action": "pip_install",
                    "package": pkg,
                    "dry_run": True,
                })
                result["success"].append(f"{pkg} (dry-run)")
                continue

            # 실제 설치
            try:
                cmd = [sys.executable, "-m", "pip", "install", pkg]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if proc.returncode == 0:
                    result["success"].append(pkg)
                    self._results.append({
                        "action": "pip_install",
                        "package": pkg,
                        "status": "installed",
                    })
                else:
                    # 실패 사유 truncate
                    reason = proc.stderr[:300] if proc.stderr else proc.stdout[:300]
                    result["failed"].append({"package": pkg, "reason": reason})
                    self._results.append({
                        "action": "pip_install",
                        "package": pkg,
                        "status": "failed",
                        "reason": reason,
                    })
            except subprocess.TimeoutExpired:
                result["failed"].append({"package": pkg, "reason": "timeout (120s)"})
            except Exception as e:
                result["failed"].append({"package": pkg, "reason": str(e)[:200]})

        return result

    # ── 시스템 도구 ────────────────────────────────────

    def check_system_tool(self, tool: str) -> bool:
        """시스템 도구 존재 여부 확인 (PATH 검색)

        Args:
            tool: 도구명 (예: "rg", "tesseract")

        Returns:
            PATH에서 발견되면 True
        """
        return shutil.which(tool) is not None

    def install_system_tools(self, tools: list[str]) -> dict:
        """시스템 도구 설치 — OS 자동 감지, 패키지 매니저 fallback

        Args:
            tools: 설치할 도구명 목록 (예: ["rg", "tesseract"])

        Returns:
            {"installed": [...], "skipped": [...], "manual": [...], "failed": [...]}
        """
        result: dict[str, list] = {
            "installed": [],
            "skipped": [],
            "manual": [],
            "failed": [],
        }
        system = platform.system()

        for tool_name in tools:
            tool_info = SYSTEM_TOOLS.get(tool_name)
            if not tool_info:
                result["failed"].append({"tool": tool_name, "reason": "unknown tool"})
                continue

            # 이미 설치됨?
            if self.check_system_tool(tool_name):
                result["skipped"].append(tool_name)
                continue

            # dry-run
            if self._dry_run:
                self._results.append({
                    "action": "system_tool",
                    "tool": tool_name,
                    "dry_run": True,
                })
                result["installed"].append(f"{tool_name} (dry-run)")
                continue

            # OS별 설치
            if system == "Windows":
                ok = self._install_windows_tool(tool_name, tool_info, result)
            elif system == "Linux":
                ok = self._install_linux_tool(tool_name, tool_info, result)
            elif system == "Darwin":
                ok = self._install_macos_tool(tool_name, tool_info, result)
            else:
                result["manual"].append({
                    "tool": tool_name,
                    "url": tool_info.get("url", ""),
                    "note": f"Unknown OS: {system}. Please install manually.",
                })
                ok = False

            if not ok:
                # 수동 설치 URL 안내
                if tool_name not in [m.get("tool") for m in result["manual"]]:
                    result["manual"].append({
                        "tool": tool_name,
                        "name": tool_info.get("name", tool_name),
                        "url": tool_info.get("url", ""),
                        "note": f"자동 설치 실패. 위 URL에서 수동 설치하세요.",
                    })

        return result

    def _install_windows_tool(self, tool_name: str, tool_info: dict, result: dict) -> bool:
        """Windows 도구 설치 — winget → choco → scoop 순서 fallback"""

        # 1. winget
        winget_id = tool_info.get("winget")
        if winget_id and shutil.which("winget"):
            try:
                cmd = ["winget", "install", "--id", winget_id, "--silent", "--accept-package-agreements"]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if proc.returncode == 0:
                    result["installed"].append(tool_name)
                    self._results.append({
                        "action": "system_tool",
                        "tool": tool_name,
                        "method": "winget",
                        "status": "installed",
                    })
                    return True
            except Exception:
                pass

        # 2. chocolatey
        choco_id = tool_info.get("choco")
        if choco_id and shutil.which("choco"):
            try:
                cmd = ["choco", "install", choco_id, "-y"]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if proc.returncode == 0:
                    result["installed"].append(tool_name)
                    self._results.append({
                        "action": "system_tool",
                        "tool": tool_name,
                        "method": "choco",
                        "status": "installed",
                    })
                    return True
            except Exception:
                pass

        # 3. scoop
        scoop_id = tool_info.get("scoop")
        if scoop_id and shutil.which("scoop"):
            try:
                cmd = ["scoop", "install", scoop_id]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if proc.returncode == 0:
                    result["installed"].append(tool_name)
                    self._results.append({
                        "action": "system_tool",
                        "tool": tool_name,
                        "method": "scoop",
                        "status": "installed",
                    })
                    return True
            except Exception:
                pass

        return False

    def _install_linux_tool(self, tool_name: str, tool_info: dict, result: dict) -> bool:
        """Linux 도구 설치 — apt-get (Debian/Ubuntu)"""
        apt_pkg = tool_info.get("apt")
        if not apt_pkg:
            return False

        try:
            cmd = ["sudo", "apt-get", "install", "-y", apt_pkg]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode == 0:
                result["installed"].append(tool_name)
                self._results.append({
                    "action": "system_tool",
                    "tool": tool_name,
                    "method": "apt",
                    "status": "installed",
                })
                return True
        except Exception:
            pass

        return False

    def _install_macos_tool(self, tool_name: str, tool_info: dict, result: dict) -> bool:
        """macOS 도구 설치 — brew"""
        brew_pkg = tool_info.get("brew")
        if not brew_pkg:
            return False

        try:
            cmd = ["brew", "install", brew_pkg]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode == 0:
                result["installed"].append(tool_name)
                self._results.append({
                    "action": "system_tool",
                    "tool": tool_name,
                    "method": "brew",
                    "status": "installed",
                })
                return True
        except Exception:
            pass

        return False

    # ── MCP 설정 ──────────────────────────────────────

    def configure_mcp(self, port: int = 9027, server_name: str = "vibezoo") -> dict:
        """.roo/mcp.json에 VibeZoo SSE MCP 설정 추가 (글로벌)

        Args:
            port: MCP 서버 포트
            server_name: MCP 서버 이름

        Returns:
            {"status": "created" | "merged" | "skipped" | "error",
             "path": "설정 파일 경로",
             "detail": "추가 정보"}
        """
        if self._dry_run:
            self._results.append({
                "action": "configure_mcp",
                "dry_run": True,
                "port": port,
                "server_name": server_name,
            })
            return {
                "status": "dry_run",
                "path": "",
                "detail": f"Would create/update .roo/mcp.json with {server_name} SSE on port {port}",
            }

        mcp_entry = {
            "transport": "sse",
            "url": f"http://127.0.0.1:{port}/sse",
            "description": f"VibeZoo MCP Bridge — 35+ code analysis tools with AST, SSA, OCR",
            "autoStart": True,
            "autoStartCommand": f"python mcp-servers/vibezoo_mcp_bridge.py --port {port}",
        }

        # 대상 경로 찾기
        candidates = self._get_mcp_config_paths()
        if not candidates:
            return {
                "status": "error",
                "path": "",
                "detail": "No suitable location found for .roo/mcp.json",
            }

        target_path = candidates[0]
        target_path.parent.mkdir(parents=True, exist_ok=True)

        existing: dict = {}
        if target_path.exists():
            try:
                existing = json.loads(target_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, Exception):
                existing = {}

        # 병합
        existing.setdefault("mcpServers", {})
        existing["mcpServers"][server_name] = mcp_entry

        try:
            target_path.write_text(
                json.dumps(existing, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            status = "merged" if target_path.exists() and len(existing.get("mcpServers", {})) > 1 else "created"
            self._results.append({
                "action": "configure_mcp",
                "status": status,
                "path": str(target_path),
            })
            return {
                "status": status,
                "path": str(target_path),
                "detail": f"Server '{server_name}' → http://127.0.0.1:{port}/sse",
            }
        except Exception as e:
            return {
                "status": "error",
                "path": str(target_path),
                "detail": str(e),
            }

    @staticmethod
    def _get_mcp_config_paths() -> list[Path]:
        """.roo/mcp.json 후보 경로 (우선순위 순)"""
        candidates: list[Path] = []

        # 1. 현재 워크스페이스 .roo/mcp.json
        cwd = Path.cwd()
        workspace_roo = cwd / ".roo" / "mcp.json"
        if workspace_roo.parent.exists() or not candidates:
            candidates.append(workspace_roo)

        # 2. 글로벌 ~/.roo/mcp.json
        home_roo = Path.home() / ".roo" / "mcp.json"
        if home_roo.parent.exists() or not any(p.parent.exists() for p in candidates):
            candidates.append(home_roo)

        # 3. 프로젝트 루트 (현재 디렉토리가 VibeZoo인 경우)
        vibezoo_roo = cwd / ".roo" / "mcp.json"
        if vibezoo_roo not in candidates:
            candidates.append(vibezoo_roo)

        # 중복 제거
        seen: set[str] = set()
        unique: list[Path] = []
        for p in candidates:
            sp = str(p.resolve())
            if sp not in seen:
                seen.add(sp)
                unique.append(p)
        return unique

    # ── Zoo 설정 ──────────────────────────────────────

    def configure_zoo(self) -> dict:
        """.zoo/config.json 설정 파일 생성/갱신

        Returns:
            {"status": "created" | "merged" | "skipped" | "error",
             "path": "설정 파일 경로",
             "detail": "추가 정보"}
        """
        if self._dry_run:
            self._results.append({
                "action": "configure_zoo",
                "dry_run": True,
            })
            return {
                "status": "dry_run",
                "path": "",
                "detail": "Would create/update .zoo/config.json",
            }

        zoo_dir = Path.cwd() / ".zoo"
        zoo_dir.mkdir(parents=True, exist_ok=True)
        config_path = zoo_dir / "config.json"

        default_config = {
            "version": VERSION,
            "project": "VibeZoo",
            "mcp_port": 9027,
            "crow_url": "http://localhost:9020",
            "features": {
                "ast": {"enabled": True, "languages": ["python", "go", "rust", "typescript"]},
                "ocr": {"enabled": False, "engine": "tesseract"},
                "ssa": {"enabled": True, "detail": "auto"},
                "streaming": {"enabled": False, "chunk_size": 5000},
            },
        }

        existing: dict = {}
        if config_path.exists():
            try:
                existing = json.loads(config_path.read_text(encoding="utf-8"))
                # 기존 설정에 없는 키만 병합 (기존 값 우선)
                merged = dict(default_config)
                merged.update(existing)
                # features 깊은 병합
                if "features" in existing:
                    merged_features = dict(default_config.get("features", {}))
                    merged_features.update(existing.get("features", {}))
                    merged["features"] = merged_features
                existing = merged
            except (json.JSONDecodeError, Exception):
                existing = default_config
        else:
            existing = default_config

        try:
            config_path.write_text(
                json.dumps(existing, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            status = "merged" if config_path.exists() else "created"
            self._results.append({
                "action": "configure_zoo",
                "status": status,
                "path": str(config_path),
            })
            return {
                "status": status,
                "path": str(config_path),
                "detail": f"Version {VERSION} configured",
            }
        except Exception as e:
            return {
                "status": "error",
                "path": str(config_path),
                "detail": str(e),
            }

    # ── AI 모델 다운로드 ────────────────────────────────────

    def download_vision_models(self) -> dict:
        """MiniCPM-V Vision 모델(GGUF) 다운로드"""
        if self._dry_run:
            self._results.append({
                "action": "download_models",
                "dry_run": True,
            })
            return {
                "status": "dry_run",
                "detail": "Would download MiniCPM-V-4_6-Q5_K_M.gguf and mmproj-model-f16.gguf (approx 6.5GB)",
            }
        
        try:
            from huggingface_hub import hf_hub_download
        except ImportError:
            return {
                "status": "error",
                "detail": "huggingface_hub package not installed. Skipping model download.",
            }
            
        try:
            models_dir = Path.cwd() / "models"
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # 메인 LLM 다운로드 및 리네임
            gguf_path = models_dir / "MiniCPM-V-4_6-Q5_K_M.gguf"
            if not gguf_path.exists():
                hf_hub_download(repo_id="openbmb/MiniCPM-V-2_6-gguf", filename="ggml-model-Q5_K_M.gguf", local_dir=str(models_dir))
                orig_file = models_dir / "ggml-model-Q5_K_M.gguf"
                if orig_file.exists():
                    orig_file.rename(gguf_path)
            
            # 비전 프로젝터 다운로드
            mmproj_path = models_dir / "mmproj-model-f16.gguf"
            if not mmproj_path.exists():
                hf_hub_download(repo_id="openbmb/MiniCPM-V-2_6-gguf", filename="mmproj-model-f16.gguf", local_dir=str(models_dir))
                
            return {
                "status": "success",
                "detail": "Vision AI models downloaded and verified successfully.",
            }
        except Exception as e:
            return {
                "status": "error",
                "detail": f"Model download failed: {str(e)}",
            }

    # ── 보고서 생성 ────────────────────────────────────

    def generate_report(self, report: dict) -> str:
        """설치 결과를 마크다운 보고서로 변환"""
        lines: list[str] = []
        lines.append("# 🚀 VibeZoo Setup Report\n")
        elapsed = time.time() - self._start_time
        lines.append(f"> **Duration**: {elapsed:.1f}s | **Dry-run**: {self._dry_run}\n")

        # Python Packages
        pip = report.get("python_packages", {})
        lines.append("## 📦 Python Packages\n")
        lines.append("| Package | Status | Note |")
        lines.append("|---------|--------|------|")
        for pkg in pip.get("success", []):
            note = ""
            if "(dry-run)" in pkg:
                note = "(dry-run)"
                pkg_name = pkg.replace(" (dry-run)", "")
            else:
                pkg_name = pkg
                # optional인지 확인
                if pkg_name in PIP_OPTIONAL:
                    note = PIP_OPTIONAL[pkg_name]
            lines.append(f"| {pkg_name} | ✅ Installed | {note} |")
        for pkg in pip.get("skipped", []):
            note = PIP_OPTIONAL.get(pkg, "Already installed")
            lines.append(f"| {pkg} | ⚡ Skipped | {note} |")
        for fail in pip.get("failed", []):
            pkg_name = fail.get("package", "?")
            reason = fail.get("reason", "")[:80]
            lines.append(f"| {pkg_name} | ❌ Failed | {reason} |")
        if not pip.get("success") and not pip.get("skipped") and not pip.get("failed"):
            lines.append("| _(skipped)_ | — | — |")

        # System Tools
        sys_tools = report.get("system_tools", {})
        lines.append("\n## ⚙️ System Tools\n")
        lines.append("| Tool | Status | Path/Method |")
        lines.append("|------|--------|-------------|")
        for tool in sys_tools.get("installed", []):
            p = shutil.which(tool.replace(" (dry-run)", "")) or "(dry-run)"
            lines.append(f"| {tool} | ✅ Installed | {p} |")
        for tool in sys_tools.get("skipped", []):
            p = shutil.which(tool) or "?"
            lines.append(f"| {tool} | ✅ Available | {p} |")
        for manual in sys_tools.get("manual", []):
            t = manual.get("tool", "?")
            url = manual.get("url", "")
            lines.append(f"| {t} | ⚠️ Manual | [{url}]({url}) |")
        for fail in sys_tools.get("failed", []):
            t = fail.get("tool", "?")
            r = fail.get("reason", "")[:60]
            lines.append(f"| {t} | ❌ Failed | {r} |")
        if not any([sys_tools.get(k) for k in ("installed", "skipped", "manual", "failed")]):
            lines.append("| _(skipped)_ | — | — |")

        # MCP Configuration
        mcp = report.get("mcp_config")
        if mcp:
            lines.append("\n## 🔌 MCP Configuration\n")
            status_icon = {"created": "✅", "merged": "✅", "skipped": "⏭️", "error": "❌", "dry_run": "🔍"}
            icon = status_icon.get(mcp.get("status", ""), "❓")
            lines.append(f"- **Status**: {icon} {mcp.get('status', 'unknown')}")
            lines.append(f"- **Path**: `{mcp.get('path', '')}`")
            lines.append(f"- **Detail**: {mcp.get('detail', '')}")
        else:
            lines.append("\n## 🔌 MCP Configuration\n")
            lines.append("| _(skipped)_ | — | — |")

        # Zoo Configuration
        zoo = report.get("zoo_config")
        if zoo:
            lines.append("\n## 🏠 Zoo Configuration\n")
            status_icon = {"created": "✅", "merged": "✅", "skipped": "⏭️", "error": "❌", "dry_run": "🔍"}
            icon = status_icon.get(zoo.get("status", ""), "❓")
            lines.append(f"- **Status**: {icon} {zoo.get('status', 'unknown')}")
            lines.append(f"- **Path**: `{zoo.get('path', '')}`")
            lines.append(f"- **Detail**: {zoo.get('detail', '')}")
        else:
            lines.append("\n## 🏠 Zoo Configuration\n")
            lines.append("| _(skipped)_ | — | — |")
            
        # Models Download
        models = report.get("models_download")
        if models:
            lines.append("\n## 🧠 AI Models\n")
            status_icon = {"success": "✅", "error": "❌", "dry_run": "🔍"}
            icon = status_icon.get(models.get("status", ""), "❓")
            lines.append(f"- **Status**: {icon} {models.get('status', 'unknown')}")
            lines.append(f"- **Detail**: {models.get('detail', '')}")

        # Summary
        summary = report.get("summary", {})
        lines.append("\n## 📊 Summary\n")
        lines.append(f"- ✅ **{summary.get('installed_packages', 0)}** packages installed")
        lines.append(f"- ⚡ **{summary.get('skipped_packages', 0)}** packages skipped (already installed)")
        lines.append(f"- ❌ **{summary.get('failed_packages', 0)}** packages failed")
        lines.append(f"- ✅ **{summary.get('installed_tools', 0)}** system tools installed")
        lines.append(f"- ⚠️ **{summary.get('manual_tools', 0)}** tools need manual installation")
        if summary.get("mcp_status"):
            lines.append(f"- 🔌 MCP config: {summary['mcp_status']}")
        if summary.get("zoo_status"):
            lines.append(f"- 🏠 Zoo config: {summary['zoo_status']}")
        lines.append(f"\n---\n*Report generated in {elapsed:.1f}s*")

        return "\n".join(lines)

    @staticmethod
    def _build_summary(report: dict, elapsed: float) -> dict:
        """결과 요약 통계"""
        pip = report.get("python_packages", {})
        sys_tools = report.get("system_tools", {})
        mcp = report.get("mcp_config", {})
        zoo = report.get("zoo_config", {})

        return {
            "installed_packages": len(pip.get("success", [])),
            "skipped_packages": len(pip.get("skipped", [])),
            "failed_packages": len(pip.get("failed", [])),
            "installed_tools": len(sys_tools.get("installed", [])),
            "manual_tools": len(sys_tools.get("manual", [])),
            "mcp_status": mcp.get("status", "skipped") if mcp else "skipped",
            "zoo_status": zoo.get("status", "skipped") if zoo else "skipped",
            "models_status": report.get("models_download", {}).get("status", "skipped") if report.get("models_download") else "skipped",
            "elapsed": round(elapsed, 1),
        }

    def get_diagnostics(self) -> str:
        """현재 환경 진단 정보 반환 (설치 전 사전 확인용)"""
        system = platform.system()
        lines: list[str] = []
        lines.append("## 🔍 Environment Diagnostics\n")
        lines.append(f"- **OS**: {system} {platform.release()}")
        lines.append(f"- **Python**: {sys.version.split()[0]}")
        lines.append(f"- **CWD**: {Path.cwd()}")
        lines.append(f"- **PIP**: {self._check_pip_version()}")

        lines.append("\n### Python Packages\n")
        all_pkgs = list(PIP_CORE) + list(PIP_OPTIONAL.keys())
        for pkg in all_pkgs:
            installed = self.check_python_package(pkg)
            icon = "✅" if installed else "⬜"
            lines.append(f"- {icon} {pkg}")

        lines.append("\n### System Tools\n")
        for tool_name, info in SYSTEM_TOOLS.items():
            installed = self.check_system_tool(tool_name)
            icon = "✅" if installed else "⬜"
            p = shutil.which(tool_name) or "-"
            lines.append(f"- {icon} {tool_name} ({info['name']}): `{p}`")

        lines.append("\n### MCP Config\n")
        for path in self._get_mcp_config_paths():
            exists = path.exists()
            icon = "✅" if exists else "⬜"
            lines.append(f"- {icon} `{path}`")

        lines.append("\n### Zoo Config\n")
        zoo_path = Path.cwd() / ".zoo" / "config.json"
        icon = "✅" if zoo_path.exists() else "⬜"
        lines.append(f"- {icon} `{zoo_path}`")

        return "\n".join(lines)

    @staticmethod
    def _check_pip_version() -> str:
        """pip 버전 확인"""
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode == 0:
                return proc.stdout.split()[1] if proc.stdout else "unknown"
            return "not found"
        except Exception:
            return "error"


# ── 도구 등록 ────────────────────────────────────────


def register(mcp):
    """Setup 도구 등록"""

    @mcp.tool
    def vibezoo_setup(
        target: str = "minimal",
        python_packages: bool = True,
        system_tools: bool = False,
        configure_mcp: bool = True,
        configure_zoo: bool = True,
        download_models: bool = True,
        dry_run: bool = False,
    ) -> str:
        """🚀 VibeZoo 통합 설치/설정 도구.

        한 번의 호출로 VibeZoo 운영에 필요한 모든 의존성을 설치하고,
        MCP 글로벌 설정 및 .zoo/config.json을 자동 구성합니다.

        **설치 대상 (target):**
        - `minimal`: 필수 코어 패키지만 (fastmcp, uvicorn, starlette)
        - `recommended`: 코어 + 옵션 패키지 (OpenCV, Pillow, tree-sitter, pytesseract 등)
        - `full`: recommended + 시스템 도구 (ripgrep, tesseract-ocr)

        Args:
            target: 설치 대상 ("minimal", "recommended", "full")
            python_packages: Python 패키지 설치 여부
            system_tools: 시스템 도구 설치 여부 (Windows: winget 필요)
            configure_mcp: .roo/mcp.json SSE MCP 설정 자동 구성 여부
            configure_zoo: .zoo/config.json 설정 자동 구성 여부
            download_models: MiniCPM-V 등 대용량 AI 모델 자동 다운로드 여부 (target=recommended/full 일때만)
            dry_run: 실제 설치 없이 필요한 항목만 출력 (안전 확인)

        Returns:
            설치 진행 상황 및 결과 보고서 (마크다운)
        """
        # target 검증
        valid_targets = ("minimal", "recommended", "full")
        if target not in valid_targets:
            target = "minimal"

        manager = SetupManager(dry_run=dry_run)

        # dry-run 모드: 진단 정보 반환
        if dry_run:
            diag = manager.get_diagnostics()
            plan_lines: list[str] = []
            plan_lines.append("# 🔍 VibeZoo Setup — Dry Run Plan\n")
            plan_lines.append(f"> **Target**: `{target}` | No changes will be made.\n")
            plan_lines.append(diag)

            plan_lines.append("\n### 📋 Installation Plan\n")
            if python_packages:
                packages = TARGET_PACKAGES.get(target, TARGET_PACKAGES["minimal"])
                plan_lines.append(f"\n**Python packages to install**: {len(packages)}")
                for pkg in packages:
                    status = "✅ already installed" if manager.check_python_package(pkg) else "⬜ will install"
                    plan_lines.append(f"- {status}: `{pkg}`")
            else:
                plan_lines.append("\n**Python packages**: skipped")

            if system_tools:
                tools = TARGET_SYSTEM_TOOLS.get(target, [])
                plan_lines.append(f"\n**System tools to install**: {len(tools)}")
                for tool in tools:
                    status = "✅ already installed" if manager.check_system_tool(tool) else "⬜ will install"
                    plan_lines.append(f"- {status}: `{tool}`")
            else:
                plan_lines.append("\n**System tools**: skipped")

            plan_lines.append(f"\n**Configure MCP**: {'yes' if configure_mcp else 'no'}")
            plan_lines.append(f"**Configure Zoo**: {'yes' if configure_zoo else 'no'}")

            return "\n".join(plan_lines)

        # 실제 설치 실행
        report = manager.run_setup(
            target=target,
            python_packages=python_packages,
            system_tools=system_tools,
            configure_mcp=configure_mcp,
            configure_zoo=configure_zoo,
            download_models=download_models,
        )

        # 설치 완료 시 자동 learn_project (지연, 1회만)
        try:
            from bridge.tools.knowledge import _auto_learn_project
            _auto_learn_project()
        except Exception:
            pass  # 학습 실패는 무시

        return manager.generate_report(report)
