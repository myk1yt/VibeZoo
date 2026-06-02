# VibeZoo — AI 코딩 도우미를 위한 지능형 동반자 확장

> **VibeZoo = [Crow Memory](#3-crow-memory-개요) (시냅틱 메모리) + [VibeZoo MCP Bridge](#1-vibezoo-mcp-bridge--전체-도구-분석-34개) (34개 도구)**

VibeZoo는 Zoo Code를 위한 VS Code 동반자 확장(Companion Extension)입니다. Zoo Code의 소스 코드를 **한 줄도 수정하지 않고**, LLM이 더 똑똑하게 코드를 검색·분석·리뷰·문서화하고, 당신의 습관과 선호도를 기억하며, 실시간 시각 협업(화이트보드·드롭존·Vision AI)을 가능하게 합니다.

---

## 1. VibeZoo MCP Bridge — 전체 도구 분석 (34개)

VibeZoo MCP Bridge는 FastMCP + SSE 기반으로 동작하며, Zoo Code의 MCP 클라이언트와 [`vibezoo_mcp_bridge_v2.py`](mcp-servers/vibezoo_mcp_bridge_v2.py)가 `localhost:9027/sse`에서 통신합니다. 총 **34개 MCP 도구**를 제공합니다.

### 1.1 UX (신규, 3개) — 의도 감지 + 자동 도구 체인

> 사용자가 "파일 보여줄게"라고 말하면 → 드롭존이 열리고 → 업로드된 파일은 자동으로 SSA→OCR→MiniCPM 파이프라인을 거쳐 분석됩니다. AI가 사용자의 의도를 먼저 파악한 뒤, 필요한 도구 체인을 제안합니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`ux_coordinator`](mcp-servers/bridge/tools/ux_coordinator.py) | 사용자 의도 분석 + 도구 체인 제안 | `intent`, `user_message` | 마크다운 제안 | "파일 보여줄게" → 드롭존 오픈 제안 |
| [`auto_analyze_after_drop`](mcp-servers/bridge/tools/ux_coordinator.py) | 드롭존 업로드 후 자동 분석 파이프라인 | `file_path` | 분석 보고서 (SSA→OCR→MiniCPM) | 이미지 업로드 → 텍스트+구조 자동 분석 |
| [`auto_analyze_whiteboard`](mcp-servers/bridge/tools/ux_coordinator.py) | 화이트보드 자동 분석 | — | 분석 보고서 | 화이트보드 그림 → Mermaid 다이어그램 변환 |

**의도 감지 엔진**: [`intent_detector.py`](mcp-servers/bridge/intent_detector.py) — 키워드 기반 자연어 분석으로 5가지 의도를 분류:
- `file_share` — "파일 보여줄게", "이 이미지 봐줘"
- `drawing_request` — "그림 그려줘", "다이어그램 만들어줘"
- `whiteboard_input` — "화이트보드에 적었어", "여기 그려놨어"
- `code_analysis` — "코드 분석해줘", "리뷰해줘"
- `general_question` — 위 카테고리에 해당하지 않는 일반 질문

### 1.2 Scout (3개) — 코드 검색 및 프로젝트 탐색

> 프로젝트 구조를 빠르게 파악하고, 원하는 심볼이나 함수를 tree-sitter AST 기반으로 정확하게 찾습니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`search_codebase`](mcp-servers/bridge/tools/scout.py) | tree-sitter AST 기반 코드 검색 (regex 폴백) | `query`, `file_patterns`, `max_results`, `mode` | 검색 결과 + 컨텍스트 라인 | "이 함수 어디서 정의했지?" |
| [`find_references`](mcp-servers/bridge/tools/scout.py) | 심볼의 모든 참조 위치 검색 | `symbol` | 정의 + 사용 위치 목록 | "이 변수 어디서 쓰지?" |
| [`summarize_architecture`](mcp-servers/bridge/tools/scout.py) | 프로젝트 구조·기술 스택·의존성 분석 | `target_path`, `mode`, `streaming` | 아키텍처 요약 보고서 | 새 프로젝트 온보딩, 구조 파악 |

