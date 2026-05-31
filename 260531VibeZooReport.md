# VibeZoo MCP Bridge — 35개 도구 실사용 평가 보고서 (v0.13.0)

> **작성일**: 2026-05-31  
> **대상**: [`mcp-servers/bridge/`](mcp-servers/bridge/) 패키지 (17개 모듈, v0.13.0)  
> **이전 대비**: 단일 파일 4,627줄 → 모듈화된 17개 파일, 인프라 4종 신설  
> **평가 기준**: 실사용 유용성, 작동 방식, 부족한 점, 개선 방안

---

## 📊 종합 평가

| 등급 | 의미 | 도구 수 |
|:---:|:---|:---:|
| ⭐⭐⭐ | **프로덕션에서 즉시 유용** | 7 |
| ⭐⭐ | **유용하나 추가 개선 필요** | 18 |
| ⭐ | **개념 증명 수준, 실사용 한계** | 8 |
| 💀 | **사실상 사용 불가/중복** | 2 |

**이전 대비 개선점**:
- 모듈화로 유지보수성 대폭 향상 (4,627줄 → 17개 파일)
- `SearchEngine` ripgrep 폴백 체인으로 검색 속도 개선 기반 마련
- `FileCache` 3계층 캐시로 중복 파일 스캔 방지
- `WhiteboardDataConverter`로 Deepseek가 화이트보드 이해 가능
- SSA 한글 경로 지원 및 자연어 요약 추가

**여전히 남은 과제**:
- LLM-도구 체인: 도구는 데이터를 수집하지만 LLM이 의미 분석하는 파이프라인 부재
- AST 멀티랭귀지: Python/Go/Rust는 구조는 갖췄으나 tree-sitter 언어 팩 로딩은 미완
- 통합 도구 간 결과 공유: `review_project`가 4개 도구를 여전히 순차 호출

---

## 1. Scout 그룹 — `scout.py` (3 tools)

### 1.1 `search_codebase(query, file_patterns?, max_results?, mode?, context_lines?)` ⭐⭐⭐

**작동 방식**:
- 내부 엔진을 `SearchEngine`으로 교체. ripgrep 우선, git grep 차선, 기존 `os.walk` 폴백
- AST 검색은 `AstEngine`으로 위임 (TS/JS용 tree-sitter, Python/Go용 regex 폴백)
- `mode` 파라미터 추가: `"auto" | "exact" | "fuzzy" | "ast" | "semantic"`
- `context_lines` 파라미터 추가: 검색 결과 전후 컨텍스트 라인 수

**실사용 예시**:
- `search_codebase(query="UserService", mode="ast")` → AST 기반 클래스 정의 검색
- `search_codebase(query="api.key", mode="exact")` → 정확 문자열 매칭 (ripgrep 활용)
- `search_codebase(query="console.log", mode="fuzzy")` → 유사 패턴 검색

**부족한 점**:
- `SearchEngine` ripgrep/git grep이 실제로 설치되어 있어야 함. 미설치 시 기존 `os.walk` 폴백 (속도 동일)
- AST 검색이 TS/JS `.ts/.tsx`로 제한됨. Python/Go는 `AstEngine`이 구조만 갖추고 실제 tree-sitter 언어팩 로딩은 `_init_legacy_tree_sitter()`로 폴백
- `max_results` 상한이 200으로 여전히 제한적
- `semantic` 모드는 아직 placeholder (LLM 호출 없음)

**개선 방안**:
- [ ] `AstEngine._init_language()` 실제 구현 — tree-sitter 언어별 `.so`/`.dll` 로딩
- [ ] `semantic` 모드 실제 구현 — `search_codebase` 결과를 LLM이 reranking
- [ ] `SearchEngine` 점진적 검색: 먼저 10개 결과 빠르게, 사용자가 "more" 요청 시 추가

---

### 1.2 `find_references(symbol, file_pattern?)` ⭐⭐

**작동 방식**: `search_codebase`를 내부적으로 호출하되 `mode="exact"` 고정. 결과를 정의/참조로 그룹화.

**실사용 예시**:
- `find_references(symbol="handleSubmit")` → 함수 호출 위치 검색
- `find_references(symbol="User")` → 타입 참조 위치 검색

**부족한 점**:
- 여전히 `search_codebase` 단순 래퍼 수준. AST 기반 정확한 심볼 바인딩 추적 아님
- 변수 섀도잉(variable shadowing) 미고려 → 동명의 다른 심볼도 함께 반환
- `file_pattern` 파라미터는 있지만 AST 스코프 분석 없음

**개선 방안**:
- [ ] AST 기반 심볼 바인딩 (정의 찾기 → 스코프 내 참조 수집)
- [ ] 언어별 스코프 규칙 적용 (블록 스코프, 함수 스코프)
- [ ] 결과를 "Definitions", "References (calls)", "References (type usage)"로 세분화

---

### 1.3 `summarize_architecture(target_path?)` ⭐⭐

**작동 방식**: 내부적으로 `_run_map_dependencies()` 호출. import 그래프 기반 레이어 분류, 패키지 매니저 정보, 기술 부채 진단, 파일 분포, git 활동 트렌드 포함.

