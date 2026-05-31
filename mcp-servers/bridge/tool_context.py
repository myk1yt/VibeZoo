# VibeZoo Bridge — ToolContext + tool_manifest
# LLM-도구 체인: 도구 수집 데이터 → LLM 분석 연결

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# ── tool_manifest 상수 ──────────────────────────────
# 각 도구가 수집하는 데이터와 LLM 지시서를 정의
# LLM이 이 manifest를 읽고 분석 방향을 결정함

MANIFEST_EXPLAIN_CODE = {
    "tool": "explain_code",
    "version": "1.0",
    "description": "특정 라인의 코드가 무엇을 하는지 AST 컨텍스트 기반 설명",
    "data_collected": {
        "function_name": "감싸고 있는 함수명 (있을 경우)",
        "class_name": "감싸고 있는 클래스명 (있을 경우)",
        "parameters": "함수 파라미터 목록",
        "return_type": "반환 타입 (TS/TSX)",
        "line_content": "해당 라인 코드",
        "surrounding_code": "전후 15줄 컨텍스트",
        "git_blame": "마지막 수정자, 날짜, 커밋 메시지",
        "related_tests": "관련 테스트 파일 (있는 경우)",
    },
    "llm_instructions": (
        "LLM은 이 데이터를 바탕으로 다음을 수행하세요:\n"
        "1. 이 코드가 속한 함수/클래스의 맥락 설명\n"
        "2. 해당 라인의 구체적 동작 설명\n"
        "3. 잠재적 문제점이나 개선 제안 (있을 경우)\n"
        "4. 관련 테스트 코드 (있을 경우)와의 연관성"
    ),
    "llm_load": "low",
}

MANIFEST_GENERATE_TESTS = {
    "tool": "generate_tests",
    "version": "1.0",
    "description": "함수 시그니처를 기반으로 단위 테스트 케이스 생성",
    "data_collected": {
        "source_path": "분석 대상 소스 파일 경로",
        "language": "감지된 프로그래밍 언어",
        "functions": "함수 목록 (이름, 파라미터, 반환 타입, 라인 범위)",
        "imports": "import/require 문 목록",
        "existing_tests": "기존 테스트 파일 정보 (있는 경우)",
        "branch_count": "조건부 분기문 수",
        "error_indicators": "에러 처리 패턴 (try-catch, null 체크 등)",
    },
    "llm_instructions": (
        "LLM은 이 데이터를 바탕으로:\n"
        "1. 각 파라미터의 경계값 테스트 케이스 생성\n"
        "2. null/undefined/빈 배열 등 edge case 포함\n"
        "3. 모킹이 필요한 의존성 식별\n"
        "4. 실제 동작하는 테스트 코드 생성"
    ),
    "llm_load": "high",
}

MANIFEST_FIND_BUGS = {
    "tool": "find_bugs",
    "version": "1.0",
    "description": "코드베이스에서 잠재적 버그 패턴 탐지 및 Crow Memory 과거 패턴 활용",
    "data_collected": {
        "target_path": "분석 대상 경로",
        "suspicious_patterns": "의심스러운 코드 패턴 목록 (console.log, debugger, .only 등)",
        "past_bugs_from_crow": "Crow Memory에서 가져온 과거 버그 패턴",
        "code_metrics": "코드 메트릭 (파일 수, 라인 수, 복잡도)",
        "pattern_analysis": "AST 기반 패턴 분석 결과 (안티패턴 포함)",
    },
    "llm_instructions": (
        "LLM은 이 데이터를 바탕으로:\n"
        "1. 각 의심 패턴의 심각도 분류 (P0: 크래시 위험, P1: 로직 버그, P2: 코드 스멜)\n"
        "2. Crow 과거 패턴과 교차 참조하여 유사 문제 식별\n"
        "3. 각 버그에 대해: 위치, 원인, 수정 제안, 영향도 추정\n"
        "4. 심각도 × 발생 빈도 × 파일 중요도로 우선순위 지정"
    ),
    "llm_load": "high",
}

MANIFEST_SUGGEST_REFACTOR = {
    "tool": "suggest_refactor",
    "version": "1.0",
    "description": "의존성 맵, 중복 패턴, 호출 그래프 기반 리팩토링 제안",
    "data_collected": {
        "target_path": "분석 대상 경로",
        "dependency_map": "모듈 간 의존성 관계",
        "pattern_duplications": "중복 코드 패턴",
        "call_graph": "함수 호출 그래프",
        "crow_style_rules": "Crow Memory 코딩 스타일 규칙",
    },
    "llm_instructions": (
        "LLM은 이 데이터를 바탕으로:\n"
        "1. 과도한 의존성을 가진 파일 (허브 모듈) 식별\n"
        "2. 순환 의존성 감지 및 분해 전략 제안\n"
        "3. 중복 코드 패턴 발견 및 추출 제안\n"
        "4. God 함수 (높은 팬아웃) 및 데드 코드 (팬인 0) 분석\n"
        "5. 각 제안에 대해: before/after 코드 예제, 영향도, 마이그레이션 단계 제공"
    ),
    "llm_load": "high",
}


