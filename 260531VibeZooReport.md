# VibeZoo MCP Bridge — 35개 도구 실사용 평가 보고서 (v0.14.0 SOTA)

> **작성일**: 2026-05-31
> **대상**: [`mcp-servers/bridge/tools/`](mcp-servers/bridge/tools/) — 12개 모듈, 35개 MCP 도구
> **버전**: v0.14.0 SOTA (SearchEngine + AstEngine + FileCache + ResultRanker + CrowClient + OcrEngine + ToolContext + LLMToolPipeline)
> **평가 기준**: VibeZoo 5대 철학 — 가벼움, 120% 우수성, 컨텍스트 절약, LLM DX, 오픈소스 활용

---

## 철학 재확인

| # | 원칙 | 판단 기준 |
|:---:|:---|:---|
| 1 | **가볍고 빨라야 함** | LLM이 동일 기능을 Python으로 직접 짜는 것보다 실행 시간·코드량·의존성 측면에서 우위 |
| 2 | **120% 이상 결과물 우수** | 도구 출력이 LLM 단독 출력보다 정확성·완결성·구조화 측면에서 1.2배 이상 |
| 3 | **LLM 컨텍스트 절약** | 원시 데이터를 전처리/요약/필터링하여 LLM에 전달되는 토큰 수 최소화 |
| 4 | **LLM DX** | 파라미터 직관성, 에러 메시지 명확성, 반환 형식 일관성 — LLM이 사용하기 편한가 |
| 5 | **오픈소스/웹 활용** | 외부 생태계(ripgrep, tree-sitter, OpenCV, DuckDuckGo)를 적극 활용하는가 |

---

## 종합 평가 매트릭스

| 등급 | 의미 | 해당 도구 |
|:---:|:---|:---|
| ⭐⭐⭐ | **LLM 단독보다 확실히 우수** — 철학 5개 중 4개 이상 충족 | 8개 |
| ⭐⭐ | **부분적 우수, 개선 여지 있음** — 2~3개 충족 | 20개 |
| ⭐ | **LLM 직접 구현과 큰 차이 없음** — 재검토 필요 | 6개 |
| 💀 | **폐기 권장 / 통합 완료** | 1개 |

---

## 1. Setup 그룹 — [`setup.py`](mcp-servers/bridge/tools/setup.py) (1 tool)

### 1.1 `vibezoo_setup(target, python_packages, system_tools, configure_mcp, configure_zoo, dry_run)` ⭐⭐⭐

**작동 방식**: `SetupManager` 클래스 — pip 패키지 설치(개별 importlib 체크), 시스템 도구(winget→choco→scoop→apt→brew fallback), `.roo/mcp.json` + `.zoo/config.json` 자동 구성. `dry_run=True` 시 진단만 수행.

**실사용 예시**:
- `vibezoo_setup(target="recommended")` → 코어 + OpenCV/Pillow/tree-sitter/pytesseract 설치, MCP 설정
- `vibezoo_setup(dry_run=True)` → 설치 전 사전 진단

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | LLM이 `pip install` + `winget install` + JSON 파일 생성 스크립트를 직접 짜는 것보다 훨씬 가벼움 (특히 OS별 fallback 로직) |
| 120% 우수 | ✅ | OS 자동 감지 + 패키지 매니저 fallback 체인(winget→choco→scoop)을 LLM이 정확히 구현하기 어려움. `importlib` 기반 설치 여부 확인도 견고함 |
| 컨텍스트 절약 | ✅ | 설치 결과를 구조화된 마크다운 보고서로 요약. LLM이 원시 pip 로그를 파싱할 필요 없음 |
| LLM DX | ✅ | `dry_run` 모드 제공으로 사전 확인 가능. 파라미터 기본값(`target="minimal"`)이 안전 |

**부족한 점**:
- `recommended`와 `full`의 차이가 시스템 도구(rg, tesseract) 뿐 — `full` 타겟의 실질적 가치 낮음
- 설치 실패 시 원인 분석 없이 단순 실패 보고. "왜 실패했는지"를 LLM에게 설명해주지 않음
- `configure_mcp`가 글로벌 MCP 설정과 프로젝트 로컬 설정 구분 없이 덮어쓰기 가능성

**개선 방안**:
- [ ] 설치 실패 원인을 LLM이 해석 가능한 형태로 반환 (예: "pip 연결 실패 → 프록시 확인 필요")
- [ ] `target="full"`에 PaddleOCR, html2text 등 추가 가치 제공
- [ ] MCP 설정 백업 후 병합 (기존 서버 설정 보존)

---

## 2. Scout 그룹 — [`scout.py`](mcp-servers/bridge/tools/scout.py) (3 tools)

### 2.1 `search_codebase(query, file_patterns?, max_results?, mode?, context_lines?)` ⭐⭐⭐

**작동 방식**: `SearchEngine` (ripgrep → git grep → os.walk 3단계 fallback) + `AstEngine` 보완. `mode`에 따라 exact/fuzzy/ast/semantic/auto 전환. 결과에 컨텍스트 라인 포함.

**실사용 예시**:
- `search_codebase(query="UserService", mode="ast")` → AST 기반 클래스 정의 검색
- `search_codebase(query="TODO", mode="exact", file_patterns="*.py")` → Python 파일 내 TODO 검색

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | ripgrep 사용 시 LLM이 `grep -r` 돌리는 것보다 수십 배 빠름. 단, ripgrep 미설치 시 `os.walk` 폴백은 LLM 직접 구현과 동일 속도 |
| 120% 우수 | ✅ | AST 검색(클래스/함수/인터페이스 심볼 매칭) + 라인 검색 동시 제공. LLM이 tree-sitter 파싱 코드를 매번 작성할 필요 없음 |
| 컨텍스트 절약 | ✅ | `max_results` 상한(200) + 컨텍스트 라인 제한. 불필요한 전체 파일 내용 전달 방지 |
| LLM DX | ⚠️ | `mode="semantic"`은 placeholder — LLM이 기대하고 호출하면 빈 결과 반환. `file_patterns` 파라미터가 쉼표 구분 문자열이라 오타 가능성 |

**부족한 점**:
- ripgrep 미설치 환경에서 `os.walk` 폴백은 LLM 직접 구현 대비 속도 이점 0
- `mode="semantic"` 미구현 — LLM이 semantic search를 기대하고 호출 시 혼란
- AST 검색은 TS/JS로 제한 (`AstEngine._init_legacy_tree_sitter()`만 호출)
- `max_results=200`은 대규모 프로젝트에서 모든 결과를 담기에 부족할 수 있음

**개선 방안**:
- [ ] `semantic` 모드 실제 구현 — embedding 기반 또는 LLM reranking
- [ ] ripgrep 미설치 시 자동 설치 안내 (`vibezoo_setup` 연계)
- [ ] `AstEngine` Python/Go 언어팩 tree-sitter 실제 로딩 구현
- [ ] `file_patterns`에 glob validation 추가

### 2.2 `find_references(symbol)` ⭐⭐

**작동 방식**: `_iter_project_files_cached`로 전체 파일 순회, AST(TS/JS)로 정의 탐지 + regex로 사용 위치 감지. 참조 유형(call/read/write/type_ref/import_ref) 분류 및 Call Chain 분석 포함.

**실사용 예시**:
- `find_references(symbol="handleSubmit")` → 정의 위치 + 호출 위치 + 호출자 함수 목록

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ⚠️ | 전체 프로젝트 파일을 순회하며 AST 파싱 → 대규모 프로젝트에서 느림. LLM이 `grep` 한 번으로 동일 결과를 더 빠르게 얻을 수 있음 |
| 120% 우수 | ✅ | 참조 유형 분류(call/read/write) + Call Chain 분석은 LLM이 grep만으로는 불가능. AST 기반 함수 범위 매칭으로 정확한 호출자 탐지 |
| 컨텍스트 절약 | ✅ | By Reference Type / By File / Call Chain 3단계 구조화. LLM이 grep 결과를 수동 분류할 필요 없음 |
| LLM DX | ✅ | 심볼 하나만 입력. 출력 구조 일관적 |

**부족한 점**:
- 변수 섀도잉 미고려 — 동명 이형 심볼도 함께 반환
- Python/Go 파일은 regex 기반으로 참조 유형 분류 정확도 낮음
- 대규모 프로젝트에서 `_iter_project_files_cached` + AST 파싱이 10초 이상 소요 가능

**개선 방안**:
- [ ] AST 기반 스코프 분석으로 심볼 섀도잉 처리
- [ ] `SearchEngine` 우선 검색으로 후보 파일 필터링 후 AST 정밀 분석 (2단계)

### 2.3 `summarize_architecture(target_path?, streaming?)` ⭐⭐

**작동 방식**: `_run_map_dependencies()` + 진입점 탐지 + 파일 타입 분포 + git 로그 + path-based 레이어 분류. `streaming=True` 시 2단계 점진적 결과 (기본 정보 → 의존성 분석).