**실사용 예시**:
- `summarize_architecture()` → 팀 온보딩 시 프로젝트 구조 파악
- 신규 프로젝트 분석 첫 단계

**부족한 점**:
- `_run_map_dependencies()`를 동기적으로 호출 → 대규모 프로젝트에서 수 초~수십 초 소요
- 레이어 분류가 path-based heuristic (실제 import 방향 아님)
- `FileCache`의 `_file_list_cache_ttl`이 5초로 고정되어, 연속 호출 시에도 재스캔 발생 가능

**개선 방안**:
- [ ] 1차 요약 먼저 반환, 의존성 분석은 비동기/점진적으로 (generator 패턴)
- [ ] import 그래프 기반 실제 레이어 분류 (Kosaraju SCC + DAG 레벨링)
- [ ] Mermaid 다이어그램을 화이트보드에 자동 렌더링

---

## 2. Reviewer 그룹 — `reviewer.py` (2 tools)

### 2.1 `review_code(file_path, severity?)` ⭐⭐

**작동 방식**: AST 분석 (TS/JS) + 15+ 코드 스멜 패턴 검사. `severity` 파라미터로 필터링 가능.

**실사용 예시**:
- `review_code(file_path="src/app.ts", severity="error")` → 에러 수준만 필터
- 코드 리뷰 시작 전 자동 검사

**부족한 점**:
- 검사 항목은 늘었지만 여전히 **표면적**: `any` 타입, `console.log`, `TODO`, `@ts-ignore` 위주
- Cyclomatic complexity, 함수 길이, 중첩 깊이 등 구조적 복잡도 검사 없음
- ESLint/Pylint 연동 없음 (설치되어 있어도 실행 안 함)
- Go/Rust는 언어별 검사 없음 (generic only)
- Python은 `print()`, `bare except`, `TODO` 3개만 체크

**개선 방안**:
- [ ] Cyclomatic complexity 계산 (AST 기반 분기문 카운팅)
- [ ] 함수 길이/파라미터 개수/중첩 깊이 임계값 검사
- [ ] ESLint/Pylint/go vet 자동 실행 및 결과 통합
- [ ] 구체적 수정 제안 생성 ("이 부분을 Optional Chaining으로 바꾸세요")

---

### 2.2 `check_quality(target_path?)` ⭐ (어댑터)

**작동 방식**: 내부적으로 `review_project(target_path, mode="quick")` 호출로 위임. 단독 도구는 폐기 예정.

**실사용 예시**: 거의 없음. `review_project()`가 더 나은 대안.

**부족한 점**:
- `review_project`의 하위 집합. 단독 가치 없음.
- 대규모 프로젝트에서 모든 파일 순회 → 느림

**개선 방안**:
- [ ] **폐기 권장**. 대신 `review_project`의 `mode="quick"` 옵션을 더 발전시킬 것

---

## 3. DeepAnalyzer 그룹 — `deep_analyzer.py` (4 tools)

### 3.1 `analyze_call_graph(file_path?, depth?, include_external?)` ⭐⭐⭐

**작동 방식**: AST 기반 호출 추출. `include_external` 파라미터로 외부 라이브러리 호출 포함 가능. Mermaid 그래프 출력.

**실사용 예시**:
- `analyze_call_graph(file_path="src/service.ts", depth=5)` → 재귀적 호출 체인
- `analyze_call_graph(file_path="src/auth.ts", include_external=True)` → 외부 라이브러리 호출 포함

**부족한 점**:
- Dynamic dispatch, 고차 함수 콜백 추적 불가
- `obj.method()` 형태의 메서드 호출은 AST만으로 알 수 없음 (타입 추론 필요)
- AST 호출 추출이 TS/JS로 제한됨 (Python/Go는 regex 폴백)

**개선 방안**:
- [ ] 타입 추론 미니엔진으로 메서드 호출 바인딩 추정
- [ ] "Virtual call graph" — 추정 호출(점선)과 확정 호출(실선) 구분
- [ ] Fan-in/Fan-out 분석으로 허브/리프 함수 식별

---

### 3.2 `map_dependencies(target_path?)` ⭐⭐⭐

**작동 방식**: AST + regex import 추출, 패키지 매니저 정보 포함. Python/Go용 별도 import 추출 함수(`_extract_python_imports`, `_extract_go_imports`) 추가. Tarjan SCC (순환 참조 탐지) 보유.

**실사용 예시**:
- `map_dependencies()` → 프로젝트 의존성 구조 파악
- 리팩토링 전 영향도 분석

**부족한 점**:
- 순환 참조 탐지는 여전히 iterative DFS (선언은 Tarjan이나 구현은 DFS). 주요 설계서 불일치
- 외부 패키지(node_modules, pip)와 내부 모듈 구분 불명확
- 출력이 장황함 (모든 파일의 모든 import를 나열)

