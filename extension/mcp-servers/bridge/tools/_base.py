# VibeZoo Bridge — 도구 기본 클래스 + 공통 데코레이터

from bridge.i18n import t


class BaseTool:
    """도구 기본 클래스 — 검증, 부분 결과, 에러 보고, 점진적 스트리밍"""

    @staticmethod
    def validate_file_path(file_path: str) -> str:
        """파일 경로 검증"""
        from bridge.utils import _validate_file_path
        err = _validate_file_path(file_path)
        if err:
            from bridge.utils import _markdown_header, _markdown_footer
            return _markdown_header(t("Error"), "❌") + f"**{err}**\n" + _markdown_footer()
        return ""

    @staticmethod
    def validate_string(value, name: str) -> str:
        """문자열 검증"""
        from bridge.utils import _validate_string
        err = _validate_string(value, name)
        if err:
            from bridge.utils import _markdown_header, _markdown_footer
            return _markdown_header(t("Error"), "❌") + f"**{err}**\n" + _markdown_footer()
        return ""

    @staticmethod
    def report_error(name: str, error: Exception, context: dict = None) -> str:
        """구조화된 에러 보고 (ErrorRegistry 자동 기록 포함)"""
        import json
        
        # ErrorRegistry에 에러 기록 (best-effort, 도구 호출에 영향 없음)
        try:
            from bridge.error_handler import ErrorRegistry
            registry = ErrorRegistry()
            registry.record(name, error, context)
        except Exception:
            pass  # Graceful degradation: 레지스트리 실패가 보고에 영향 없음
        
        error_info = {
            "tool": name,
            "error": str(error),
            "type": type(error).__name__,
        }
        if context:
            error_info["context"] = context
        return json.dumps(error_info)

    @staticmethod
    def progress_chunk(stage: str, progress: int, message: str) -> str:
        """부분 결과 청크 반환 (streaming=True 시 사용).

        Args:
            stage: 현재 단계 식별자 (예: '1/4', '2/4')
            progress: 진행률 퍼센트 (0-100)
            message: 진행 상태 설명 메시지
        Returns:
            HTML 코멘트로 래핑된 진행 청크 문자열
        """
        return f"<!-- VIBEZOO_PROGRESS stage={stage} progress={progress}% -->\n**{message}**\n"

    @staticmethod
    def final_result(output: str, stats: dict = None) -> str:
        """최종 결과 + 통계.

        Args:
            output: 최종 결과 문자열
            stats: 추가 통계 정보 딕셔너리 (선택)
        Returns:
            최종 결과 (통계 포함 시 HTML 코멘트로 래핑)
        """
        if stats:
            import json
            stats_str = json.dumps(stats, ensure_ascii=False)
            return f"{output}\n\n<!-- VIBEZOO_STATS {stats_str} -->\n"
        return output
