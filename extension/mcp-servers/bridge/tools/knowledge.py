# VibeZoo Bridge — Knowledge 도구 그룹
# recall_project + learn_preference + get_preferences
# 프로젝트 지식 자동 수집 (_auto_learn_project, register 시 지연 초기화, 1회만)

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Optional

from bridge.config import (
    VERSION, PREFERENCES_FILE,
)
from bridge.i18n import t
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string,
    _truncate, _atomic_write_json,
    get_project_root,
)
from bridge.crow_client import try_crow_ingest, try_crow_recall

# ── 자동 프로젝트 지식 수집 관리 ──────────────────────

_learned_projects: set[str] = set()
_learning_lock = threading.Lock()
_auto_learn_scheduled = False


def _auto_learn_project(target_path: Optional[str] = None) -> None:
    """등록 시 프로젝트 지식을 자동 수집 (지연 초기화, 최초 1회만).
    
    Args:
        target_path: 분석 대상 경로 (기본: 현재 작업 디렉토리)
    
    Thread-safe하며, 이미 학습된 프로젝트는 건너뜁니다.
    자동 수집 실패 시에도 예외를 삼키고 조용히 진행합니다.
    """
    root = str(Path(get_project_root(target_path)).resolve())
    
    with _learning_lock:
        if root in _learned_projects:
            return
        _learned_projects.add(root)
    
    try:
        # 자동 수집 로직 직접 호출 (async-safe)
        from bridge.tools.scout import summarize_architecture
        from bridge.tools.deep_analyzer import extract_patterns, map_dependencies
        
        # 1. Architecture → arch register
        arch_summary = summarize_architecture(target_path=root)
        try_crow_ingest(
            json.dumps({
                "action": "auto_learn_project",
                "type": "architecture",
                "target": root,
                "summary": arch_summary[:500],
                "timestamp": time.time(),
            }),
            register="arch"
        )
        
        # 2. Patterns → style register
        patterns = extract_patterns(target_path=root, min_occurrences=3)
        try_crow_ingest(
            json.dumps({
                "action": "auto_learn_project",
                "type": "patterns",
                "target": root,
                "patterns": patterns[:500],
                "timestamp": time.time(),
            }),
            register="style"
        )
        
        # 3. Dependencies → arch register
        deps = map_dependencies(target_path=root)
        try_crow_ingest(
            json.dumps({
                "action": "auto_learn_project",
                "type": "dependencies",
                "target": root,
                "deps": deps[:500],
                "timestamp": time.time(),
            }),
            register="arch"
        )
        
        # 4. Project identity → life_context
        project_key = f"project:{hashlib.md5(root.encode()).hexdigest()[:8]}"
        try_crow_ingest(
            json.dumps({
                "action": "auto_learn_project",
                "type": "identity",
                "project_key": project_key,
                "target": root,
                "timestamp": time.time(),
            }),
            register="life_context"
        )
    except Exception:
        pass  # 자동 학습 실패는 무시 (조용한 폴백)