**개선 방안**:
- [ ] 실제 Tarjan SCC 알고리즘 구현 (또는 NetworkX 연동)
- [ ] "Hub modules" 섹션을 별도로 추출 (가장 많이 참조되는 모듈 Top 10)
- [ ] "영향도 분석" 기능: "이 파일을 수정하면 N개 파일이 영향받습니다"

---

### 3.3 `extract_patterns(target_path?, min_occurrences?)` ⭐

**작동 방식**: AST 서브트리 매칭으로 전환 시도했으나 실제로는 키워드 카운팅에 가까움. `content.count("async ")` 방식.

**실사용 예시**:
- `extract_patterns(min_occurrences=5)` → "프로젝트에서 가장 흔한 패턴은?"
- 참고용 통계

**부족한 점**:
- 구조적 패턴 매칭(예: "try { ... } catch { ... } finally { ... }") 감지 못함
- 안티패턴(콜백 지옥, God Class) 탐지 없음
- 단순 빈도수만 알려줄 뿐 "어디에 있는지" 위치 정보 없음

**개선 방안**:
- [ ] tree-sitter AST 서브트리 매칭으로 진정한 구조적 패턴 탐지
- [ ] 안티패턴 템플릿 라이브러리 구축 (Crow bug register에 저장)
- [ ] 각 패턴의 예시 코드 + 위치 정보 함께 제시

---

### 3.4 `reverse_engineer(target_path?, output_format?)` ⭐⭐

**작동 방식**: regex 기반 API 라우트 추출 (Express, FastAPI, Flask, Gin). TS 타입 기반 데이터 모델 추출. Mermaid ERD / OpenAPI 3.0 출력.

**실사용 예시**:
- `reverse_engineer(output_format="mermaid")` → ERD 다이어그램
- `reverse_engineer(output_format="openapi")` → OpenAPI 스펙

**부족한 점**:
- API 라우트 추출이 여전히 regex 기반. NestJS/Next.js App Router 미지원
- 생성된 ERD가 TypeScript 타입 기반이라 실제 DB 스키마와 다름
- OpenAPI 출력이 기본적인 path/method만 있음. request/response body, validation, description 누락
- JSDoc/TSDoc 주석 미활용

**개선 방안**:
- [ ] AST 기반 라우트 핸들러 추출 (express.Router() 체인 추적)
- [ ] TypeORM/Prisma/Mongoose 데코레이터 분석으로 실제 DB 스키마 추론
- [ ] JSDoc/TSDoc에서 description, param, response 타입 추출

---

## 4. Tester 그룹 — `tester.py` (2 tools)

### 4.1 `generate_tests(source_path, framework?)` ⭐⭐

**작동 방식**: 함수/클래스 시그니처 추출 → 테스트 템플릿 생성. 파라미터 타입 기반 경계값 힌트 포함.

**실사용 예시**:
- `generate_tests(source_path="src/auth.ts")` → 테스트 뼈대 생성
- 새 기능 구현 후 빠른 테스트 시작

**부족한 점**:
- 생성된 테스트는 **템플릿** 수준. `test_() { ... }` 내부는 비어있거나 기본 assert만 있음
- Mock/stub 생성 불가
- Edge case(null, undefined, 빈 배열)를 자동 생성하지 않음
- Python 파일은 함수명만 추출 → `def test_(): pass`

**개선 방안**:
- [ ] LLM-도구 체인: `generate_tests`가 데이터(함수 시그니처, 타입, docstring)를 수집하고 LLM이 실제 테스트 로직 생성
- [ ] 모킹 프레임워크 템플릿 (jest.mock, unittest.mock) 기본 포함
- [ ] Property-based testing (fast-check, hypothesis) 템플릿 추가

---

### 4.2 `analyze_coverage(target_path?)` ⭐

**작동 방식**: vitest/pytest --cov 실행. 설정 파일 자동 감지 (실패 시 대체 분석으로 파일 존재 여부만 체크).

**실사용 예시**:
- 거의 사용 안 함. 대부분의 프로젝트에서 "No coverage data found" 반환

**부족한 점**:
- vitest/pytest/pytest-cov가 설치되어 있어야 함. 대부분 미설치
- 실패 시 원인 분석 없이 빈 결과 반환
- Go/Node.js 설정 파일 경로 하드코딩

**개선 방안**:
- [ ] 커버리지 도구 미설치 시 "파일 존재 여부 기반 테스트/소스 매핑"이라도 제공
- [ ] 실패 원인을 구체적으로 출력 (미설치 / 설정 파일 없음 / 실행 타임아웃)
- [ ] `npx jest --coverage` 등 대체 도구 체인 추가

---

## 5. Whiteboard 그룹 — `whiteboard.py` (5 tools + 변환기)

### 5.1 `draw_on_whiteboard(commands)` ⭐⭐

**작동 방식**: Fabric.js JSON 명령을 `~/.vibezoo-whiteboard.json`에 저장. `WhiteboardDataConverter.to_mermaid()`로 Mermaid 변환 가능.

**실사용 예시**:
- `draw_on_whiteboard('[{"type":"rect","props":{...}}]')` → 아키텍처 다이어그램
- 다이어그램 그린 후 `get_whiteboard_state()`로 LLM-readable 텍스트 확인