**실사용 예시**:
- `summarize_architecture()` → 프로젝트 구조 한눈에 파악
- `summarize_architecture(streaming=False)` → 전체 결과 한 번에

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ❌ | `_run_map_dependencies()` 내부에서 전체 파일 AST 파싱 + `_iter_project_files_cached`로 모든 파일 읽기 → 대규모 프로젝트에서 30초↑. LLM이 `ls -R` + `grep import`로 더 가볍게 가능 |
| 120% 우수 | ⚠️ | 레이어 분류·기술 부채 진단·git 트렌드는 LLM 단독으로는 어려운 분석. **그러나 결과물이 지나치게 장황**하여 오히려 LLM 컨텍스트 낭비 |
| 컨텍스트 절약 | ❌ | 가장 큰 문제. 레이어 구조에 모든 파일을 나열(최대 5개+...more)하고, git log, import count 등 장황한 섹션이 LLM 토큰을 대량 소비. streaming도 실질적 분할이 아닌 HTML 주석 마커만 추가 |
| LLM DX | ⚠️ | `streaming` 파라미터가 있지만 실제로 MCP 프로토콜에서 점진적 결과를 스트리밍하지 않음 (HTML 코멘트로 마커만 삽입) |

**부족한 점**:
- **결과물 너무 김** — 특히 Layer Structure 섹션이 모든 파일을 나열하여 LLM 컨텍스트 초과 위험
- path-based 레이어 분류는 휴리스틱에 불과 (실제 import 방향 무시)
- `streaming=True`가 실질적 스트리밍이 아닌 HTML 코멘트 마커 — LLM이 중간 결과를 활용할 수 없음
- `_run_map_dependencies()` 호출로 인해 `map_dependencies()` 단독 호출 대비 중복 작업

**개선 방안**:
- [ ] **핵심 요약 모드 추가**: 파일 목록 대신 레이어별 파일 수 + 대표 파일 1개만 표시
- [ ] LLM 컨텍스트 윈도우에 맞춘 `max_tokens` 파라미터
- [ ] MCP 프로토콜의 진정한 streaming(청크 단위 부분 응답) 활용

---

## 3. Reviewer 그룹 — [`reviewer.py`](mcp-servers/bridge/tools/reviewer.py) (2 tools)

### 3.1 `review_code(file_path, severity?)` ⭐⭐⭐

**작동 방식**: AST(TS/JS)로 함수/클래스 구조 파악 + 15개 이상 코드 스멜 패턴 검사 + Cyclomatic Complexity + 중첩 깊이 + 함수 길이 + 파라미터 개수. `severity` 파라미터로 필터링.

**실사용 예시**:
- `review_code(file_path="src/app.ts", severity="error")` → 에러 수준만 필터
- `review_code(file_path="src/utils.py")` → Python 파일 대상 bare except, print() 탐지

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | 단일 파일 AST 파싱 + regex 검사. LLM이 동일 검사를 위해 파일 전체를 읽고 패턴 매칭 코드를 생성하는 것보다 가벼움 |
| 120% 우수 | ✅ | Cyclomatic complexity + 중첩 깊이 + 함수 길이 + 파라미터 개수 등 **정량적 지표**는 LLM이 직관적으로 판단하기 어려움. 객관적 수치 제공이 120% 가치 |
| 컨텍스트 절약 | ✅ | severity 필터 + 구조화된 이슈 목록. LLM이 전체 파일을 읽지 않고도 문제점 파악 가능 |
| LLM DX | ✅ | `severity="all"|"error"|"warning"|"info"` 직관적. ESLint 연동 시도 |

**부족한 점**:
- Python 검사 항목이 3개(print, bare except, TODO)로 빈약
- Cyclomatic complexity가 regex 기반(`\bif\s+`)이라 실제 AST 분기와 차이 가능
- 중첩 깊이가 들여쓰기 기반(4 spaces = 1 level) — 탭 사용 파일에서 부정확
- ESLint 미설치 시 "ESLint not installed"만 출력 — 대안 없음

**개선 방안**:
- [ ] Python 검사 확장: `assert` 남용, `global` 사용, `exec()` 호출, mutable default args
- [ ] AST 노드 카운팅 기반 Cyclomatic complexity (tree-sitter `if_statement` 노드)
- [ ] `.editorconfig` 또는 `.vscode/settings.json` 읽어서 들여쓰기 설정 감지
- [ ] ESLint 미설치 시 `npx eslint` 자동 설치 시도

### 3.2 `check_quality(target_path?)` ⭐

**작동 방식**: `_review_project_core()`로 완전 위임. Cyclomatic complexity + 코드 스멜 집계 + 품질 등급(A+~F) + 파일별 등급 + ESLint.

**실사용 예시**: `check_quality()` → 프로젝트 전체 품질 점수

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ❌ | 전체 프로젝트 파일을 모두 읽고 regex 검사 → 대규모 프로젝트에서 느림. `_review_project_core`가 `review_project`의 일부 기능과 중복 |
| 120% 우수 | ⚠️ | 품질 등급(A+~F)과 파일별 등급은 직관적. 그러나 `review_project()`의 하위 집합으로 단독 가치 낮음 |
| 컨텍스트 절약 | ⚠️ | 품질 점수는 간결하나 파일별 등급 리스트가 장황 |
| LLM DX | ⚠️ | `review_project`와 기능 중복으로 LLM이 어떤 도구를 써야 할지 혼란 |

**부족한 점**:
- `review_project()`와 기능 중복. 단독 존재 가치가 희박
- 대규모 프로젝트에서 전체 파일 순회로 인한 지연

**개선 방안**:
- [ ] `review_project(target_path, mode="quick")`으로 통합하고 `check_quality`는 내부 어댑터로 유지
- [ ] 품질 점수만 빠르게 반환하는 `mode="score"` 추가

---

## 4. DeepAnalyzer 그룹 — [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py) (4 tools)

### 4.1 `analyze_call_graph(file_path?, depth?, include_external?)` ⭐⭐⭐

**작동 방식**: AST로 함수 정의 맵 구축 → 호출 관계 추출 → Fan-in/Fan-out 메트릭 + Dead Code Detection + Per-File Call Analysis.

**실사용 예시**:
- `analyze_call_graph(file_path="src/service.ts", depth=5)` → 호출 체인 분석
- `analyze_call_graph()` → 전체 프로젝트 Dead Code 탐지

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ⚠️ | 전체 TS/JS 파일 AST 파싱 + 호출 추출 + 함수 정의 매칭(O(N²)). LLM이 파일 하나씩 읽으며 호출 관계를 추적하는 것보다 정확하지만 반드시 가볍지는 않음 |
| 120% 우수 | ✅ | Fan-in/Fan-out + Dead Code Detection은 LLM 단독으로는 거의 불가능한 분석. Mermaid 그래프 자동 생성도 가치 있음 |
| 컨텍스트 절약 | ✅ | Per-File Call Analysis가 파일별로 top 10 호출만 표시. Dead Code 목록도 상위 10개로 제한 |
| LLM DX | ✅ | `depth` 파라미터 직관적. Dead Code Detection은 실용적 가치 높음 |

**부족한 점**:
- TS/JS로 제한 — Python/Go 함수는 감지되지 않음
- Dynamic dispatch, 고차 함수 콜백 추적 불가
- Dead Code Detection이 "호출자 없음"으로만 판단 — export된 public API도 dead로 오판 가능

**개선 방안**:
- [ ] Python/Go 함수 정의 감지 (tree-sitter 언어팩 로딩)
- [ ] `export` 키워드 감지 → public API는 dead code에서 제외
- [ ] Mermaid 호출 그래프를 화이트보드에 자동 렌더링

### 4.2 `map_dependencies(target_path?)` ⭐⭐⭐

**작동 방식**: AST(TS/JS) + regex(Python/Go) import 추출. 패키지 매니저 정보 + 순환 참조 탐지(iterative DFS) + 영향도 분석(Impact Analysis).

**실사용 예시**:
- `map_dependencies()` → 프로젝트 의존성 구조 및 순환 참조 파악

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ⚠️ | 전체 파일 import 추출 + 순환 참조 DFS. 중간 규모 프로젝트까지는 허용 가능 |
| 120% 우수 | ✅ | 순환 참조 탐지 + 영향도 분석(LOW/MEDIUM/HIGH/CRITICAL)은 LLM이 수동으로 수행하기 매우 어려움 |
| 컨텍스트 절약 | ⚠️ | Import Count by File이 모든 파일의 모든 import를 나열 → 장황함. 영향도 분석은 top 10만 표시하여 양호 |
| LLM DX | ✅ | 패키지 매니저 자동 감지. 순환 참조 발견 시 명확한 경로 표시 |

**부족한 점**:
- 순환 참조 탐지가 iterative DFS로, Tarjan SCC 알고리즘과 다름 (설계서 불일치)
- 외부 패키지(node_modules)와 내부 모듈 구분 불명확
- 영향도 분석이 직접 import에만 기반 — transitive 의존성 미고려