### 1.3 Reviewer (2개) — 코드 품질 검사

> PR 올리기 전에 자동으로 코드 품질을 점검합니다. ESLint, go vet과 통합됩니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`review_code`](mcp-servers/bridge/tools/reviewer.py) | 코드 품질 검사 (TODO, console.log, 긴 라인 등) | `file_path`, `severity` | 리뷰 보고서 (error/warning/info) | "이 파일 리뷰해줘" |
| [`check_quality`](mcp-servers/bridge/tools/reviewer.py) | ESLint / go vet 통합 품질 검사 | `target_path` | 품질 보고서 | "린트 한 번 돌려줘" |

### 1.4 Tester (2개) — 테스트 생성 및 커버리지

> 함수 시그니처를 감지해 자동으로 테스트 템플릿을 생성하고, 커버리지를 측정합니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`generate_tests`](mcp-servers/bridge/tools/tester.py) | 함수 감지 → 테스트 템플릿 생성 (jest/vitest/pytest/go test) | `source_path`, `framework` | 테스트 코드 | "이 파일 유닛 테스트 만들어줘" |
| [`analyze_coverage`](mcp-servers/bridge/tools/tester.py) | vitest / pytest 커버리지 실행 + 분석 | `target_path` | 커버리지 보고서 | "테스트 커버리지 얼마나 되지?" |

### 1.5 Deep Analyzer (4개) — 심층 AST 분석

> tree-sitter AST로 코드의 호출 그래프, 의존성, 반복 패턴을 분석하고 문서를 자동 생성합니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`analyze_call_graph`](mcp-servers/bridge/tools/deep_analyzer.py) | AST `call_expression` 기반 호출 그래프 분석 | `file_path`, `depth`, `include_external` | 호출 관계도 | "이 함수가 누구를 호출하지?" |
| [`map_dependencies`](mcp-servers/bridge/tools/deep_analyzer.py) | AST import 추출 + Tarjan 순환 참조 탐지 | `target_path` | 의존성 맵 | "순환 참조 있는지 확인해줘" |
| [`extract_patterns`](mcp-servers/bridge/tools/deep_analyzer.py) | 반복 코드 패턴 마이닝 (async, try-catch 등) | `target_path`, `min_occurrences` | 패턴 빈도표 | "이 프로젝트에서 자주 쓰는 패턴이 뭐지?" |
| [`reverse_engineer`](mcp-servers/bridge/tools/deep_analyzer.py) | AST 필드 추출 → Mermaid ERD·OpenAPI·마크다운 문서 생성 | `target_path`, `output_format` | 자동 생성 문서 | "이 API 스펙 문서로 만들어줘" |

### 1.6 Whiteboard (4개) — AI-인간 시각 협업

> AI가 Fabric.js 캔버스에 그림을 그리고, 사용자가 수정한 내용을 읽고, 화면 캡처도 가능합니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`draw_on_whiteboard`](mcp-servers/bridge/tools/whiteboard.py) | Fabric.js 드로잉 명령 전송 (rect, circle, line, arrow, text 등) | `commands` (JSON) | 화이트보드 렌더링 | "아키텍처 다이어그램 그려줘" |
| [`get_whiteboard_state`](mcp-servers/bridge/tools/whiteboard.py) | 사용자가 화이트보드에 수정한 내용 조회 | — | 화이트보드 상태 JSON | "내가 뭐 그렸는지 확인해봐" |
| [`capture_screen`](mcp-servers/bridge/tools/whiteboard.py) | 화면 캡처 또는 드롭존 열기 | `source` ("screen"/"dropzone"/"file") | 캡처 이미지 / 드롭존 | "이 화면 분석해줘" |
| [`auto_analyze_whiteboard`](mcp-servers/bridge/tools/ux_coordinator.py) | 화이트보드 내용 자동 분석 | — | 분석 보고서 | 그림 → Mermaid / 코드 변환 |

