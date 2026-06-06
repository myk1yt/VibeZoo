"""VibeZoo Bridge — 모든 MCP 도구를 FastMCP 인스턴스에 등록

★ 에러 캡처: register_all_tools() 진입 시 mcp.tool()을 래핑하여
   모든 MCP 도구 호출이 자동으로 @capture_tool_errors로 감싸지도록 함.
"""

import sys
from pathlib import Path

# Pylance: ensure the extension root is in package search path
_EXT_ROOT = str(Path(__file__).resolve().parent.parent)
if _EXT_ROOT not in sys.path:
    sys.path.insert(0, _EXT_ROOT)


from bridge.tools.file_analyzer import register as register_file_analyzer


def register_all_tools(mcp):
    """모든 tools/*.py의 register(mcp) 함수를 호출하여 도구 등록
    
    ★ 에러 캡처: 각 도구 등록 전에 mcp.tool()을 래핑하여
       모든 MCP 도구 호출이 자동으로 try/except로 감싸지도록 함.
       @mcp.tool (괄호 없음, 14개 도구)와 @mcp.tool() (괄호 있음, feedback.py) 모두 지원.
    """
    from bridge.error_handler import capture_tool_errors

    # 원본 mcp.tool 참조 저장
    _original_tool = mcp.tool

    def _wrapped_tool(*targs, **tkwargs):
        """mcp.tool()을 래핑하여 자동 에러 캡처 적용
        
        두 가지 호출 패턴 지원:
        1. @mcp.tool — targs=(func,), tkwargs={}
        2. @mcp.tool() / @mcp.tool(name=...) — targs=(), tkwargs={...}
        """
        # 패턴 1: @mcp.tool (괄호 없음, 데코레이터에 함수가 직접 전달됨)
        if targs and callable(targs[0]) and not tkwargs:
            func = targs[0]
            wrapped = capture_tool_errors(func.__name__)(func)
            return _original_tool(wrapped)

        # 패턴 2: @mcp.tool() 또는 @mcp.tool(name=...) (팩토리 호출)
        name = tkwargs.get("name") or (targs[0].__name__ if targs else "unknown")

        def decorator(func):
            wrapped = capture_tool_errors(name)(func)
            return _original_tool(*targs, **tkwargs)(wrapped)
        return decorator

    # mcp.tool을 래핑된 버전으로 교체
    mcp.tool = _wrapped_tool

    try:
        # 지연 임포트로 순환 참조 방지
        from bridge.tools.setup import register as reg_setup
        from bridge.tools.scout import register as reg_scout
        from bridge.tools.reviewer import register as reg_reviewer
        from bridge.tools.deep_analyzer import register as reg_deep
        from bridge.tools.tester import register as reg_tester
        from bridge.tools.whiteboard import register as reg_wb
        from bridge.tools.fix_loop import register as reg_fix
        from bridge.tools.integrated import register as reg_integrated
        from bridge.tools.analysis import register as reg_analysis
        from bridge.tools.knowledge import register as reg_knowledge
        from bridge.tools.web import register as reg_web
        from bridge.tools.ssa import register as reg_ssa
        from bridge.tools.editor import register as reg_editor
        from bridge.tools.ux_coordinator import register as reg_ux
        from bridge.tools.feedback import register as reg_feedback

        for reg in [reg_setup, reg_scout, reg_reviewer, reg_deep, reg_tester, register_file_analyzer,
                    reg_wb, reg_fix, reg_integrated, reg_analysis,
                    reg_knowledge, reg_web, reg_ssa, reg_editor, reg_ux, reg_feedback]:
            reg(mcp)
    finally:
        # 원본 mcp.tool 복원 (다른 코드와의 호환성)
        mcp.tool = _original_tool