**개선 방안**:
- [ ] 실제 Tarjan SCC 알고리즘 구현
- [ ] 내부/외부 의존성 구분 표시
- [ ] "이 파일을 수정하면 N개 파일이 간접 영향" transitive 분석

### 4.3 `extract_patterns(target_path?, min_occurrences?)` ⭐⭐

**작동 방식**: `_extract_patterns_ast()` — tree-sitter AST 서브트리 매칭 + regex 폴백. 10개 패턴 템플릿(try-catch, callback-hell, god-class, promise-chain, long-method 등). 안티패턴 태깅.

**실사용 예시**:
- `extract_patterns(min_occurrences=5)` → "이 프로젝트에서 5회 이상 반복되는 패턴"

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | AST 파싱 + 템플릿 매칭. LLM이 모든 파일을 읽고 패턴을 수동 분류하는 것보다 가벼움 |
| 120% 우수 | ✅ | 안티패턴(god-class, callback-hell, long-method) 자동 태깅은 LLM이 간과하기 쉬운 정량적 분석 |
| 컨텍스트 절약 | ✅ | 패턴별 발생 횟수 + 예시 3개만 표시. `min_occurrences`로 노이즈 필터링 |
| LLM DX | ✅ | 안티패턴이 명확히 태깅(⚠️ ANTIPATTERN)되어 LLM이 빠르게 인지 |

**부족한 점**:
- 템플릿 10개로 제한 — 프로젝트 특화 패턴 감지 불가
- AST 매칭이 TS/JS 함수 타입 필드(`func['type']`) 기반 — tree-sitter 실제 노드 타입과 다를 수 있음
- 커스텀 패턴 추가 인터페이스 없음

**개선 방안**:
- [ ] Crow Memory에 프로젝트별 커스텀 패턴 저장 및 로드
- [ ] tree-sitter query 파일(.scm) 기반 패턴 정의 지원
- [ ] 패턴 발생 위치에 대한 코드 스니펫 포함

### 4.4 `reverse_engineer(target_path?, output_format?)` ⭐⭐

**작동 방식**: regex 기반 API 라우트 추출(Express/FastAPI/Flask/Gin) + AST 기반 데이터 모델 필드 추출 + Mermaid ERD/OpenAPI 3.0 출력.

**실사용 예시**:
- `reverse_engineer(output_format="mermaid")` → ERD 다이어그램
- `reverse_engineer(output_format="openapi")` → OpenAPI 스펙

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ⚠️ | 파일 전체 순회 + regex/AST 추출. 중간 규모까지 허용 |
| 120% 우수 | ✅ | Mermaid ERD + OpenAPI 3.0 스펙 자동 생성은 LLM이 수동으로 작성하기 번거로운 작업 |
| 컨텍스트 절약 | ✅ | OpenAPI 출력이 구조화된 YAML. Mermaid는 다이어그램으로 압축 |
| LLM DX | ✅ | `output_format` 3가지(markdown/openapi/mermaid) 지원 |

**부족한 점**:
- API 라우트 추출이 regex 기반 — NestJS/Next.js App Router 미지원, 데코레이터 패턴 누락
- 데이터 모델 관계 추론이 필드명 기반 휴리스틱 (`User` → `userId` → 관계)
- OpenAPI 출력이 path/method만 있고 request/response body 스키마 누락

**개선 방안**:
- [ ] AST 기반 데코레이터/어노테이션 분석 (NestJS `@Controller`, `@Get` 등)
- [ ] TypeORM/Prisma/SQLAlchemy 모델 데코레이터로 실제 DB 스키마 추론
- [ ] JSDoc/TSDoc/docstring에서 description, param 추출

---

## 5. Tester 그룹 — [`tester.py`](mcp-servers/bridge/tools/tester.py) (2 tools)

### 5.1 `generate_tests(source_path, framework?)` ⭐

**작동 방식**: AST로 함수 시그니처 추출 → 경계값 테스트 힌트 + 브랜치 커버리지 + 에러 케이스 + Mock 제안 + Expected Behavior 추론 + 테스트 뼈대 코드 생성.

**실사용 예시**:
- `generate_tests(source_path="src/auth.ts")` → Jest/Vitest 테스트 템플릿
- `generate_tests(source_path="utils.py")` → pytest 템플릿

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | 단일 파일 AST 파싱으로 빠름 |
| 120% 우수 | ❌ | **핵심 문제**. 생성된 테스트가 `test_() { /* TODO: write test */ }` 수준의 빈 템플릿. LLM이 직접 테스트를 작성하는 것이 200% 이상 우수 |
| 컨텍스트 절약 | ✅ | 함수 시그니처 + 파라미터 정보만 LLM에 전달 |
| LLM DX | ⚠️ | Boundary Value, Branch Coverage, Error Cases, Mock Suggestions 등 다양한 섹션이 있으나 실질적 도움은 제한적 |

**부족한 점**:
- **LLM 직접 작성 대비 열등**: 테스트 템플릿만 생성하고 실제 로직은 비어있음. LLM이 함수 코드를 직접 보고 테스트를 작성하는 것이 훨씬 나음
- Mock 데이터가 "use 42" 수준의 일반론
- Expected Behavior 추론이 함수명 prefix 기반(get→returns data 등) 휴리스틱
- Python은 함수 시그니처 추출이 regex 기반이라 `def test_(): pass`만 생성

**개선 방안**:
- [ ] **LLM-도구 체인으로 역할 전환**: `generate_tests`는 함수 시그니처 + 타입 + docstring + 의존성 그래프를 **수집**하고, LLM이 이 데이터를 기반으로 실제 테스트 로직을 **생성**
- [ ] Property-based testing 템플릿 (fast-check/hypothesis)
- [ ] 기존 테스트 파일 분석 → 프로젝트 테스트 컨벤션 자동 감지

### 5.2 `analyze_coverage(target_path?)` ⭐⭐

**작동 방식**: 파일 존재 기반 빠른 경로(테스트/소스 매핑) + vitest/pytest 외부 도구 실행 시도.

**실사용 예시**:
- `analyze_coverage()` → "54개 소스 파일 중 12개만 테스트 있음"

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | 빠른 경로는 파일 존재 여부만 확인. 외부 도구 실행은 30초 타임아웃 |
| 120% 우수 | ⚠️ | Test/Source ratio + Missing Test Detection은 유용하지만, LLM이 `find . -name "*.test.*"`로 유사 결과 가능 |
| 컨텍스트 절약 | ✅ | 누락된 테스트 파일 목록 top 10만 표시 |
| LLM DX | ✅ | vitest/pytest 자동 감지 및 실행 시도 |

**부족한 점**:
- vitest/pytest 미설치 시 "No coverage data found" — 실패 원인 구체적이지 않음
- 테스트-소스 매핑이 파일명 규칙 기반이라 부정확 (예: `user.test.ts` → `user.ts`)
- 커버리지 임계값(0.3/0.5)이 하드코딩

**개선 방안**:
- [ ] vitest/pytest 미설치 시 `vibezoo_setup` 안내
- [ ] `import` 관계 기반 테스트-소스 매핑 (파일명 규칙 없이도)
- [ ] 커버리지 목표 설정 파라미터 추가

---

## 6. Whiteboard 그룹 — [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) (5 tools)

### 6.1 `draw_on_whiteboard(commands)` ⭐⭐

**작동 방식**: Fabric.js JSON 명령을 `~/.vibezoo-whiteboard.json`에 저장. `WhiteboardDataConverter`로 Mermaid 변환 가능.

**실사용 예시**:
- `draw_on_whiteboard('[{"type":"rect","props":{"left":100,"top":100,"width":200,"height":50,"fill":"#4ec9ff"}}]')` → 사각형 그리기

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | JSON 파일 쓰기 한 번 |
| 120% 우수 | ⚠️ | LLM이 Fabric.js JSON을 직접 생성해야 함 — 문법 오류 가능성. Mermaid→Fabric.js 변환 레이어가 없어 LLM이 이중 작업 |
| 컨텍스트 절약 | n/a | 시각적 도구 |
| LLM DX | ❌ | Fabric.js JSON 문법을 LLM이 알아야 함. 자연어→JSON 변환 레이어 부재 |

**부족한 점**:
- LLM이 Fabric.js JSON을 직접 작성해야 함 — 높은 진입 장벽
- 복잡한 다이어그램에서 JSON이 수백 줄로 폭증

**개선 방안**:
- [ ] Mermaid 텍스트를 직접 입력받아 Fabric.js JSON으로 변환 (역변환)
- [ ] 다이어그램 템플릿 라이브러리: flowchart, ERD, sequence diagram

### 6.2 `get_whiteboard_state()` ⭐⭐⭐

**작동 방식**: `WhiteboardDataConverter` — Fabric.js JSON → 객체 목록 + 관계(연결/포함/근접/정렬) + 공간 레이아웃(그리드/크기/색상) + Mermaid 다이어그램 + 원본 JSON(2000자 제한).

