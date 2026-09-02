"""
VibeZoo UX Coordinator — 사용자 의도에 따라 최적의 도구 체인을 제안/실행.
Zoo(LLM)가 이 도구를 호출하여 워크플로우 자동화.

Pillar 2: Crow-Aware Contextual Intent Routing
  - detect_intent_v2() 기반 의도 감지 + 메타데이터 표시
"""

import os
from bridge.intent_detector import detect_intent_v2, get_workflow_hints
from bridge.i18n import t


# ── MCP 도구 등록 ────────────────────────────────────────


def register(mcp):
    @mcp.tool
    def ux_coordinator(intent: str = "auto", user_message: str = "",
                       context: str = "") -> str:
        """사용자 의도를 분석하고 최적의 VibeZoo 도구 체인을 제안합니다.

        Zoo는 이 도구를 사용하여:
        1. 사용자 메시지에서 의도 자동 감지 (intent="auto")
        2. 의도에 맞는 도구 체인 제안 받기
        3. 다음 액션 결정에 참고

        Args:
            intent: 의도 유형 ("auto"=자동감지, "file_share", "drawing_request",
                    "whiteboard_input", "code_analysis", "project_setup")
            user_message: 사용자 원본 메시지 (intent="auto"일 때 필요)
            context: 추가 문맥 (현재 화이트보드 상태, 열린 파일 등)

        Returns:
            마크다운 형식의 워크플로우 제안
        """
        metadata = {}

        if intent == "auto" and user_message:
            # [v2.0] detect_intent_v2 사용
            result = detect_intent_v2(user_message)
            intents = result["intents"]
            metadata = result["metadata"]

            if intents:
                intent = intents[0][0]

                # [NEW] Dropzone 바인딩: file_path 자동 주입
                if intent == "file_share" and metadata.get("dz_file_path"):
                    pass

        hints = get_workflow_hints(intent)

        # 응답 구성
        response_parts = [f"## 🧠 {t('Intent Analysis Result')}"]
        response_parts.append(f"- **{t('Detected intent')}**: `{intent}`")

        # 메타데이터 표시
        if metadata.get("crow_used"):
            response_parts.append(f"- **{t('Crow context')}**: {t('activated')}")
        if metadata.get("dz_recent"):
            file_name = os.path.basename(metadata.get("dz_file_path", ""))
            response_parts.append(f"- **{t('Recent upload')}**: `{file_name}` ({t('Dropzone binding')})")

        if hints["primary_tool"]:
            response_parts.append(f"- **{t('Recommended tool')}**: `{hints['primary_tool']}`")
            if hints["primary_args"]:
                args_str = ", ".join(f"{k}={v}" for k, v in hints["primary_args"].items())
                response_parts.append(f"- **{t('Recommended arguments')}**: `{args_str}`")
            if hints["next_tool"]:
                response_parts.append(f"- **{t('Next tool')}**: `{hints['next_tool']}`")

        response_parts.append("")
        response_parts.append(f"### 💡 {t('Suggestions')}")
        if hints.get("suggested_response"):
            response_parts.append(hints["suggested_response"])
        else:
            response_parts.append(t("How can I help you?"))

        # [NEW] file_share + dz_file_path → 자동 분석 제안
        if intent == "file_share" and metadata.get("dz_file_path"):
            dz_path = metadata["dz_file_path"]
            response_parts.append("")
            response_parts.append(f"### 📎 {t('Dropzone Auto Binding')}")
            response_parts.append(t("A recently uploaded file was detected: `{0}`", os.path.basename(dz_path)))
            response_parts.append(t("Suggest calling `auto_analyze_after_drop(file_path=\"{0}\")`.", dz_path))

        if context:
            response_parts.append("")
            response_parts.append(f"**{t('Context')}**: {context}")

        return "\n".join(response_parts)