**부족한 점**:
- 사용자가 직접 Fabric.js JSON을 알아야 함. 자연어→JSON 변환 레이어 부재
- 복잡한 다이어그램에서 JSON이 너무 장황해짐
- `fs.watchFile` 200ms debounce — 실시간 느낌 부족

**개선 방안**:
- [ ] Intent-to-Code 브릿지 활성화: "데이터베이스와 서비스를 연결하는 화살표를 그려줘" → JSON 자동 생성
- [ ] Mermaid 텍스트를 직접 입력받아 Fabric.js JSON으로 변환 (역변환)
- [ ] 그리기 템플릿 라이브러리: flowchart, ERD, sequence diagram

---

### 5.2 `get_whiteboard_state()` ⭐⭐⭐ (개선됨)

**작동 방식**: 이전과 달리 raw JSON 대신 **구조화된 텍스트** 반환. `WhiteboardDataConverter`가 변환:
1. 객체 목록 (유형, 위치, 크기, 색상, 텍스트 레이블)
2. 객체 간 관계 (연결선/포함/근접/정렬)
3. 공간 레이아웃 분석 (그리드 위치, 크기 범주, 색상명)
4. Mermaid 다이어그램 변환
5. 원본 JSON (2000자 제한)

**실사용 예시**:
- 화이트보드에 다이어그램을 그리고 `"지금 화이트보드에 뭐가 그려져 있어?"` → LLM이 설명
- Fix Loop 중 사용자 annotation 확인

**부족한 점**:
- 화이트보드를 실제로 사용하지 않으면 무의미
- 사용자의 의도(annotation의 의미)는 파악 불가

**개선 방안**:
- [ ] 화이트보드 사용 시나리오 확장 (코드 리뷰, 아키텍처 논의 등)
- [ ] 사용자 annotation을 자연어로 요약하는 LLM 체인

---

### 5.3 `open_whiteboard(message?)` ⭐

**작동 방식**: `WHITEBOARD_ACTION_FILE`에 `{"action": "open", "message": ...}` 기록.

**실사용 예시**: 패널 열기

**부족한 점**:
- `message` 파라미터가 있지만 Extension이 실제로 활용하지 않음. (VibeZoo Extension이 이 파일을 watch하지만, message를 표시하는 로직 없음)

**개선 방안**:
- [ ] Extension이 `message`를 실제 Webview에 표시하도록 연동
- [ ] 특정 다이어그램을 미리 로드해서 열기

---

### 5.4 `capture_screen()` ⭐⭐ (개선됨)

**작동 방식**: 3단계 fallback: PIL `ImageGrab` → PowerShell `[System.Windows.Forms]` → mss. 캡처 결과를 `WHITEBOARD_FILE`에 저장.

**실사용 예시**:
- `capture_screen()` → 현재 화면 캡처 (Windows에서도 작동)
- `aggregate_spatial_pixels(image_path="...")` → 캡처 이미지 분석

**부족한 점**:
- PowerShell fallback은 새로운 프로세스 생성, MessageBox 표시 등 UX 노이즈
- 캡처 이미지를 화이트보드에 표시하지만, 사용자 확인 UI 없음
- 캡처 후 자동 SSA 분석 파이프라인 부재

**개선 방안**:
- [ ] PowerShell fallback을 조용하게 실행 (`-WindowStyle Hidden`)
- [ ] 캡처 후 자동으로 SSA 분석을 호출하는 옵션
- [ ] 캡처 전 "화면에서 캡처할 영역을 선택하세요" UI (VS Code Webview)

---

### 5.5 `open_ui_preview(code?, framework?)` ⭐⭐

**작동 방식**: 코드를 `UI_ACTION_FILE`에 저장. Extension Webview가 이를 읽어서 Babel standalone + iframe으로 렌더링.

**실사용 예시**:
- React 컴포넌트 미리보기
- HTML/CSS 디자인 확인

**부족한 점**:
- Babel standalone 변환이라 실제 React 환경과 차이
- 외부 CSS/JS/이미지 로딩 안 됨
- 에러 발생 시 조용히 실패

**개선 방안**:
- [ ] 에러 메시지를 Webview에 표시
- [ ] Tailwind CSS CDN 기본 포함
- [ ] 외부 리소스 URL 임포트 지원

---

## 6. Fix Loop 그룹 — `fix_loop.py` (3 tools)

### 6.1 `auto_fix_status()` ⭐⭐⭐

**작동 방식**: `~/.vibezoo-fix-request.json`에서 에러 정보 + Crow 과거 패턴 조회.

**실사용 예시**:
- 빌드 실패 → LLM이 `auto_fix_status()` 호출 → "무슨 에러야?"

**부족한 점**:
- 상태 머신 `idle/pending/in_progress/building/resolved/abandoned` 6개. Extension `FixLoopManager`는 8개 상태 (awaiting_user, user_override 추가). 불일치 그대로
- JSON 파일 기반 LLM 통신이라 race condition 가능성
- Crow 과거 패턴이 구체적 solution 코드가 아닌 메타데이터만 포함

