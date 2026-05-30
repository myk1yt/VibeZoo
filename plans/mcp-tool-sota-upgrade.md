# VibeZoo MCP Tools SOTA 업그레이드 계획

> **목표**: 27개 MCP 도구(Whiteboard 제외)를 상위 0.01% 수준의 SOTA급 도구로 업그레이드
> **핵심 원칙**: AI가 직접 Python 스크립트를 짜는 것보다 이 도구를 쓰는 게 10배 더 효율적이어야 함

---

## 0. 현황 진단

### 근본 문제: "AI가 직접 코딩하는 게 더 나은 도구"

| 문제 | 영향 | 심각도 |
|------|------|--------|
| 단순 문자열 매칭 (grep 수준) | 검색 누락/오검출 50%+ | 🔴 |
| tree-sitter 미설치 시 regex 폴백으로 전락 | AST 기능 무력화 | 🔴 |
| 파일 I/O 매번 처음부터 스캔 (캐싱 없음) | 대형 프로젝트에서 10초+ | 🔴 |
| 단일 언어(TS/JS)만 AST 지원 | Python/Go/Rust 프로젝트에서 무용지물 | 🟡 |
| 결과 후처리/랭킹 없음 | 관련 없는 결과가 먼저 노출 | 🟡 |
| 오류 발생 시 전체 실패 | 부분 결과도 없이 에러 반환 | 🟡 |
| 동기식 처리로 대기 시간 김 | AI가 빈 응답을 기다리는 시간 낭비 | 🟡 |
| Whiteboard/시각화 연동 없음 | 텍스트로만 결과 반환 | 🟢 |

### 업그레이드 방향

**Before**: 단순 grep → 일차원 텍스트 → AI가 다시 가공해야 쓸모있음
**After**: 구조적 분석 → 풍부한 맥락 → AI가 바로 활용 가능

---

## 1. Core Infrastructure 개선 (모든 도구의 기반)

### 1.1 지능형 파일 시스템 캐시 (FileCache)

**현재**: `_iter_project_files_cached()`는 5초 TTL의 단순 파일 목록 캐시

**업그레이드**:
```python
class FileCache:
    """SOTA 파일 시스템 캐시 — 3계층"""
    
    # L1: 메모리 (파일 내용 + AST 결과) — LRU, max 50 files
    # L2: 디스크 (파일 목록 + 해시) — ~/.vibezoo-cache/catalog.json  
    # L3: 실시간 (fs.watchFile 기반 무효화)
    
    # 특징:
    # - 파일 mtime 기반 자동 무효화
    # - 검색 결과의 체크섬 저장으로 중복 검색 방지
    # - 대형 파일(>5000라인)은 인덱스만 캐싱
    # - Git 변경 파일 우선 스캔
```

**성능 예상**: 반복 검색 100ms → 5ms (20x 개선)

### 1.2 멀티랭귀지 AST 엔진

**현재**: TS/JS만 tree-sitter 지원, 나머지는 regex

**업그레이드**:
```python
class AstEngine:
    """통합 AST 파서 — 7개 언어 지원"""
    
    LANGUAGES = {
        '.ts': 'typescript', '.tsx': 'typescript',
        '.js': 'javascript', '.jsx': 'javascript',
        '.py': 'python',
        '.go': 'go',
        '.rs': 'rust',
        '.java': 'java',
    }
    
    # 각 언어별:
    # - 함수/메서드 정의 추출
    # - 클래스/인터페이스 정의 추출
    # - import/require 문 추출
    # - 함수 호출 그래프 추출
    # - 변수/타입 참조 추출
    
    # tree-sitter 미설치 시 regex 폴백 (But AST 우선)
```

### 1.3 지능형 결과 랭커 (ResultRanker)

**현재**: 단순 priority 정수값

**업그레이드**:
```python
class ResultRanker:
    def rank(self, query, results):
        """BM25 + 시그니처 + 위치 기반 하이브리드 랭킹"""
        score = 0
        score += bm25_similarity(query, result.text) * 0.4  # TF-IDF 유사도
        score += exact_match_bonus * 0.3                     # 정확 매칭 가중치
        score += location_boost * 0.2                        # 정의부 > 사용부
        score += context_density * 0.1                       # 주변 맥락 밀도
        return score
```

---

## 2. Scout 계열 업그레이드 (3개 도구)

### 2.1 `search_codebase` — ★★★ 최우선

