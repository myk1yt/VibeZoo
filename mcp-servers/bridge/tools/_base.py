# VibeZoo Bridge — 도구 기본 클래스 + 공통 데코레이터


class BaseTool:
    """도구 기본 클래스 — 검증, 부분 결과, 에러 보고"""

    @staticmethod
    def validate_file_path(file_path: str) -> str:
        """파일 경로 검증"""
        from bridge.utils import _validate_file_path
        err = _validate_file_path(file_path)
        if err:
            from bridge.utils import _markdown_header, _markdown_footer
            return _markdown_header("Error", "❌") + f"**{err}**\n" + _markdown_footer()
        return ""

    @staticmethod
    def validate_string(value, name: str) -> str:
        """문자열 검증"""
        from bridge.utils import _validate_string
        err = _validate_string(value, name)
        if err:
            from bridge.utils import _markdown_header, _markdown_footer
            return _markdown_header("Error", "❌") + f"**{err}**\n" + _markdown_footer()
        return ""

    @staticmethod
    def partial_result(name: str, data: dict) -> str:
        """점진적 스트리밍 — 부분 결과 반환 (향후 확장)"""
        import json
        return json.dumps({"partial": True, "tool": name, "data": data})

    @staticmethod
    def report_error(name: str, error: Exception, context: dict = None) -> str:
        """구조화된 에러 보고"""
        import json
        error_info = {
            "tool": name,
            "error": str(error),
            "type": type(error).__name__,
        }
        if context:
            error_info["context"] = context
        return json.dumps(error_info)
