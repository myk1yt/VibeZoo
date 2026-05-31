# VibeZoo MCP Bridge — 도구 설명서 (v0.17.0)

> **작성일**: 2026-05-31
> **대상**: [`mcp-servers/bridge/tools/`](mcp-servers/bridge/tools/) — 12개 모듈, 31개 MCP 도구
> **버전**: v0.17.0 (Cycle 3 완결)
> **목적**: LLM이 VibeZoo MCP 도구를 효과적으로 활용하기 위한 사용 설명서

---

## 섹션 1: 개요

### VibeZoo 철학

VibeZoo는 LLM의 **인지적 상위 계층(cognitive superlayer)** 으로 기능하는 MCP 도구 모음입니다. 도구가 수집한 데이터가 LLM의 추론을 대체하는 것이 아니라, LLM이 더 높은 수준의 판단에 집중할 수 있도록 **인지 부하를 흡수**합니다.

**4대 설계 원칙:**

| # | 원칙 | 의미 |
|:---:|:---|:---|
| 1 | **가볍고 빨라야 함** | LLM이 동일 기능을 Python으로 직접 짜는 것보다 실행 시간·코드량·의존성 측면에서 우위 |
| 2 | **120% 이상 결과물 우수** | 도구 출력이 LLM 단독 출력보다 정확성·완결성·구조화 측면에서 1.2배 이상 |
| 3 | **LLM 컨텍스트 절약** | 원시 데이터를 전처리/요약/필터링하여 LLM에 전달되는 토큰 수 최소화 |
| 4 | **LLM DX** | 파라미터 직관성, 에러 메시지 명확성, 반환 형식 일관성 |

### 설치 방법

**MCP Bridge는 자동 실행됩니다.** (`vibezoo_setup()`으로 설치한 후 VS Code 재시작 시 자동 시작)

```python
# 최초 설치 (권장)
vibezoo_setup(target="recommended", dry_run=False)

# 설치 전 미리보기
vibezoo_setup(target="recommended", dry_run=True)
```

**파라미터:**
- `target`: `"minimal"` (핵심만) | `"recommended"` (권장, tree-sitter 언어팩 포함) | `"full"` (전체)
- `python_packages`: 설치할 추가 pip 패키지 (예: `"opencv-contrib-python-headless"`)
- `system_tools`: 시스템 도구 설치 여부 (기본 `False`)
- `configure_mcp`: `.roo/mcp.json` 자동 생성 (기본 `True`)
- `dry_run`: `True` 시 설치 없이 진단만 수행

**LLM 힌트**: VibeZoo를 처음 사용할 때 가장 먼저 호출하세요. `dry_run=True`로 설치 전 진단을 먼저 확인하는 것이 안전합니다.

---

## 섹션 2: Setup 그룹 — [`setup.py`](mcp-servers/bridge/tools/setup.py) (1 tool)

### `vibezoo_setup(target, python_packages, system_tools, configure_mcp, configure_zoo, dry_run)`