**실사용 예시**:
- `get_whiteboard_state()` → "화이트보드에 뭐가 그려져 있어?"

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | JSON 파일 읽기 + 변환 |
| 120% 우수 | ✅ | **이 도구의 핵심 가치**. Fabric.js 좌표 데이터를 LLM이 이해할 수 있는 텍스트(그리드 위치, 색상명, 관계)로 변환. LLM이 raw JSON을 해석하는 것보다 300% 이상 우수 |
| 컨텍스트 절약 | ✅ | 원본 JSON은 2000자로 제한. Mermaid 다이어그램으로 시각적 구조 압축 |
| LLM DX | ✅ | 반환 형식이 구조화된 마크다운 — Objects 테이블 + Relationships 리스트 + Spatial Layout + Mermaid |

**부족한 점**:
- 화이트보드에 이미지(스크린샷)가 있을 때는 변환하지 않고 raw JSON만 반환
- Mermaid 변환이 모든 객체 유형을 완벽히 지원하지 않음 (image, freehand 등)
- 사용자 annotation의 의미론적 해석 없음

**개선 방안**:
- [ ] 이미지 데이터를 SSA 분석 파이프라인에 자동 연결
- [ ] annotation 텍스트에 대한 감정/의도 분석 (LLM 체인)

### 6.3 `open_whiteboard(message?)` ⭐

**작동 방식**: `WHITEBOARD_ACTION_FILE`에 `{"action":"open"}` 기록. VSCode Extension이 파일 watch.

**실사용 예시**: `open_whiteboard(message="이 다이어그램을 확인해주세요")`

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | JSON 파일 쓰기 한 번 |
| 120% 우수 | ❌ | LLM이 직접 "화이트보드를 열어주세요"라고 말하는 것과 기능적 차이 없음 |
| 컨텍스트 절약 | n/a | |
| LLM DX | ❌ | `message` 파라미터가 있지만 Extension이 활용하지 않음 |

**부족한 점**:
- `message` 파라미터가 Extension에서 무시됨
- 단순 패널 열기 이상의 가치 없음

**개선 방안**:
- [ ] Extension이 `message`를 Webview에 표시
- [ ] 특정 다이어그램을 미리 로드해서 열기 (상태 복원)

### 6.4 `capture_screen(source?)` ⭐⭐⭐

**작동 방식**: 3단계 fallback — PIL `ImageGrab` → PowerShell `[System.Windows.Forms]` → mss. `source="dropzone"`이면 Webview 드롭존 열기. `source="file"`이면 파일 선택 다이얼로그.

**실사용 예시**:
- `capture_screen()` → 화면 캡처 후 화이트보드에 표시
- `capture_screen(source="dropzone")` → 이미지 업로드 UI

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | OS 네이티브 API 호출. LLM이 스크린샷 스크립트를 직접 작성하는 것보다 가벼움 |
| 120% 우수 | ✅ | 크로스플랫폼 fallback 체인 + 화이트보드 자동 연동. LLM이 OS별 다른 방식으로 구현할 필요 없음 |
| 컨텍스트 절약 | ✅ | 캡처 성공/실패만 간결히 보고 |
| LLM DX | ✅ | `source` 파라미터 하나로 화면/드롭존/파일 3가지 모드 |

**부족한 점**:
- PowerShell fallback이 MessageBox 등 UX 노이즈 발생 가능
- 캡처 후 자동 SSA 분석 파이프라인 부재

**개선 방안**:
- [ ] PowerShell `-WindowStyle Hidden` 적용
- [ ] 캡처 후 자동 `aggregate_spatial_pixels` 호출 옵션 (`analyze=True`)

### 6.5 `open_ui_preview(code?, framework?)` ⭐⭐

**작동 방식**: 코드를 `UI_ACTION_FILE`에 저장. Extension Webview가 Babel standalone + iframe으로 렌더링.

**실사용 예시**:
- `open_ui_preview(code="<Button>Click</Button>", framework="react")` → UI 미리보기

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | 파일 쓰기 한 번 |
| 120% 우수 | ✅ | LLM이 생성한 UI 코드를 실제 렌더링하여 확인 가능 — LLM 단독으로는 불가능 |
| 컨텍스트 절약 | n/a | |
| LLM DX | ⚠️ | Babel standalone 변환으로 실제 환경과 차이. 외부 CSS/JS 로딩 불가 |

**부족한 점**:
- 외부 리소스(이미지, CSS, JS) 로딩 불가
- 에러 발생 시 조용히 실패 (Webview에 피드백 없음)
- Tailwind CSS 등 유틸리티 CSS 미지원

**개선 방안**:
- [ ] Tailwind CSS CDN 기본 포함
- [ ] 컴파일 에러를 Webview에 표시
- [ ] 외부 리소스 URL 임포트 지원

---

## 7. Fix Loop 그룹 — [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py) (3 tools)

### 7.1 `auto_fix_status()` ⭐⭐⭐

**작동 방식**: `FIX_REQUEST_FILE`에서 에러 정보 읽기 + Crow 과거 유사 에러 패턴 조회 + 상태 업데이트.

**실사용 예시**:
- 빌드 실패 → `auto_fix_status()` → "TS2322 에러, 과거 2회 유사 패턴 있음"

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | JSON 파일 읽기 + Crow 쿼리 |
| 120% 우수 | ✅ | Crow Memory에서 과거 유사 에러 패턴을 자동 조회 — LLM이 수동으로 기억을 검색하는 것보다 우수 |
| 컨텍스트 절약 | ✅ | 에러 정보 + 과거 해결책만 LLM에 전달 |
| LLM DX | ✅ | 상태 머신(idle/in_progress/resolved/abandoned)으로 현재 Fix Loop 상태 파악 가능 |

**부족한 점**:
- JSON 파일 기반 통신으로 race condition 가능성
- Crow 과거 패턴이 메타데이터만 포함하고 구체적 diff 코드는 없음
- Extension `FixLoopManager`(8개 상태)와 Bridge(6개 상태) 상태 머신 불일치

**개선 방안**:
- [ ] Crow 과거 패턴에 구체적 diff/solution 코드 포함
- [ ] 상태 머신 Extension-Bridge 동기화

### 7.2 `retry_build(build_command?)` ⭐⭐

**작동 방식**: 프로젝트 타입별 빌드 명령어 자동 감지(package.json → `npx tsc --noEmit`). `build_command`로 override 가능. 빌드 결과를 FIX_REQUEST_FILE 기록.

**실사용 예시**:
- `retry_build()` → 코드 수정 후 빌드 재시도

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | subprocess 실행 |
| 120% 우수 | ⚠️ | 빌드 실행 자체는 LLM이 터미널 명령으로도 가능. 자동 감지 + Crow 기록은 부가 가치 |
| 컨텍스트 절약 | ❌ | 빌드 로그 전체(2000자) 반환 — 에러 부분만 추출하지 않음. LLM이 전체 로그에서 에러를 찾아야 함 |
| LLM DX | ⚠️ | 프로젝트 타입 감지가 package.json 존재 여부로만 판단 |

**부족한 점**:
- 빌드 로그 전체 반환 → LLM 컨텍스트 낭비. 에러/경고만 추출 필요
- 타임아웃 60초 — 대규모 프로젝트에서 부족
- `npx tsc --noEmit`만 자동 감지 (npm run build, make, cargo build 등 미지원)

**개선 방안**:
- [ ] 빌드 로그에서 에러/경고 라인만 지능적 추출
- [ ] `package.json`의 `scripts.build` 읽어서 자동 감지
- [ ] 타임아웃 설정 파라미터화

### 7.3 `check_intervention()` ⭐⭐

**작동 방식**: Whiteboard 상태 + Chat 메시지 파일 체크 → HITL 인터럽트 확인.

**실사용 예시**:
- Auto-Fix Loop 중 `check_intervention()` → 사용자 개입 여부 확인

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | JSON 파일 2개 읽기 |
| 120% 우수 | ⚠️ | Whiteboard/Chat 통합 확인은 LLM 단독으로 불가능하나, 실질적 활용도 낮음 |
| 컨텍스트 절약 | ✅ | `should_pause` 불리언으로 간결 |
| LLM DX | ⚠️ | `should_pause` 설정 주체가 불명확 |

**부족한 점**:
- `should_pause` 필드를 누가 설정하는지 불명확 (Extension? Bridge?)
- 채팅 메시지 읽은 후 파일 삭제 → 메시지 소실 위험

**개선 방안**:
- [ ] Extension 명령과 Bridge 체크 양방향 통합
- [ ] 사용자 개입 이력을 Crow Memory에 저장 → 패턴 학습

---

## 8. Integrated 그룹 — [`integrated.py`](mcp-servers/bridge/tools/integrated.py) (4 tools)

### 8.1 `review_project(target_path, streaming?)` ⭐⭐