### 1.7 Fix Loop (3개) — 자율 빌드 수정 루프

> 빌드가 실패하면 LLM이 자동으로 오류를 분석하고, Crow Memory에서 과거 해결 패턴을 조회하여 수정 코드를 제안합니다. Human-in-the-Loop으로 사용자가 개입할 수 있습니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`auto_fix_status`](mcp-servers/bridge/tools/fix_loop.py) | 수정 요청 상태 조회 + Crow 과거 버그 패턴 검색 | — | 진단 정보 + 과거 수정 이력 | "빌드 왜 깨졌지?" |
| [`retry_build`](mcp-servers/bridge/tools/fix_loop.py) | 빌드 재실행 + 결과 기록 + Crow 자동 인제스트 | `build_command` | 빌드 결과 | "수정했으니 다시 빌드해봐" |
| [`check_intervention`](mcp-servers/bridge/tools/fix_loop.py) | 화이트보드·채팅에 사용자 개입이 있는지 확인 | — | 개입 상태 | "사용자가 뭐라고 했는지 확인" |

### 1.8 Integrated (4개) — 통합 시나리오 도구

> 여러 도구를 하나의 워크플로우로 묶어 "한 번에" 실행합니다. "리뷰해줘" 한 마디면 search → review → quality → patterns가 순차 실행됩니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`review_project`](mcp-servers/bridge/tools/integrated.py) | `search_codebase` + `review_code` + `check_quality` + `extract_patterns` 통합 | `target_path`, `mode`, `streaming` | 종합 리뷰 보고서 | "프로젝트 전체 리뷰해줘" |
| [`find_bugs`](mcp-servers/bridge/tools/integrated.py) | `extract_patterns` + suspicious search + `crow_recall(bug)` 통합 | `target_path`, `mode` | 버그 리포트 | "잠재적 버그 찾아줘" |
| [`suggest_refactor`](mcp-servers/bridge/tools/integrated.py) | `map_dependencies` + `extract_patterns` + `analyze_call_graph` 통합 | `target_path`, `mode` | 리팩터링 제안서 | "이 코드 어떻게 개선할까?" |
| [`generate_docs`](mcp-servers/bridge/tools/integrated.py) | `summarize_architecture` + `reverse_engineer` + `draw_on_whiteboard` 통합 | `target_path`, `format`, `mode` | 문서 + 다이어그램 | "이 프로젝트 문서화해줘" |

### 1.9 Analysis (4개) — 코드 설명 및 변경 분석

> 특정 코드 라인이 무엇을 하는지 설명하고, git 변경 사항을 분석하며, PR 리뷰와 일괄 리팩터링을 지원합니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`explain_code`](mcp-servers/bridge/tools/analysis.py) | AST 컨텍스트 기반 코드 설명 | `file_path`, `line_number` | 자연어 설명 | "이 줄이 뭐 하는 코드야?" |
| [`analyze_changes`](mcp-servers/bridge/tools/analysis.py) | `git diff` 분석 + Crow 컨텍스트 조회 | — | 변경 요약 보고서 | "내가 뭐 바꿨지?" |
| [`review_pr`](mcp-servers/bridge/tools/analysis.py) | `analyze_changes` + `review_code` 통합 PR 리뷰 | `base_branch`, `head_branch` | PR 리뷰 보고서 | "이 PR 검토해줘" |
| [`refactor_across_files`](mcp-servers/bridge/tools/analysis.py) | 패턴 검색 → 모든 파일 일괄 변경 제안 (dry_run 가능) | `pattern`, `new_pattern`, `file_patterns`, `dry_run` | 변경 제안서 / 실제 수정 | "이 import 패턴 싹 바꿔줘" |

### 1.10 Knowledge (2개) — 프로젝트 지식 기억·회상