**역할**: VibeZoo MCP Bridge를 설치·설정합니다. pip 패키지 설치, 시스템 도구 설치, MCP 설정 파일 생성까지 원스톱으로 처리합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target` | `str` | `"minimal"` | 설치 범위 (`"minimal"`/`"recommended"`/`"full"`) |
| `python_packages` | `str` | `""` | 추가 pip 패키지 (공백 구분) |
| `system_tools` | `bool` | `False` | 시스템 도구(ripgrep 등) 설치 여부 |
| `configure_mcp` | `bool` | `True` | `.roo/mcp.json` 생성 여부 |
| `configure_zoo` | `bool` | `True` | `.zoo/config.json` 생성 여부 |
| `dry_run` | `bool` | `False` | `True` 시 실제 설치 없이 진단만 수행 |

**사용 예시:**
```
vibezoo_setup(target="recommended", dry_run=False)
→ pip install fastmcp tree-sitter tree-sitter-python ...
→ winget install BurntSushi.ripgrep.MSVC
→ .roo/mcp.json 자동 생성 (SSE transport, port 9027)
→ 설치 결과 마크다운 보고서 반환
```

**LLM 힌트**: 
- 새 환경에서 VibeZoo를 처음 사용할 때 호출하세요.
- `dry_run=True`로 먼저 체크하고, 문제가 없으면 `dry_run=False`로 설치하세요.
- 패키지 매니저는 OS별로 자동 fallback합니다 (winget→choco→scoop→apt→brew).

---

## 섹션 3: Scout 그룹 — [`scout.py`](mcp-servers/bridge/tools/scout.py) (3 tools)

### `search_codebase(query, file_patterns?, max_results?, mode?, context_lines?)`

**역할**: 프로젝트 코드베이스에서 쿼리와 관련된 코드를 검색합니다. tree-sitter AST 파싱을 우선 시도하고, 실패 시 regex로 폴백합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `query` | `str` | **필수** | 검색할 내용 (자연어 또는 코드 스니펫) |
| `file_patterns` | `str` | `None` | 검색 대상 파일 패턴 (예: `"*.ts,*.tsx"`) |
| `max_results` | `int` | `10` | 최대 결과 수 |
| `mode` | `str` | `"auto"` | 검색 모드 (`"ast"`/`"exact"`/`"semantic"`/`"auto"`) |
| `context_lines` | `int` | `3` | 결과 주변 컨텍스트 라인 수 |

**사용 예시:**
```
search_codebase(query="login", file_patterns="*.py,*.go", mode="ast")
→ AST 기반: Python `def login()`, Go `func Login()` 정확히 검출
→ ripgrep fallback: 전체 텍스트 매칭
→ 결과: 함수 정의 위치 + 파일 경로 + 컨텍스트 라인
```

**LLM 힌트**:
- 특정 함수/변수/클래스의 정의 위치를 찾을 때 사용하세요.
- `mode="ast"`로 설정하면 AST 기반 정확한 심볼 검색이 가능합니다 (Python/Go/Rust/TS/JS 지원).
- `file_patterns`로 언어/디렉토리를 필터링하면 검색 속도가 빨라집니다.
- `max_results=500`까지 확장 가능하나, 컨텍스트 절약을 위해 기본 10개로 충분합니다.

---

### `find_references(symbol)`

**역할**: 주어진 심볼(함수, 클래스, 변수)의 모든 참조를 찾습니다. 정의와 사용 위치를 구분하여 반환합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `symbol` | `str` | **필수** | 찾을 심볼 이름 |

**사용 예시:**
```
find_references(symbol="authenticate")
→ TS/JS: AST로 `authenticate()` 호출·할당·import 위치 모두 탐지
→ Python: `authenticate()` 호출 + `from auth import authenticate` 참조
→ Go: `authenticate()` 호출 + `import (... auth.Authenticate)` 참조
→ 결과: By Reference Type / By File / Call Chain 3단계 구조화
```

**LLM 힌트**:
- 리팩토링 전에 영향도 분석이 필요할 때 사용하세요.
- 함수 이름만 입력하면 모든 참조 위치를 반환합니다.
- Python/Go/Rust/TS/JS에서 AST 기반 정밀 참조 분석이 가능합니다.
- Call Chain 정보로 호출 그래프를 파악할 수 있습니다.

---

### `summarize_architecture(target_path?, streaming?, mode?, max_tokens?)`

**역할**: 프로젝트 아키텍처를 분석하여 요약합니다. 내부적으로 `map_dependencies` + `analyze_call_graph`를 호출하여 실제 모듈 의존성, 진입점, 레이어 구조를 분석합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | `None` | 분석 대상 디렉토리 경로 |
| `streaming` | `bool` | `False` | 스트리밍 출력 여부 |
| `mode` | `str` | `"summary"` | `"summary"` (요약) / `"full"` (전체) |
| `max_tokens` | `int` | `1000` | 최대 출력 토큰 수 |

**사용 예시:**
```
summarize_architecture(mode="summary")
→ 프로젝트 진입점: src/main.py, src/app.ts
→ 기술 스택: Python + FastAPI + TypeScript + React
→ 총 파일: 124개, 함수: 342개
→ 순환 의존성: 없음 ✅
→ 레이어: presentation → application → domain → infrastructure
```

**LLM 힌트**:
- 새 프로젝트에 온보딩할 때 가장 먼저 호출하세요.
- `mode="summary"`(기본값)로 핵심 정보만 빠르게 파악하세요.
- `mode="full"`로 더 자세한 의존성 그래프를 확인할 수 있습니다.
- 500자 내외로 프로젝트 전반을 이해할 수 있습니다.

---

## 섹션 4: Reviewer 그룹 — [`reviewer.py`](mcp-servers/bridge/tools/reviewer.py) (1 tool)

### `review_code(file_path, severity?)`

**역할**: 지정된 파일의 코드 리뷰를 수행합니다. tree-sitter AST로 함수/클래스 구조와 실제 코드 품질 이슈를 탐지합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `file_path` | `str` | **필수** | 리뷰할 파일 경로 |
| `severity` | `str` | `"all"` | 심각도 필터 (`"all"`/`"error"`/`"warning"`/`"info"`) |

**사용 예시:**
```
review_code(file_path="src/auth.ts")
→ 구조: 함수 5개, 클래스 2개, 인터페이스 3개, 최대 중첩 깊이 3
→ 이슈:
  - ⚠️ `any` type used 3 time(s) — consider using specific types
  - 📏 Long function `validateUser()`: 72 lines (line 42) — consider splitting
  - 📝 TODO/FIXME/HACK: 2 marker(s)
→ 총 5개 이슈 발견
```

**LLM 힌트**:
- 특정 파일의 코드 품질을 검토할 때 사용하세요.
- `severity="error"`로 심각한 이슈만 필터링할 수 있습니다.
- Cyclomatic complexity, 중첩 깊이, 함수 길이 등 **정량적 지표**를 제공합니다.
- Python/Go/Rust/TS/JS/기타 언어를 지원합니다.

> **참고**: 프로젝트 전체 품질 검사는 `review_project(mode="quality")`를 사용하세요.
> `check_quality`는 내부 함수로 전환되어 MCP 도구 목록에서 제거되었습니다.

---

## 섹션 5: DeepAnalyzer 그룹 — [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py) (4 tools)

### `analyze_call_graph(file_path?, depth?, include_external?)`

**역할**: 프로젝트의 함수 호출 그래프를 분석합니다. tree-sitter AST로 실제 `call_expression` 노드를 추출하여 정확한 호출 관계를 파악합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `file_path` | `str` | `None` | 분석할 파일 경로 (기본: 전체 프로젝트) |
| `depth` | `int` | `3` | 호출 깊이 |
| `include_external` | `bool` | `False` | 외부 라이브러리 호출 포함 여부 |

**사용 예시:**
```
analyze_call_graph(file_path="src/auth.py", depth=3)
→ Python AST: `def login()` → 호출 감지: `validate_email()`, `hash_password()`, `create_token()`
→ Fan-in: 5 (5곳에서 login 호출) / Fan-out: 3 (login이 3개 함수 호출)
→ Dead Code: `debug_login()` — Fan-in 0, export되지 않음
→ Mermaid 호출 그래프 생성
```

**LLM 힌트**:
- 함수의 영향도/의존성을 파악할 때 사용하세요.
- Dead Code Detection으로 사용되지 않는 함수를 찾을 수 있습니다.
- `depth`를 늘리면 더 깊은 호출 관계까지 추적합니다.
- Python/Go/TS/JS를 지원합니다.

---

### `map_dependencies(target_path?)`

**역할**: 프로젝트 파일 간 의존성을 분석하고 순환 참조를 탐지합니다. tree-sitter AST로 import/require 문을 정확히 분석합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | `None` | 분석 대상 경로 |

**사용 예시:**
```
map_dependencies()
→ 모듈 의존성 맵 (총 45개 파일)
→ 순환 의존성 발견: auth/utils.py ↔ auth/validators.py
→ Import Count by File:
  - auth/handlers.py: 12 imports
  - utils/helpers.py: 8 imports