**작동 방식**: 4단계 파이프라인 — `search_codebase`(TODO/FIXME/HACK/BUG) → `review_code`(top 5 files) → `check_quality` → `extract_patterns`. `streaming=True` 시 HTML 코멘트 진행 마커.

**실사용 예시**:
- `review_project(target_path=".")` → 프로젝트 종합 리뷰

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ❌ | 4개 도구 순차 호출 + 각각 파일 스캔 중복. 대규모 프로젝트에서 60초↑ |
| 120% 우수 | ⚠️ | 4개 도구 통합은 편리하나, 각 도구의 출력을 그대로 합쳐서 **결과물이 너무 김** |
| 컨텍스트 절약 | ❌ | **가장 심각한 문제**. 모든 하위 도구 결과를 구분자(`---`)로 연결 → LLM 컨텍스트 윈도우를 쉽게 초과. `review_code` 섹션이 top 5 파일의 전체 리뷰 결과를 그대로 포함 |
| LLM DX | ⚠️ | `streaming`이 HTML 코멘트 마커만 추가하여 실질적 streaming 아님 |

**부족한 점**:
- **결과물 과잉**: 4개 도구의 전체 출력을 모두 포함 → LLM이 중요 정보를 찾기 어려움
- 파일 스캔 중복: `search_codebase` → `review_code` → `check_quality` → `extract_patterns` 각각 `_iter_project_files` 호출
- `streaming=True`가 MCP 프로토콜의 진정한 streaming을 활용하지 않음

**개선 방안**:
- [ ] **요약 우선 모드**: 핵심 발견 사항만 Executive Summary로 반환, 상세는 접을 수 있는 `<details>` 태그 사용
- [ ] `FileCache` 활용한 파일 목록 공유 (중복 스캔 방지)
- [ ] 중요도/심각도 기반 결과 정렬 — "Quick Wins" 섹션 별도

### 8.2 `find_bugs(target_path)` ⭐⭐

**작동 방식**: `extract_patterns` + `search_codebase`(14개 suspicious 패턴: console.log, debugger, .only, fit, any, @ts-ignore 등) + Crow recall.

**실사용 예시**:
- `find_bugs(target_path=".")` → console.log, debugger, any 타입 등 탐지

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ⚠️ | 14개 `search_codebase` 순차 호출 → 각각 파일 스캔. 중복 많음 |
| 120% 우수 | ⚠️ | 정적 분석 패턴 탐지는 유용하나, LLM도 `grep`으로 유사 결과 가능. **실제 로직 버그 미탐지** |
| 컨텍스트 절약 | ⚠️ | 각 suspicious query 결과를 그대로 포함 → 중복된 파일 목록이 여러 번 등장 |
| LLM DX | ⚠️ | 찾는 "버그"가 실제 버그가 아닌 코드 스멜(console.log, any) — 명칭이 오해의 소지 |

**부족한 점**:
- 검색 패턴이 14개로 고정 — 프로젝트별 버그 패턴 대응 불가
- `search_codebase` 14회 순차 호출로 인한 지연 + 중복 결과
- "버그"보다는 "코드 스멜 / 안티패턴" 탐지에 가까움

**개선 방안**:
- [ ] 14개 패턴을 단일 `search_codebase` 정규식으로 통합 (OR 조건)
- [ ] Crow bug register에 프로젝트별 버그 패턴 DB 구축
- [ ] `npx tsc --noEmit --strict` 결과 통합

### 8.3 `suggest_refactor(target_path)` ⭐⭐

**작동 방식**: `map_dependencies` + `extract_patterns` + `analyze_call_graph` 통합 + Crow style rules 조회.

**실사용 예시**:
- `suggest_refactor(target_path=".")` → "이 파일은 의존성이 너무 많습니다"

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ❌ | 3개重型 도구 순차 호출 → 대규모 프로젝트에서 매우 느림 |
| 120% 우수 | ⚠️ | 의존성 분석 + 호출 그래프 + 패턴 분석 통합은 LLM 단독으로 어려우나, 제안이 일반론 수준 |
| 컨텍스트 절약 | ❌ | 세 도구의 전체 출력을 포함 → 결과물 과잉 |
| LLM DX | ⚠️ | "파일이 너무 큼" 수준의 일반적 제안만 생성 |

**부족한 점**:
- 리팩토링 제안이 일반론 — "파일이 너무 큼", "함수가 너무 많음". 구체적 액션 없음
- 변경 전/후 코드 예시 없음
- 세 도구의 전체 결과를 포함하여 LLM 컨텍스트 낭비

**개선 방안**:
- [ ] LLM-도구 체인: 도구가 데이터 수집 → LLM이 구체적 리팩토링 제안 생성
- [ ] "Quick Wins" 섹션 — 즉시 적용 가능한 작은 리팩토링 제안
- [ ] 영향도 점수 포함 ("이 변경으로 N개 파일 영향")

### 8.4 `generate_docs(target_path, output_format?)` ⭐⭐

**작동 방식**: `summarize_architecture` + `reverse_engineer` + `draw_on_whiteboard`(디렉토리 트리 다이어그램).

**실사용 예시**:
- `generate_docs(output_format="mermaid")` → 아키텍처 문서 + ERD + 화이트보드 다이어그램

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ❌ | 3개重型 도구 순차 호출 |
| 120% 우수 | ✅ | 아키텍처 문서 + API 명세 + ERD + 화이트보드 다이어그램을 한 번에 생성. LLM이 수동으로 Markdown 문서를 작성하는 것보다 우수 |
| 컨텍스트 절약 | ❌ | 모든 하위 도구 출력을 포함 → 과잉 |
| LLM DX | ⚠️ | 화이트보드 다이어그램이 디렉토리 트리(파일/폴더)만 그려서 실질적 가치 낮음 |

**부족한 점**:
- 화이트보드 다이어그램이 단순 디렉토리 트리 — 아키텍처 다이어그램이 아님
- `draw_on_whiteboard` 실패 시 전체 문서 생성이 중단되지 않으나, 실패 원인 분석 없음

**개선 방안**:
- [ ] 화이트보드에 실제 아키텍처 다이어그램(모듈 간 의존성 그래프) 렌더링
- [ ] 생성된 문서를 파일로 저장하는 옵션 (`output_path`)

---

## 9. Analysis 그룹 — [`analysis.py`](mcp-servers/bridge/tools/analysis.py) (4 tools)

### 9.1 `explain_code(file_path, line_number)` ⭐⭐⭐

**작동 방식**: AST로 감싸는 함수/클래스/인터페이스 정보 추출 + 라인 유형 분석(import/export/function/class/if/return 등) + 전후 컨텍스트 표시.

**실사용 예시**:
- `explain_code(file_path="src/auth.ts", line_number=42)` → "42번 라인이 무슨 역할을 하는가?"

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | 단일 파일 AST 파싱 |
| 120% 우수 | ✅ | AST로 정확한 함수/클래스 범위(시작~끝 라인) 탐지 — LLM이 중괄호 매칭만으로 찾기 어려운 구조적 컨텍스트 |
| 컨텍스트 절약 | ✅ | 해당 라인 주변 컨텍스트(±3줄) + AST 정보만 반환 |
| LLM DX | ✅ | 파일 경로 + 라인 번호만 입력 |

**부족한 점**:
- TS/JS에서만 AST 컨텍스트 분석. Python/Go는 라인 내용만 표시
- git blame 정보 없음 ("누가, 언제, 왜" 이 라인을 작성했는지)
- 관련 테스트 코드 자동 탐지 없음

**개선 방안**:
- [ ] Python/Go AST 컨텍스트 지원 (tree-sitter 언어팩)
- [ ] git blame 통합 — "2주 전 @user가 'JWT 만료일 검증 추가' 커밋에서 작성"
- [ ] 관련 테스트 파일 자동 탐지 및 링크

### 9.2 `analyze_changes()` ⭐⭐⭐

**작동 방식**: `git diff --stat` + `git diff` 실행. 변경 파일 분류(refactoring/bugfix/feature/docs) + Crow 컨텍스트 조회.

**실사용 예시**:
- `analyze_changes()` → "지금까지 변경한 내용 요약"
- 커밋 메시지 작성 전 점검

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | git 명령어 2회 실행 |
| 120% 우수 | ✅ | 변경 유형 자동 분류(refactoring/bugfix/feature) + Crow 연관 컨텍스트 조회. LLM이 git diff 원시 출력을 수동 분석하는 것보다 우수 |
| 컨텍스트 절약 | ✅ | 8000자 제한. diff가 크면 truncated |
| LLM DX | ✅ | 파라미터 없이 호출 가능 |

**부족한 점**:
- 변경 유형 분류가 파일 확장자 + diff 내 키워드 기반으로 부정확
- Crow 컨텍스트 조회가 파일명 단순 매칭
- diff가 8000자 초과 시 단순 truncate → 중요한 변경 사항이 잘릴 수 있음