**개선 방안**:
- [ ] 상태 머신 Extension-Bridge 싱크 (추천: Extension 우선, Bridge는 읽기 전용)
- [ ] Crow 과거 패턴에 구체적 diff/solution 코드 포함
- [ ] JSON 파일 대신 Fix Loop 전용 MCP 채널

---

### 6.2 `retry_build(build_command?)` ⭐⭐

**작동 방식**: 프로젝트 타입별 빌드 명령어 자동 감지. `build_command` 파라미터로 override 가능.

**실사용 예시**:
- LLM 수정 후 `retry_build()` → 빌드 재시도

**부족한 점**:
- 타임아웃 120초 — 대규모 프로젝트에선 부족
- 빌드 로그를 전체 반환 (LLM이 파싱하기 어려움). 에러 부분만 추출 필요
- 프로젝트 타입 감지 로직이 단순 파일 존재 검사에 의존

**개선 방안**:
- [ ] 빌드 로그의 에러/경고 부분만 지능적으로 추출
- [ ] 타임아웃 설정 가능하도록 파라미터화
- [ ] 여러 빌드 도구 fallback (npm → yarn → pnpm)

---

### 6.3 `check_intervention()` ⭐⭐

**작동 방식**: Whiteboard 상태 + Chat 메시지 파일 체크. HITL 인터럽트 확인.

**실사용 예시**:
- Auto-Fix Loop 중 사용자 개입 확인

**부족한 점**:
- `should_pause` 필드의 설정 주체 불명확 (누가 이 필드를 쓰는가?)
- Extension의 명령(`pauseFixLoop`/`resumeFixLoop`/`abortFixLoop`)과 Bridge의 `check_intervention`이 분리됨

**개선 방안**:
- [ ] Extension 명령과 Bridge 체크를 양방향 통합
- [ ] 사용자 개입 이력을 Crow Memory에 저장 → 패턴 학습

---

## 7. Integrated 그룹 — `integrated.py` (4 tools)

### 7.1 `review_project(target_path)` ⭐⭐

**작동 방식**: 내부에서 `search_codebase` + `review_code` + `check_quality` + `extract_patterns` 순차 호출.

**실사용 예시**:
- `review_project(target_path=".")` → 프로젝트 전체 리뷰

**부족한 점**:
- 4개 도구를 순차 호출, 각각 `os.walk` 중복 실행 → 느림
- 결과가 너무 길어서 LLM 컨텍스트 초과 위험
- 중요도/심각도 정렬 없음

**개선 방안**:
- [ ] `FileCache`를 활용한 중복 스캔 방지
- [ ] 점진적 결과 반환 (generator): "Search complete. Reviewing files..."
- [ ] 결과를 중요도/심각도로 정렬하고 "Quick Wins" 섹션 별도 추출

---

### 7.2 `find_bugs(target_path)` ⭐⭐

**작동 방식**: `extract_patterns` + `search_codebase(console.log|debugger|any)` + Crow recall 통합.

**실사용 예시**:
- `find_bugs()` → console.log, debugger, any 타입, 미사용 변수 탐지

**부족한 점**:
- 찾는 "버그"가 정적 분석 수준 (console.log, debugger, any). **실제 로직 버그** 못 찾음
- Crow recall로 과거 버그 패턴을 조회하지만, 현재 코드와의 구조적 비교 없음
- null 포인터, 메모리 누수, 레이스 컨디션 감지 불가

**개선 방안**:
- [ ] ESLint 규칙 (`no-unused-vars`, `no-empty`, `no-extra-boolean-cast`) 통합
- [ ] `npx tsc --noEmit --strict` 실행 결과 통합
- [ ] 일반적인 안티패턴 DB를 Crow bug register에 구축→매칭

---

### 7.3 `suggest_refactor(target_path)` ⭐⭐

**작동 방식**: `map_dependencies` + `extract_patterns` + `analyze_call_graph` 통합.

**실사용 예시**:
- `suggest_refactor()` → "이 파일은 책임이 너무 많습니다", "순환 참조가 있습니다"

**부족한 점**:
- 제안이 일반론 수준. "파일이 너무 큼", "함수가 너무 많음" — 구체적 액션 없음
- 리팩토링 패턴(Extract Method, Move Class, Split Module) 적용 안 됨
- 변경 전/후 코드 예시 없음

**개선 방안**:
- [ ] 구체적 리팩토링 제안: "`handleAuth()` 함수에서 JWT 검증 로직을 별도 `validateToken()`으로 추출"
- [ ] LLM-도구 체인: 도구가 데이터 수집 → LLM이 리팩토링 제안 생성
- [ ] 예상 영향도 포함 ("이 변경으로 N개 파일이 영향을 받습니다")

---

### 7.4 `generate_docs(target_path, output_format?)` ⭐⭐

**작동 방식**: `reverse_engineer` + `summarize_architecture` 호출. Mermaid 다이어그램 생성.