→ 패키지 매니저: npm (package.json)
```

**LLM 힌트**:
- 리팩토링 전에 의존성 구조를 파악할 때 사용하세요.
- 순환 의존성은 `suggest_refactor`에서 더 자세히 분석할 수 있습니다.
- 패키지 매니저 정보를 자동 감지합니다.

---

### `extract_patterns(target_path?, min_occurrences?)`

**역할**: 프로젝트 전체에서 반복되는 코드 패턴을 AST 기반으로 추출합니다. tree-sitter AST로 실제 코드 구조를 분석하여 정확한 패턴 빈도를 계산합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | `None` | 분석 대상 경로 |
| `min_occurrences` | `int` | `3` | 최소 발생 횟수 |

**사용 예시:**
```
extract_patterns(target_path="src/", min_occurrences=3)
→ 5 patterns found (≥3 occurrences):
  - 🔴 ANTIPATTERN try-catch (empty): 12 occurrences
  - 📝 callback-hell: 5 occurrences
  - 📝 god-class: 3 occurrences
  - 🟢 promise-chain: 8 occurrences
  - 🟢 factory-function: 4 occurrences
```

**LLM 힌트**:
- 프로젝트 전체의 코드 패턴과 안티패턴을 파악할 때 사용하세요.
- `min_occurrences`를 조정하여 더 희소한 패턴까지 탐지할 수 있습니다.
- 10개의 패턴 템플릿(try-catch, callback-hell, god-class 등)을 지원합니다.

---

### `reverse_engineer(target_path?, output_format?)`

**역할**: 코드베이스로부터 아키텍처 문서, API 명세, ERD를 자동 생성합니다. tree-sitter AST로 데이터 모델의 실제 필드까지 추출합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | `None` | 분석 대상 경로 |
| `output_format` | `str` | `"markdown"` | 출력 형식 (`"markdown"`/`"openapi"`/`"mermaid"`) |

**사용 예시:**
```
reverse_engineer(output_format="openapi")
→ API 라우트 자동 추출 (Express/FastAPI/Flask/Gin)
→ OpenAPI 3.0 YAML 생성
→ 데이터 모델 ERD (Mermaid)
→ 아키텍처 문서
```

**LLM 힌트**:
- 기존 코드베이스의 API 문서가 필요할 때 사용하세요.
- `output_format="openapi"`로 OpenAPI 3.0 스펙을 생성할 수 있습니다.
- `output_format="mermaid"`로 ERD 다이어그램을 생성할 수 있습니다.

---

## 섹션 6: Tester 그룹 — [`tester.py`](mcp-servers/bridge/tools/tester.py) (2 tools)

### `generate_tests(source_path, framework?)`

**역할**: 지정된 소스 파일에 대한 단위 테스트를 생성합니다. tree-sitter AST로 함수 시그니처를 더 정확히 감지합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `source_path` | `str` | **필수** | 테스트 대상 소스 파일 경로 |
| `framework` | `str` | `None` | 테스트 프레임워크 (`"jest"`/`"vitest"`/`"pytest"`/`"go test"`). 생략 시 자동 감지 |

**사용 예시:**
```
generate_tests(source_path="src/auth.py", framework="pytest")
→ AST: `def login(email, password)` + `def validate_email(email)` → dependencies
→ Mock 제안: `unittest.mock.patch('auth.validate_email')` 구체적 템플릿
→ 테스트 케이스: 정상 로그인, 빈 이메일, None 비밀번호, DB 연결 실패 등
```

**LLM 힌트**:
- 함수 단위 테스트를 자동 생성할 때 사용하세요.
- `dependencies` 그래프로 함수의 실제 의존성을 파악할 수 있습니다.
- `mock_suggestions`로 언어별 모킹 템플릿을 제공합니다.
- 프레임워크는 자동 감지되나 명시적으로 지정할 수도 있습니다.

---

### `analyze_coverage(target_path?)`

**역할**: 테스트 커버리지를 분석합니다. 빠른 경로(테스트 파일 존재 여부, 테스트/소스 비율 자체 분석) + vitest/pytest 외부 도구 실행 시도.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | `None` | 분석 대상 경로 |

**사용 예시:**
```
analyze_coverage()
→ 빠른 경로: Test/Source ratio = 28/45 (62.2%)
→ 누락된 테스트 (Top 10):
  - src/utils/parser.py (0 test files)
  - src/auth/handler.py (0 test files)
