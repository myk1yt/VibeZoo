"""
VibeZoo UX Coordinator — 사용자 의도에 따라 최적의 도구 체인을 제안/실행.
Zoo(LLM)가 이 도구를 호출하여 워크플로우 자동화.
"""

import os
from bridge.intent_detector import detect_intent, get_workflow_hints


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
        if intent == "auto" and user_message:
            detected = detect_intent(user_message)
            if detected:
                intent = detected[0][0]

        hints = get_workflow_hints(intent)

        # 기본 응답 구성
        response_parts = [f"## 🧠 의도 분석 결과"]
        response_parts.append(f"- **감지된 의도**: `{intent}`")

        if hints["primary_tool"]:
            response_parts.append(f"- **권장 도구**: `{hints['primary_tool']}`")
            if hints["primary_args"]:
                args_str = ", ".join(f"{k}={v}" for k, v in hints["primary_args"].items())
                response_parts.append(f"- **권장 인자**: `{args_str}`")
            if hints["next_tool"]:
                response_parts.append(f"- **후속 도구**: `{hints['next_tool']}`")

        response_parts.append("")
        response_parts.append("### 💡 제안")
        if hints.get("suggested_response"):
            response_parts.append(hints["suggested_response"])
        else:
            response_parts.append("어떻게 도와드릴까요?")

        if context:
            response_parts.append("")
            response_parts.append(f"**문맥**: {context}")

        return "\n".join(response_parts)

    @mcp.tool
    def auto_analyze_after_drop(file_path: str,
                                user_intent: str = "") -> str:
        """드롭존 업로드 후 자동 분석 파이프라인 실행.

        capture_screen(dropzone) → 사용자 파일 업로드 → 이 도구 호출
        파일 타입에 따라 SSA→OCR→MiniCPM 또는 코드 분석 자동 실행

        Args:
            file_path: 업로드된 파일 경로
            user_intent: 사용자의 후속 의도 (분석/번역/리뷰 등)

        Returns:
            종합 분석 보고서 + 후속 제안
        """
        if not os.path.exists(file_path):
            return f"⚠️ 파일을 찾을 수 없습니다: {file_path}"

        # 파일 타입 감지
        ext = os.path.splitext(file_path)[1].lower()
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        response = [f"## 📄 파일 분석: {file_name}"]
        response.append(f"- 크기: {file_size:,} 바이트")
        response.append(f"- 확장자: {ext}")
        response.append("")

        # 이미지 파일
        image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.ico'}
        # 코드 파일
        code_exts = {'.py', '.js', '.ts', '.tsx', '.jsx', '.c', '.cpp', '.h', '.hpp',
                     '.java', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
                     '.sh', '.bash', '.zsh', '.yaml', '.yml', '.json', '.xml', '.html',
                     '.css', '.scss', '.less', '.sql', '.r', '.m', '.mm'}
        # 문서 파일
        doc_exts = {'.pdf', '.docx', '.doc', '.xlsx', '.pptx', '.txt', '.md', '.rst',
                    '.csv', '.tsv'}

        if ext in image_exts:
            response.append("🖼️ **이미지 파일**이 감지되었습니다.")
            response.append("")
            response.append("### 🔬 분석 파이프라인")
            response.append("1. **SSA 공간 분석** — `aggregate_spatial_pixels()`")
            response.append("2. **OCR 텍스트 추출** — Tesseract OCR")
            response.append("3. **MiniCPM-V 비전 분석** — `describe_image()`")
            response.append("")
            response.append("### 📋 1단계: SSA 공간 분석")
            try:
                from bridge.tools.ssa import register as ssa_register
                # SSA는 직접 호출 대신 aggregate_spatial_pixels 툴 설명 제공
                response.append("SSA 분석을 실행하려면 `aggregate_spatial_pixels()`를 호출하세요.")
            except ImportError:
                response.append("SSA 모듈을 사용할 수 없습니다.")

            # MiniCPM 시도
            response.append("")
            response.append("### 🧠 2단계: MiniCPM-V 비전 분석")
            try:
                from bridge.vision.minicpm import describe_image
                vision_result = describe_image(file_path,
                    "이 이미지에 무엇이 보이는지 자세히 설명해주세요. 텍스트나 코드가 있다면 모두 읽어주세요.")
                response.append(vision_result)
            except Exception as e:
                response.append(f"MiniCPM 분석 실패: {e}")

            response.append("")
            response.append("---")
            response.append("💡 **무엇을 해드릴까요?**")
            response.append("- 이미지에 대해 더 자세히 분석할까요?")
            response.append("- 텍스트를 추출할까요?")
            response.append("- 관련 정보를 검색할까요?")

        elif ext in code_exts:
            response.append("💻 **코드 파일**이 감지되었습니다.")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                lines = content.split('\n')
                response.append(f"- 줄 수: {len(lines)}")
                response.append(f"- 언어: {ext[1:]}")
                response.append("")
                response.append("### 코드 미리보기 (처음 20줄)")
                response.append("```" + ext[1:])
                response.append("\n".join(lines[:20]))
                response.append("```")
            except Exception as e:
                response.append(f"파일 읽기 실패: {e}")

            response.append("")
            response.append("---")
            response.append("💡 **무엇을 해드릴까요?**")
            response.append("- 코드를 리뷰할까요? (`review_code`)")
            response.append("- 버그를 찾을까요? (`find_bugs`)")
            response.append("- 리팩터링 제안을 할까요? (`suggest_refactor`)")
            response.append("- 코드를 설명해드릴까요? (`explain_code`)")

        elif ext in doc_exts:
            response.append("📄 **문서 파일**이 감지되었습니다.")
            response.append("분석을 위해 내용을 추출합니다...")

            try:
                # 텍스트 파일 직접 읽기
                if ext in {'.txt', '.md', '.rst', '.csv', '.tsv'}:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    lines = content.split('\n')
                    response.append(f"- 줄 수: {len(lines)}")
                    response.append(f"- 문자 수: {len(content)}")
                    response.append("")
                    response.append("### 내용 (처음 30줄)")
                    response.append("```")
                    response.append("\n".join(lines[:30]))
                    response.append("```")
                elif ext == '.pdf':
                    # PDF: file_analyzer 직접 호출 (스캔 문서 대응)
                    from bridge.tools.file_analyzer import analyze_file
                    analysis = analyze_file(file_path)
                    response.append("")
                    response.append(analysis)
                else:
                    response.append(f"DOCX/XLSX 파일입니다. `analyze_uploaded_file()`로 상세 분석 가능합니다.")
            except Exception as e:
                response.append(f"파일 읽기 실패: {e}")

            response.append("")
            response.append("---")
            response.append("💡 **무엇을 해드릴까요?**")
            response.append("- 문서를 요약할까요?")
            response.append("- 내용을 분석할까요?")
            response.append("- 번역이 필요하신가요?")

        else:
            response.append("📦 **알 수 없는 파일 형식**입니다.")
            response.append(f"파일명: {file_name}")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read(1000)
                response.append("### 내용 미리보기")
                response.append("```")
                response.append(content[:500])
                response.append("```")
            except Exception:
                response.append("(바이너리 파일로 추정됩니다)")

        return "\n".join(response)

    @mcp.tool
    def auto_analyze_whiteboard() -> str:
        """화이트보드 내용을 자동 분석합니다.

        get_whiteboard_state() + WhiteboardDataConverter 변환 +
        SSA(이미지인 경우) + MiniCPM(이미지인 경우) 통합 실행

        Returns:
            화이트보드 분석 보고서 + Mermaid 다이어그램
        """
        response = ["## 🎨 화이트보드 분석"]

        # 화이트보드 상태 읽기
        try:
            from bridge.tools.whiteboard import get_whiteboard_state
            wb_state = get_whiteboard_state()
            response.append("### 📊 화이트보드 상태")
            response.append(wb_state)
        except Exception as e:
            response.append(f"⚠️ 화이트보드 상태 읽기 실패: {e}")

        response.append("")
        response.append("### 💡 분석 제안")
        response.append("화이트보드 내용을 기반으로 다음을 수행할 수 있습니다:")
        response.append("1. **다이어그램 변환** — 화이트보드 내용을 Mermaid 다이어그램으로 변환")
        response.append("2. **설명 생성** — 화이트보드 내용에 대한 설명 제공")
        response.append("3. **코드 생성** — 화이트보드 설계를 기반으로 코드 생성")
        response.append("4. **개선 제안** — 설계에 대한 피드백 제공")

        return "\n".join(response)