**실사용 예시**:
- `generate_docs(output_format="mermaid")` → 아키텍처 문서 + ERD

**부족한 점**:
- 자동 생성된 티가 너무 남. 가독성 낮음
- Mermaid 다이어그램이 너무 복잡하면 이해 불가
- 생성된 문서의 정확성 검증 불가

**개선 방안**:
- [ ] LLM이 생성된 원본 데이터를 자연스러운 문장으로 재작성
- [ ] 각 정보에 신뢰도 표시 ("추정: FastAPI 엔드포인트" vs "확정: @app.get()")
- [ ] 생성된 문서 diff를 사용자에게 제공하여 검토 후 반영

---

## 8. Analysis 그룹 — `analysis.py` (4 tools)

### 8.1 `explain_code(file_path, line_number)` ⭐⭐⭐

**작동 방식**: AST로 감싸고 있는 함수/클래스 정보 추출. Python/Go regex fallback.

**실사용 예시**:
- `explain_code(file_path="src/auth.ts", line_number=42)` → "이 코드의 역할은?"

**부족한 점**:
- AST로 찾은 컨텍스트(함수명, 파라미터)만 표시. LLM 없이 "의미" 설명 불가
- `AstEngine`의 멀티랭귀지 확장이 아직 TS/JS 중심
- 관련 테스트 코드, git blame 정보 없음

**개선 방안**:
- [ ] LLM-도구 체인: AST 데이터 + git blame + 관련 테스트를 LLM에 전달, LLM이 종합 설명 생성
- [ ] "이 코드는 2주 전에 @user가 'JWT 만료일 검증 추가'라는 이유로 수정했습니다" 같은 맥락

---

### 8.2 `analyze_changes()` ⭐⭐⭐

**작동 방식**: `git diff` 실행 + Crow 컨텍스트 조회.

**실사용 예시**:
- `analyze_changes()` → "지금까지 변경한 내용 요약"
- 커밋 메시지 작성 전 점검

**부족한 점**:
- Crow 컨텍스트 조회가 단순 키워드 매칭. 변경 파일과 관련된 구체적 기억 조회 안 함
- 변경 유형(추가/수정/삭제) 구분이 불명확
- 변경 파일이 많으면 출력 너무 김

**개선 방안**:
- [ ] 변경 유형별 필터 (추가만 / 삭제만 / 수정만)
- [ ] 각 변경 파일에 대해 Crow Memory에서 관련 컨텍스트 조회
- [ ] `git diff --stat` 먼저 요약, 상세는 선택적

---

### 8.3 `review_pr(base_branch?, head_branch?)` ⭐⭐

**작동 방식**: `analyze_changes` + `review_code` 통합. git merge-base 미사용.

**실사용 예시**:
- `review_pr(base_branch="main", head_branch="feature/auth")` → PR 리뷰

**부족한 점**:
- 단순히 변경된 각 파일을 `review_code`로 개별 검사. 변경 사항의 **논리적 문제** 발견 못 함
- `git merge-base`를 안 써서 머지 충돌 사전 감지 불가
- PR 설명/커밋 메시지/이슈 트래커 연동 없음

**개선 방안**:
- [ ] `git merge-base`를 사용한 3-way diff
- [ ] "새로운 함수를 추가했는데 아무데서도 호출하지 않음" 같은 논리적 검증
- [ ] GitHub/GitLab API 연동으로 PR description과 diff 일관성 검증

---

### 8.4 `refactor_across_files(pattern, new_pattern, file_patterns?)` ⭐

**작동 방식**: `search_codebase`로 패턴 검색 → 변경 제안서 생성. AST 고려 없는 단순 문자열 치환 제안.

**실사용 예시**:
- `refactor_across_files(pattern="console.log", new_pattern="// console.log", file_patterns="*.ts")` → console.log 주석 처리 제안

**부족한 점**:
- **변경 제안만 하고 실제 파일 수정 안 함**. 사용자가 직접 수동 적용
- AST 고려 없이 단순 문자열 패턴. `User`→`AppUser` 변경 시 변수명까지 다 바뀜
- 변경 제안서가 파일마다 전체 diff를 표시해서 너무 장황

**개선 방안**:
- [ ] AST-aware rename (scope 고려한 rename). 예: `User` 타입만 변경, 변수명은 유지
- [ ] YOLO + yocto 백업과 연동한 자동 적용 (사용자 승인 후)
- [ ] 변경 전/후 통계 ("N개 파일, M개 위치가 변경됩니다")

---

## 9. Knowledge 그룹 — `knowledge.py` (4 tools)

### 9.1 `learn_project(target_path?)` ⭐⭐

**작동 방식**: 프로젝트 구조/패턴/의존성 → Crow Memory arch/style/life_context 레지스터에 저장.

**실사용 예시**:
- `learn_project()` → "이 프로젝트를 기억해둬"

**부족한 점**:
- 저장된 지식이 **자동으로 로드되지 않음**. LLM이 명시적으로 `recall_project` 호출해야 함
- 저장 정보가 일반적 (파일 수, 확장자 분포). 프로젝트별 핵심 지식(라이브러리, 컨벤션) 부족

