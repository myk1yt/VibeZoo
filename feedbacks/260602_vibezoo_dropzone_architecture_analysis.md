# VibeZoo Drop Zone — 전체 아키텍처 분석 및 미구현 현황

> **작성일:** 2026-06-02
> **대상 버전:** VibeZoo v0.14.0
> **목적:** Drop Zone의 현재 구현 상태를 분석하고, 누락된 기능과 개선 필요 사항을 문서화

---

## 1. Drop Zone 전체 아키텍처 개요

```
사용자 ──→ [Drop Zone Webview] ──→ [TS Extension] ──→ [디스크 저장]
                              ↓
                    [analyze_uploaded_file MCP tool]
                              ↓
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         [Phase 1: SSA]  [Phase 2: OCR]  [Phase 3: MiniCPM-V]
         (Statistical     (Tesseract/     (Local Vision LLM)
          Spatial          PaddleOCR)     ✅ 코드는 있음
          Aggregator)                     ❌ 모델 파일 없음
         ✅ 구현 완료      ✅ 코드 있음
                          ❌ Tesseract 미설치
```

---

## 2. 현재 구현된 컴포넌트 상세

### 2.1 Drop Zone Webview (프론트엔드)

| 항목 | 파일 | 상태 |
|------|------|:----:|
| 드래그앤드롭 UI | [`extension/src/visual/VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts:889) - `dropzoneHtml()` | ✅ |
| 파일 선택 버튼 | 동일 함수 | ✅ |
| 이미지 미리보기 | 동일 함수 | ✅ |
| 업로드 상태 메시지 | 동일 함수 | ✅ |
| 클립보드 붙여넣기 | 동일 함수 | ✅ |
| 업로드 완료/에러 메시지 수신 | 동일 함수 | ✅ |

**지원 파일 형식:** 모든 파일 형식 (이미지/텍스트/코드/문서/이진 파일 모두 업로드 가능)

### 2.2 TS Extension (업로드 처리)

| 항목 | 파일 | 상태 |
|------|------|:----:|
| `handleDropzoneUpload()` - 파일 저장 | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts:454) | ✅ |
| 저장 경로: `~/.vibezoo-uploads/<날짜>/upload_<timestamp>.<ext>` | 동일 함수 | ✅ |
| MIME 타입 → 확장자 매핑 | 동일 함수 | ✅ |
| 업로드 완료 메시지 전송 | 동일 함수 | ✅ |
| `openDropzone()` - 웹뷰 열기 | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts:426) | ✅ |

### 2.3 Python MCP: `analyze_uploaded_file` 도구

| 항목 | 파일 | 상태 |
|------|------|:----:|
| 파일 메타데이터 수집 | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:7) - `_get_file_info()` | ✅ |
| 이미지 → 안전한 Data URI 변환 (Pillow 리사이징) | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:61) - `_encode_image_as_safe_data_uri()` | ✅ |
| **Phase 1: SSA 분석** | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:150) | ✅ |
| **Phase 2: OCR 텍스트 추출** | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:173) | ⚠️ (의존성 필요) |
| **Phase 3: MiniCPM-V Vision** | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:189) | ❌ (모델 파일 없음) |
| 텍스트/코드 파일 읽기 | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:201) | ✅ |
| PDF 텍스트 추출 (PyMuPDF) | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:213) | ⚠️ (의존성 필요) |
| DOCX 텍스트 추출 | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:233) | ⚠️ (의존성 필요) |

---

## 3. 3계층 이미지 분석 파이프라인 상세

### Phase 1: SSA (Statistical Spatial Aggregator) ✅ 구현 완료

| 모듈 | 파일 |
|------|------|
| SSA 코어 | [`mcp-servers/bridge/tools/ssa.py`](mcp-servers/bridge/tools/ssa.py:100) |
| MCP 도구 등록 | [`ssa.py`](mcp-servers/bridge/tools/ssa.py) (하단) |

**분석 항목:**
- 8×8 그리드 색상 분석
- GrabCut 객체 감지 (전경/배경 분리)
- Median Cut 주색상 추출 (4색)
- 공간 균일성 점수 (0~1)
- Edge 밀도 분석
- 휘도/채도 통계
- RGB 히스토그램 피크

**의존성:** `opencv-python` (cv2), `numpy` ✅

### Phase 2: OCR 텍스트 추출 ⚠️ 부분 구현

| 모듈 | 파일 |
|------|------|
| OCR 엔진 | [`mcp-servers/bridge/ocr_engine.py`](mcp-servers/bridge/ocr_engine.py) |
| 우선 엔진: Tesseract | ❌ Windows에 Tesseract 미설치 |
| Fallback 엔진: PaddleOCR | ❌ (의존성 설치 필요) |
| 언어 자동 감지 | ✅ (파일명 기반) |
| 상세 모드 (바운딩 박스) | ✅ |
| 마크다운 변환 | ✅ |

### Phase 3: MiniCPM-V Vision LLM ❌ 모델 파일 없음

| 모듈 | 파일 |
|------|------|
| MiniCPM-V 래퍼 | [`mcp-servers/bridge/vision/minicpm.py`](mcp-servers/bridge/vision/minicpm.py) |
| `describe_image()` 함수 | ✅ 코드 완비 |
| `is_available()` 검사 | ✅ 코드 완비 |
| `llama-cpp-python` | ✅ 설치됨 (v0.3.24) |
| **`models/MiniCPM-V-4_6-Q5_K_M.gguf`** | ❌ **파일 없음** |
| **`models/mmproj-model-f16.gguf`** | ❌ **파일 없음** |

---

## 4. ❌ 미구현 / 누락된 기능 목록

### 🔴 Critical (기능 동작 불가)

| # | 기능 | 설명 | 영향 |
|---|------|------|:----:|
| 1 | **MiniCPM-V 모델 파일** | `models/` 디렉토리 자체가 없음. GGUF 모델 파일 2개 필요 | Phase 3 분석 불가 |
| 2 | **Tesseract OCR 엔진** | Windows에 Tesseract CLI 미설치 | Phase 2 분석 불가 |
| 3 | **자동 분석 트리거** | 업로드 완료 후 자동으로 `analyze_uploaded_file`이 호출되지 않음 | 사용자가 수동으로 MCP 도구 호출 필요 |

### 🟡 Major (기능 제한적 동작)

| # | 기능 | 설명 | 영향 |
|---|------|------|:----:|
| 4 | **분석 모드 선택기** | 업로드 시 SSA/OCR/LLM 중 무엇을 실행할지 선택 불가 | 3계층 항상 모두 실행 (또는 실패) |
| 5 | **파일 타입별 분기** | 이미지가 아닌 파일(코드/문서/오디오) 업로드 시 분석 파이프라인이 없음 | Drop Zone이 단순 파일 저장소 역할 |
| 6 | **PDF/DOCX 의존성** | PyMuPDF, python-docx 미설치 시 문서 분석 불가 | 문서 파일 처리 불가 |
| 7 | **아카이브 파일** | ZIP 등 목록에는 있지만 분석 코드 없음 | `analyze_file()`에서 무시됨 |

### 🟢 Minor (개선 사항)

| # | 기능 | 설명 |
|---|------|------|
| 8 | **일괄 업로드** | 현재 1회 1파일만 업로드 가능 |
| 9 | **업로드 진행바** | 진행 상태 표시 없음 (단순 텍스트) |
| 10 | **비이미지 파일 미리보기** | 코드/텍스트 파일의 내용 미리보기 없음 |
| 11 | **VS Code Explorer 드래그** | Webview 내 드래그만 가능, Explorer에서 직접 드래그 불가 |
| 12 | **파일 삭제 기능** | 업로드 후 Drop Zone에서 파일 삭제 불가 |
| 13 | **`stopWatching()` 누락** | `DZ_ACTION_FILE()`의 `unwatchFile()` 호출 빠짐 |
| 14 | **카탈로그 파일** | `catalog.json`이 생성되지만 활용되지 않음 |

---

## 5. 개선 방안 제안

### 5.1 분석 모드 선택기 (분기점)

현재 아키텍처는 업로드 → 저장 → 수동 분석의 단순 흐름입니다.  
개선 방향:

```
[Drop Zone Webview]
    ├── 파일 업로드
    └── [분석 모드 선택]  ← NEW
         ├── 🖼️ SSA (공간 통계)
         ├── 📝 OCR (텍스트 추출)
         ├── 🤖 MiniCPM-V (LLM 비전)
         ├── 🔄 통합 (3계층 모두)
         └── 📂 원본 저장만 (분석 안 함)
```

**구현 방안:**
1. Drop Zone Webview에 모드 선택 UI 추가 (라디오 버튼/드롭다운)
2. 업로드 메시지에 `mode` 필드 포함 → `{type:'uploadFile', fileName, data, mimeType, mode:'ssa|ocr|vision|full|none'}`
3. TS Extension이 모드에 따라 `analyze_uploaded_file` 호출 또는 각 phase별 개별 호출

### 5.2 자동 분석 체인

```
업로드 완료
  ↓
TS Extension → Python MCP 서버에 분석 요청
  ↓
분석 완료 → 결과를 action 파일에 기록
  ↓
웹뷰에 분석 결과 표시 (자동)
  ↓
사용자 확인 → LLM 컨텍스트에 포함
```

### 5.3 파일 타입별 파이프라인

| 파일 타입 | SSA | OCR | MiniCPM-V | 텍스트 추출 | 비고 |
|-----------|:---:|:---:|:---------:|:----------:|------|
| 이미지 (.jpg/.png 등) | ✅ | ✅ | ✅ | - | 3계층 풀파이프라인 |
| 텍스트 (.txt/.md 등) | - | - | - | ✅ | 내용 직접 읽기 |
| 코드 (.py/.ts 등) | - | - | - | ✅ | 구문 강조 포함 |
| PDF | - | - | - | ✅ (PyMuPDF) | 페이지별 텍스트 |
| DOCX | - | - | - | ✅ (python-docx) | 문단별 텍스트 |
| 오디오 | ❌ | ❌ | ❌ | ❌ | **미지원** |
| 비디오 | ❌ | ❌ | ❌ | ❌ | **미지원** |
| 아카이브 | ❌ | ❌ | ❌ | ❌ | **미지원** |

### 5.4 우선 설치 필요 사항

```bash
# 1. MiniCPM-V 모델 다운로드 (Phase 3)
mkdir models
# HuggingFace: openbmb/MiniCPM-V-4.6-gguf (578MB)
# - ggml-model-Q5_K_M.gguf (Renamed to MiniCPM-V-4_6-Q5_K_M.gguf)
# - mmproj-model-f16.gguf

# 2. Tesseract OCR 설치 (Phase 2)
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# 또는: winget install UB-Mannheim.TesseractOCR

# 3. Python 문서 분석 패키지 (선택)
pip install PyMuPDF python-docx
```

---

## 6. 결론

| 구분 | 상태 | 비고 |
|------|:----:|------|
| Drop Zone Webview UI | ✅ | 기본 업로드 기능 완비 |
| 파일 저장 (TS → 디스크) | ✅ | 정상 동작 |
| SSA 분석 (Phase 1) | ✅ | 완전 구현 |
| OCR 분석 (Phase 2) | ⚠️ | 엔진 미설치 |
| MiniCPM-V 분석 (Phase 3) | ❌ | 모델 파일 없음 |
| 자동 분석 체인 | ❌ | 수동 호출 필요 |
| 분석 모드 선택 | ❌ | 미구현 |
| 문서/코드 파일 분석 | ⚠️ | 일부 의존성 필요 |
| 오디오/비디오 지원 | ❌ | 미지원 |

**즉시 조치 가능:** MiniCPM-V 모델 파일 다운로드 + Tesseract 설치  
**중기 개선:** 분석 모드 선택기 + 자동 분석 체인  
**장기 개선:** 오디오/비디오 지원 + 일괄 업로드