**현재**:
- O(n*m) 문자열 비교
- 파일당 500라인 제한
- 단순 priority 정렬

**SOTA 업그레이드**:
```python
@mcp.tool
def search_codebase(query, file_patterns=None, max_results=10, 
                    mode='auto', context_lines=3):
    """
    Args:
        query: 검색어 (자연어 또는 코드)
        file_patterns: 파일 패턴 (예: *.ts,*.py)
        max_results: 최대 결과 (기본 10, 최대 500)
        mode: 'auto' | 'exact' | 'fuzzy' | 'ast' | 'semantic'
        context_lines: 컨텍스트 라인 수 (기본 3)
    """
    # 1. 쿼리 자동 분석 (AST 쿼리? 텍스트 쿼리? 심볼 쿼리?)
    # 2. 멀티 프로세스 병렬 검색 (n=CPU 코어)
    # 3. 결과 하이라이트 + 컨텍스트 + 파일 미리보기
    # 4. BM25 랭킹 + 정확도 점수
    # 5. Crow Memory에 검색 패턴 저장 (반복 검색 최적화)
```

**핵심 차별화**:
- ✅ 자연어 쿼리 지원 ("로그인 함수 찾아줘" → `find_login()`, `loginUser()`, `handleLogin()`)
- ✅ AST 모드: "interface User" → 정확히 인터페이스 정의만 검색
- ✅ Fuzzy 모드: 오타/카멜케이스 불일치 자동 보정
- ✅ 결과에 신뢰도 점수 표시 (90%+만 표시)

### 2.2 `find_references` — 심볼 참조 검색

**현재**: `search_codebase` 래퍼

**SOTA 업그레이드**:
```python
@mcp.tool
def find_references(symbol, file_pattern=None):
    # 1. AST 기반 정확한 정의 찾기
    # 2. 정의 타입에 따른 참조 패턴 분석 (호출? 할당? 타입 참조?)
    # 3. 참조 종류별 그룹화 (read/write/call)
    # 4. 호출 체인 표시 (누가 이 함수를 호출하는지)
```

### 2.3 `summarize_architecture` — 아키텍처 분석

**현재**: 디렉토리명 키워드 기반 레이어 분류

**SOTA 업그레이드**:
```python
@mcp.tool
def summarize_architecture(target_path=None):
    # 1. AST 기반 진입점 + 의존성 + 레이어 자동 발견
    # 2. Mermaid 다이어그램 자동 생성 (draw_on_whiteboard 연동)
    # 3. 기술 부채 진단 (순환 참조, 과도한 의존성, 레이어 위반)
    # 4. 메트릭: 유지보수성 지수, 복잡도, 응집도/결합도
    # 5. 이전 분석과 diff (Crow Memory 활용)
```

---

## 3. Reviewer 계열 업그레이드 (2개 도구)

### 3.1 `review_code` — ★★★ 핵심 도구

**현재**: console.log, TODO, 라인 길이만 체크

**SOTA 업그레이드**:
```python
@mcp.tool
def review_code(file_path, severity='all'):
    # ===== 정적 분석 (Built-in, 외부 도구 불필요) =====
    
    # 1. AST 구조 분석
    #    - 함수 길이/복잡도 (10라인 초과 함수 태깅)
    #    - 중첩 깊이 (4depth 초과 = 리팩터링 권장)
    #    - 매개변수 개수 (4개 초과 = 객체 리터럴 권장)
    
    # 2. 코드 스멜 탐지 (15+ 패턴)
    #    - 매직 넘버/스트링
    #    - 중복 코드 (파일 내 유사 블록)
    #    - 긴 매개변수 목록
    #    - 과도한 조건문 (if/else 체인 → switch 권장)
    #    - 미사용 변수/함수
    #    - null 체인 (a?.b?.c?.d → 중간에 실패하면?)
    #    - 콜백 지옥 (중첩 콜백 3depth+)
    #    - TODO/FIXME 심각도 분류 (SECURITY/BUG/PERF/STYLE)
    
    # 3. 성능 힌트
    #    - O(n²) 연산 발견
    #    - 불필요한 배열 복사
    #    - 메모이제이션 가능 패턴
    
    # 4. 보안 힌트
    #    - SQL 인젝션 가능 패턴
    #    - XSS 취약 패턴
    #    - 하드코딩된 시크릿
```

