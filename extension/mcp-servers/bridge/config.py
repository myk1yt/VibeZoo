# VibeZoo Bridge — 설정/상수 모듈
# 모든 상수, 경로, 버전 정보를 중앙 관리

import os
from pathlib import Path

# ── 버전 ─────────────────────────────────────────────

VERSION = "0.16.0"

# ── Crow Memory ──────────────────────────────────────

CROW_URL = os.environ.get("CROW_SERVER_URL", "http://localhost:9020")
CROW_TIMEOUT = 3  # 3초 타임아웃 (권장)

# ── 파일 경로 ─────────────────────────────────────────

HOME_DIR = Path.home()

WHITEBOARD_FILE = str(HOME_DIR / ".vibezoo-whiteboard.json")
FIX_REQUEST_FILE = str(HOME_DIR / ".vibezoo-fix-request.json")
CHAT_PENDING_FILE = str(HOME_DIR / ".vibezoo-chat-pending.json")
PREFERENCES_FILE = str(HOME_DIR / ".vibezoo-preferences.json")
WHITEBOARD_ACTION_FILE = str(HOME_DIR / ".vibezoo-whiteboard-action.json")
UI_ACTION_FILE = str(HOME_DIR / ".vibezoo-ui-action.json")
DZ_ACTION_FILE = str(HOME_DIR / ".vibezoo-dropzone-action.json")
DZ_SESSION_FILE = str(HOME_DIR / ".vibezoo-uploads" / "dz_session.json")

# ── 캐시 ─────────────────────────────────────────────

from datetime import date
_DATE_STR = date.today().isoformat()  # "2026-06-01"
CACHE_DIR = str(HOME_DIR / ".vibezoo-uploads" / _DATE_STR)
IMAGE_CACHE_DIR = str(HOME_DIR / ".vibezoo-uploads" / _DATE_STR)
MAX_CACHE_SIZE = 50  # L1 메모리 캐시 최대 파일 수

# ── 검색 / 파일 필터 ──────────────────────────────────

DEFAULT_EXCLUDE_DIRS = {
    ".git", "node_modules", ".zoo-code", "dist", "build",
    ".next", "coverage", "target", "vendor", "__pycache__",
    ".venv", "env", ".env", ".vibezoo-uploads",
}
SOURCE_EXTS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs",
    # C/C++
    ".cpp", ".hpp", ".cc", ".h", ".c",
    # Shell
    ".sh", ".bash", ".ps1",
    # 설정 파일
    ".yaml", ".yml", ".json",
}
TS_JS_EXTS = {".ts", ".tsx", ".js", ".jsx"}

# C/C++ 확장자 그룹 (→ reviewer.py, ast_engine.py 에서 import)
CPP_EXTS = {".cpp", ".hpp", ".cc", ".h", ".c"}

# Shell 확장자 그룹
SHELL_EXTS = {".sh", ".bash", ".ps1"}

# 확장자 없는 설정 파일명 (→ _iter_project_files()의 include_names 파라미터에서 사용)
CONFIG_FILES = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}

# Generic / non-AST 파일 (reviewer 기본 패턴만 적용) (→ reviewer.py 에서 import)
GENERIC_EXTS = {".sh", ".bash", ".ps1", ".yaml", ".yml", ".json"}

# 모든 리뷰 가능 확장자 (→ review_code() 진입 검증에 사용) (M5)
REVIEWABLE_EXTS = SOURCE_EXTS | GENERIC_EXTS

# ── SSA ──────────────────────────────────────────────

# Windows TEMP 폴더에 이미지 저장 (c:\temp 대신 시스템 temp 사용)
import tempfile
_TEMP_DIR = Path(tempfile.gettempdir())
UPLOADED_IMAGE_PATH = str(_TEMP_DIR / "vibezoo_uploaded_image.png")

# ── 업로드 경로 ─────────────────────────────────────────
import uuid
DEFAULT_UPLOAD_NAME = "dropped_image.png"

def get_uploaded_path(filename: str = None) -> str:
    """파일명 기반 업로드 경로 반환. 없으면 기본값.
    
    확장자를 보존하여 PDF, DOCX 등 모든 파일 타입 지원.
    """
    if filename and os.path.splitext(filename)[1]:
        safe_name = str(uuid.uuid4())[:8] + "_" + os.path.basename(filename)
        return str(HOME_DIR / ".vibezoo-cache" / safe_name)
    return str(HOME_DIR / ".vibezoo-cache" / DEFAULT_UPLOAD_NAME)