# ── manifest 조회 헬퍼 ──────────────────────────────

_MANIFEST_REGISTRY: dict[str, dict] = {
    "explain_code": MANIFEST_EXPLAIN_CODE,
    "generate_tests": MANIFEST_GENERATE_TESTS,
    "find_bugs": MANIFEST_FIND_BUGS,
    "suggest_refactor": MANIFEST_SUGGEST_REFACTOR,
}


def get_manifest(tool_name: str) -> Optional[dict]:
    """도구명으로 manifest JSON 조회"""
    return _MANIFEST_REGISTRY.get(tool_name)


def format_manifest_markdown(tool_name: str) -> str:
    """manifest를 LLM이 읽기 쉬운 마크다운으로 변환"""
    manifest = get_manifest(tool_name)
    if not manifest:
        return ""

    lines = []
    lines.append(f"## Tool Manifest: `{manifest['tool']}` v{manifest['version']}")
    lines.append(f"\n### Description\n{manifest['description']}")
    lines.append(f"\n### Data Collected\n")

    data = manifest.get("data_collected", {})
    if data:
        lines.append("| Field | Description |")
        lines.append("|-------|-------------|")
        for field, desc in data.items():
            lines.append(f"| `{field}` | {desc} |")

    lines.append(f"\n### LLM Instructions\n{manifest['llm_instructions']}")
    lines.append(f"\n### Expected LLM Load\n{manifest.get('llm_load', 'medium')}")

    return "\n".join(lines)


# ── ToolContext ──────────────────────────────────────


@dataclass
class ToolContext:
    """도구 수집 데이터를 LLM에 전달하는 표준 컨테이너

    각 도구는 자신의 tool_manifest에 정의된 데이터 구조에 맞춰
    ToolContext를 채운 후, 결과 문자열에 포함하여 반환한다.
    LLM은 이 구조화된 데이터를 기반으로 의미 분석/판단을 수행한다.
    """

    tool_name: str
    data: dict[str, Any] = field(default_factory=dict)
    manifest: dict = field(default_factory=dict)
    collected_at: float = field(default_factory=time.time)
    source_file: str = ""
    language: str = ""

    # LLM 분석 지침 (manifest에서 자동 설정)
    llm_instructions: str = ""
    suggested_steps: list[str] = field(default_factory=list)

    def __post_init__(self):
        """manifest가 비어있으면 레지스트리에서 자동 로드"""
        if not self.manifest:
            self.manifest = get_manifest(self.tool_name) or {}
        if not self.llm_instructions and self.manifest:
            self.llm_instructions = self.manifest.get("llm_instructions", "")

    def to_markdown(self) -> str:
        """LLM이 이해하기 쉬운 마크다운 형식으로 직렬화

        Returns:
            LLM 프롬프트에 포함될 마크다운 문자열
        """
        lines = []
        lines.append(f"## ToolContext: `{self.tool_name}`")
        lines.append(f"- **Language**: {self.language or 'mixed'}")
        lines.append(f"- **Source file**: `{self.source_file}`")
        lines.append(f"- **Collected at**: {time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(self.collected_at))}")

        if self.manifest:
            lines.append(f"- **Manifest version**: {self.manifest.get('version', 'N/A')}")
            lines.append(f"- **Description**: {self.manifest.get('description', '')}")

        if self.llm_instructions:
            lines.append(f"\n### LLM Instructions\n{self.llm_instructions}")

        if self.suggested_steps:
            lines.append("\n### Suggested Analysis Steps")
            for i, step in enumerate(self.suggested_steps, 1):
                lines.append(f"{i}. {step}")

        if self.data:
            lines.append("\n### Collected Data")
            lines.append("```json")
            lines.append(json.dumps(self.data, indent=2, ensure_ascii=False, default=str))
            lines.append("```")

        return "\n".join(lines)

    def to_crow_rule(self, register: str = "life_context") -> dict:
        """Crow Memory rule 형식으로 변환

        Args:
            register: Crow 레지스터명 (기본: life_context)

        Returns:
            Crow ingest용 payload 딕셔너리
        """
        return {
            "key": f"{self.tool_name}_context",
            "value": json.dumps({
                "tool": self.tool_name,
                "language": self.language,
                "source_file": self.source_file,
                "instructions": self.llm_instructions,
                "steps": self.suggested_steps,
                "manifest_version": self.manifest.get("version", "1.0"),
            }, ensure_ascii=False),
            "register": register,
        }


# ── 도구별 팩토리 함수 ──────────────────────────────


