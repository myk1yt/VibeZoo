"""VibeZoo Bridge — 모든 MCP 도구를 FastMCP 인스턴스에 등록"""


from bridge.tools.file_analyzer import register as register_file_analyzer


def register_all_tools(mcp):
    """모든 tools/*.py의 register(mcp) 함수를 호출하여 도구 등록"""
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

    for reg in [reg_setup, reg_scout, reg_reviewer, reg_deep, reg_tester, register_file_analyzer,
                reg_wb, reg_fix, reg_integrated, reg_analysis,
                reg_knowledge, reg_web, reg_ssa]:
        reg(mcp)
