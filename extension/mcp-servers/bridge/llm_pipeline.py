# VibeZoo Bridge — LLM-도구 체인 파이프라인
# 데이터 수집(도구) → LLM 분석 → Crow Memory 저장

import json
import time
from typing import Any, Optional

from bridge.tool_context import ToolContext, get_manifest, format_manifest_markdown
from bridge.crow_client import try_crow_ingest


class LLMToolPipeline:
    """데이터 수집(도구) → LLM 분석 → Crow Memory 저장 파이프라인

    사용 패턴:
        1. collect() — 도구가 데이터를 수집하여 ToolContext 생성
        2. analyze() — ToolContext + manifest를 LLM에 전달할 형태로 준비
        3. store() — LLM 분석 결과를 Crow Memory에 저장 (재사용)

    이 클래스는 기존 도구 시그니처를 변경하지 않으며, 내부에서만 사용된다.
    각 도구는 collect()로 수집한 데이터에 manifest 정보를 포함하여 반환하고,
    LLM은 이 manifest를 보고 분석 방향을 결정한다.
    """

    # ── 1단계: 데이터 수집 ──────────────────────────────

    @staticmethod
    def collect(tool_name: str, **kwargs) -> ToolContext:
        """1단계: 도구가 데이터 수집하여 ToolContext 생성

        이 메서드는 각 도구 함수 내부에서 호출되어,
        수집된 데이터를 표준화된 ToolContext로 포장한다.

        Args:
            tool_name: 도구명 (예: "explain_code", "generate_tests")
            **kwargs: ToolContext.data에 저장될 키-값 쌍
                - source_file: 분석 대상 파일 경로 (권장)
                - language: 프로그래밍 언어 (권장)
                - 그 외 도구별 수집 데이터

        Returns:
            ToolContext 인스턴스 (manifest 자동 포함)
        """
        source_file = kwargs.pop("source_file", "")
        language = kwargs.pop("language", "")
        suggested_steps = kwargs.pop("suggested_steps", [])

        ctx = ToolContext(
            tool_name=tool_name,
            data=kwargs,
            source_file=source_file,
            language=language,
            suggested_steps=suggested_steps,
        )
        return ctx

    # ── 2단계: LLM 분석 준비 ────────────────────────────

    @staticmethod
    def analyze(ctx: ToolContext) -> dict:
        """2단계: ToolContext + manifest 정보를 LLM이 처리할 수 있는 형태로 준비

        MCP 도구 결과에 manifest 정보를 포함하여 반환.
        LLM은 이 manifest를 보고 분석 방향을 결정한다.

        Args:
            ctx: collect()에서 생성된 ToolContext

        Returns:
            dict with keys:
                - "manifest": tool_manifest 딕셔너리
                - "context_markdown": ToolContext.to_markdown() 결과
                - "llm_prompt": LLM 프롬프트에 바로 포함할 수 있는 전체 문자열
        """
        manifest = get_manifest(ctx.tool_name) or {}

        # LLM 프롬프트 구성
        prompt_parts = []

        # 1. tool_manifest 헤더
        if manifest:
            prompt_parts.append(format_manifest_markdown(ctx.tool_name))
            prompt_parts.append("")

        # 2. ToolContext 데이터 (마크다운)
        prompt_parts.append(ctx.to_markdown())

        llm_prompt = "\n\n".join(prompt_parts)

        return {
            "manifest": manifest,
            "context_markdown": ctx.to_markdown(),
            "llm_prompt": llm_prompt,
        }

    # ── 3단계: Crow Memory 저장 ─────────────────────────

    @staticmethod
    def store(
        ctx: ToolContext,
        llm_result: str,
        polarity: float = 0.5,
        register: str = "arch",
    ):
        """3단계: LLM 분석 결과를 Crow Memory에 저장

        도구 수집 데이터 + LLM 분석 결과를 함께 저장하여,
        향후 유사 요청 시 Crow Memory에서 참조할 수 있게 한다.

        Args:
            ctx: collect()에서 생성된 ToolContext
            llm_result: LLM이 생성한 분석 결과 문자열
            polarity: Crow Memory 극성값 (-2.0 ~ 2.0, 기본 0.5)
            register: Crow 레지스터명 (기본 "arch")
        """
        payload = {
            "tool": ctx.tool_name,
            "source_file": ctx.source_file,
            "language": ctx.language,
            "data_summary": json.dumps(ctx.data, default=str, ensure_ascii=False)[:500],
            "llm_result_summary": llm_result[:1000],
            "manifest_version": ctx.manifest.get("version", "1.0") if ctx.manifest else "1.0",
            "timestamp": time.time(),
        }

        try_crow_ingest(
            content=json.dumps(payload, ensure_ascii=False),
            register=register,
        )

    # ── 편의: 한 번에 처리 ──────────────────────────────

    @staticmethod
    def run(tool_name: str, llm_result: str, **kwargs) -> dict:
        """collect + analyze + store를 한 번에 실행

        Args:
            tool_name: 도구명
            llm_result: LLM이 생성한 분석 결과
            **kwargs: collect()에 전달할 데이터

        Returns:
            analyze()의 결과 dict
        """
        ctx = LLMToolPipeline.collect(tool_name, **kwargs)
        analysis = LLMToolPipeline.analyze(ctx)
        LLMToolPipeline.store(ctx, llm_result)
        return analysis

    # ── 하위 호환: prepare_for_llm + ingest_result_to_crow ──

    @staticmethod
    def prepare_for_llm(tool_name: str, context: ToolContext) -> str:
        """도구 수집 데이터를 LLM이 처리할 수 있는 형태로 변환

        Args:
            tool_name: 도구명 (manifest 로드용)
            context: ToolContext 인스턴스

        Returns:
            LLM 프롬프트에 포함될 마크다운 문자열
        """
        manifest = get_manifest(tool_name)
        parts = []

        # 1. tool_manifest 정보
        if manifest:
            parts.append(f"## Tool: {tool_name}\n")
            parts.append(f"### Description\n{manifest.get('description', '')}\n")
            if "llm_instructions" in manifest:
                parts.append(f"### LLM Instructions\n{manifest['llm_instructions']}\n")

        # 2. ToolContext 데이터
        parts.append(context.to_markdown())

        return "\n\n".join(parts)

    @staticmethod
    def ingest_result_to_crow(
        tool_name: str,
        context: ToolContext,
        llm_result: str,
        polarity: float = 0.5,
    ):
        """LLM 분석 결과를 Crow Memory에 저장

        Args:
            tool_name: 도구명
            context: ToolContext 인스턴스
            llm_result: LLM 생성 결과 문자열
            polarity: Crow Memory 극성값
        """
        payload = {
            "tool": tool_name,
            "context_summary": json.dumps(context.data, default=str, ensure_ascii=False)[:500],
            "llm_result_summary": llm_result[:1000],
            "timestamp": time.time(),
        }
        try_crow_ingest(
            content=json.dumps(payload, ensure_ascii=False),
            register="arch",
        )


# ── 편의 함수 ────────────────────────────────────────


def prepare_llm_context(tool_name: str, **kwargs) -> str:
    """단일 함수로 LLM 컨텍스트 준비 (collect + analyze 한 번에)

    Args:
        tool_name: 도구명
        **kwargs: ToolContext.data에 저장될 데이터

    Returns:
        LLM 프롬프트에 바로 포함할 수 있는 마크다운 문자열
    """
    ctx = LLMToolPipeline.collect(tool_name, **kwargs)
    return LLMToolPipeline.prepare_for_llm(tool_name, ctx)


__all__ = [
    "LLMToolPipeline",
    "prepare_llm_context",
]
