"""
자연어 의도 감지 모듈.
LLM 없이 키워드 + 패턴 매칭으로 사용자 의도를 빠르게 분류.
Zoo가 ux_coordinator를 호출할 때 힌트로 사용.

Pillar 2: Crow-Aware Contextual Intent Routing
  - Crow Memory 컨텍스트 기반 의도 바이어스 (v2.0 D7: 단일 호출)
  - Dropzone 시간적 바인딩 (v2.0 D1 연계)
  - fix_loop 의도 추가 (v2.0 D6)
"""

import os
import time
from typing import Optional

from bridge.config import DZ_SESSION_FILE


# ── 상수 ─────────────────────────────────────────────────

CROW_BIAS_WEIGHT = 0.4           # Crow 컨텍스트 바이어스 가중치
DZ_BIAS_WEIGHT = 0.6             # Dropzone 시간적 바이어스 가중치
LOW_CONFIDENCE_THRESHOLD = 3.0   # 이 임계값 미만이면 Crow/DZ 보강
DZ_TIME_THRESHOLD_MINUTES = 3    # Dropzone 세션 유효 시간 (분)

DEMONSTRATIVES = [
    # 한국어
    "이거", "그거", "저거", "방금", "아까",
    "이 파일", "그 파일", "저 파일",
    "올린", "올렸", "첨부", "업로드",
    "여기", "저기",
    # 영어
    "this", "that", "it", "the file",
    "just now", "recently", "uploaded", "attached",
]


# ── INTENT_SIGNATURES ────────────────────────────────────

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
    # [v2.0 D6] fix_loop 의도 추가
    ("fix_loop", 7, [
        "고쳐줘", "버그", "수정", "에러", "오류", "고장",
        "fix", "bug", "error", "crash", "issue", "fail",
        "디버그", "debug", "패치", "patch"
    ], []),
    # [v2.0 D6] code_analysis priority 7→6 (fix_loop이 7을 차지)
    ("code_analysis", 6, [
        "코드", "분석", "리뷰", "리팩터", "검색",
        "code", "analyze", "review", "refactor", "search"
    ], []),
    ("project_setup", 5, [
        "설치", "설정", "셋업", "초기화",
        "install", "setup", "init", "configure"
    ], []),
]


# ── 헬퍼 함수 ────────────────────────────────────────────


def _has_demonstrative(message: str) -> bool:
    """한국어/영어 지시 대명사 포함 여부 확인."""
    msg = message.lower()
    return any(d.lower() in msg for d in DEMONSTRATIVES)


def _get_default_priority(intent_name: str) -> int:
    """알려지지 않은 의도의 기본 우선순위 반환."""
    priority_map = {
        "file_share": 10,
        "drawing_request": 9,
        "whiteboard_input": 8,
        "fix_loop": 7,
        "code_analysis": 6,
        "project_setup": 5,
        "general_question": 0,
    }
    return priority_map.get(intent_name, 5)


# ── STEP 1: 키워드 매칭 ──────────────────────────────────


def _keyword_match(user_message: str) -> tuple[list, float]:
    """기존 키워드 매칭 로직 (분리) → (results, max_confidence)

    v2.0 변경:
      - D6: fix_loop 시그니처 매칭 로직 포함
      - 지시 대명사 감지 시 약한 file_share 신호 추가
    """
    results = []
    max_confidence = 0.0
    message_lower = user_message.lower()

    for intent_name, priority, keywords, _ in INTENT_SIGNATURES:
        matched = sum(1 for kw in keywords if kw.lower() in message_lower)
        if matched > 0:
            confidence = matched / max(len(keywords), 1) * 10.0

            # 정확한 문장 패턴 매칭으로 신뢰도 보정
            if intent_name == "file_share":
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
            # [v2.0 D6] fix_loop 패턴 보정
            elif intent_name == "fix_loop":
                if "고쳐줘" in message_lower:
                    confidence += 3.0
                if "버그" in message_lower or "에러" in message_lower:
                    confidence += 2.0

            confidence = min(confidence, 10.0)
            results.append((intent_name, priority, confidence))
            max_confidence = max(max_confidence, confidence)

    # [v2.0] 지시 대명사 감지 → 약한 file_share 신호 추가 (Crow/DZ 바이어스로 증폭)
    if _has_demonstrative(user_message):
        existing = {r[0]: i for i, r in enumerate(results)}
        if "file_share" not in existing:
            results.append(("file_share", 10, 0.5))
            max_confidence = max(max_confidence, 0.5)

    return results, max_confidence


# ── STEP 2: Crow Memory Bias ─────────────────────────────


