"""
자연어 의도 감지 모듈.
LLM 없이 키워드 + 패턴 매칭으로 사용자 의도를 빠르게 분류.
Zoo가 ux_coordinator를 호출할 때 힌트로 사용.
"""

# 의도 시그니처: (의도명, 우선순위, 키워드_리스트, 컨텍스트_키워드)
INTENT_SIGNATURES = [
    ("file_share", 10, [
        "파일", "보여줄게", "보여줘", "올릴게", "업로드", "첨부", "드래그",
        "이미지", "사진", "스크린샷", "캡처", "png", "jpg", "pdf",
        "show you", "upload", "attach", "file", "image", "screenshot"
    ], []),
    ("drawing_request", 9, [
        "그림", "그려줘", "다이어그램", "차트", "시각화", "그래프",
        "draw", "diagram", "chart", "visualize", "graph",
        "아키텍처", "구조도", "플로우", "흐름도"
    ], []),
    ("whiteboard_input", 8, [
        "화이트보드", "칠판", "그렸어", "그려놨어", "스케치",
        "whiteboard", "sketch", "drew", "drawing"
    ], []),
    ("code_analysis", 7, [
        "코드", "분석", "리뷰", "버그", "리팩터", "검색",
        "code", "analyze", "review", "bug", "refactor", "search"
    ], []),
    ("project_setup", 5, [
        "설치", "설정", "셋업", "초기화",
        "install", "setup", "init", "configure"
    ], []),
]


def detect_intent(user_message: str) -> list[tuple[str, int, float]]:
    """사용자 메시지에서 의도를 감지하여 (의도명, 우선순위, 신뢰도) 목록 반환"""
    results = []
    message_lower = user_message.lower()

    for intent_name, priority, keywords, _ in INTENT_SIGNATURES:
        matched = sum(1 for kw in keywords if kw.lower() in message_lower)
        if matched > 0:
            confidence = matched / max(len(keywords), 1) * 10.0
            # 정확한 문장 패턴 매칭으로 신뢰도 보정
            if intent_name == "file_share":
                # "보여줄게" 패턴
                if "보여줄게" in message_lower or "보여줘" in message_lower:
                    confidence += 3.0
                if "파일" in message_lower and ("보여줄게" in message_lower or "있어" in message_lower):
                    confidence += 2.0
            elif intent_name == "drawing_request":
                if "그려줘" in message_lower:
                    confidence += 3.0
            elif intent_name == "whiteboard_input":
                if "화이트보드" in message_lower:
                    confidence += 2.0

            results.append((intent_name, priority, min(confidence, 10.0)))

    # 우선순위 정렬 (높은 순)
    results.sort(key=lambda x: (-x[1], -x[2]))

    if not results:
        results.append(("general_question", 0, 1.0))

    return results


def get_workflow_hints(intent: str) -> dict:
    """의도에 따른 워크플로우 힌트 반환 (Zoo가 사용할 도구 체인 제안)"""
    workflow_map = {
        "file_share": {
            "primary_tool": "capture_screen",
            "primary_args": {"source": "dropzone"},
            "next_tool": "auto_analyze_after_drop",
            "description": "드롭존을 열어 파일 업로드를 요청합니다. 파일이 업로드되면 자동 분석합니다.",
            "suggested_response": "파일을 여기로 드래그하거나 업로드해 주세요. 업로드하시면 분석해 드리겠습니다."
        },
        "drawing_request": {
            "primary_tool": "draw_on_whiteboard",
            "primary_args": {},
            "next_tool": None,
            "description": "화이트보드에 그림을 그립니다. 필요한 참고 자료가 있다면 search_codebase로 검색합니다.",
            "suggested_response": "어떤 다이어그램이나 그림을 원하시나요? 구체적으로 알려주시면 그려드리겠습니다."
        },
        "whiteboard_input": {
            "primary_tool": "get_whiteboard_state",
            "primary_args": {},
            "next_tool": "auto_analyze_whiteboard",
            "description": "화이트보드의 현재 상태를 읽고 분석합니다.",
            "suggested_response": "화이트보드 내용을 분석해 보겠습니다."
        },
        "code_analysis": {
            "primary_tool": "review_code",
            "primary_args": {},
            "next_tool": None,
            "description": "코드 리뷰, 버그 분석, 리팩터링 제안 등을 수행합니다.",
            "suggested_response": "어떤 코드를 분석할까요? 파일 경로를 알려주세요."
        },
        "project_setup": {
            "primary_tool": "vibezoo_setup",
            "primary_args": {},
            "next_tool": None,
            "description": "VibeZoo 설치 및 설정을 진행합니다.",
            "suggested_response": "VibeZoo 설정을 진행하겠습니다. 설치 대상을 선택해 주세요."
        },
        "general_question": {
            "primary_tool": None,
            "primary_args": {},
            "next_tool": None,
            "description": "일반적인 질문에 답변합니다.",
            "suggested_response": None
        }
    }
    return workflow_map.get(intent, workflow_map["general_question"])