→ 전체 경로: pytest --cov 실행 → 72.3% line coverage
```

**LLM 힌트**:
- 테스트 커버리지를 빠르게 확인할 때 사용하세요.
- 빠른 경로(파일 존재 기반)로 즉시 결과를 얻을 수 있습니다.
- 전체 경로는 실제 테스트 도구를 실행하여 정확한 커버리지를 측정합니다.

---

## 섹션 7: Whiteboard 그룹 — [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) (3 tools)

### `draw_on_whiteboard(commands)`

**역할**: AI가 화이트보드에 그림을 그립니다. VibeZoo가 이 명령을 받아 Webview에 렌더링합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `commands` | `str` | **필수** | JSON 배열 형태의 Fabric.js 드로잉 명령. 각 명령: `{"type":"rect|circle|line|text|arrow|freehand|clear", "props":{...}}` |

**사용 예시:**
```
draw_on_whiteboard('[{"type":"rect","props":{"left":100,"top":50,"width":200,"height":100,"fill":"#4ec9ff"}},{"type":"text","props":{"left":150,"top":80,"text":"Hello World"}}]')
→ 2개 도형을 화이트보드에 그림
```

**LLM 힌트**:
- 아키텍처 다이어그램, 플로우차트 등 시각적 설명이 필요할 때 사용하세요.
- Fabric.js JSON 형식의 명령을 문자열로 전달해야 합니다.
- 각 도형은 `type`(종류)과 `props`(속성)로 구성됩니다.
- 복잡한 다이어그램은 `generate_docs()`를 통해 자동 생성할 수 있습니다.

---

### `get_whiteboard_state()`

**역할**: 현재 화이트보드의 상태를 조회합니다. 사용자가 수정한 내용을 확인합니다.

**파라미터:** 없음

**사용 예시:**
```
get_whiteboard_state()
→ 화이트보드 내용 분석:
  - Objects: 5 (3 rectangles, 2 text)
  - Relationships: Service ──depends on──▶ Database
  - Mermaid 다이어그램 자동 생성
```

**LLM 힌트**:
- `draw_on_whiteboard()` 후 사용자가 수정한 내용을 확인할 때 사용하세요.
- 화이트보드의 Fabric.js 데이터를 LLM이 이해할 수 있는 텍스트로 변환합니다.
- Mermaid 다이어그램, 객체 테이블, 관계 목록을 제공합니다.
- 파라미터 없이 호출 가능합니다.

---

### `capture_screen(source?)`

**역할**: 화면을 캡처하여 화이트보드에 자동으로 붙여넣습니다. AI가 시각적 분석이 필요할 때 호출합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `source` | `str` | `"screen"` | `"screen"` (화면 캡처) / `"dropzone"` (드롭존 열기) / `"file"` (파일 선택) |

**사용 예시:**
```
# 화면 캡처
capture_screen()
→ Screen captured (1920x1080). Image saved to whiteboard.

# 드롭존 열기 (이미지 업로드)
capture_screen(source="dropzone")
→ Drop zone opened in VS Code Webview.

# 파일 선택
capture_screen(source="file")
→ File picker opened in VS Code Webview.
```

**LLM 힌트**:
- 시각적 정보가 필요할 때 화면을 캡처하세요.
- `source="dropzone"`으로 이미지를 업로드할 수 있습니다.
- 캡처 후 `aggregate_spatial_pixels()`로 이미지를 분석할 수 있습니다.
- 캡처된 이미지는 자동으로 화이트보드에 저장됩니다.

> **참고**: `open_whiteboard`와 `open_ui_preview`는 MCP 도구 목록에서 제거되었습니다.
> 화이트보드는 `draw_on_whiteboard()` 호출 시 Extension이 자동으로 엽니다.
> UI 프리뷰는 생성된 UI 코드를 직접 제공하여 사용할 수 있습니다.

---

## 섹션 8: Fix Loop 그룹 — [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py) (3 tools)

### `auto_fix_status()`

**역할**: 현재 진행 중인 Auto-Fix 세션의 상태와 에러 정보를 조회합니다. LLM이 빌드 에러를 분석하고 수정을 시작할 때 호출합니다. 과거 유사 에러 패턴을 Crow Memory에서 조회하여 함께 반환합니다.

**파라미터:** 없음

**사용 예시:**
```
auto_fix_status()
→ Status: in_progress (attempt 2/3)
→ 에러: TS2322 (src/auth.ts:42) — Type 'string' is not assignable to type 'number'
→ 과거 유사 에러 (Crow Memory):
  - TS2322 → 타입 불일치 (3회 발생) → 주로 `any` 사용으로 해결