> 프로젝트 구조와 패턴을 Crow Memory에 저장하고, 나중에 다시 불러옵니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`learn_project`](mcp-servers/bridge/tools/knowledge.py) | `summarize_architecture` + `extract_patterns` + `map_dependencies` 결과를 Crow에 저장 | `target_path` | 저장 결과 | "이 프로젝트 기억해둬" |
| [`recall_project`](mcp-servers/bridge/tools/knowledge.py) | Crow에서 저장된 프로젝트 지식 회상 | `target_path` | 회상 결과 | "아까 그 프로젝트 분석 결과 보여줘" |

### 1.11 Preferences (2개) — 사용자 선호도 학습

> 당신의 코딩 스타일과 선호도를 Crow Memory에 저장하고 필요할 때 조회합니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`learn_preference`](mcp-servers/bridge/tools/knowledge.py) | 사용자 코딩 선호도 저장 (탭 사이즈, 네이밍, 아키텍처 스타일 등) | `rule`, `category` | 저장 결과 | "탭 사이즈 2로 기억해줘" |
| [`get_preferences`](mcp-servers/bridge/tools/knowledge.py) | 저장된 모든 선호도 조회 | `category` (선택) | 선호도 목록 | "내 코딩 설정 알려줘" |

### 1.12 Web (2개) — 웹 검색 및 페이지 분석

> 외부 문서를 참조하거나 최신 기술 정보를 검색할 때 사용합니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`fetch_page`](mcp-servers/bridge/tools/web.py) | 웹 페이지 가져오기 → 마크다운 변환 | `url`, `max_length` | 마크다운 텍스트 | "이 블로그 글 요약해줘" |
| [`web_search`](mcp-servers/bridge/tools/web.py) | 다중 엔진 웹 검색 (DuckDuckGo → Mojeek → Wikipedia 폴백) | `query`, `max_results`, `engine` | 검색 결과 | "Python 3.13 새로운 기능 검색" |

### 1.13 SSA (1개) — 이미지 공간 통계 분석

> Spatial Statistical Aggregator: OpenCV 기반 이미지 픽셀 통계 분석. OCR 텍스트 추출을 포함합니다.

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`aggregate_spatial_pixels`](mcp-servers/bridge/tools/ssa.py) | 이미지 공간 통계 분석 + OCR | `image_path`, `detail`, `ocr`, `ocr_lang` | 통계 + 텍스트 보고서 | "이 스크린샷 분석해줘" |

### 1.14 Setup (1개) — 설치 및 설정 자동화

| 도구 | 설명 | 입력 | 출력 | 활용 예시 |
|:---|:---|:---|:---|:---|
| [`vibezoo_setup`](mcp-servers/bridge/tools/setup.py) | VibeZoo 의존성 설치 + MCP/Zoo 설정 자동 구성 | `target`, `python_packages`, `system_tools`, `configure_mcp`, `configure_zoo` | 설치 결과 | "VibeZoo 설정해줘" |

---

### 도구 카테고리별 요약

| 카테고리 | 도구 수 | 주요 기능 |
|:---|:---:|:---|
| **UX** | 3 | 의도 감지, 드롭존 자동 분석, 화이트보드 분석 |
| **Scout** | 3 | AST 기반 코드 검색, 심볼 참조, 아키텍처 요약 |
| **Reviewer** | 2 | 코드 품질 검사, ESLint/go vet 통합 |
| **Tester** | 2 | 테스트 생성, 커버리지 분석 |
| **Deep Analyzer** | 4 | 호출 그래프, 의존성 맵, 패턴 마이닝, 리버스 엔지니어링 |
| **Whiteboard** | 4 | AI 드로잉, 사용자 상태 조회, 화면 캡처, 자동 분석 |
| **Fix Loop** | 3 | 자율 빌드 수정, Crow 과거 패턴, HITL 개입 확인 |
| **Integrated** | 4 | 리뷰·버그·리팩터·문서화 통합 시나리오 |
| **Analysis** | 4 | 코드 설명, git diff, PR 리뷰, 일괄 리팩터링 |
| **Knowledge** | 2 | 프로젝트 지식 저장·회상 |
| **Preferences** | 2 | 코딩 선호도 저장·조회 |
| **Web** | 2 | 웹 검색, 페이지 마크다운 변환 |
| **SSA** | 1 | 이미지 공간 통계 분석 |
| **Setup** | 1 | 설치·설정 자동화 |
| **합계** | **34** | |

