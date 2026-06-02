# VibeZoo Universal File Intake + MiniCPM-V 통합 설계

## 1. 개요

VibeZoo의 드롭존 업로드 파이프라인을 **이미지 전용 → 유니버설 파일**로 확장하고, MiniCPM-V-4.6 Q5_K_M 비전 모델을 통합하여 AI가 업로드된 파일 내용을 이해하고 소통할 수 있게 한다.

## 2. MiniCPM-V 통합 설계

### 2.1 모델 정보
| 항목 | 값 |
|------|-----|
| 모델 | MiniCPM-V-4.6 |
| 포맷 | GGUF Q5_K_M |
| 크기 | ~850MB |
| 런타임 | llama-cpp-python |

### 2.2 브릿지 통합 구조
```
VibeZoo Bridge (port 9027)
├── bridge/
│   ├── vision/
│   │   ├── __init__.py       (새 모듈)
│   │   └── minicpm.py        (MiniCPM-V 래퍼)
│   ├── tools/
│   │   ├── ssa.py            (기존 → 수정, Vision 호출 추가)
│   │   └── whiteboard.py     (기존 → 수정)
│   └── config.py             (수정: 모델 경로 추가)
└── models/                   (신규: 모델 다운로드 디렉터리)
    └── MiniCPM-V-4.6-Q5_K_M.gguf
```

### 2.3 의존성 추가
```bash
pip install llama-cpp-python  # ~50MB
```

### 2.4 MCP 도구 API 설계
```python
@mcp.tool
def vision_describe(image_path: str, question: str = None) -> str:
    """MiniCPM-V로 이미지 설명 또는 질문 답변
    
    Args:
        image_path: 분석할 이미지 경로
        question: 옵션 질문 (없으면 기본 설명)
    Returns:
        이미지에 대한 텍스트 설명
    """
```

## 3. 유니버설 파일 드롭존 설계

### 3.1 현재 vs 목표
| | 현재 | 목표 |
|---|------|------|
| 파일 타입 | 이미지만 | **모든 파일** |
| 업로드 방식 | FileReader → base64 → postMessage | **FileReader → base64 + filename** → postMessage |
| 저장 위치 | C:\Users\...\Temp\ | ~/.vibezoo-uploads/YYYY-MM-DD/ (구조화) |
| 분석 방식 | SSA 픽셀 | **파일 타입별 라우터** |

### 3.2 파일 타입 라우터
```
업로드된 파일
├── 이미지 (.png/.jpg/.gif/.webp/.bmp)
│   ├── SSA + OCR (기존)
│   └── MiniCPM-V Vision Describe (신규)
├── PDF (.pdf)
│   └── 텍스트 추출 (PyMuPDF)
├── 워드 (.docx)
│   └── 텍스트 추출 (python-docx)
├── 텍스트 (.txt/.md/.py/.js/.ts/.json/.yaml/.csv)
│   ├── 텍스트 직접 읽기
│   └── 토큰 수 제한 (초과 시 요약)
└── 기타 (.xlsx/.pptx 등)
    └── 지원 포맷에 따라 텍스트 추출
```

### 3.3 Webview HTML 수정
- `accept="image/*"` → `accept="*"` 또는 제거
- 지원 포맷 표시 업데이트
- 파일명 + 파일타입 표시
- 비이미지 파일은 파일명 아이콘으로 표시

### 3.4 Extension 측 수정
- [`openDropzone`](extension/src/visual/VisualVibePanels.ts) 메서드 확장
- `uploadImage` 메시지 → `uploadFile` 메시지로 통합
- 저장 경로: `~/.vibezoo-uploads/{today}/{timestamp}_{original_name}`

## 4. 통합 파일 처리 파이프라인 (MCP 도구)

### 4.1 신규 도구: `analyze_uploaded_file`
```python
@mcp.tool
def analyze_uploaded_file(file_path: str) -> str:
    """드롭존에 업로드된 파일을 분석
    
    파일 타입을 자동 감지하여 적절한 분석 수행:
    - 이미지: SSA + OCR + MiniCPM-V Vision
    - PDF/DOCX/TXT: 텍스트 추출 + 내용 요약
    - 코드 파일: 구조 분석 + 코드 설명
    
    Args:
        file_path: 업로드된 파일 경로
    Returns:
        마크다운 형식 분석 보고서 (이미지 포함 시 data URI)
    """
```