```

**LLM 힌트**:
- 빌드 에러 발생 후 Fix Loop의 현재 상태를 확인할 때 사용하세요.
- 과거 유사 에러 패턴을 Crow Memory에서 자동 조회합니다.
- 파라미터 없이 호출 가능합니다.

---

### `retry_build(build_command?)`

**역할**: 빌드를 재실행하고 결과를 반환합니다. LLM이 수정 코드를 적용한 후 빌드 성공 여부를 확인할 때 호출합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `build_command` | `str` | `None` | 빌드 명령어 (생략 시 프로젝트 타입별 자동 감지) |

**사용 예시:**
```
retry_build()
→ [build] npm run build 실행
→ _extract_build_errors()가 stdout에서 TS2322, TS2532 등 에러 추출
→ {"errors": [{"file":"auth.ts","line":42,"code":"TS2322","message":"..."}], "error_count":3, "warning_count":1}
```

**LLM 힌트**:
- 코드 수정 후 빌드가 성공했는지 확인할 때 사용하세요.
- 빌드 명령어는 프로젝트 타입별로 자동 감지됩니다 (npm/pip/go/rust).
- 에러 메시지가 구조화된 JSON으로 반환되어 파일·라인·에러코드를 정확히 파악할 수 있습니다.
- Python/TS/JS/Go/Rust 5개 언어의 에러 패턴을 추출합니다.

---

### `check_intervention()`

**역할**: Auto-Fix Loop 진행 전 사용자 개입 여부를 확인합니다. Whiteboard 상태와 대기 중인 채팅 메시지를 조회합니다.

**파라미터:** 없음

**사용 예시:**
```
check_intervention()
→ Whiteboard annotations: 없음
→ Pending messages: 없음
→ User guidance: 없음
→ should_pause: False
```

**LLM 힌트**:
- Fix Loop의 각 시도 전에 사용자 개입이 필요한지 확인할 때 사용하세요.
- 사용자가 화이트보드에 메모를 남겼거나 채팅 메시지가 있는 경우 `should_pause=True`가 됩니다.

---

## 섹션 9: Integrated 그룹 — [`integrated.py`](mcp-servers/bridge/tools/integrated.py) (4 tools)

### `review_project(target_path, streaming?, mode?, max_tokens?)`

**역할**: `search_codebase` + `review_code` + `check_quality` + `extract_patterns` 통합. 프로젝트 전체를 종합 리뷰하여 하나의 마크다운 보고서로 반환합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | **필수** | 분석 대상 디렉토리 경로 |
| `streaming` | `bool` | `False` | 스트리밍 출력 여부 |
| `mode` | `str` | `"summary"` | `"summary"` (요약) / `"full"` (전체) / `"quality"` (품질 검사만) |
| `max_tokens` | `int` | `2000` | 최대 출력 토큰 수 |

**사용 예시:**
```
review_project(target_path="src/", mode="summary")
→ 파일: 124개, 함수: 342개, 클래스: 28개
→ TODO/FIXME: 12개, console.*: 8개
→ 품질 등급: B (Good) — Score: 84.5/100
→ 누락된 테스트: 5개 파일
```

**LLM 힌트**:
- 프로젝트 전체의 건강 상태를 빠르게 진단할 때 사용하세요.
- `mode="summary"`(기본값)로 ~500자의 핵심 요약을 얻을 수 있습니다.
- `mode="quality"`로 품질 검사만 수행할 수 있습니다 (구 `check_quality` 대체).
- `mode="full"`로 상세 리뷰를 확인할 수 있습니다.

---

### `find_bugs(target_path, mode?, max_tokens?)`

**역할**: `extract_patterns` + `search_codebase`(console.log/debugger/any) + Crow recall 통합. 프로젝트에서 잠재적 버그를 찾아 마크다운으로 반환합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | **필수** | 분석 대상 디렉토리 경로 |
| `mode` | `str` | `"summary"` | `"summary"` (요약) / `"full"` (전체) |
| `max_tokens` | `int` | `2000` | 최대 출력 토큰 수 |

**사용 예시:**
```
find_bugs(target_path="src/", mode="summary")
→ 14개 suspicious 패턴 검사
→ console.log: 8개 (P2)
→ any 타입: 15개 (P1)
→ ESLint: 23 issues (12 errors, 11 warnings)
→ tsc: 3 errors, 5 warnings
→ Crow Memory: 과거 유사 버그 패턴 2건 조회됨
```

**LLM 힌트**:
- 프로젝트의 잠재적 버그를 종합적으로 찾을 때 사용하세요.
- ESLint + tsc 통합으로 실제 컴파일/린트 에러까지 탐지합니다.
- Crow Memory에서 과거 유사 버그 패턴을 조회합니다.
- `<!-- LLM_TASK -->` 마커로 P0/P1/P2 심각도 분류 정보를 포함합니다.

---

### `suggest_refactor(target_path, mode?, max_tokens?)`

**역할**: `map_dependencies` + `extract_patterns` + `analyze_call_graph` 통합. 프로젝트의 리팩터링 제안을 마크다운으로 반환합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | **필수** | 분석 대상 디렉토리 경로 |
| `mode` | `str` | `"summary"` | `"summary"` (요약) / `"full"` (전체) |
| `max_tokens` | `int` | `2000` | 최대 출력 토큰 수 |

**사용 예시:**
```
suggest_refactor(target_path="src/", mode="summary")
→ Grade: B — 순환 의존성 1개 발견, 허브 모듈 3개
→ 제안 1: `auth/utils.py`와 `auth/validators.py` 간 순환 의존성 분해
→ 제안 2: `handlers.py`(742라인, 24개 함수) → 도메인별 4개 파일로 분할
→ 제안 3: `validate_email()` 패턴이 8개 파일에 중복 → 공통 모듈로 추출
```

**LLM 힌트**:
- 리팩토링이 필요한 부분을 찾을 때 사용하세요.
- Grade(A/B/C) 시스템으로 리팩토링 우선순위를 파악할 수 있습니다.
- `mode="summary"`(기본값)로 핵심 제안 3~5개를 빠르게 확인하세요.
- 순환 의존성, 허브 모듈, 중복 패턴을 자동 탐지합니다.

---

### `generate_docs(target_path, output_format?, mode?, max_tokens?)`

**역할**: `reverse_engineer` + `summarize_architecture` + `draw_on_whiteboard`(architecture diagram) 통합. 프로젝트 문서를 자동 생성하고 아키텍처 다이어그램을 화이트보드에 그립니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | **필수** | 분석 대상 디렉토리 경로 |
| `output_format` | `str` | `"markdown"` | 출력 형식 (`"markdown"`/`"openapi"`/`"mermaid"`) |
| `mode` | `str` | `"summary"` | `"summary"` (요약) / `"full"` (전체) |
| `max_tokens` | `int` | `2000` | 최대 출력 토큰 수 |

**사용 예시:**
```
generate_docs(target_path="src/", mode="summary")
→ 아키텍처 문서: 프로젝트 구조, 진입점, 레이어 구성
→ API 명세: 주요 라우트와 엔드포인트
→ ERD: 데이터 모델 관계도 (Mermaid)
→ 화이트보드: 아키텍처 다이어그램 자동 렌더링
```

**LLM 힌트**:
- 프로젝트 문서가 필요할 때 한 번에 생성하세요.
- `output_format="mermaid"`로 ERD 다이어그램을 생성할 수 있습니다.
- 아키텍처 다이어그램이 화이트보드에 자동으로 렌더링됩니다.
- `mode="summary"`(기본값)로 핵심 문서만 빠르게 생성하세요.

---

## 섹션 10: Analysis 그룹 — [`analysis.py`](mcp-servers/bridge/tools/analysis.py) (4 tools)

### `explain_code(file_path, line_number)`

**역할**: 지정된 파일의 특정 라인에 있는 코드가 무엇을 하는지 tree-sitter AST로 분석하여 설명합니다. AST 노드 트리를 통해 해당 라인의 함수/클래스/인터페이스 컨텍스트를 파악하고 간단한 설명을 생성합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `file_path` | `str` | **필수** | 분석할 파일의 상대 경로 |
| `line_number` | `int` | **필수** | 설명을 원하는 1-based 라인 번호 |

**사용 예시:**
```
explain_code(file_path="src/auth.py", line_number=42)
→ Python AST: `def verify_jwt(token: str) -> User | None` 감지
→ Enclosing scope: class `AuthMiddleware`
→ git blame: "fix: JWT expiration handling" (2026-05-15, k1yt)
→ Related tests: tests/test_auth.py::test_verify_jwt_expired
→ ToolContext: Summary / Context / Data Flow / Related Code / Caveats
```

**LLM 힌트**:
- 특정 라인의 코드를 이해해야 할 때 사용하세요.
- AST 기반으로 정확한 함수/클래스 범위를 탐지합니다.
- git blame 정보를 통합하여 최근 변경 이력을 확인할 수 있습니다.
- Python/Go/Rust/TS/JS를 지원합니다.

---

### `analyze_changes()`

**역할**: 현재 워크스페이스의 git diff를 분석하여 변경된 파일 목록과 diff 내용을 반환합니다. git diff --stat + git diff를 실행하여 변경 사항을 요약하고, Crow Memory에서 관련 컨텍스트를 조회합니다.

**파라미터:** 없음

**사용 예시:**
```
analyze_changes()
→ 변경 파일: 5개 (src/auth.py, src/utils/helpers.py, ...)
→ 변경 유형: refactoring (3), bugfix (1), feature (1)
→ Crow Memory: 연관 컨텍스트 2건 조회됨
```

**LLM 힌트**:
- 현재 작업 중인 변경사항을 리뷰할 때 사용하세요.
- 변경 유형(refactoring/bugfix/feature)을 자동 분류합니다.
- 파라미터 없이 호출 가능합니다.
- Crow Memory에서 연관 컨텍스트를 자동 조회합니다.

---

### `review_pr(base_branch?, head_branch?)`

**역할**: `analyze_changes` + `review_code`를 통합하여 PR 리뷰 보고서를 생성합니다. 두 브랜치 간의 git diff를 분석하고, 변경된 파일들에 대해 코드 리뷰를 수행합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `base_branch` | `str` | `"main"` | 기준 브랜치 |
| `head_branch` | `str` | `""` | 대상 브랜치 (기본: 현재 브랜치) |

**사용 예시:**
```
review_pr(base_branch="main")
→ 변경 파일: 8개 (diff: +245/-89 라인)
→ 위험도: 🟡 Medium (롤백 위험: auth.py 의존성 높음)
→ 리뷰 요약:
  - auth.py: `any` 타입 2건, console.log 1건 (P2)
  - utils.py: 순환 의존성 위험 (P1)
  - tests/: 커버리지 85% ✅