---

## 2. Vision AI 파이프라인

VibeZoo는 이미지 분석을 위한 Vision AI 파이프라인을 내장하고 있습니다.

| 구성 요소 | 기술 | 설명 |
|:---|:---|:---|
| **MiniCPM-V** | GGUF + llama-cpp-python | 경량 Vision-Language Model. 로컬에서 이미지 캡션·분석 수행 |
| **OCR** | Tesseract / PaddleOCR | 이미지에서 텍스트 추출 (한국어·영어·일본어·중국어 지원) |
| **SSA** | OpenCV 기반 Spatial Statistical Aggregator | 픽셀 통계, 히스토그램, 공간 패턴 분석 |

**파이프라인 흐름**:  
```
이미지 업로드 → SSA(공간 통계) → OCR(텍스트 추출) → MiniCPM-V(VLM 분석) → 분석 보고서
```

[`minicpm.py`](mcp-servers/bridge/vision/minicpm.py)에서 llama-cpp-python을 통해 GGUF 모델을 로드하고, OpenAI-compatible API로 추론합니다.

---

## 3. Crow Memory 개요

### 3.1 철학 — "까마귀는 코드가 아니라, 코드를 쓴 손을 기억한다"

> *"Crow remembers not the code, but the hand that wrote it."*

Transformer 기반 LLM은 학습 시점에 고정되어 사용자를 기억할 수 없습니다. RAG나 SQLite 기반 솔루션은 정보를 무한히 쌓아 "100% 정확한 메모장"처럼 동작하지만, 인간의 뇌는 그렇게 동작하지 않습니다. 오래된 습관은 희미해지고, 새로운 패턴은 강화됩니다.

**망각은 버그가 아닙니다.** Crow의 고정 크기 가중치 행렬과 λ(감쇠율)는 "창조적 망각"을 구현합니다. 100% 정확한 회상을 포기함으로써, Crow를 통해 기억하는 AI는 **현재의 당신**에 더 가까운 편향으로 응답합니다.

### 3.2 8개 레지스터 (Code 4 + Life 4)

**Code Domain**

| 레지스터 | 차원 | λ (EMA decay) | 용량 | 도메인 |
|:---|:---|:---|:---|:---|
| `style` | 4096×4096 | 0.9999 | ~2,000 패턴 | 변수명, 주석 스타일, 폴더 구조 미학 |
| `bug` | 2048×2048 | 0.9995 | ~800 패턴 | 추상적 버그 패밀리 (정확한 수정이 아닌 유형) |
| `arch` | 2048×2048 | 0.9995 | ~800 패턴 | early-return vs deep-nesting, 에러 처리 철학 |
| `context` | 2048×4096 | 0.9500 | ~400 패턴 | 최근 프로젝트 컨텍스트, 활성 파일 컨텍스트 |

**Life Domain**

| 레지스터 | 차원 | λ (EMA decay) | 용량 | 도메인 |
|:---|:---|:---|:---|:---|
| `life_pref` | 4096×4096 | 0.9999 | ~2,000 | 개인 취향, 선호 환경, 습관 |
| `life_avoid` | 2048×2048 | 0.9995 | ~800 | 피해야 할 상황, 싫어하는 것, 과거 실수 |
| `life_phil` | 2048×2048 | 0.9995 | ~800 | 인생 철학, 의사 결정 원칙, 가치관 |
| `life_context` | 2048×4096 | 0.9500 | ~400 | 현재 계획, 최근 사건, 진행 중인 고민 |

### 3.3 Hebbian EMA 업데이트 규칙