### 4.2 내부 처리 흐름
```
analyze_uploaded_file(path)
├── 확장자 감지 → 파일 타입 결정
├── [이미지] → _analyze_image(path)
│   ├── SSA 분석 (기존)
│   ├── OCR 텍스트 추출 (기존)
│   ├── MiniCPM-V 설명 (신규)
│   └── data URI 포함 (기존)
├── [PDF] → _analyze_pdf(path)
│   ├── PyMuPDF 텍스트 추출
│   ├── 페이지 수, 메타데이터
│   └── 내용 요약 (LLM 프롬프트)
├── [DOCX] → _analyze_docx(path)
│   ├── python-docx 텍스트 추출
│   ├── 문단 수, 스타일
│   └── 내용 요약
├── [텍스트/코드] → _analyze_text(path)
│   ├── 텍스트 직접 읽기
│   ├── 파일 길이, 언어 감지
│   └── 내용 요약 또는 전문 (제한 내)
└── [기타] → _analyze_generic(path)
    ├── 기본 정보 (크기, 타입, 생성일)
    └── Hex 덤프 또는 미리보기
```

## 5. 파일 구조 변경사항

### 5.1 신규 디렉터리
```
~/.vibezoo-uploads/
├── 2026-06-01/
│   ├── 173315_vibezoo_mascot.png
│   ├── 173511_document.pdf
│   └── 173623_readme.txt
```

### 5.2 Bridge 소스 변경
| 파일 | 변경사항 | 난이도 |
|------|---------|--------|
| `bridge/config.py` | 모델 경로, 업로드 디렉터리 추가 | 하 |
| `bridge/vision/__init__.py` | 새 모듈 | 하 |
| `bridge/vision/minicpm.py` | MiniCPM-V 래퍼 클래스 | 중 |
| `bridge/tools/ssa.py` | Vision 호출 추가 | 중 |
| `bridge/tools/whiteboard.py` | 드롭존 HTML + 업로드 로직 확장 | 중 |
| `bridge/tools/file_analyzer.py` | **신규** 유니버설 파일 분석 | 상 |
| `bridge/tools/__init__.py` | 새 도구 등록 | 하 |

### 5.3 Extension 소스 변경
| 파일 | 변경사항 | 난이도 |
|------|---------|--------|
| `extension/src/visual/VisualVibePanels.ts` | `openDropzone` 확장, `uploadFile` 메시지 | 중 |

## 6. 구현 순서

### Phase 1: MiniCPM-V 통합 (선행)
1. `llama-cpp-python` 설치
2. MiniCPM-V-4.6 Q5_K_M GGUF 다운로드
3. `bridge/vision/minicpm.py` 래퍼 클래스 구현
4. `vision_describe` MCP 도구 등록
5. SSA에 Vision 분석 결과 추가
6. 브릿지 재시작 → 테스트

### Phase 2: 유니버설 파일 드롭존
1. Webview HTML 파일 타입 제한 해제
2. Extension `openDropzone` 확장
3. 파일 타입별 임시 저장 라우터
4. 신규 `bridge/tools/file_analyzer.py` 구현

### Phase 3: 통합 테스트
1. 이미지 업로드 → MiniCPM-V 설명 확인
2. PDF 업로드 → 텍스트 추출 확인
3. TXT 업로드 → 내용 읽기 확인
4. DOCX 업로드 → 텍스트 추출 확인
5. 드롭존 UI 개선 (파일명 표시 등)

## 7. 예상 용량/성능
| 항목 | 예상치 |
|------|--------|
| MiniCPM-V GGUF | 578MB |
| llama-cpp-python | 50MB |
| PyMuPDF + 의존성 | 30MB |
| python-docx | 5MB |
| **총 모델/의존성 증가** | **~935MB** |
| 이미지 분석 속도 | 3~5초 |
| PDF/DOCX 추출 속도 | 0.5~2초 |
| TXT 읽기 속도 | 즉시 |

---

*본 설계는 Architect 모드에서 2026-06-01 작성되었습니다. 다음 단계: Code 모드에서 Phase 1부터 구현 시작.*