**차별화**: 외부 도구(ESLint 등)에 의존하지 않고 자체 추진. 단, ESLint가 있으면 통합하여 더 풍부한 결과.

### 3.2 `check_quality` — 품질 검사

**현재**: npx eslint 실행 (없으면 빈 결과)

**SOTA 업그레이드**:
```python
@mcp.tool
def check_quality(target_path=None):
    # 1. 프로젝트 전체 메트릭 수집
    #    - 파일 수, 라인 수, 함수 수, 클래스 수, 주석 밀도
    #    - 테스트 커버리지 (존재하는 테스트 파일 기반 추정)
    #    - 기술 부채 추정 (TODO/FIXME 밀도 + 복잡도)
    
    # 2. 등급 산정 (A-F)
    #    A: 유지보수 용이
    #    B: 양호
    #    C: 개선 필요
    #    D: 주의
    #    F: 대규모 리팩터링 필요
    
    # 3. 90일 트렌드 (Crow Memory)
    #    - 품질 지표 변화 추이
    #    - 많이 실수하는 파일 Top 5
```

---

## 4. Deep Analyzer 계열 업그레이드 (4개 도구)

### 4.1 `analyze_call_graph` — 함수 호출 그래프

**현재**: AST call_expression 단순 추출

**SOTA 업그레이드**:
```python
@mcp.tool
def analyze_call_graph(file_path=None, depth=3, include_external=False):
    # 1. 전체 프로젝트 함수 정의 맵 구축 (캐싱)
    # 2. 호출 그래프 구축 (방향성 그래프)
    # 3. 그래프 메트릭
    #    - Fan-in: 이 함수를 호출하는 곳 (많으면 중요 함수)
    #    - Fan-out: 이 함수가 호출하는 곳 (많으면 복잡)
    #    - 허브: 중앙 노드 (가장 많이 호출되는 함수)
    #    - 리프: 말단 노드
    # 4. 순환 호출 감지 (A→B→C→A)
    # 5. 데드 코드 감지 (호출되지 않는 함수)
    # 6. Mermaid 다이어그램 자동 생성 (draw_on_whiteboard)
```

### 4.2 `map_dependencies` — 의존성 맵

**현재**: AST import 추출 + DFS 순환 참조 탐지

**SOTA 업그레이드**:
```python
@mcp.tool
def map_dependencies(target_path=None):
    # 1. AST 기반 정확한 import 추출 (7개 언어)
    # 2. 패키지 매니저 통합
    #    - package.json → 실제 설치된 버전과 대조
    #    - go.mod, Cargo.toml, requirements.txt
    # 3. 순환 참조 탐지 + 시각화
    # 4. 의존성 건강 진단
    #    - Outdated 패키지
    #    - 미사용 패키지
    #    - 과도한 의존성 (직접 의존 20개 초과)
    # 5. 영향도 분석: "이 파일을 수정하면?"
```

### 4.3 `extract_patterns` — 패턴 분석

**현재**: regex 키워드 카운팅

**SOTA 업그레이드**:
```python
@mcp.tool
def extract_patterns(target_path=None, min_occurrences=3):
    # 1. AST 기반 정확한 패턴 카운팅
    #    - async/await 사용 패턴
    #    - 에러 처리 패턴 (try-catch vs .catch() vs if-error)
    #    - 상태 관리 패턴 (useState, useReducer, Redux, Zustand)
    #    - 의존성 주입 패턴
    #    - 테스트 패턴 (describe/it 스타일)
    
    # 2. 코드 스타일 일관성 분석
    #    - 함수 선언 스타일 (function vs const = () =>)
    #    - import 스타일 (named vs default)
    #    - 네이밍 컨벤션 (camelCase vs snake_case)
    
    # 3. 프로젝트 전체 통계
    #    - 가장 많이 사용된 라이브러리 함수 Top 10
    #    - 가장 많이 등장한 에러 처리 패턴
```

### 4.4 `reverse_engineer` — 리버스 엔지니어링

**현재**: regex API 추출 + AST 필드 추출