**개선 방안**:
- [ ] 파일별 변경 요약을 AI가 생성 (파일명 + 변경 유형 + 변경 규모)
- [ ] `git diff --stat` 우선 요약, 상세 diff는 선택적
- [ ] 변경 파일이 많을 때 우선순위(크기, 중요도) 기반 정렬

### 9.3 `review_pr(base_branch?, head_branch?)` ⭐⭐⭐

**작동 방식**: 두 브랜치 간 `git diff` + 의존성 분석 + 롤백 위험도 평가(🟢🟡🟠🔴) + changed files `review_code` 개별 실행 + Crow 컨텍스트.

**실사용 예시**:
- `review_pr(base_branch="main")` → 현재 브랜치 PR 리뷰
- `review_pr(base_branch="main", head_branch="feature/auth")` → 특정 브랜치 PR 리뷰

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ⚠️ | git diff + changed files 개별 `review_code` 실행. 변경 파일이 많으면 느림 |
| 120% 우수 | ✅ | 의존성 분석(Cross-file dependencies) + 롤백 위험도 평가(위험 요소 나열) + Crow 컨텍스트 통합. LLM 단독 PR 리뷰 대비 객관적 메트릭 제공 |
| 컨텍스트 절약 | ⚠️ | changed files 10개만 리뷰, diff는 4000자 제한. 양호하나 리뷰 결과가 장황해질 수 있음 |
| LLM DX | ✅ | base_branch 기본값 "main". 위험도 시각화(🟢🟡🟠🔴) |

**부족한 점**:
- `git merge-base` 미사용 — 3-way diff가 아닌 2-way diff
- changed files 각각 `review_code` 호출 → 중복 AST 파싱
- PR description/커밋 메시지 분석 없음

**개선 방안**:
- [ ] `git merge-base` 사용한 3-way diff
- [ ] `review_code` 결과를 캐싱하여 중복 방지
- [ ] GitHub/GitLab API 연동 (PR description ↔ diff 일관성 검증)

### 9.4 `refactor_across_files(pattern, new_pattern, file_patterns?)` ⭐

**작동 방식**: `search_codebase`로 패턴 검색 → 변경 제안서 생성 (diff 형식). **실제 파일 수정 안 함**.

**실사용 예시**:
- `refactor_across_files(pattern="console.log", new_pattern="logger.debug", file_patterns="*.ts")` → console.log → logger.debug 일괄 변경 제안

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ⚠️ | `search_codebase` 1회 호출 + diff 생성 |
| 120% 우수 | ❌ | **변경 제안만 하고 실제 파일 수정 안 함**. LLM이 직접 `sed`나 find-and-replace로 수정하는 것이 더 효율적 |
| 컨텍스트 절약 | ⚠️ | 변경 제안이 파일별 diff 형식으로 장황 |
| LLM DX | ❌ | 단순 문자열 치환 — AST 고려 없음. `User`→`AppUser` 변경 시 변수명까지 변경됨 |

**부족한 점**:
- **실제 파일 수정 안 함** — 제안만 생성. LLM이 직접 수정하는 것보다 비효율적
- AST 고려 없는 단순 문자열 치환 → 의도치 않은 변경 위험
- YOLO + yocto 백업 연동 없음

**개선 방안**:
- [ ] AST-aware rename (scope 고려). 예: `User` 타입만 변경, 변수명 유지
- [ ] YOLO + yocto 백업과 연동한 자동 적용 (사용자 승인 후)
- [ ] 변경 전/후 통계 + 롤백 가이드 포함

---

## 10. Knowledge 그룹 — [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py) (4 tools)

### 10.1 `learn_project(target_path?)` ⭐⭐

**작동 방식**: `summarize_architecture` + `extract_patterns` + `map_dependencies` 결과를 Crow Memory arch/style/life_context 레지스터에 저장. 프로젝트별 MD5 해시 키 사용.

**실사용 예시**:
- `learn_project()` → "이 프로젝트를 기억해둬"

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ❌ | 3개重型 도구를 순차 호출 + Crow에 4회 ingest |
| 120% 우수 | ⚠️ | 프로젝트 지식 영속화는 가치 있으나, 저장된 정보가 다음 세션에서 자동 로드되지 않음 |
| 컨텍스트 절약 | ✅ | 각 도구 결과를 1000자로 truncate하여 저장 |
| LLM DX | ⚠️ | `recall_project`를 명시적으로 호출해야 저장된 정보 활용 가능 |

**부족한 점**:
- 저장된 지식이 **자동으로 로드되지 않음** — LLM이 `recall_project`를 명시적 호출 필요
- 저장 정보가 일반적 (파일 수, 확장자 분포). 프로젝트별 핵심 패턴(라이브러리, 컨벤션, 아키텍처 스타일) 부족

**개선 방안**:
- [ ] `recall_project`를 세션 시작 시 system prompt 규칙으로 자동 호출
- [ ] 프로젝트별 핵심 컨텍스트 추출: 사용 라이브러리, 코딩 컨벤션, 디렉토리 구조 패턴

### 10.2 `recall_project(target_path?)` ⭐⭐

**작동 방식**: Crow Memory arch/style/life_context 레지스터에서 `learn_project` 저장 정보 조회.

**실사용 예시**:
- `recall_project()` → "이 프로젝트에 대해 기억나는 정보"

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | Crow 쿼리 3회 |
| 120% 우수 | ⚠️ | Crow 조회를 LLM이 직접 할 수도 있음 (`crow_recall`). 단, 레지스터 선택 자동화는 편의성 |
| 컨텍스트 절약 | ✅ | 결과 300자 truncate |
| LLM DX | ⚠️ | `learn_project` 호출 이력이 없으면 빈 결과 |

**부족한 점**:
- 저장된 정보의 신선도(freshness) 미표시
- 현재 코드 상태와 저장된 정보 차이 검증 없음

**개선 방안**:
- [ ] 정보 생성일/수정일 표시
- [ ] git HEAD 해시 비교로 코드 변경 감지 → "학습 이후 15개 파일 변경됨" 경고

### 10.3 `learn_preference(rule, category?)` ⭐⭐⭐

**작동 방식**: 로컬 JSON(`PREFERENCES_FILE`) + Crow `life_context` 이중 저장.

**실사용 예시**:
- `learn_preference(rule="Prefer functional components", category="coding_style")`
- `learn_preference(rule="Tab width: 2", category="formatting")`

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | JSON 파일 + Crow API 각 1회 |
| 120% 우수 | ✅ | LLM이 사용자 선호도를 자체적으로 영속화할 방법이 없음 (stateless). 이 도구가 유일한 해결책 |
| 컨텍스트 절약 | ✅ | 룰 텍스트만 저장 |
| LLM DX | ✅ | 카테고리 5개(coding_style, naming, formatting, architecture, workflow) 직관적 |

**부족한 점**:
- 이중 저장소 동기화 문제 가능성 (로컬 vs Crow 불일치)
- `get_preferences`를 자동 호출하지 않으면 저장된 선호도가 활용되지 않음

**개선 방안**:
- [ ] `get_preferences` 세션 시작 시 자동 호출 (system prompt 규칙)
- [ ] Crow Memory 우선, 로컬 JSON은 backup

### 10.4 `get_preferences(category?)` ⭐⭐⭐

**작동 방식**: 로컬 JSON + Crow Memory 조회. 시간순 정렬.

**실사용 예시**:
- `get_preferences()` → "내 모든 선호도 보여줘"
- `get_preferences(category="coding_style")` → 특정 카테고리만

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | 로컬 파일 + Crow API 각 1회 |
| 120% 우수 | ✅ | 로컬/Crow 이중 저장소 통합 조회. LLM이 각 저장소를 개별 쿼리할 필요 없음 |
| 컨텍스트 절약 | ⚠️ | 선호도가 많으면 컨텍스트 차지. 중요도 태깅 없음 |
| LLM DX | ✅ | `category` 파라미터로 필터링 가능 |

**부족한 점**:
- Crow Memory와 로컬 JSON 불일치 시 어느 쪽 우선인지 불명확
- 선호도 간 우선순위/충돌 해결 로직 없음

**개선 방안**:
- [ ] Crow Memory 우선 조회, 로컬 JSON 폴백 명시
- [ ] 중요도 태깅 (필수 규칙 vs 희망 사항)

---

## 11. Web 그룹 — [`web.py`](mcp-servers/bridge/tools/web.py) (2 tools)

### 11.1 `fetch_page(url, max_length?)` ⭐⭐⭐

**작동 방식**: 순수 Python 표준 라이브러리 `urllib.request` + 자체 `_html_to_markdown` 변환기. JSON 응답 자동 감지.

**실사용 예시**:
- `fetch_page(url="https://docs.python.org/3/library/re.html")` → 문서 가져오기
- `fetch_page(url="https://api.github.com/repos/zoocode/vibezoo")` → JSON API 응답

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | 외부 의존성 없는 순수 Python. LLM이 `requests` + `BeautifulSoup` 스크립트를 매번 작성하는 것보다 가벼움 |
| 120% 우수 | ✅ | HTML→마크다운 변환 + JSON 자동 감지. LLM이 HTML을 직접 파싱하는 것보다 우수 |
| 컨텍스트 절약 | ✅ | `max_length`로 결과 크기 제한 (기본 50000). HTML 태그 제거로 토큰 절약 |
| LLM DX | ✅ | URL만 입력. http:// 자동 보정 |