**개선 방안**:
- [ ] `recall_project`를 세션 시작 시 자동 호출 (system prompt 규칙 추가)
- [ ] 프로젝트별 핵심 패턴 저장 (사용된 라이브러리, 코딩 컨벤션, 아키텍처 패턴)

---

### 9.2 `recall_project(target_path?)` ⭐⭐

**작동 방식**: Crow Memory에서 `learn_project`로 저장된 정보 회상.

**실사용 예시**:
- `recall_project()` → "이 프로젝트에 대해 기억나는 정보"

**부족한 점**:
- 저장된 정보의 신선도(freshness) 미표시. 구버전 정보일 수 있음
- `learn_project`로 저장한 정보만 회상

**개선 방안**:
- [ ] 정보 생성일/수정일 표시
- [ ] 현재 코드 상태와 저장된 정보의 차이 검증

---

### 9.3 `learn_preference(rule, category?)` ⭐⭐⭐

**작동 방식**: 로컬 JSON + Crow `life_context` 이중 저장.

**실사용 예시**:
- `learn_preference(rule="Prefer functional components", category="coding_style")`
- `learn_preference(rule="Tab width: 2", category="formatting")`

**부족한 점**:
- 이중 저장소 동기화 문제 가능성
- 저장된 선호도가 자동으로 LLM에 주입되지 않음
- 카테고리 5개 고정

**개선 방안**:
- [ ] `get_preferences` 세션 시작 시 자동 호출
- [ ] Crow Memory 우선, 로컬 JSON은 backup

---

### 9.4 `get_preferences(category?)` ⭐⭐⭐

**작동 방식**: 로컬 JSON + Crow Memory 조회.

**실사용 예시**:
- `get_preferences()` → "내 선호도를 보여줘"

**부족한 점**:
- Crow Memory와 로컬 JSON 불일치 시 어느 쪽이 우선인지 불명확
- 선호도가 많으면 LLM 컨텍스트 차지

**개선 방안**:
- [ ] Crow Memory 우선 조회, 로컬 JSON 폴백
- [ ] 중요도 태깅 (필수 규칙 vs 희망 사항)으로 컨텍스트 최적화

---

## 10. Web 그룹 — `web.py` (2 tools)

### 10.1 `fetch_page(url, max_length?)` ⭐⭐⭐

**작동 방식**: 순수 Python 표준 라이브러리. `urllib.request` + 자체 HTML→마크다운 변환기.

**실사용 예시**:
- `fetch_page(url="https://docs.python.org/3/")` → 문서 가져오기
- API 문서 참조

**부족한 점**:
- JavaScript 렌더링(SPA) 페이지는 HTML만으로 내용 파악 불가
- 자체 HTML 파서(`_html_to_markdown`)가 모든 HTML 태그/속성 미처리
- User-Agent 차단 가능성

**개선 방안**:
- [ ] SPA 페이지 감지 시 "이 페이지는 JavaScript 렌더링이 필요합니다" 표시
- [ ] `html2text` 라이브러리 선택적 활용
- [ ] User-Agent 로테이션

---

### 10.2 `web_search(query, max_results?, engine?)` ⭐⭐⭐

**작동 방식**: DuckDuckGo HTML 검색. `engine` 파라미터로 검색 엔진 선택 가능 (auto/duckduckgo/google/bing). Google/Bing은 API 키 필요 시 경고.

**실사용 예시**:
- `web_search(query="Python 3.13 new features")` → 최신 정보 검색
- `web_search(query="TS2322 error fix", engine="google")` → 구글 검색 (API 키 설정 시)

**부족한 점**:
- DuckDuckGo HTML 엔드포인트 차단/변경 시 검색 불가 (이미 간헐적 차단 발생)
- Google/Bing은 API 키 필요. 환경변수 설정 안내 부족
- 검색 결과 5개 제한 → 정보량 부족

**개선 방안**:
- [ ] 환경변수 `VIBEZOO_GOOGLE_API_KEY`, `VIBEZOO_BING_API_KEY` 설정 안내를 도움말에 포함
- [ ] 검색 결과를 LLM 컨텍스트에 최적화: 중복 제거, 요약, 신뢰도 추정
- [ ] 결과 수를 10개까지 확장

---

## 11. SSA 그룹 — `ssa.py` (2 tools)

### 11.1 `aggregate_spatial_pixels(image_path, detail?)` ⭐⭐⭐ (개선됨)

**작동 방식**: OpenCV 기반 6가지 분석 (GrabCut/k-means/MedianCut/LBP/Saliency/Histogram). `detail="auto"`가 실제로 동작 (파일 크기+해상도 기반 판단). 한글 경로 지원(`_imread_korean_safe`). 결과 자연어 요약(`_summarize_ssa_results`) 추가.

**실사용 예시**:
- `aggregate_spatial_pixels(image_path="diagram.png")` → 다이어그램 구조 분석
- `aggregate_spatial_pixels(image_path="screenshot.png", detail="full")` → 전체 분석