**SOTA 업그레이드**:
```python
@mcp.tool
def reverse_engineer(target_path=None, output_format='markdown'):
    # 1. API 완전 분석
    #    - Express/FastAPI/Flask/Gin 엔드포인트 + 미들웨어
    #    - Request/Response 타입 자동 연결
    #    - 에러 응답 패턴 분석
    
    # 2. 데이터 모델 관계 분석 (ERD)
    #    - AST 기반 모든 모델/인터페이스 추출
    #    - 필드 타입 + nullable + 기본값
    #    - 모델 간 관계 추론 (foreign key 패턴)
    #    - Mermaid ERD 생성
    
    # 3. OpenAPI 3.0 스펙 자동 생성
    #    - 실제 코드 기반 (추측 아님)
    #    - 예제 값 포함 (테스트 데이터 기반)
    #    - 에러 응답 스키마 포함
```

---

## 5. Tester 계열 업그레이드 (2개 도구)

### 5.1 `generate_tests` — 테스트 생성

**현재**: 함수 시그니처만 추출하고 빈 템플릿 생성

**SOTA 업그레이드**:
```python
@mcp.tool
def generate_tests(source_path, framework='auto'):
    # 1. 함수 분석
    #    - 입력 타입 → 경계값 테스트 케이스 생성
    #    - 조건문 분기 → 모든 브랜치 커버하는 테스트
    #    - 에러 처리 → 에러 케이스 테스트
    #    - 비동기 코드 → 타이밍 이슈 테스트
    
    # 2. 실제 mock 데이터 생성
    #    - 타입 정보 기반 실제 값 생성
    #    - 기존 테스트에서 사용된 fixture 재활용
    
    # 3. 테스트 품질 평가
    #    - 예상 커버리지 추정
    #    - 놓친 엣지 케이스 제안
```

### 5.2 `analyze_coverage` — 커버리지 분석

**현재**: 테스트 파일 존재 비율만 체크

**SOTA 업그레이드**:
```python
@mcp.tool
def analyze_coverage(target_path=None):
    # 1. 테스트/소스 매핑 (어느 소스에 어느 테스트?)
    # 2. 누락된 테스트 감지 (테스트 없는 중요 함수)
    # 3. 테스트 품질 메트릭
    #    - describe/it 비율
    #    - assertion 수
    #    - Mock 사용 패턴
    # 4. 커버리지 갭 분석 (Crow Memory 이력 기반)
```

---

## 6. Fix Loop 계열 업그레이드 (3개 도구)

### 6.1 `auto_fix_status` — 자동 수정 상태

**현재**: fix request 파일 JSON 읽기

**SOTA 업그레이드**:
```python
@mcp.tool
def auto_fix_status():
    # 1. 현재 빌드 에러의 근본 원인 분석
    #    - 에러 메시지에서 핵심 식별자 추출
    #    - 관련 코드 검색 (search_codebase)
    #    - 유사 과거 에러 패턴 조회 (Crow bug register)
    
    # 2. 수정 우선순위 제안
    #    - P0: 빌드 브레이커
    #    - P1: 타입 에러
    #    - P2: 린트 경고
```

### 6.2 `retry_build` — 빌드 재시도

**현재**: tsc --noEmit 실행

**SOTA 업그레이드**: 
전체 빌드 파이프라인 이해 필요, 현재 구조 유지

### 6.3 `check_intervention` — 사용자 개입 확인

**현재**: Whiteboard + Chat 메시지 확인

**SOTA 업그레이드**:
사용자 의도 추론 추가 (단순 메시지 존재 여부 → 의도 분석)

---

## 7. 시나리오 통합 도구 업그레이드 (4개 도구)

### 7.1 `review_project` — 프로젝트 리뷰

**현재**: 개별 도구 순차 호출 후 결합

**업그레이드**: 각 단계 결과를 상호 참조하여 더 깊은 인사이트 도출

### 7.2 `find_bugs` — 버그 찾기

**현재**: 의심 패턴 리스트 + Crow recall

**업그레이드**:
- 인터-파일 분석 (A 파일에서 수정한 내용이 B 파일에 영향)
- 데이터 흐름 분석 (undefined 전파 추적)

### 7.3 `suggest_refactor` — 리팩터링 제안

**현재**: deps + patterns + callgraph

**업그레이드**:
- 구체적인 리팩터링 액션 아이템 (파일:라인 레벨)
- 리팩터링 난이도/영향도 평가
- Before/After 코드 예시

### 7.4 `generate_docs` — 문서 생성

**현재**: arch + reverse + whiteboard diagram

**업그레이드**:
- 코드 변경사항 자동 반영 (Crow Memory 기반)
- 문서 버전 관리
- 누락된 문서 감지