→ Crow Memory: 연관 컨텍스트 3건
```

**LLM 힌트**:
- PR 리뷰가 필요할 때 사용하세요.
- 위험도 시각화(🟢🟡🟠🔴)로 리뷰 우선순위를 파악할 수 있습니다.
- 의존성 분석 + 롤백 위험도 평가를 제공합니다.
- `base_branch="main"`이 기본값입니다.

---

### `refactor_across_files(pattern, new_pattern, file_patterns?, dry_run?)`

**역할**: `search_codebase`로 패턴을 찾고, 모든 발생 위치에 대해 일괄 수정 제안을 생성합니다. `dry_run=True` 시 실제 파일 수정 없이 변경 제안서를 마크다운으로 반환합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `pattern` | `str` | **필수** | 찾을 코드 패턴 (검색어) |
| `new_pattern` | `str` | **필수** | 대체할 새 패턴 (변경 제안) |
| `file_patterns` | `str` | `None` | 검색 대상 파일 패턴 (예: `"*.ts,*.tsx"`) |
| `dry_run` | `bool` | `True` | `True` 시 변경 제안만 표시, 실제 수정 없음 |

**사용 예시:**
```
refactor_across_files(pattern="User", new_pattern="AppUser", dry_run=True)
→ search_codebase로 "User" 15개 발생 위치 찾음 (5개 파일)
→ _ast_aware_rename(): AST로 `class User`, `def create_user()` 정의부만 치환
→ 변수 `user = User()` → 변수명 `user`는 치환하지 않음 (shadowing 고려)
→ dry_run=True → 변경 제안 diff만 표시, 실제 파일 수정 없음
```

**LLM 힌트**:
- 리팩토링 시 변수명/함수명/클래스명을 일괄 변경할 때 사용하세요.
- `dry_run=True`(기본값)로 먼저 변경 제안을 확인하세요.
- **AST-aware rename**: 단순 문자열 치환이 아닌 Scope-aware + Shadowing-aware 치환을 수행합니다.
  - Python `=`, TS `const`, Go `:=`, Rust `let` 패턴 감지
  - 섀도잉 이후 참조는 치환에서 제외
- `.bak` 백업 파일이 자동 생성됩니다.

---

## 섹션 11: Knowledge 그룹 — [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py) (4 tools)

### `learn_project(target_path?)`

**역할**: `summarize_architecture` + `extract_patterns` + `map_dependencies` 결과를 Crow Memory에 축적합니다. 프로젝트 분석 결과를 Crow arch/style/life_context 레지스터에 각각 저장하여, 이후 세션에서 프로젝트 컨텍스트를 자동으로 복원할 수 있게 합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | `None` | 분석 대상 디렉토리 경로 (기본: 현재 작업 디렉토리) |

**사용 예시:**
```
# MCP Bridge 시작 → 3초 후 자동 실행 (별도 호출 불필요)
# _auto_learn_project()가 자동 실행됨
→ summarize_architecture() → Crow arch register
→ extract_patterns() → Crow style register
→ map_dependencies() → Crow arch register
→ project identity (MD5 hash) → Crow life_context register
→ 이후 recall_project()로 즉시 활용 가능
```

**LLM 힌트**:
- **MCP Bridge 시작 시 자동 실행**되므로 명시적 호출이 필요하지 않습니다.
- 프로젝트 지식이 Crow Memory에 영속화되어 다음 세션에서도 활용 가능합니다.
- `recall_project()`로 저장된 지식을 조회할 수 있습니다.

---

### `recall_project(target_path?)`

**역할**: Crow Memory에서 `learn_project`로 저장된 프로젝트 지식을 회상합니다. arch, style, life_context 레지스터에서 관련 정보를 조회하여 반환합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `target_path` | `str` | `None` | 분석 대상 디렉토리 경로 (기본: 현재 작업 디렉토리) |

**사용 예시:**
```
recall_project()
→ arch: TypeScript + FastAPI, 3-layer architecture, 124 files
→ style: tab width 2, PascalCase classes, camelCase functions
→ life_context: project identity (MD5), last learned 2026-05-31
```

**LLM 힌트**:
- `learn_project()`가 자동 실행되었으므로, 언제든지 `recall_project()`로 저장된 지식을 조회할 수 있습니다.
- 프로젝트 온보딩 시 컨텍스트를 빠르게 복원할 수 있습니다.
- Crow `life_context` rule이 system prompt에 자동 주입되어 명시적 호출 없이도 프로젝트 컨텍스트를 활용할 수 있습니다.

---

### `learn_preference(rule, category?)`

**역할**: 사용자의 코딩 스타일 규칙이나 선호도를 Crow Memory에 저장합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `rule` | `str` | **필수** | 저장할 규칙 또는 선호도 설명 |
| `category` | `str` | `"coding_style"` | 카테고리 (`"coding_style"`/`"naming"`/`"formatting"`/`"architecture"`/`"workflow"`) |

**사용 예시:**
```
learn_preference(rule="함수형 컴포넌트 선호", category="coding_style")
→ 저장 완료. 다음 세션부터 자동 적용.
```

**LLM 힌트**:
- 사용자의 코딩 스타일 선호도를 저장할 때 사용하세요.
- 저장된 선호도는 이후 모든 세션에서 자동으로 적용됩니다.
- 카테고리별로 구분하여 저장할 수 있습니다.

---

### `get_preferences(category?)`

**역할**: 저장된 모든 사용자 선호도/규칙을 조회합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `category` | `str` | `None` | 특정 카테고리만 조회 (생략 시 전체) |

**사용 예시:**
```
get_preferences(category="coding_style")
→ coding_style:
  - 함수형 컴포넌트 선호
  - interface보다 type 사용
  - tab width: 2