**부족한 점**:
- JavaScript 렌더링(SPA) 페이지 내용 추출 불가
- 자체 HTML 파서가 모든 태그/속성 처리 못 함
- User-Agent 차단 가능성

**개선 방안**:
- [ ] SPA 페이지 감지 시 "JavaScript 렌더링 필요" 경고
- [ ] `html2text` 선택적 활용 (설치 시)
- [ ] User-Agent 로테이션

### 11.2 `web_search(query, max_results?, engine?)` ⭐⭐

**작동 방식**: DuckDuckGo HTML 엔드포인트(`html.duckduckgo.com`) 파싱. `engine` 파라미터로 auto/duckduckgo/google/bing 선택 가능 (Google/Bing은 API 키 필요).

**실사용 예시**:
- `web_search(query="Python 3.13 new features")` → 최신 정보 검색
- `web_search(query="TypeScript TS2322 error fix")` → 에러 해결책 검색

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | 단일 HTTP 요청 + HTML 파싱 |
| 120% 우수 | ⚠️ | LLM이 웹 검색을 직접 수행할 수 없으므로 도구 자체는 필수적. 그러나 DuckDuckGo 차단 시 대안 없음 |
| 컨텍스트 절약 | ✅ | 검색 결과 5개로 제한. 제목+URL+요약만 반환 |
| LLM DX | ⚠️ | `engine` 파라미터가 있으나 Google/Bing은 API 키 필요 → LLM이 설정 방법을 모르면 사용 불가 |

**부족한 점**:
- **DuckDuckGo 차단/변경 시 검색 불가** — 이미 간헐적 차단 발생
- Google/Bing은 API 키 필요. 환경변수(`VIBEZOO_GOOGLE_API_KEY`, `VIBEZOO_BING_API_KEY`) 설정 안내 부족
- 검색 결과 5개 제한 — 많은 정보가 필요할 때 부족

**개선 방안**:
- [ ] DuckDuckGo 차단 감지 → 자동으로 대체 엔진 시도 (Bing 무료 티어, SearXNG 공개 인스턴스)
- [ ] `vibezoo_setup`에 API 키 설정 가이드 포함
- [ ] 검색 결과 10개까지 확장 + LLM 요약 옵션
- [ ] `fetch_page` 연계: 검색 결과 URL을 자동으로 fetch하여 상세 내용 제공

---

## 12. SSA 그룹 — [`ssa.py`](mcp-servers/bridge/tools/ssa.py) (2 tools)

### 12.1 `aggregate_spatial_pixels(image_path, detail?, ocr?, ocr_lang?)` ⭐⭐⭐

**작동 방식**: OpenCV 기반 8가지 분석 — 8×8 그리드(Spatial Grid), GrabCut 객체 분할, k-means 색상, Median Cut, LBP 텍스처, Saliency, Histogram 비교, 엣지 검출(full). 한글 경로 지원(`_imread_korean_safe`). `OcrEngine` 통합(OCR 텍스트 추출). 자연어 요약(`_summarize_ssa_results`).

**실사용 예시**:
- `aggregate_spatial_pixels(image_path="screenshot.png")` → 공간 분석 + OCR 텍스트
- `aggregate_spatial_pixels(image_path="diagram.png", detail="full")` → 전체 분석

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | OpenCV 네이티브 연산. LLM이 PIL/numpy로 동일 분석을 구현하는 것보다 훨씬 가벼움 |
| 120% 우수 | ✅ | **VibeZoo 최고 가치 도구 중 하나**. GrabCut 객체 분할 + LBP 텍스처 + Saliency + OCR 텍스트 추출 — LLM이 Python으로 직접 구현하기 매우 어려운 컴퓨터 비전 파이프라인. OCR 통합으로 이미지 내 텍스트까지 추출 |
| 컨텍스트 절약 | ✅ | 8×8 그리드 + 자연어 요약 + OCR 텍스트(<details> 접기). 이미지 자체는 base64로 전달하지 않고 분석 결과만 반환 |
| LLM DX | ✅ | `detail="auto"`로 파일 크기/해상도 기반 자동 판단. `ocr=True`로 텍스트 추출 자동화 |

**부족한 점**:
- OCR이 Tesseract/PaddleOCR 설치 시에만 동작 — 미설치 시 조용히 스킵
- 분석 결과가 여전히 기술적 (`Red(S)`, `LBP Uniformity: 72%`) — 비전문가 LLM이 해석하기 어려울 수 있음
- SSIM 분석은 단일 이미지에 대해 self-SSIM(블러 비교)만 수행 → 실질적 가치 낮음

**개선 방안**:
- [ ] OCR 미설치 시 `vibezoo_setup` 안내
- [ ] 분석 결과를 자연어로 더 풍부하게 변환 ("이 이미지는 상단에 파란색 헤더, 중앙에 큰 흰색 객체가 있는 UI 스크린샷입니다")
- [ ] UI 요소 감지(버튼, 입력창, 리스트) 템플릿 매칭 추가
- [ ] 두 이미지 비교 모드 (before/after 스크린샷)

### 12.2 `open_image_dropzone()` 💀 (폐기 권장)

**작동 방식**: 내부적으로 `capture_screen(source="dropzone")` 호출. VS Code Webview 내장 드롭존.

**실사용 예시**: 거의 사용 안 함. `capture_screen(source="dropzone")`이 대체.

**LLM 관점 평가**:

| 축 | 평가 | 근거 |
|:---|:---:|:---|
| 가벼움 | ✅ | 단순 위임 |
| 120% 우수 | ❌ | `capture_screen(source="dropzone")`과 100% 중복. 단독 가치 없음 |
| 컨텍스트 절약 | n/a | |
| LLM DX | ❌ | Deprecated 마킹이 docstring에만 있고 도구명에 표시 안 됨 |

**부족한 점**:
- `capture_screen(source="dropzone")`과 완전 중복
- 업로드 경로가 `~/.vibezoo-cache/dropped_image.png` 1개로 고정

**개선 방안**:
- [ ] **폐기**. MCP 도구 목록에서 제거하고 `capture_screen(source="dropzone")`으로 완전 통합
- [ ] 다중 이미지 업로드 지원 (통합 시)

---

## 13. 특별 중점 평가

### 13.1 `search_codebase` — 검색 속도 최적화

| 상황 | 속도 | LLM 직접 구현 대비 |
|:---|:---|:---|
| ripgrep 설치됨 | ⚡ 매우 빠름 (수백 ms) | 100배↑ |
| git grep fallback | 🟡 보통 (1~3초) | 10배↑ |
| os.walk fallback | 🐢 느림 (10초↑) | 1배 (동일) |

**핵심 문제**: ripgrep 미설치 시 `os.walk` 폴백은 LLM이 `grep -r` 실행하는 것과 동일 속도. 이 경우 도구 사용의 가벼움 이점이 사라짐.

**제안**: `search_codebase` 첫 호출 시 ripgrep/git grep 상태를 진단하고, 둘 다 없으면 `vibezoo_setup`으로 ripgrep 설치를 권장하는 메시지를 결과에 포함.

### 13.2 `summarize_architecture` / `review_project` — 결과물 과잉

두 도구 모두 **LLM 컨텍스트 절약** 철학에 정면으로 위배됨:
- `summarize_architecture`: Layer Structure가 모든 파일을 나열 (프로젝트 크기에 비례)
- `review_project`: 4개 하위 도구의 전체 출력을 구분자로 연결

**제안**: 
1. `mode="summary"` 추가 — 핵심 발견 사항만 Executive Summary로 반환 (전체 결과의 10% 이내)
2. `max_tokens` 파라미터 — LLM 컨텍스트 윈도우 크기에 맞춘 출력 제한
3. 상세 결과는 `<details>` HTML 태그로 접을 수 있게 제공 (LLM이 필요 시 열람)

### 13.3 `generate_tests` — LLM 직접 작성 대비 열등

**현재 상태**: 테스트 템플릿만 생성. `test_() { /* TODO: write test */ }` 수준.

**근본적 재설계 제안**:
- **도구 역할**: 함수 시그니처 + 타입 + docstring + 의존성 그래프를 **수집**하는 데이터 수집기
- **LLM 역할**: 수집된 데이터를 기반으로 실제 의미 있는 테스트 로직을 **생성**
- 즉, `generate_tests`는 더 이상 "테스트 생성기"가 아니라 "테스트 작성을 위한 컨텍스트 수집기"로 재정의

### 13.4 `aggregate_spatial_pixels` — OCR 통합으로 이미지 분석 완전도

**v0.14.0 개선 사항**: `OcrEngine` 통합으로 이미지 내 텍스트를 추출하여 SSA 분석 결과에 포함. OCR 결과는 접을 수 있는 `<details>` 태그로 제공.