def make_explain_code_context(
    file_path: str,
    line_number: int,
    language: str,
    symbol_info: dict,
    enclosing_scope: dict,
    references: list[dict],
    git_blame: Optional[dict] = None,
    related_tests: Optional[list[dict]] = None,
) -> ToolContext:
    """explain_code 도구용 ToolContext 생성

    Args:
        file_path: 분석 대상 파일 경로
        line_number: 분석 대상 라인 번호
        language: 프로그래밍 언어
        symbol_info: 심볼 정보 (name, kind, signature, line_range)
        enclosing_scope: 감싸는 스코프 (type, name, line_range)
        references: 참조 위치 목록
        git_blame: git blame 정보 (author, date, commit_message, commit_hash)
        related_tests: 관련 테스트 파일 목록

    Returns:
        explain_code용 ToolContext
    """
    ctx = ToolContext(
        tool_name="explain_code",
        data={
            "file_path": file_path,
            "line_number": line_number,
            "symbol_info": symbol_info,
            "enclosing_scope": enclosing_scope,
            "references": references,
            "git_blame": git_blame or {},
            "related_tests": related_tests or [],
        },
        source_file=file_path,
        language=language,
        suggested_steps=[
            "1. Identify what the code does based on symbol name and signature",
            "2. Explain the enclosing scope context (class/module role)",
            "3. Trace data flow through references (where inputs come from, where outputs go)",
            "4. Check git blame for recent change intent",
            "5. Verify expected behavior against related tests",
            "6. Mark uncertain inferences with [추정] tag",
        ],
    )
    return ctx


def make_generate_tests_context(
    source_path: str,
    language: str,
    functions: list[dict],
    imports: list[dict],
    existing_tests: list[dict],
) -> ToolContext:
    """generate_tests 도구용 ToolContext 생성

    Args:
        source_path: 분석 대상 소스 파일 경로
        language: 프로그래밍 언어
        functions: 함수 목록 (name, params, return_type, line, end_line)
        imports: import 문 목록
        existing_tests: 기존 테스트 파일 정보

    Returns:
        generate_tests용 ToolContext
    """
    ctx = ToolContext(
        tool_name="generate_tests",
        data={
            "source_path": source_path,
            "language": language,
            "functions": functions,
            "imports": imports,
            "existing_tests": existing_tests,
        },
        source_file=source_path,
        language=language,
        suggested_steps=[
            "1. For each function, identify input types and edge cases",
            "2. Generate test cases for: normal operation, boundary values, null/undefined, error conditions",
            "3. If async functions, include timing/delay scenarios",
            "4. Generate mock/stub templates for external dependencies",
            "5. Check existing tests to avoid duplication",
        ],
    )
    return ctx


def make_find_bugs_context(
    target_path: str,
    suspicious_patterns: list[dict],
    crow_past_bugs: list[dict],
    code_metrics: dict,
) -> ToolContext:
    """find_bugs 도구용 ToolContext 생성

    Args:
        target_path: 분석 대상 경로
        suspicious_patterns: 의심 패턴 목록
        crow_past_bugs: Crow Memory 과거 버그 패턴
        code_metrics: 코드 메트릭 정보

    Returns:
        find_bugs용 ToolContext
    """
    ctx = ToolContext(
        tool_name="find_bugs",
        data={
            "target_path": target_path,
            "suspicious_patterns": suspicious_patterns,
            "past_bugs_from_crow": crow_past_bugs,
            "code_metrics": code_metrics,
        },
        language="mixed",
        suggested_steps=[
            "1. Classify each suspicious pattern by severity (P0: crash risk, P1: logic bug, P2: code smell)",
            "2. Cross-reference with Crow past bug patterns for similar issues",
            "3. For each bug, provide: location, probable cause, suggested fix, impact estimate",
            "4. Prioritize by: severity × occurrence frequency × file importance",
        ],
    )
    return ctx


def make_suggest_refactor_context(
    target_path: str,
    dependency_map: dict,
    pattern_duplications: list[dict],
    call_graph: dict,
    crow_style_rules: list[dict],
) -> ToolContext:
    """suggest_refactor 도구용 ToolContext 생성

    Args:
        target_path: 분석 대상 경로
        dependency_map: 모듈 의존성 맵
        pattern_duplications: 중복 패턴 목록
        call_graph: 호출 그래프
        crow_style_rules: Crow Memory 스타일 규칙

    Returns:
        suggest_refactor용 ToolContext
    """
    ctx = ToolContext(
        tool_name="suggest_refactor",
        data={
            "target_path": target_path,
            "dependency_map": dependency_map,
            "pattern_duplications": pattern_duplications,
            "call_graph": call_graph,
            "crow_style_rules": crow_style_rules,
        },
        language="mixed",
        suggested_steps=[
            "1. Identify files with excessive dependencies (hub modules)",
            "2. Detect circular dependencies and propose break strategies",
            "3. Find duplicated code patterns and suggest extraction",
            "4. Analyze call graph for God functions (high fan-out) and dead code (zero fan-in)",
            "5. For each suggestion, provide: before/after code example, impact estimate, migration steps",
        ],
    )
    return ctx


# ── 공개 API ────────────────────────────────────────

__all__ = [
    "ToolContext",
    # Manifest 상수
    "MANIFEST_EXPLAIN_CODE",
    "MANIFEST_GENERATE_TESTS",
    "MANIFEST_FIND_BUGS",
    "MANIFEST_SUGGEST_REFACTOR",
    # Manifest 헬퍼
    "get_manifest",
    "format_manifest_markdown",
    # 팩토리 함수
    "make_explain_code_context",
    "make_generate_tests_context",
    "make_find_bugs_context",
    "make_suggest_refactor_context",
]