```

**LLM 힌트**:
- 저장된 사용자 선호도를 확인할 때 사용하세요.
- `category`로 특정 카테고리만 필터링할 수 있습니다.

---

## 섹션 12: Web 그룹 + SSA 그룹 — (3 tools)

### [`web.py`](mcp-servers/bridge/tools/web.py) (2 tools)

#### `fetch_page(url, max_length?)`

**역할**: URL의 웹 페이지 내용을 가져와 마크다운으로 변환합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `url` | `str` | **필수** | 가져올 URL |
| `max_length` | `int` | `5000` | 결과 최대 길이 (bytes) |

**사용 예시:**
```
fetch_page(url="https://example.com/docs/api", max_length=3000)
→ HTML → 마크다운 변환된 문서 내용 반환
→ JSON 페이지는 자동 감지되어 포맷팅된 JSON 반환
```

**LLM 힌트**: 문서, API 응답 등 웹 페이지의 내용을 가져와 분석해야 할 때 사용하세요.

#### `web_search(query, max_results?, engine?)`

**역할**: 웹 검색을 수행하여 결과를 반환합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `query` | `str` | **필수** | 검색어 |
| `max_results` | `int` | `5` | 최대 결과 수 |
| `engine` | `str` | `"auto"` | 검색 엔진 (`"auto"`/`"duckduckgo"`/`"searxng"`/`"google"`/`"bing"`) |

**사용 예시:**
```
web_search(query="Python async/await best practices", max_results=3)
→ DuckDuckGo → (실패 시 SearXNG/Google/Bing 병렬 fallback)
→ 결과: 제목 + URL + 요약 3개 반환
```

**LLM 힌트**: 실시간 정보가 필요할 때 사용하세요. DuckDuckGo 차단 시 자동 병렬 fallback합니다.

---

### [`ssa.py`](mcp-servers/bridge/tools/ssa.py) (1 tool)

#### `aggregate_spatial_pixels(image_path, detail?, ocr?, ocr_lang?)`

**역할**: Statistical Spatial Aggregator v3 — 이미지를 공간 통계 매트릭스로 압축합니다. 선택적으로 OCR 텍스트 추출을 포함합니다.

**파라미터:**

| 이름 | 타입 | 기본값 | 설명 |
|:---|:---:|:---:|:---|
| `image_path` | `str` | **필수** | 분석할 이미지 파일 경로 |
| `detail` | `str` | `"auto"` | 분석 상세도 (`"auto"`/`"quick"`/`"full"`) |
| `ocr` | `bool` | `True` | OCR 텍스트 추출 여부 |
| `ocr_lang` | `str` | `"auto"` | OCR 언어 (`"auto"`/`"eng"`/`"kor"`/`"chi_sim"`/`"jpn"`) |

**사용 예시:**
```
aggregate_spatial_pixels(image_path="screenshot.png", detail="full")
→ SSA v3 분석:
  - 해상도: 1920×1080 (2.1MP)
  - 8×8 그리드: 색상+텍스처 맵
  - 객체 분할 (GrabCut): 전경 45%, 위치 중앙
  - 주요 색상: Blue(34%), White(28%), Gray(22%)
  - 텍스처: Moderately textured (uniformity 58%)
  - OCR: "Welcome to VibeZoo" detected (eng, confidence 92%)