**부족한 점**:
- **OCR 없음**. OpenCV 수학 연산만으로 텍스트/UI 요소 파악 불가
- 분석 결과가 여전히 추상적 (`Red(S) | Blue(R)` 그리드). 일반 사용자 이해 어려움
- SSIM 분석 추가됐지만, 비교 대상 이미지가 없으면 무의미

**개선 방안**:
- [ ] **가장 시급**: Tesseract OCR 또는 PaddleOCR 연동 (이미지 내 텍스트 추출)
- [ ] 분석 결과를 자연어 변환하는 LLM 체인 ("이 이미지는 청색 계열 UI 스크린샷으로 상단에 헤더, 중앙에 버튼이 있습니다")
- [ ] UI 요소 감지 모델 (버튼, 입력창, 리스트) - 템플릿 매칭 활용

---

### 11.2 `open_image_dropzone()` ⭐ (어댑터)

**작동 방식**: VS Code Webview 내 드롭존 (내부 HTML base64) + 외부 브라우저 fallback.

**실사용 예시**: 이미지 업로드

**부족한 점**:
- Webview fallback이지만 여전히 외부 브라우저일 가능성
- 업로드 파일이 `~/.vibezoo-cache/dropped_image.png` 1개로 고정

**개선 방안**:
- [ ] 다중 이미지 업로드 지원
- [ ] 업로드 완료 시 자동 SSA 분석 파이프라인

---

## 12. 🗑️ 폐기/통합 권장 도구

### 💀 `check_quality()` — `review_project()`에 흡수 완료 (어댑터)

내부에서 `review_project(mode="quick")` 호출로 위임. 단독 도구로서 존재 가치 낮음.

### 💀 `open_image_dropzone()` — `capture_screen()`에 통합 중

외부 브라우저 UX는 "VS Code Lock-In" 원칙에 위배. Webview 드롭존으로 전환 중이나 아직 불완전.

### 💀 `extract_patterns()` — 독립 도구 유지 (내부만 AST로 재구현)

폐기 대신 내부를 AST 서브트리 매칭으로 재구현하고, `review_code`(안티패턴)와 `map_dependencies`(의존성 패턴)가 내부적으로 활용.

---

## 13. 종합 개선 제안 (Top 5)

| 순위 | 제안 | 영향 | 난이도 | 현재 상태 |
|:---:|:---|:---:|:---:|:---|
| 1 | **LLM-도구 체인**: 도구는 데이터 수집, LLM은 의미 분석. `generate_tests`, `explain_code`, `find_bugs`에 우선 적용 | ★★★★★ | 중 | ❌ 미적용 |
| 2 | **AST 언어 팩 로딩**: Python/Go/Rust tree-sitter 언어별 `.so`/`.dll` 실제 로딩 구현 | ★★★★ | 중 | 🔶 `AstEngine` 구조만 있음 |
| 3 | **점진적/스트리밍 결과**: `review_project`, `summarize_architecture`가 부분 결과 먼저 반환 | ★★★★ | 중 | ❌ 미적용 |
| 4 | **Web search API 키 문서화**: Google/Bing API 키 설정 방법을 README 및 도움말에 포함 | ★★★ | 하 | ❌ 미적용 |
| 5 | **OCR 연동**: Tesseract/PaddleOCR로 이미지 내 텍스트 추출 | ★★★★★ | 중 | ❌ 미적용 |

---

## 14. 결론

### 이전(v0.12.0) 대비 개선된 점
1. **모듈화 완료**: 4,627줄 단일 파일 → 17개 모듈 (평균 200~400줄)
2. **검색 인프라**: `SearchEngine` ripgrep/git grep/walk 3단계 폴백
3. **캐시**: `FileCache` 3계층 (L1 메모리 LRU + L2 디스크 + L3 mtime)
4. **화이트보드 변환**: `WhiteboardDataConverter`로 Deepseek가 그림 이해 가능
5. **SSA 개선**: 한글 경로, 자연어 요약, detail 모드, SSIM 분석
6. **다국어 import**: Python/Go 전용 import 추출 함수 추가

### 여전히 남은 도전 과제
1. **LLM-도구 체인 부재**: 가장 큰 갭. 도구는 "데이터 수집기"에서 "분석기"로 진화해야 함
2. **AST 멀티랭귀지**: 구조는 갖췄으나 실제 tree-sitter 언어팩 로딩은 미완성
3. **통합 도구 성능**: `review_project` 등이 여전히 순차 동기 호출
4. **리팩토링 자동화**: `refactor_across_files`가 실제 파일을 수정하지 않음
5. **OCR**: 이미지 분석의 가장 큰 약점. 텍스트를 읽을 수 없음

> **핵심 메시지**: "v0.13.0은 **기초 공사**를 완료했다. 다음 버전은 **LLM과의 협업**을 전제로 한 도구 체인과 **AST 멀티랭귀지**에 집중해야 한다. 도구가 데이터를 수집하면 LLM이 분석하고, LLM이 결정하면 도구가 실행하는 — 이 순환 고리를 완성하는 것이 VibeZoo의 다음 단계."