Crow는 Hebbian 학습("함께 발화하는 뉴런은 연결된다")에 기반한 지수 이동 평균(EMA)으로 가중치를 갱신합니다:

```
W_new = λ · W_old + (1 - λ) · (key ⊗ value)
```

고정 크기 `crow.bin`(140MB)에 모든 기억이 압축되어 저장되며, 용량을 초과하면 오래된 기억이 자연스럽게 희미해집니다.

### 3.4 자동 기억/회상 메커니즘

| 계층 | 메커니즘 | 작동 시점 |
|:---|:---|:---|
| **AUTO-INGEST** | AI가 매 교환마다 선호도·철학·수정 사항을 감지하여 `crow_ingest` 호출 | 매 응답마다 |
| **MCP Prompt** | `crow_memory_bias`가 세션 시작 시 LLM 호스트에 의해 자동 로드 | 매 세션 |
| **Auto-Inject** | 커스텀 모드 시스템 프롬프트가 `[User Bias]` 블록을 사전 생성 | 작업 전 |
| **Evolved Rules** | 통계적으로 유의미한 패턴이 HITL 승인을 거쳐 `system_prompt.md`에 영구 반영 | 영구적 |

### 3.5 10개 Crow MCP 도구

| 도구 | 설명 |
|:---|:---|
| [`crow_recall`](mcp-servers/crow_memory_server.py) | 코딩 스타일/버그 직관/아키텍처 선호도 회상 |
| [`crow_ingest`](mcp-servers/crow_memory_server.py) | 새로운 경험을 시냅틱 메모리에 저장 |
| [`crow_evolve_propose`](mcp-servers/crow_memory_server.py) | 통계적으로 유의미한 패턴에서 영구 규칙 제안 |
| [`crow_diagnostics`](mcp-servers/crow_memory_server.py) | 메모리 상태 진단 (레지스터 놈, 희소성, 업데이트 횟수) |
| [`crow_check_drift`](mcp-servers/crow_memory_server.py) | 메모리 드리프트 감지 (신뢰도 저하) |
| [`crow_ingest_from_build`](mcp-servers/crow_memory_server.py) | 빌드 종료 코드에서 자동 극성 평가 후 저장 |
| [`crow_get_user_bias`](mcp-servers/crow_memory_server.py) | 프롬프트 주입용 `[User Bias]` 블록 생성 |
| [`crow_manage_prompt`](mcp-servers/crow_memory_server.py) | `system_prompt.md` 읽기/추가/통계 |
| [`crow_manage_backup`](mcp-servers/crow_memory_server.py) | 메모리 백업 생성/순환/조회/복구 |
| [`crow_project_info`](mcp-servers/crow_memory_server.py) | 프로젝트별 격리 메모리 인스턴스 |

---

## 4. Quick Start

### 4.1 요구사항

- **Python 3.10+**
- **Zoo Code** (또는 MCP 호환 AI 코딩 에이전트)
- Git

### 4.2 설치 (원 커맨드)

**Windows (PowerShell):**
```powershell
git clone https://github.com/myk1yt/crowmemory.git
cd crowmemory
.\install.ps1
```

**macOS / Linux:**
```bash
git clone https://github.com/myk1yt/crowmemory.git
cd crowmemory
python install.py
```

인스톨러가 자동으로:
- Python 의존성 설치
- `crow.bin` (140MB 고정 크기 가중치 행렬) 초기화
- `.vscode/tasks.json` 생성 — 워크스페이스 열면 SSE 서버 자동 시작
- **"Orchestrator + Crow"** 커스텀 모드 생성
- 글로벌 MCP 설정에 Crow Memory 등록
- Windows 시작 프로그램에 SSE 서버 등록
- 10개 Crow 도구 사전 승인 (`alwaysAllow`)

### 4.3 VibeZoo MCP Bridge 수동 설정

VibeZoo Bridge는 VS Code Extension으로 자동 관리되지만, 수동 설정이 필요한 경우:

