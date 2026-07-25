"""Shared AST engine singleton — one parser warm-up across all tools."""
from bridge.ast_engine import AstEngine

_instance: AstEngine | None = None

def get_ast_engine() -> AstEngine:
    global _instance
    if _instance is None:
        _instance = AstEngine()
    return _instance