**잔여 과제**: 
- OCR + SSA 결과를 결합한 종합적 이미지 이해 ("이 이미지는 로그인 폼 UI로, 상단에 'Welcome' 텍스트, 중앙에 입력 필드 2개, 하단에 파란색 버튼이 있습니다")
- OCR 미설치 환경 자동 감지 및 설치 안내

### 13.5 `web_search` — DuckDuckGo 차단 시 대안

**현재**: DuckDuckGo HTML 엔드포인트만 사용. 차단 시 빈 결과.

**제안하는 대안 체인**:
1. DuckDuckGo HTML (현재) 
2. DuckDuckGo Instant Answer API (`api.duckduckgo.com`) — JSON, 덜 차단됨
3. SearXNG 공개 인스턴스 (`searx.be`, `search.sapti.me` 등) — 무료, 비차단
4. Google/Bing API (API 키 필요) — 최후 수단

### 13.6 `vibezoo_setup` — 설치 후 사용자 경험

**현재**: 설치 완료 후 마크다운 보고서 반환. MCP 설정 파일 생성.

**UX 개선 제안**:
- 설치 완료 후 "다음 단계" 가이드 제공: "이제 `summarize_architecture()`로 프로젝트를 분석하거나 `learn_project()`로 프로젝트를 학습시키세요"
- 설치 실패 패키지에 대한 구체적 해결 방법 제시 (OS별)
- `dry_run` 결과를 기반으로 한 "권장 설치 커맨드" 제안

---

## 14. 전체 도구 LLM 관점 평가 매트릭스

| # | 도구 | 가벼움 | 120%↑ | 컨텍스트↓ | LLM DX | 종합 |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| 1 | `vibezoo_setup` | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| 2 | `search_codebase` | ✅ | ✅ | ✅ | ⚠️ | ⭐⭐⭐ |
| 3 | `find_references` | ⚠️ | ✅ | ✅ | ✅ | ⭐⭐ |
| 4 | `summarize_architecture` | ❌ | ⚠️ | ❌ | ⚠️ | ⭐⭐ |
| 5 | `review_code` | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| 6 | `check_quality` | ❌ | ⚠️ | ⚠️ | ⚠️ | ⭐ |
| 7 | `analyze_call_graph` | ⚠️ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| 8 | `map_dependencies` | ⚠️ | ✅ | ⚠️ | ✅ | ⭐⭐⭐ |
| 9 | `extract_patterns` | ✅ | ✅ | ✅ | ✅ | ⭐⭐ |
| 10 | `reverse_engineer` | ⚠️ | ✅ | ✅ | ✅ | ⭐⭐ |
| 11 | `generate_tests` | ✅ | ❌ | ✅ | ⚠️ | ⭐ |
| 12 | `analyze_coverage` | ✅ | ⚠️ | ✅ | ✅ | ⭐⭐ |
| 13 | `draw_on_whiteboard` | ✅ | ⚠️ | n/a | ❌ | ⭐⭐ |
| 14 | `get_whiteboard_state` | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| 15 | `open_whiteboard` | ✅ | ❌ | n/a | ❌ | ⭐ |
| 16 | `capture_screen` | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| 17 | `open_ui_preview` | ✅ | ✅ | n/a | ⚠️ | ⭐⭐ |
| 18 | `auto_fix_status` | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| 19 | `retry_build` | ✅ | ⚠️ | ❌ | ⚠️ | ⭐⭐ |
| 20 | `check_intervention` | ✅ | ⚠️ | ✅ | ⚠️ | ⭐⭐ |
| 21 | `review_project` | ❌ | ⚠️ | ❌ | ⚠️ | ⭐⭐ |
| 22 | `find_bugs` | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⭐⭐ |
| 23 | `suggest_refactor` | ❌ | ⚠️ | ❌ | ⚠️ | ⭐⭐ |
| 24 | `generate_docs` | ❌ | ✅ | ❌ | ⚠️ | ⭐⭐ |
| 25 | `explain_code` | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| 26 | `analyze_changes` | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| 27 | `review_pr` | ⚠️ | ✅ | ⚠️ | ✅ | ⭐⭐⭐ |
| 28 | `refactor_across_files` | ⚠️ | ❌ | ⚠️ | ❌ | ⭐ |
| 29 | `learn_project` | ❌ | ⚠️ | ✅ | ⚠️ | ⭐⭐ |
| 30 | `recall_project` | ✅ | ⚠️ | ✅ | ⚠️ | ⭐⭐ |
| 31 | `learn_preference` | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| 32 | `get_preferences` | ✅ | ✅ | ⚠️ | ✅ | ⭐⭐⭐ |
| 33 | `fetch_page` | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| 34 | `web_search` | ✅ | ⚠️ | ✅ | ⚠️ | ⭐⭐ |
| 35 | `aggregate_spatial_pixels` | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| — | `open_image_dropzone` | — | — | — | — | 💀 |

---

## 15. 종합 개선 제안 (Top 5)

| 순위 | 제안 | 영향 | 현재 상태 |
|:---:|:---|:---:|:---|
| 1 | **LLM-도구 체인 재정립**: `generate_tests`, `explain_code`, `suggest_refactor`는 도구가 데이터 수집 → LLM이 의미 분석 생성. 현재는 도구가 분석까지 시도하여 품질 저하 | ★★★★★ | ❌ 미적용 |
| 2 | **컨텍스트 최적화**: `summarize_architecture`, `review_project`, `generate_docs`에 `mode="summary"` 및 `max_tokens` 파라미터 추가. 상세 결과는 `<details>` 태그로 접기 | ★★★★★ | ❌ 미적용 |
| 3 | **AST 멀티랭귀지**: `AstEngine`에 Python/Go/Rust tree-sitter 언어팩 실제 로딩 구현. 현재 TS/JS만 AST 분석, 나머지는 regex 폴백 | ★★★★ | 🔶 구조만 |
| 4 | **Web Search 대안 체인**: DuckDuckGo → SearXNG → Google/Bing API 순차 fallback. 차단 시 자동 전환 | ★★★ | ❌ 미적용 |
| 5 | **통합 도구 중복 제거**: `review_project`/`find_bugs`/`suggest_refactor`에서 `FileCache` 공유로 중복 파일 스캔 방지 | ★★★ | ❌ 미적용 |

---

## 16. 결론

### v0.14.0 SOTA — 달성한 것

1. **12개 모듈, 35개 도구** — 단일 파일(4,627줄)에서 완전한 모듈화 달성
2. **8개 ⭐⭐⭐ 도구** — `vibezoo_setup`, `search_codebase`, `review_code`, `analyze_call_graph`, `map_dependencies`, `get_whiteboard_state`, `capture_screen`, `aggregate_spatial_pixels`, `explain_code`, `analyze_changes`, `review_pr`, `learn_preference`, `get_preferences`, `fetch_page`, `auto_fix_status` 등이 LLM 단독 작업 대비 명확한 우위
3. **OCR 통합** — `aggregate_spatial_pixels`가 Tesseract/PaddleOCR 연동으로 이미지 내 텍스트 추출
4. **Cyclomatic Complexity** — `review_code`가 AST 기반 복잡도 + 중첩 깊이 + 함수 길이 + 파라미터 개수 검사
5. **영향도 분석** — `map_dependencies`가 파일별 영향도 등급(LOW~CRITICAL) 제공
6. **Dead Code Detection** — `analyze_call_graph`가 호출자 없는 함수 자동 탐지
7. **설치 자동화** — `vibezoo_setup`이 OS별 패키지 매니저 fallback + MCP/Zoo 설정

### 여전히 남은 도전 과제

1. **LLM-도구 체인 부재** — 가장 큰 갭. `generate_tests`가 대표적: 도구가 템플릿만 생성하고 LLM이 실제 로직을 작성하지 않음
2. **컨텍스트 과잉** — `summarize_architecture`, `review_project` 등 통합 도구들이 LLM 컨텍스트 윈도우를 쉽게 초과
3. **AST 멀티랭귀지** — 구조는 갖췄으나 Python/Go/Rust tree-sitter 언어팩 로딩 미완성
4. **Web Search 취약성** — DuckDuckGo 단일 엔진 의존. 차단 시 대안 없음
5. **실제 파일 수정** — `refactor_across_files`가 제안만 하고 실행하지 않음

> **핵심 메시지**: "v0.14.0은 **SOTA 인프라**를 완성했다. SearchEngine(ripgrep), AstEngine(tree-sitter), OcrEngine(Tesseract/PaddleOCR), FileCache(3계층) 등 핵심 인프라가 갖춰졌다. 다음 버전은 **LLM-도구 협업 패러다임**으로 전환해야 한다 — 도구는 데이터를 수집하고, LLM은 의미를 분석하며, 도구는 LLM의 결정을 실행하는 순환 고리를 완성하는 것이 VibeZoo의 다음 단계."