```json
// .roo/mcp.json
{
  "mcpServers": {
    "vibezoo": {
      "url": "http://localhost:9027/sse"
    }
  }
}
```

### 4.4 확인

AI에게 물어보세요:
> "crow_diagnostics 도구를 호출해서 Crow 메모리 상태를 확인해줘."

Crow가 살아있다면 레지스터 놈(norm), 업데이트 횟수, 값 뱅크 크기 등을 보고합니다.

---

## 5. 아키텍처 개요

```
┌──────────────────────────────────────────────────────────────┐
│                      VS Code Window                           │
│                                                               │
│  ┌──────────────────────┐    ┌────────────────────────────┐  │
│  │   Zoo Code (LLM)     │    │  VibeZoo Extension          │  │
│  │                      │    │                             │  │
│  │  • LLM Reasoning     │    │  • FixLoopManager (자율 수정)│  │
│  │  • Crow Memory 내장  │    │  • VisualVibePanels (화이트 │  │
│  │    (localhost:9020)  │    │    보드·UI Preview)         │  │
│  │  • MCP Client        │    │  • Safety Net (yocto·File  │  │
│  │                      │    │    Guard·Git Stash)         │  │
│  └──────────┬───────────┘    └─────────────┬──────────────┘  │
│             │ MCP/SSE                      │ child_process    │
└─────────────┼──────────────────────────────┼──────────────────┘
              ▼                              ▼
┌─────────────────────────┐  ┌─────────────────────────────────┐
│ Crow Memory (9020)      │  │ VibeZoo MCP Bridge (9027)       │
│                         │  │                                 │
│ • crow_recall           │  │ • 34 MCP Tools                 │
│ • crow_ingest           │  │ • tree-sitter AST               │
│ • crow_diagnostics      │  │ • intent_detector (UX)          │
│ • 7 more tools          │  │ • Vision AI (MiniCPM)           │
└─────────────────────────┘  └─────────────────────────────────┘
```

자세한 내용은 [`Architecture.md`](fromscratch/Architecture.md)를 참조하세요.

---

## 6. 라이선스 및 연락처

MIT License — [`LICENSE`](LICENSE) 참조.

### 상업 서비스 / 맞춤형 개발 문의

Crow Memory는 MIT 라이선스로 누구나 무료로 사용할 수 있습니다. 하지만 모든 조직은 저마다 다른 요구사항을 가지고 있습니다 — 보안 요구사항, 독점 LLM 통합, 커스텀 인코딩, 산업별 컴플라이언스 등.

**다음과 같은 맞춤형 개발 서비스를 제공합니다:**

- 🔒 **보안 강화 배포** — 에어갭 환경, 온프레미스 전용, 암호화된 `crow.bin` 저장소, 감사 로깅, RBAC 통합
- 🏢 **엔터프라이즈 커스터마이징** — 커스텀 레지스터 차원, 산업별 감쇠 프로필 (금융·의료·법률), SLA 기반 MCP 서버 클러스터
- 🤖 **LLM 특화 최적화** — 파인튜닝된 임베딩 모델, 커스텀 프로젝션 레이어, 특정 LLM 아키텍처에 최적화된 가중치 행렬
- 🧩 **소프트웨어 통합** — 비 VS Code IDE용 플러그인, CI/CD 파이프라인 훅, 커스텀 빌드 이벤트 감지기
- 🌐 **추가 언어 지원** — 36개 VS Code 로케일 외 모든 언어 및 도메인 특화 용어 지원
- 📊 **엔터프라이즈 분석** — 메모리 사용 대시보드, 팀 단위 스타일 일관성 모니터링, 드리프트 알림

> **보안강화형, 기업용 혹은 특정 LLM이나 소프트웨어 맞춤형 Crow Memory 개발을 원하시는 분은 아래로 연락주세요.**

📧 **myk1yt@gmail.com**

---

*VibeZoo v0.14.0 — 2026년 6월*
*Co-designed by Stefano, Kim & AI*
