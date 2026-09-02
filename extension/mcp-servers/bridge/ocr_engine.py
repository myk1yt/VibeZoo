# VibeZoo Bridge — OCR 엔진
# Tesseract 우선, PaddleOCR fallback
# 선택적 의존성: 둘 다 없으면 OCR 비활성화 (기존 SSA 동작 유지)

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ── Tesseract 윈도우 기본 설치 경로 ─────────────────────

_TESSERACT_WINDOWS_PATHS = []
if os.environ.get("TESSERACT_PATH"):
    _TESSERACT_WINDOWS_PATHS.append(os.environ["TESSERACT_PATH"])

for _pf_env in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432", "LOCALAPPDATA"):
    _pf_dir = os.environ.get(_pf_env)
    if _pf_dir:
        _TESSERACT_WINDOWS_PATHS.append(os.path.join(_pf_dir, "Tesseract-OCR", "tesseract.exe"))

# 사용자 환경변수 PATH에서 tesseract 찾기
_TESSERACT_PATH: Optional[str] = None


def _find_tesseract_windows() -> Optional[str]:
    """Windows에서 tesseract 실행 파일 경로 탐색"""
    for p in _TESSERACT_WINDOWS_PATHS:
        if os.path.exists(p):
            return p

    # PATH에서 tesseract 검색
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path_dir, "tesseract.exe")
        if os.path.exists(candidate):
            return candidate

    return None