```

**LLM 힌트**:
- **VibeZoo 최고 가치 도구** 중 하나입니다.
- 이미지 분석이 필요할 때 사용하세요 (스크린샷, 다이어그램, UI 등).
- `detail="auto"`(기본값)가 파일 크기/해상도 기반으로 자동 판단합니다.
- OCR이 기본 활성화되어 있어 이미지 속 텍스트를 추출할 수 있습니다.
- `capture_screen()`으로 캡처한 후 분석하는 일반적인 워크플로우를 지원합니다.

> **참고**: `open_image_dropzone`은 MCP 도구 목록에서 제거되었습니다. `capture_screen(source="dropzone")`로 대체 사용하세요.

---

## 섹션 13: 빠른 시작 가이드

LLM이 VibeZoo를 처음 사용할 때 참고할 워크플로우입니다.

### 1. 설치 및 초기화

```python
# 1) 설치 전 진단
vibezoo_setup(dry_run=True)

# 2) 권장 설치
vibezoo_setup(target="recommended", dry_run=False)
```

### 2. 프로젝트 탐색 (온보딩)

```python
# 1) 프로젝트 아키텍처 파악
summarize_architecture()

# 2) (자동) 프로젝트 지식 저장 → 이후 recall_project()로 조회 가능

# 3) 코드 검색
search_codebase(query="login", mode="ast")

# 4) 심볼 참조 조회
find_references(symbol="authenticate")
```

### 3. 코드 리뷰 및 품질 검사

```python
# 1) 프로젝트 전체 리뷰
review_project(mode="summary")

# 2) 특정 파일 리뷰
review_code(file_path="src/auth.py")

# 3) 버그 탐지
find_bugs(mode="summary")
```

### 4. 리팩토링

```python
# 1) 리팩토링 제안
suggest_refactor(mode="summary")

# 2) 의존성 분석
map_dependencies()

# 3) 호출 그래프
analyze_call_graph(file_path="src/core.py", depth=3)

# 4) 일괄 리팩토링 (dry-run 먼저)
refactor_across_files(pattern="User", new_pattern="AppUser", dry_run=True)
```

### 5. 문서화

```python
# 1) 문서 자동 생성 (아키텍처 + API + ERD)
generate_docs(mode="summary")

# 2) API 문서 (OpenAPI)
reverse_engineer(output_format="openapi")

# 3) 아키텍처 다이어그램
draw_on_whiteboard('[{"type":"rect","props":{"left":100,"top":50,"width":200,"height":100,"fill":"#4ec9ff","text":"API Gateway"}}, ...]')
```

### 6. 시각 정보 처리

```python
# 1) 화면 캡처
capture_screen()

# 2) 이미지 분석 (SSA + OCR)
aggregate_spatial_pixels(image_path="screenshot.png", detail="full")

# 3) 드롭존으로 이미지 업로드
capture_screen(source="dropzone")
```

### 7. 빌드 및 디버깅

```python
# 1) Auto-Fix 시작 전 상태 확인
auto_fix_status()

# 2) 빌드 재실행
retry_build()

# 3) 사용자 개입 확인
check_intervention()
```

### 8. 유용한 팁

| 상황 | 사용할 도구 | 이유 |
|:---|:---|---|
| 새 프로젝트 투입 | `summarize_architecture()` | 500자로 전체 구조 파악 |
| 코드 이해 막힘 | `explain_code(file, line)` | AST 기반 정확한 컨텍스트 |
| 버그 찾기 | `find_bugs()` | 14개 패턴 + ESLint + tsc 통합 |
| 리팩토링 | `suggest_refactor()` | Grade + 구체적 제안 |
| 테스트 생성 | `generate_tests(source)` | 의존성 그래프 + 모킹 템플릿 |
| 코드 리뷰 | `review_code(file)` | 정량적 지표 (복잡도/중첩) |
| 이미지 분석 | `aggregate_spatial_pixels()` | 8종 분석 + OCR 통합 |
| 문서화 | `generate_docs()` | 아키텍처 + API + ERD 원스톱 |
| 일괄 리팩토링 | `refactor_across_files()` | AST-aware rename (섀도잉 방지) |
| 웹 검색 | `web_search()` | 병렬 fallback으로 안정적 |
| 선호도 저장 | `learn_preference(rule)` | 세션 간 지속성 |

---

> **문서 버전**: v0.17.0 (Cycle 3 완결)
> **총 도구 수**: 31개 (12개 모듈)
> **이전 버전 대비 제거된 도구**: `check_quality`, `open_image_dropzone`, `open_whiteboard`, `open_ui_preview`