---

## 8. 분석 도구 업그레이드 (4개 도구)

### 8.1 `explain_code` — 코드 설명

**현재**: 단순 라인 타입 분류 (import, function, class...)

**SOTA 업그레이드**:
```python
@mcp.tool
def explain_code(file_path, line_number):
    # 1. AST 깊은 분석
    #    - 해당 라인이 속한 함수/클래스/블록의 완전한 AST 컨텍스트
    #    - 변수의 타입/범위/수명 추적
    #    - 호출 체인: "이 함수는 X에서 호출되며, Y를 반환"
    
    # 2. 데이터 흐름
    #    - "이 변수는 여기서 선언되어 저기서 사용됨"
    #    - "이 값은 A→B→C를 거쳐 여기로 전달됨"
    
    # 3. 의도 추론
    #    - "이 코드는 JWT 토큰을 검증하는 미들웨어"
    #    - "이 패턴은 Rate Limiting을 구현"
    
    # 4. 관련 문서/커밋 연결 (git blame)
```

### 8.2 `analyze_changes` — 변경 분석

**현재**: git diff + Crow context

**SOTA 업그레이드**:
- 변경 영향도 분석 (이 파일이 바뀌면 어디가 영향받는지)
- 변경 유형 분류 (리팩터링/버그픽스/피쳐/문서)
- 리뷰 포인트 자동 추출

### 8.3 `review_pr` — PR 리뷰

**현재**: diff + review_code 조합

**SOTA 업그레이드**:
- 변경된 파일 간 의존성 분석
- 롤백 위험도 평가
- 테스트 누락 감지

### 8.4 `refactor_across_files` — 멀티파일 리팩터링

**현재**: 텍스트 치환 제안

**SOTA 업그레이드**:
- AST 기반 정확한 심볼 치환 (텍스트 치환 아님)
- 변경 영향도 미리 분석
- 단계별 마이그레이션 플랜

---

## 9. 지식/선호도 도구 (4개 도구)

### 9.1 `learn_project` — 프로젝트 학습

**현재**: arch + patterns + deps → Crow 저장

**업그레이드**: 델타 업데이트 (전체 재저장 → 변경분만 저장)

### 9.2 `recall_project` — 프로젝트 회상

**현재**: Crow recall 결과 표시

**업그레이드**: 다중 소스 회상 (Crow + 로컬 파일 + git history)

### 9.3 `learn_preference` / `get_preferences` — 선호도

현재 구조로 충분, Crow Memory life_context 활용 강화

---

## 10. 구현 우선순위

### Phase 1 (즉시 효과) — 1일
| 순위 | 도구 | 예상 효과 |
|:----:|:----|:---------:|
| 1 | `search_codebase` | 검색 정확도 10x↑, 속도 5x↑ |
| 2 | `review_code` | 발견 이슈 10x↑, 거짓 경고 90%↓ |
| 3 | `explain_code` | 코드 이해도 100x↑ |

### Phase 2 (핵심 가치) — 3일
| 순위 | 도구 | 예상 효과 |
|:----:|:----|:---------:|
| 4 | `map_dependencies` | 의존성 파악 시간 90%↓ |
| 5 | `analyze_call_graph` | 호출 관계 시각화 |
| 6 | `reverse_engineer` | 문서화 시간 95%↓ |

### Phase 3 (완성도) — 5일
| 순위 | 도구 | 예상 효과 |
|:----:|:----|:---------:|
| 7 | `generate_tests` | 테스트 작성 시간 80%↓ |
| 8 | `find_references` | 참조 정확도 90%↑ |
| 9 | `summarize_architecture` | 온보딩 시간 90%↓ |

---

## 11. 측정 가능한 목표 (KPI)

| 메트릭 | 현재 | Phase 1 | Phase 2 | Phase 3 |
|--------|:----:|:-------:|:-------:|:-------:|
| 도구 호출당 평균 결과 품질 (1-10) | 2 | 6 | 8 | 9 |
| 검색 정확도 (Precision@10) | 30% | 80% | 90% | 95% |
| 리뷰당 발견 이슈 수 | 3 | 15 | 25 | 30+ |
| 거짓 경고 비율 | 60% | 20% | 10% | 5% |
| AI가 도구 선호도 (직접 코딩 vs 도구) | 직접 코딩 | 도구 우선 | 도구 90% | 도구 99% |