def _find_tesseract() -> Optional[str]:
    """플랫폼에 맞게 tesseract 실행 파일 경로 반환"""
    global _TESSERACT_PATH
    if _TESSERACT_PATH is not None:
        return _TESSERACT_PATH

    if sys.platform == "win32":
        _TESSERACT_PATH = _find_tesseract_windows()
    else:
        # Linux/macOS: PATH에서 tesseract 찾기
        try:
            result = subprocess.run(
                ["which", "tesseract"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                _TESSERACT_PATH = result.stdout.strip()
            else:
                _TESSERACT_PATH = None
        except Exception:
            _TESSERACT_PATH = None

    return _TESSERACT_PATH


# ── OCR 엔진 클래스 ────────────────────────────────────


class OcrEngine:
    """OCR 엔진 — Tesseract 우선, PaddleOCR fallback.

    선택적 의존성: pytesseract + tesseract CLI, 또는 PaddleOCR.
    둘 다 없으면 OCR 비활성화 상태로 동작 (``is_available()`` → ``False``).
    """

    def __init__(self):
        self._tesseract_available: Optional[bool] = None
        self._paddle_available: Optional[bool] = None
        self._active_engine: Optional[str] = None

    # ── 상태 확인 ──────────────────────────────────────

    def is_available(self) -> bool:
        """어떤 OCR 엔진이든 사용 가능한지 여부"""
        return self.tesseract_available() or self.paddle_available()

    def tesseract_available(self) -> bool:
        """pytesseract + tesseract CLI 설치 확인"""
        if self._tesseract_available is not None:
            return self._tesseract_available

        try:
            import pytesseract  # type: ignore[import]

            # tesseract 실행 파일 확인
            tess_path = _find_tesseract()
            if tess_path is None:
                self._tesseract_available = False
                return False

            # pytesseract에 경로 설정
            pytesseract.pytesseract.tesseract_cmd = tess_path  # type: ignore[attr-defined]

            # 버전 확인
            result = subprocess.run(
                [tess_path, "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                self._tesseract_available = True
                self._active_engine = "tesseract"
                return True
        except Exception:
            pass

        self._tesseract_available = False
        return False

    def paddle_available(self) -> bool:
        """PaddleOCR 설치 확인"""
        if self._paddle_available is not None:
            return self._paddle_available

        try:
            from paddleocr import PaddleOCR  # type: ignore[import]
            self._paddle_available = True
            if not self._active_engine:
                self._active_engine = "paddle"
            return True
        except ImportError:
            self._paddle_available = False
            return False

    # ── 언어 감지 ──────────────────────────────────────

    @staticmethod
    def _detect_language(image_path: str, lang: str = "auto") -> str:
        """이미지 경로/파일명에서 언어 추론.

        ``lang="auto"``일 때:
          - 파일명/경로에 ``kor``, ``한글``, ``한국어`` 포함 → ``"kor"``
          - ``chi``, ``cn``, ``중국어`` 포함 → ``"chi_sim"``
          - ``jpn``, ``jp``, ``일본어`` 포함 → ``"jpn"``
          - 그 외 → ``"eng"``

        Args:
            image_path: 이미지 파일 경로
            lang: 사용자 지정 언어 ("auto"이면 자동 추론)

        Returns:
            감지된 언어 코드 ("eng", "kor", "chi_sim", "jpn")
        """
        if lang != "auto":
            return lang

        fname = os.path.basename(image_path).lower()
        path_lower = image_path.lower()

        # 파일명/경로 기반 언어 추론
        kor_hints = ["kor", "한글", "한국어", "korean", "ko_"]
        chi_hints = ["chi", "cn_", "중국어", "chinese", "zh_"]
        jpn_hints = ["jpn", "jp_", "일본어", "japanese", "ja_"]

        for hint in kor_hints:
            if hint in fname or hint in path_lower:
                return "kor"
        for hint in chi_hints:
            if hint in fname or hint in path_lower:
                return "chi_sim"
        for hint in jpn_hints:
            if hint in fname or hint in path_lower:
                return "jpn"

        return "eng"

    # ── OCR 실행 ───────────────────────────────────────

    def ocr(self, image_path: str, lang: str = "auto", detail: str = "quick") -> dict:
        """이미지 OCR 실행.

        Args:
            image_path: 분석할 이미지 파일 경로
            lang: OCR 언어 ("auto", "eng", "kor", "chi_sim", "jpn")
            detail: 결과 상세도
                - ``"quick"``: 전체 텍스트만 추출 (빠름)
                - ``"full"``: 각 텍스트 블록의 바운딩 박스 + 신뢰도 포함

        Returns:
            {
                "text": "추출된 전체 텍스트",
                "blocks": [  # detail="full"일 때만
                    {"text": "...", "confidence": 95.0, "bbox": [x1,y1,x2,y2]},
                ],
                "language": "kor+eng",
                "engine": "tesseract" | "paddle" | "none",
                "stats": {"word_count": 10, "line_count": 3},
            }
        """
        # 언어 결정
        resolved_lang = self._detect_language(image_path, lang)

        if self.tesseract_available():
            result = self._ocr_tesseract(image_path, resolved_lang, detail)
            result["language"] = resolved_lang
            return result
        elif self.paddle_available():
            result = self._ocr_paddle(image_path, resolved_lang, detail)
            result["language"] = resolved_lang
            return result
        else:
            return {
                "text": "",
                "blocks": [],
                "language": resolved_lang,
                "engine": "none",
                "stats": {"word_count": 0, "line_count": 0},
            }

    # ── Tesseract OCR ──────────────────────────────────

    def _ocr_tesseract(self, image_path: str, lang: str, detail: str) -> dict:
        """Tesseract OCR 실행"""
        import pytesseract  # type: ignore[import]
        from PIL import Image
        import numpy as np

        # pytesseract에 tesseract 경로 설정
        tess_path = _find_tesseract()
        if tess_path:
            pytesseract.pytesseract.tesseract_cmd = tess_path  # type: ignore[attr-defined]

        # 이미지 열기 (한글 경로 대응)
        try:
            # PIL로 직접 열기 (한글 경로 지원)
            pil_img = Image.open(image_path)
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
        except Exception:
            # PIL 실패 시 OpenCV 경유
            try:
                import cv2
                with open(image_path, "rb") as f:
                    file_bytes = np.frombuffer(f.read(), np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                if img is None:
                    return self._empty_result("tesseract", "Cannot read image")
                pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            except Exception:
                return self._empty_result("tesseract", "Cannot read image")

        # 이미지 전처리 (OCR 정확도 향상)
        pil_img = self._preprocess_for_ocr(pil_img)

        # Tesseract 언어 설정
        tesseract_lang = self._map_tesseract_lang(lang)

        if detail == "full":
            # 상세 모드: 바운딩 박스 + 신뢰도
            try:
                data = pytesseract.image_to_data(
                    pil_img, lang=tesseract_lang,
                    output_type=pytesseract.Output.DICT,
                )
            except Exception:
                # 언어팩 없으면 영어로 fallback
                data = pytesseract.image_to_data(
                    pil_img, lang="eng",
                    output_type=pytesseract.Output.DICT,
                )

            blocks = []
            full_lines = []
            img_w, img_h = pil_img.size

            for i, text in enumerate(data["text"]):
                if not text.strip():
                    continue

                conf_str = data["conf"][i]
                conf = int(conf_str) if conf_str and conf_str != "-1" else 50
                x, y, bw, bh = (
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i],
                )

                # 공간 위치 분류
                h_pos = "left" if x < img_w / 3 else "right" if x > 2 * img_w / 3 else "center"
                v_pos = "top" if y < img_h / 3 else "bottom" if y > 2 * img_h / 3 else "middle"

                # 텍스트 크기
                if bh < 15:
                    size = "small"
                elif bh < 35:
                    size = "medium"
                else:
                    size = "large"

                blocks.append({
                    "text": text.strip(),
                    "confidence": conf,
                    "bbox": [x, y, x + bw, y + bh],
                    "position": f"{v_pos}-{h_pos}",
                    "size": size,
                })
                full_lines.append(text.strip())

            word_count = len(full_lines)
            line_count = len(set(full_lines))

            return {
                "text": "\n".join(full_lines),
                "blocks": blocks,
                "engine": "tesseract",
                "stats": {"word_count": word_count, "line_count": line_count},
            }
        else:
            # Quick 모드: 전체 텍스트만 추출
            try:
                raw_text = pytesseract.image_to_string(
                    pil_img, lang=tesseract_lang,
                )
            except Exception:
                raw_text = pytesseract.image_to_string(
                    pil_img, lang="eng",
                )

            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
            word_count = sum(len(l.split()) for l in lines)
            return {
                "text": "\n".join(lines),
                "blocks": [],
                "engine": "tesseract",
                "stats": {"word_count": word_count, "line_count": len(lines)},
            }

    # ── PaddleOCR ──────────────────────────────────────

    def _ocr_paddle(self, image_path: str, lang: str, detail: str) -> dict:
        """PaddleOCR 실행 (fallback)"""
        from paddleocr import PaddleOCR  # type: ignore[import]

        paddle_lang = self._map_paddle_lang(lang)
        ocr = PaddleOCR(use_angle_cls=True, lang=paddle_lang, show_log=False)

        try:
            result = ocr.ocr(image_path, cls=True)
        except Exception:
            return self._empty_result("paddle", "PaddleOCR inference failed")

        full_lines = []
        blocks = []

        if result and result[0]:
            for line in result[0]:
                bbox, (text, confidence) = line
                x1, y1 = int(bbox[0][0]), int(bbox[0][1])
                x2, y2 = int(bbox[2][0]), int(bbox[2][1])

                if detail == "full":
                    blocks.append({
                        "text": text,
                        "confidence": round(confidence * 100, 1),
                        "bbox": [x1, y1, x2, y2],
                        "position": "auto",
                        "size": "auto",
                    })

                full_lines.append(text)

        return {
            "text": "\n".join(full_lines),
            "blocks": blocks if detail == "full" else [],
            "engine": "paddle",
            "stats": {"word_count": len(full_lines), "line_count": len(full_lines)},
        }

    # ── 이미지 전처리 ──────────────────────────────────

    @staticmethod
    def _preprocess_for_ocr(pil_img):
        """OCR 정확도 향상을 위한 이미지 전처리.
        
        Adaptive Thresholding + 노이즈 제거 적용.
        OpenCV가 없으면 원본 반환.
        """
        try:
            import cv2
            import numpy as np

            # PIL → OpenCV 변환
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            # 그레이스케일 변환
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            # Adaptive Thresholding (조명 불균일 보정)
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 31, 10
            )

            # 노이즈 제거
            denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)

            from PIL import Image
            return Image.fromarray(denoised)
        except Exception:
            # OpenCV 없으면 원본 반환
            return pil_img

    # ── 헬퍼 ───────────────────────────────────────────

    @staticmethod
    def _map_tesseract_lang(lang: str) -> str:
        """내부 언어 코드 → Tesseract 언어 코드"""
        mapping = {
            "eng": "eng",
            "kor": "kor+eng",
            "chi_sim": "chi_sim+eng",
            "jpn": "jpn+eng",
        }
        return mapping.get(lang, "eng")

    @staticmethod
    def _map_paddle_lang(lang: str) -> str:
        """내부 언어 코드 → PaddleOCR 언어 코드"""
        mapping = {
            "eng": "en",
            "kor": "korean",
            "chi_sim": "ch",
            "jpn": "japan",
        }
        return mapping.get(lang, "en")

    @staticmethod
    def _empty_result(engine: str, reason: str = "") -> dict:
        """빈 OCR 결과"""
        return {
            "text": "",
            "blocks": [],
            "engine": engine,
            "stats": {"word_count": 0, "line_count": 0},
        }

    # ── OCR → 마크다운 변환 ────────────────────────────

    @staticmethod
    def ocr_to_markdown(ocr_result: dict) -> str:
        """OCR 결과를 마크다운으로 변환.

        Args:
            ocr_result: ``ocr()`` 메서드의 반환값

        Returns:
            마크다운 형식의 OCR 추출 결과 문자열
        """
        lines = []
        engine = ocr_result.get("engine", "none")
        text = ocr_result.get("text", "")
        blocks = ocr_result.get("blocks", [])
        stats = ocr_result.get("stats", {})

        if engine == "none":
            lines.append("### OCR Text Extraction")
            lines.append("- OCR not available.")
            lines.append("- Install Tesseract: `pip install pytesseract` + system package")
            lines.append("- Or PaddleOCR: `pip install paddleocr`")
            return "\n".join(lines)

        lines.append(f"### OCR Text Extraction ({engine})")
        lines.append(f"- **Words**: {stats.get('word_count', 0)}")
        lines.append(f"- **Lines**: {stats.get('line_count', 0)}")
        lines.append(f"- **Language**: {ocr_result.get('language', 'unknown')}")

        if blocks:
            # 신뢰도 평균
            avg_conf = sum(b.get("confidence", 0) for b in blocks) / max(len(blocks), 1)
            lines.append(f"- **Blocks**: {len(blocks)}")
            lines.append(f"- **Avg Confidence**: {avg_conf:.0f}%")

            # 상위 블록 테이블
            top_blocks = sorted(blocks, key=lambda b: -b.get("confidence", 0))[:10]
            lines.append("\n| # | Text | Conf | Position | Size |")
            lines.append("|---|------|------|----------|------|")
            for i, b in enumerate(top_blocks, 1):
                t = b.get("text", "")[:50]
                if len(b.get("text", "")) > 50:
                    t += "…"
                lines.append(
                    f"| {i} | {t} | {b.get('confidence', 0):.0f}% "
                    f"| {b.get('position', '?')} | {b.get('size', '?')} |"
                )

        if text:
            lines.append(f"\n<details>\n<summary>Full extracted text ({len(text)} chars)</summary>\n\n```\n{text[:2000]}\n```\n</details>")

        return "\n".join(lines)