def register(mcp):
    """Knowledge 도구 등록 (자동 프로젝트 지식 수집 스케줄 포함)"""
    
    # ── 자동 프로젝트 지식 수집 스케줄 (지연 초기화, 1회만) ──
    global _auto_learn_scheduled
    if not _auto_learn_scheduled:
        _auto_learn_scheduled = True
        def _deferred_learn():
            """서버 시작 후 3초 지연 → 자동 프로젝트 지식 수집 실행"""
            import time as _time
            _time.sleep(3.0)
            _auto_learn_project()
        t = threading.Thread(target=_deferred_learn, daemon=True)
        t.start()

    @mcp.tool
    def recall_project(target_path: Optional[str] = None) -> str:
        """Crow Memory에 자동 수집된 프로젝트 지식을 회상합니다.
        arch, style, life_context 레지스터에서 관련 정보를 조회하여 반환합니다.

        Args:
            target_path: 분석 대상 디렉토리 경로 (기본: 현재 작업 디렉토리)

        Returns:
            Markdown 보고서: Crow에서 회상된 프로젝트 지식
        """
        root = Path(get_project_root(target_path))
        root_str = str(root)
        project_key = f"project:{hashlib.md5(root_str.encode()).hexdigest()[:8]}"

        output = _markdown_header("Project Knowledge Recall")
        output += f"> Target: `{root}`\n"
        output += f"> Project key: `{project_key}`\n\n"

        # 1. arch register
        output += "## 🏗️ Architecture (arch register)\n\n"
        arch_results = try_crow_recall(query=root_str, register="arch", limit=5)
        if arch_results:
            for item in arch_results:
                content = item.get("content", item.get("value", str(item)))
                output += f"- {_truncate(content, 300)}\n"
        else:
            output += f"- {t('No architecture data found in Crow.')}\n"
            output += f"  → {t('Project knowledge is auto-captured at bridge startup (_auto_learn_project); force-refresh via summarize_architecture/extract_patterns/map_dependencies and recall again.')}\n"

        # 2. style register
        output += "\n## 📊 Code Patterns (style register)\n\n"
        style_results = try_crow_recall(query=root_str, register="style", limit=5)
        if style_results:
            for item in style_results:
                content = item.get("content", item.get("value", str(item)))
                output += f"- {_truncate(content, 300)}\n"
        else:
            output += f"- {t('No pattern data found in Crow.')}\n"

        # 3. life_context
        output += "\n## 🔑 Project Identity (life_context)\n\n"
        life_results = try_crow_recall(query=project_key, register="life_context", limit=3)
        if life_results:
            for item in life_results:
                content = item.get("content", item.get("value", str(item)))
                output += f"- {_truncate(content, 300)}\n"
        else:
            output += f"- {t('No project identity found in Crow.')}\n"

        total = len(arch_results) + len(style_results) + len(life_results)
        output += f"\n---\n**Total {total} knowledge items recalled from Crow.**\n"
        output += _markdown_footer()
        return output

    @mcp.tool
    def learn_preference(rule: str, category: str = "coding_style") -> str:
        """사용자의 코딩 스타일 규칙이나 선호도를 Crow Memory에 저장합니다.
        예: "함수형 컴포넌트 선호", "interface보다 type 사용", "tab width: 2"

        Args:
            rule: 저장할 규칙 또는 선호도 설명
            category: 카테고리 (coding_style, naming, formatting, architecture, workflow)

        Returns:
            저장 확인 메시지
        """
        err = _validate_string(rule, "rule")
        if err:
            return (_markdown_header("Learn Preference Error", "❌")
                    + f"**{err}**\n"
                    + _markdown_footer())

        allowed_categories = {"coding_style", "coding", "naming", "formatting", "architecture", "workflow"}
        if category not in allowed_categories:
            return (_markdown_header("Learn Preference Error", "❌")
                    + f"**{t('Invalid category: `{0}`. Allowed: {1}', category, ', '.join(allowed_categories))}**\n"
                    + _markdown_footer())

        # Store in local preferences file
        try:
            prefs = {}
            if os.path.exists(PREFERENCES_FILE):
                try:
                    with open(PREFERENCES_FILE) as f:
                        prefs = json.load(f)
                except Exception:
                    prefs = {}
            if category not in prefs:
                prefs[category] = []
            prefs[category].append({
                "rule": rule,
                "timestamp": time.time(),
            })
            _atomic_write_json(PREFERENCES_FILE, prefs, indent=2)
        except Exception as e:
            return (_markdown_header("Learn Preference Error", "❌")
                    + f"**{t('Failed to save: `{0}`', e)}**\n"
                    + _markdown_footer())

        # Also store in Crow life_context
        try_crow_ingest(
            json.dumps({
                "action": "learn_preference",
                "category": category,
                "rule": rule,
                "timestamp": time.time(),
            }),
            register="life_context"
        )

        return (_markdown_header("Preference Saved")
                + f"**Category**: `{category}`\n"
                + f"**Rule**: `{rule}`\n\n"
                + t("Stored in local preferences file and Crow Memory (`life_context`).") + "\n"
                + _markdown_footer())

    @mcp.tool
    def get_preferences(category: Optional[str] = None) -> str:
        """저장된 모든 사용자 선호도/규칙을 조회합니다.

        Args:
            category: 특정 카테고리만 조회 (생략 시 전체)

        Returns:
            Markdown 형식의 저장된 선호도 목록
        """
        output = _markdown_header("User Preferences")

        prefs = {}
        if os.path.exists(PREFERENCES_FILE):
            try:
                with open(PREFERENCES_FILE) as f:
                    prefs = json.load(f)
            except Exception:
                prefs = {}

        if not prefs:
            output += f"{t('No preferences saved yet.')}\n"
            output += f"\n> {t('Use `learn_preference(rule, category)` to save your first preference.')}\n"
            output += _markdown_footer()
            return output

        categories_to_show = [category] if category else list(prefs.keys())

        for cat in categories_to_show:
            if cat not in prefs:
                output += f"### {cat}\n\n⚠️ {t('Category not found.')}\n\n"
                continue
            rules = prefs[cat]
            if not rules:
                continue
            output += f"## {cat}\n\n"
            for i, entry in enumerate(rules, 1):
                rule_text = entry.get("rule", str(entry))
                ts = entry.get("timestamp", 0)
                if ts:
                    d = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
                    output += f"{i}. `{rule_text}` _(saved: {d})_\n"
                else:
                    output += f"{i}. `{rule_text}`\n"
            output += "\n"

        # Also recall from Crow
        output += "## 🔄 Crow Memory (life_context)\n\n"
        crow_prefs = try_crow_recall(query="learn_preference", register="life_context", limit=5)
        if crow_prefs:
            for item in crow_prefs:
                content = item.get("content", item.get("value", str(item)))
                output += f"- {_truncate(content, 200)}\n"
        else:
            output += f"- {t('No preference data in Crow.')}\n"

        output += _markdown_footer()
        return output