def _query_crow_for_bias(user_message: str) -> Optional[dict]:
    """Crow Memory에서 최근 컨텍스트를 조회하여 의도 바이어스 계산.

    [v2.0 D7] 단일 호출로 통합: context/bug/arch 3회 호출 → 1회 호출

    Returns:
        {"active_registers": [...], "bias": {intent_name: score, ...}}
        또는 None (Crow 비활성 / 실패)
    """
    try:
        from bridge.crow_client import try_crow_recall

        # [v2.0 D7] 단일 호출로 통합
        all_results = try_crow_recall("recent_context", register="context", limit=3)

        if not all_results:
            return None

        bias = {}
        active_registers = []

        # 결과 텍스트 기반 분석
        context_text = " ".join(str(r) for r in all_results).lower()

        active_registers.append("context")

        # 디버깅/버그 수정 컨텍스트
        if any(kw in context_text for kw in ["debug", "bug", "error", "fix", "에러", "버그", "디버깅", "고쳐"]):
            bias["code_analysis"] = bias.get("code_analysis", 0) + 2.5
            bias["fix_loop"] = bias.get("fix_loop", 0) + 3.0

        # 파일/편집 컨텍스트
        if any(kw in context_text for kw in ["file", "edit", "patch", "파일", "수정", "편집"]):
            bias["file_share"] = bias.get("file_share", 0) + 2.0

        # 아키텍처/설계 컨텍스트
        if any(kw in context_text for kw in ["arch", "design", "architecture", "설계", "구조"]):
            active_registers.append("arch")
            bias["drawing_request"] = bias.get("drawing_request", 0) + 2.0
            bias["code_analysis"] = bias.get("code_analysis", 0) + 1.5

        # 버그 레지스터 컨텍스트 감지
        if any(kw in context_text for kw in ["bug", "fix_loop", "auto_fix"]):
            active_registers.append("bug")
            bias["fix_loop"] = bias.get("fix_loop", 0) + 3.0
            bias["code_analysis"] = bias.get("code_analysis", 0) + 2.0

        if not bias:
            return None

        return {
            "active_registers": active_registers,
            "bias": bias,
        }
    except Exception:
        return None


# ── STEP 3: Dropzone Session Check ───────────────────────


def _check_dropzone_session(user_message: str) -> Optional[dict]:
    """dz_session.json 확인 → 3분 이내 업로드 + 지시 대명사 → file_share 바이어스.

    Returns:
        {
            "file_path": str,
            "file_name": str,
            "uploaded_at": float,
            "seconds_ago": int,
            "has_demonstrative": bool,
        }
        또는 None
    """
    import json

    dz_file = os.path.expanduser(DZ_SESSION_FILE)
    if not os.path.exists(dz_file):
        return None

    try:
        with open(dz_file, 'r', encoding='utf-8', errors='replace') as f:
            session = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    last_upload = session.get("last_upload")
    if not last_upload:
        return None

    uploaded_ts = last_upload.get("timestamp")
    if not uploaded_ts:
        return None

    now = time.time()
    seconds_ago = now - uploaded_ts

    if seconds_ago > DZ_TIME_THRESHOLD_MINUTES * 60:
        return None  # 너무 오래됨

    has_demonstrative = _has_demonstrative(user_message)

    return {
        "file_path": last_upload.get("file_path", ""),
        "file_name": last_upload.get("file_name", ""),
        "uploaded_at": uploaded_ts,
        "seconds_ago": int(seconds_ago),
        "has_demonstrative": has_demonstrative,
    }


# ── Bias Application ─────────────────────────────────────


def _apply_crow_bias(results: list, crow_bias: dict) -> list:
    """Crow Memory 바이어스를 기존 결과에 적용.

    각 intent의 confidence에 crow_bias.get(intent_name, 0) * CROW_BIAS_WEIGHT 더함.
    """
    bias_map = crow_bias.get("bias", {})
    if not bias_map:
        return results

    existing_intents = {r[0]: i for i, r in enumerate(results)}

    for intent_name, bias_value in bias_map.items():
        if intent_name in existing_intents:
            idx = existing_intents[intent_name]
            name, priority, confidence = results[idx]
            new_confidence = min(confidence + bias_value * CROW_BIAS_WEIGHT, 10.0)
            results[idx] = (name, priority, new_confidence)
        else:
            # 새로운 의도 추가
            priority = _get_default_priority(intent_name)
            confidence = min(bias_value * CROW_BIAS_WEIGHT, 10.0)
            results.append((intent_name, priority, confidence))

    return results


def _apply_dz_bias(results: list, dz_info: dict) -> list:
    """Dropzone 시간적 바인딩 바이어스 적용.

    recency * DZ_BIAS_WEIGHT * 10.0 만큼 file_share 의도 증폭.
    없으면 새로 추가.
    """
    has_demonstrative = dz_info.get("has_demonstrative", False)
    seconds_ago = dz_info.get("seconds_ago", 999)

    recency_factor = max(0, 1.0 - (seconds_ago / (DZ_TIME_THRESHOLD_MINUTES * 60)))
    bias_strength = recency_factor * (0.8 if has_demonstrative else 0.4)
    bias_value = bias_strength * 10.0 * DZ_BIAS_WEIGHT

    if bias_value <= 0:
        return results

    existing = {r[0]: i for i, r in enumerate(results)}
    if "file_share" in existing:
        idx = existing["file_share"]
        name, priority, confidence = results[idx]
        results[idx] = (name, priority, min(confidence + bias_value, 10.0))
    else:
        results.append(("file_share", 10, min(bias_value, 10.0)))

    return results


# ── V2: 통합 의도 감지 ──────────────────────────────────


def detect_intent_v2(user_message: str) -> dict:
    """Crow-Aware 통합 의도 감지 (v2).

    4단계 통합:
      - STEP 1: _keyword_match() (기존 detect_intent 로직)
      - STEP 2: max_conf < 3.0이면 _query_crow_for_bias() → _apply_crow_bias()
      - STEP 3: 항상 _check_dropzone_session() → _apply_dz_bias()
      - STEP 4: sort((priority, confidence))

    Returns:
        {
            "intents": [(name, priority, confidence), ...],
            "metadata": {
                "crow_used": bool,
                "dz_recent": bool,
                "dz_file_path": str | None,
                "adjustments": list[dict],
            }
        }
    """
    # STEP 1: 기존 키워드 매칭
    results, max_confidence = _keyword_match(user_message)

    metadata = {
        "crow_used": False,
        "dz_recent": False,
        "dz_file_path": None,
        "adjustments": [],
    }

    # STEP 2: 저신뢰도 → Crow Memory 보강 [v2.0 D7] 단일 호출로 통합
    if max_confidence < LOW_CONFIDENCE_THRESHOLD:
        crow_bias = _query_crow_for_bias(user_message)
        if crow_bias:
            metadata["crow_used"] = True
            results = _apply_crow_bias(results, crow_bias)
            metadata["adjustments"].append({
                "source": "crow_memory",
                "details": crow_bias,
            })

    # STEP 3: Dropzone 시간적 바인딩
    dz_info = _check_dropzone_session(user_message)
    if dz_info:
        metadata["dz_recent"] = True
        metadata["dz_file_path"] = dz_info.get("file_path")
        results = _apply_dz_bias(results, dz_info)
        metadata["adjustments"].append({
            "source": "dropzone",
            "details": dz_info,
        })

    # STEP 4: 병합 및 정렬
    results.sort(key=lambda x: (-x[1], -x[2]))
    if not results:
        results = [("general_question", 0, 1.0)]

    return {"intents": results, "metadata": metadata}


# ── V1: 하위 호환 래퍼 ──────────────────────────────────


def detect_intent(user_message: str) -> list[tuple[str, int, float]]:
    """사용자 메시지에서 의도를 감지하여 (의도명, 우선순위, 신뢰도) 목록 반환.

    하위 호환 래퍼 — 내부적으로 detect_intent_v2() 호출.
    """
    result = detect_intent_v2(user_message)
    return result["intents"]


# ── 워크플로우 힌트 ──────────────────────────────────────


def get_workflow_hints(intent: str) -> dict:
    """의도에 따른 워크플로우 힌트 반환 (Zoo가 사용할 도구 체인 제안)"""
    workflow_map = {
        "file_share": {
            "primary_tool": "capture_screen",
            "primary_args": {"source": "dropzone"},
            "next_tool": "analyze_uploaded_file",
            "description": "드롭존을 열어 파일 업로드를 요청합니다. 파일이 업로드되면 analyze_uploaded_file(file_path, track_dropzone=True)로 분석합니다.",
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
            "next_tool": "get_whiteboard_state",
            "description": "화이트보드의 현재 상태를 읽고 분석합니다.",
            "suggested_response": "화이트보드 내용을 분석해 보겠습니다."
        },
        # [v2.0 D6] fix_loop 워크플로우 힌트
        "fix_loop": {
            "primary_tool": "auto_fix_status",
            "primary_args": {},
            "next_tool": "retry_build",
            "description": "빌드 에러를 분석하고 자동 수정을 진행합니다.",
            "suggested_response": "빌드 에러를 확인하고 자동 수정을 시작하겠습니다."
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
