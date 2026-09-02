# Project Research Report — VibeZoo 기능 쓸모 평가 (Utility Audit)

## Task Summary
"이 도구는 순전히 AI들을 위해 만들어진 것"이라는 사용자 기준으로, VibeZoo의 모든 MCP 툴(45개 등록), VS Code 커맨드(31개), UI 표면(10개)의 실제 쓸모를 정량 평가. 각 기능에 대해 4가지 기준(A~D)으로 채점하고, KEEP/MERGE/DELETE 판정을 내림.

## 평가 기준
- **A. AI 워크플로우 필수성**: AI가 실제로 이 툴을 호출해야만 하는가? (빌트인 기능/다른 툴로 대체 가능 여부)
- **B. 동작 현실성**: 코드상 실제로 작동하는가? (의존성, 옵션, 고장 상태)
- **C. 중복도**: 같은 역할을 하는 MCP 툴/커맨드/UI가 존재하는가?
- **D. 유지비용**: 의존성/버그면/코드 량 대비 가치

## 판정 기준
- **KEEP**: 필수적이거나 유니크한 기능
- **MERGE**: 중복 기능 → 통합 후보 (이번 세션에는 기록만)
- **DELETE**: 쓸모없음 (명백한 것만)

---

# Part 1: MCP 툴 평가 (45개)

## 1.1 탐색/검색 (Scout 모듈)

### `search_codebase`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🔴 높음 — ripgrep/git grep + embedding 시맨틱 랭킹 조합. AI 빌트인 search로 부분 대체 가능하나 시맨틱 모드는 유니크 |
| **B. 동작현실성** | ✅ 동작 (ripgrep 미설치 시 os.walk 폴백, embedding 서버 미실행 시 키워드 검색으로 degraded) |
| **C. 중복도** | 🟡 VS Code `search_files`, AI 빌트인 `codebase_search`와 기능 겹침. 그러나 시맨틱 모드는 유니크 |
| **D. 유지비용** | 🟡 ~300줄, ripgrep/embedding_client/file_cache/result_ranker 의존 |
| **판정** | **KEEP** — 시맨틱 검색 모드가 유니크 가치 |

### `find_references`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 심볼 참조 검색. AI가 search_files로 유사 동작 가능 |
| **B. 동작현실성** | ✅ 동작 (ripgrep 기반) |
| **C. 중복도** | 🟠 `search_codebase` + VS Code 'Find All References'로 대체 가능 |
| **D. 유지비용** | 🟢 ~90줄, 가벼움 |
| **판정** | **KEEP** — 경량이고 불필요한 오버헤드 없음. 편의성 제공 |

### `summarize_architecture`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 프로젝트 구조 요약. AI가 직접 분석 가능하나 통합 자동화 가치 있음 |
| **B. 동작현실성** | ✅ 동작 (map_dependencies + git log 통합) |
| **C. 중복도** | 🟠 `review_project(mode="summary")`와 기능 겹침 |
| **D. 유지비용** | 🟡 ~200줄 |
| **판정** | **MERGE** → `review_project(mode="summary")`에 통합 후보. 별도 툴로서도 KEEP 가능 |

### `embedding_health_check`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 임베딩 서버 상태 확인은 AI가 직접 할 수 없는 인프라 체크 |
| **B. 동작현실성** | ✅ 동작 (HTTP probing) |
| **C. 중복도** | 🟢 없음 — 유니크 |
| **D. 유지비용** | 🟢 ~20줄, 매우 가벼움 |
| **판정** | **KEEP** |

### `rebuild_code_index`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 인덱스 리빌드는 인프라 작업으로 AI 직접 불가 |
| **B. 동작현실성** | ✅ 동작 (CodeIndexCache.rebuild) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟢 ~20줄 |
| **판정** | **KEEP** |

---

## 1.2 코드 리뷰 (Reviewer 모듈)

### `review_code`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — AST 기반 복잡도/중첩/언어별 특화 규칙(Rust unsafe, Go 고루틴 등)은 AI가 빌트인으로 수행 불가 |
| **B. 동작현실성** | ✅ 동작 (TS/JS/Python/Go/Rust/C++/Shell/YAML/JSON/Dockerfile 지원) |
| **C. 중복도** | 🟢 없음 — 유니크한 다국어 리뷰 규칙 |
| **D. 유지비용** | 🟠 ~1000줄로 큼. 언어별 규칙 확장 시 비용 증가 |
| **판정** | **KEEP** — 다국어 AST 리뷰는 핵심 가치 |

---

## 1.3 분석 (Analysis 모듈)

### `explain_code`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🔴 낮음 — [analysis.py#L231](mcp-servers/bridge/tools/analysis.py#L231)에서 `TOOL_CONTEXT: 설명에 필요한 데이터 수집 완료. LLM은 이 데이터로 종합 설명 생성`이라고 명시. 즉, **도구가 설명을 생성하는 게 아니라 AI에게 데이터를 주고 설명하라고 시키는 것**. AI는 이미 read_file + AST로 같은 설명 가능 |
| **B. 동작현실성** | ✅ 동작 (AST 파싱, git blame, 관련 테스트 검색) |
| **C. 중복도** | 🔴 AI 빌트인 read_file + codebase_search로 90% 대체 가능. git blame 컨텍스트만 유니크하나 가치 낮음 |
| **D. 유지비용** | 🟠 ~230줄 (analysis.py 내 최대 함수) |
| **판정** | **DELETE** — "AI에게 설명을 시키는" 구조. AI가 직접 파일을 읽고 분석하는 게 효율적 |

### `analyze_changes`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — git diff 분석. AI가 `execute_command("git diff")`로 직접 가능 |
| **B. 동작현실성** | ✅ 동작 (subprocess로 git diff 실행 + Crow 컨텍스트) |
| **C. 중복도** | 🟠 AI 빌트인 execute_command + git으로 대체 가능 |
| **D. 유지비용** | 🟡 ~100줄 |
| **판정** | **DELETE** — AI가 `git diff --stat && git diff`를 직접 실행하는 게 더 효율적 |

### `review_pr`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — PR 리뷰 자동화. git diff + review_code 통합 |
| **B. 동작현실성** | ✅ 동작 (review_code 내부 호출 + 의존성 분석 + 롤백 리스크) |
| **C. 중복도** | 🟡 git diff + review_code 조합. 통합 편의성 있음 |
| **D. 유지비용** | 🟡 ~170줄 |
| **판정** | **MERGE** → GitHub MCP의 PR 리뷰 기능과 통합 후보. 현재는 **KEEP** |

### `refactor_across_files`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 멀티파일 리팩토링. AST-aware rename 유니크 |
| **B. 동작현실성** | ✅ 동작 (search_codebase + AST rename + .bak 백업) |
| **C. 중복도** | 🟡 VS Code Find-and-Replace + AI 빌트인 도구로 부분 대체 가능 |
| **D. 유지비용** | 🟡 ~130줄 |
| **판정** | **KEEP** — AST-aware rename은 유니크 가치 |

---

## 1.4 딥 분석 (Deep Analyzer 모듈)

### `analyze_call_graph`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — AST 기반 fan-in/fan-out/데드 코드 탐지. AI가 직접 대규모 프로젝트에서 수행 어려움 |
| **B. 동작현실성** | ✅ 동작 (tree-sitter AST 기반) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟡 ~150줄 |
| **판정** | **KEEP** |

### `map_dependencies`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 순환 참조 탐지 + 영향도 분석. 인프라 수준 분석 |
| **B. 동작현실성** | ✅ 동작 (AST import 추출 + cycle detection) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟡 ~140줄 |
| **판정** | **KEEP** |

### `extract_patterns`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — AST 서브트리 매칭 기반 코드 패턴 탐지. AI가 직접 large-scale로 수행 어려움 |
| **B. 동작현실성** | ✅ 동작 (11개 패턴 템플릿, regex 폴백) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟡 ~170줄 (패턴 템플릿 포함) |
| **판정** | **KEEP** |

### `reverse_engineer`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — API 엔드포인트 + 데이터 모델 추출. 유용하나 자주 호출 안 됨 |
| **B. 동작현실성** | ✅ 동작 (AST 기반 필드 추출 + OpenAPI/Mermaid 출력) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟡 ~190줄 |
| **판정** | **KEEP** |

---

## 1.5 테스트 (Tester 모듈)

### `generate_tests`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 테스트 스캐폴딩 생성. AI가 직접 작성 가능 |
| **B. 동작현실성** | ✅ 동작 (AST 기반 함수 감지 + mock 제안) |
| **C. 중복도** | 🟡 AI 빌트인으로 직접 테스트 작성 가능 |
| **D. 유지비용** | 🟠 ~270줄 |
| **판정** | **DELETE** — AI가 직접 read_file + 코드 분석으로 더 정확한 테스트 생성 가능. 스캐폴딩은 AI 빌트인 역할 |

### `analyze_coverage`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 파일 기반 커버리지 분석. 실제 커버리지 도구(vitest/pytest --cov) 실행은 별도 |
| **B. 동작현실성** | ✅ 동작 (파일명 매칭 기반, vitest/pytest 폴백) |
| **C. 중복도** | 🟡 vitest/pytest --cov 직접 실행으로 대체 가능 |
| **D. 유지비용** | 🟡 ~130줄 |
| **판정** | **DELETE** — AI가 직접 `pytest --cov` 실행이 더 정확 |

---

## 1.6 통합/컴포지트 (Integrated 모듈)

### `review_project`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — review_code + check_quality + extract_patterns 통합. 자동화 편의성 |
| **B. 동작현실성** | ✅ 동작 (summary/full 모드) |
| **C. 중복도** | 🟠 개별 도구组合. 통합 자체는 가치 있으나 개별 도구와 중복 |
| **D. 유지비용** | 🟠 ~240줄 (개별 도구 의존) |
| **판정** | **KEEP** — 프로젝트 전체 리뷰 자동화는 유니크 |

### `find_bugs`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 패턴 + 검색 + ESLint/tsc + Crow 통합 |
| **B. 동작현실성** | ✅ 동작 (native linter 통합, summary/full 모드) |
| **C. 중복도** | 🟡 개별 도구组合 |
| **D. 유지비용** | 🟠 ~250줄 |
| **판정** | **KEEP** — ESLint/tsc/native linter 통합은 유니크 |

### `suggest_refactor`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — deps + patterns + call graph 통합 |
| **B. 동작현실성** | ✅ 동작 (summary/full 모드) |
| **C. 중복도** | 🟠 개별 도구组合 |
| **D. 유지비용** | 🟡 ~130줄 |
| **판정** | **KEEP** |

### `generate_docs`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 아키텍처 문서 자동 생성 |
| **B. 동작현실성** | ✅ 동작 (reverse_engineer + summarize_architecture + whiteboard) |
| **C. 중복도** | 🟠 개별 도구组合 |
| **D. 유지비용** | 🟡 ~150줄 |
| **판정** | **KEEP** |

---

## 1.7 파일 분석 (File Analyzer 모듈)

### `analyze_uploaded_file`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 파일 타입별 분석 파이프라인 (이미지→SSA→OCR→MiniCPM, 코드→미리보기, PDF→텍스트 추출). AI가 직접 pip install 없이 수행 불가 |
| **B. 동작현실성** | 🟡 선택적 의존성 (PyMuPDF, OpenCV, MiniCPM) 미설치 시 degraded |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟠 ~360줄 |
| **판정** | **KEEP** — 바이너리/이미지/PDF 분석은 유니크 |

---

## 1.8 화이트보드 (Whiteboard 모듈)

### `check_uploaded_files`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 드롭존 업로드 파일 목록 조회 |
| **B. 동작현실성** | ✅ 동작 |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟢 ~60줄 |
| **판정** | **KEEP** |

### `capture_screen`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 화면 캡처/드롭존 열기/파일 선택기 |
| **B. 동작현실성** | ✅ 동작 (Extension Webview 연동) |
| **C. 중복도** | 🟡 `openDropzone` 커맨드와 기능 겹침 |
| **D. 유지비용** | 🟡 ~100줄 |
| **판정** | **KEEP** — MCP에서 드롭존을 열 수 있는 유일한 경로 |

### `draw_on_whiteboard`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — AI가 화이트보드에 다이어그램을 그리는 유일한 경로 |
| **B. 동작현실성** | ✅ 동작 (Fabric.js JSON → Webview) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟡 ~150줄 |
| **판정** | **KEEP** |

### `get_whiteboard_state`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 화이트보드 상태를 LLM-readable 텍스트로 변환. AI가 직접 Webview JSON을 해석 불가 |
| **B. 동작현실성** | ✅ 동작 (WhiteboardDataConverter) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟡 ~80줄 |
| **판정** | **KEEP** |

---

## 1.9 SSA (Spatial Statistics Analysis)

### `aggregate_spatial_pixels`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 이미지的空间 통계 분석 + OCR 통합. AI 빌트인으로 이미지 분석 불가 |
| **B. 동작현실성** | 🟡 OpenCV 필요. 미설치 시 에러 반환. OCR도 선택적 |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟠 ~830줄 (가장 큰 모듈 중 하나) |
| **판정** | **KEEP** — 이미지 분석은 유니크 |

---

## 1.10 Fix Loop (Fix Loop 모듈)

### `auto_fix_status`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — Fix Loop 세션 상태 조회 (파일 기반 상태 관리) |
| **B. 동작현실성** | ✅ 동작 |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟢 ~45줄 |
| **판정** | **KEEP** |

### `retry_build`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 빌드 재시도 + 에러 추출. AI가 직접 subprocess로 가능하나 구조화된 에러 출력 유용 |
| **B. 동작현실성** | ✅ 동작 (multi-language 에러 추출) |
| **C. 중복도** | 🟡 AI가 직접 `tsc --noEmit` 실행 가능 |
| **D. 유지비용** | 🟡 ~120줄 |
| **판정** | **KEEP** — 구조화된 에러 추출은 유용 |

### `check_intervention`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 화이트보드/채팅 메시지로 사용자 개입 확인 |
| **B. 동작현실성** | ✅ 동작 |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟢 ~50줄 |
| **판정** | **KEEP** |

---

## 1.11 지식/메모리 (Knowledge 모듈)

### `learn_project`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 프로젝트 분석 결과를 Crow Memory에 축적. AI 빌트인으로 장기 기억 불가 |
| **B. 동작현실성** | ✅ 동작 (자동 learn_project 스케줄 포함) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟡 ~100줄 |
| **판정** | **KEEP** |

### `recall_project`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — Crow에서 프로젝트 지식 회상 |
| **B. 동작현실성** | ✅ 동작 |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟢 ~55줄 |
| **판정** | **KEEP** |

### `learn_preference`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 코딩 선호도 저장 (로컬 파일 + Crow Memory) |
| **B. 동작현실성** | ✅ 동작 |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟢 ~65줄 |
| **판정** | **KEEP** |

### `get_preferences`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 저장된 선호도 조회 |
| **B. 동작현실성** | ✅ 동작 |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟢 ~60줄 |
| **판정** | **KEEP** |

---

## 1.12 UX 코디네이터 (UX Coordinator 모듈)

### `ux_coordinator`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 의도 감지 + 워크플로우 제안. AI가 직접 같은 판단 가능 |
| **B. 동작현실성** | ✅ 동작 (intent_detector 연동) |
| **C. 중복도** | 🟠 AI가 직접 같은 의도 분석 가능 |
| **D. 유지비용** | 🟡 ~75줄 + intent_detector.py 의존 |
| **판정** | **DELETE** — AI가 직접 intent를 파악하고 tool chain을 결정하는 게 더 효율적. 이 도구는 "AI에게 제안하는" 구조로, AI 자체가 이미 그 역할 수행 |

### `auto_analyze_after_drop`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — 드롭존 업로드 후 자동 분석. 실제 분석은 다른 도구에 위임 |
| **B. 동작현실성** | ✅ 동작 (파일 타입 감지 + 분석 파이프라인 제안) |
| **C. 중복도** | 🟡 `analyze_uploaded_file` + `aggregate_spatial_pixels` 조합 |
| **D. 유지비용** | 🟡 ~130줄 |
| **판정** | **DELETE** — AI가 `analyze_uploaded_file()`을 직접 호출하는 게 더 효율적. "무엇을 할지 제안하는" 도구는 AI 자체 역할과 중복 |

### `auto_analyze_whiteboard`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🔴 없음 — 코드상 `[DEPRECATED]` 명시. `get_whiteboard_state(analyze=True)`로 대체 |
| **B. 동작현실성** | ✅ 동작하나 deprecated |
| **C. 중복도** | 🔴 `get_whiteboard_state(analyze=True)`와 100% 동일 |
| **D. 유지비용** | 🟢 ~20줄 |
| **판정** | **DELETE** — 명시적 deprecated + 대체 도구 존재 |

---

## 1.13 피드백 (Feedback 모듈)

### `vibezoo_feedback`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — AI가 자율적으로 개선 제안. 유니크한 역할이나 실질 사용 빈도 불명 |
| **B. 동작현실성** | ✅ 동작 (JSONL 파일 쓰기) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟢 ~50줄 |
| **판정** | **KEEP** — AI 자율 피드백은 유니크 |

---

## 1.14 웹 (Web 모듈)

### `fetch_page`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 웹 페이지를 markdown으로 변환. AI 빌트인으로 웹페이지 직접 접근 불가 |
| **B. 동작현실성** | ✅ 동작 (urllib + _html_to_markdown) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟡 ~65줄 |
| **판정** | **KEEP** |

### `web_search`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 웹 검색. Exa neural search + DuckDuckGo 폴백 |
| **B. 동작현실성** | ✅ 동작 (Exa API 키 없으면 DDG 폴백) |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟡 ~110줄 |
| **판정** | **KEEP** |

---

## 1.15 편집 (Editor 모듈)

### `apply_patch`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — SEARCH/REPLACE 패치. VS Code의 `edit` 도구와 유사 |
| **B. 동작현실성** | ✅ 동작 (fuzzy 매칭, AST ellipsis 검증, 트랜잭셔널 롤백, 자동 백업) |
| **C. 중복도** | 🟡 VS Code `edit` 도구와 기능 겹침 |
| **D. 유지비용** | 🟠 ~620줄 (가장 큰 모듈) |
| **판정** | **DELETE** — VS Code의 `edit`/`apply_diff` 도구가 동일 기능 제공. fuzzy 매칭, ellipsis 검증 등은 과도한 오버엔지니어링. AI가 직접 read → search/replace하는 게 더 안전 |

---

## 1.16 설정 (Setup 모듈)

### `vibezoo_setup`
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟢 높음 — 통합 설치 도구 (pip, 시스템 패키지, MCP 설정, Zoo 설정, 모델 다운로드). 설치 자동화는 AI 빌트인으로 불가 |
| **B. 동작현실성** | ✅ 동작 |
| **C. 중복도** | 🟢 없음 |
| **D. 유지비용** | 🟠 ~400줄 (큰 모듈) |
| **판정** | **KEEP** |

---

## 1.17 GitHub (GitHub Diver 모듈) — ⚠️ 미등록!

### `explore_github` (github_diver.py)
| 항목 | 평가 |
|------|------|
| **A. 필수성** | 🟡 중간 — GitHub 저장소 탐색. 현재 GitHub MCP 서버와 100% 중복 |
| **B. 동작현실성** | 🔴 **미등록** — `__init__.py`에 import/register 없음. 호출 불가 |
| **C. 중복도** | 🔴 GitHub MCP 서버(15개 도구: search_repositories, get_file_contents 등)와 완전 중복 |
| **D. 유지비용** | 🟡 ~200줄. stale 함수명 참조 2건 (`github_explore_repository`, `github_read_file`) |
| **판정** | **DELETE** — 미등록 + GitHub MCP와 중복. 파일 전체 삭제 대상 |

---

## MCP 툴 요약 통계

| 판정 | 개수 | 툴 목록 |
|------|------|---------|
| **KEEP** | 34 | search_codebase, find_references, embedding_health_check, rebuild_code_index, review_code, analyze_call_graph, map_dependencies, extract_patterns, reverse_engineer, review_project, find_bugs, suggest_refactor, generate_docs, analyze_uploaded_file, check_uploaded_files, capture_screen, draw_on_whiteboard, get_whiteboard_state, aggregate_spatial_pixels, auto_fix_status, retry_build, check_intervention, learn_project, recall_project, learn_preference, get_preferences, vibezoo_feedback, fetch_page, web_search, vibezoo_setup, review_pr, refactor_across_files, summarize_architecture |
| **MERGE** | 0 | (기록만, 이번 세션 미실행) |
| **DELETE** | 7 | explain_code, analyze_changes, generate_tests, analyze_coverage, ux_coordinator, auto_analyze_after_drop, auto_analyze_whiteboard, apply_patch, explore_github |

> 참고: DELETE는 총 9개 (explain_code, analyze_changes, generate_tests, analyze_coverage, ux_coordinator, auto_analyze_after_drop, auto_analyze_whiteboard, apply_patch, explore_github)

---

# Part 2: VS Code 커맨드 평가 (31개)

## 2.1 기능 커맨드 (실제 로직 존재)

| # | 커맨드 ID | 판정 | 근거 |
|---|-----------|------|------|
| 1 | `vibezoo.selfCheck` | **KEEP** | [extension.ts#L618](extension/src/extension.ts#L618) — 시스템 자가진단, 실제 로직 |
| 2 | `vibezoo.verifyFoundation` | **KEEP** | [extension.ts#L369](extension/src/extension.ts#L369) — 진단 실행 |
| 3 | `vibezoo.reconnectCrow` | **KEEP** | [extension.ts#L403](extension/src/extension.ts#L403) — Crow 재연결 |
| 4 | `vibezoo.instantRewind` | **KEEP** | [extension.ts#L324](extension/src/extension.ts#L324) — Yocto 스냅샷 복원 |
| 5 | `vibezoo.toggleYolo` | **KEEP** | [extension.ts#L342](extension/src/extension.ts#L342) — YOLO 모드 토글 |
| 6 | `vibezoo.scanProject` | **KEEP** | [extension.ts#L356](extension/src/extension.ts#L356) — 프로젝트 트리 스캔 |
| 7 | `vibezoo.openWhiteboard` | **KEEP** | [extension.ts#L419](extension/src/extension.ts#L419) — 화이트보드 Webview |
| 8 | `vibezoo.openUIPreview` | **KEEP** | [extension.ts#L426](extension/src/extension.ts#L426) — UI 프리뷰 |
| 9 | `vibezoo.openDashboard` | **KEEP** | [extension.ts#L433](extension/src/extension.ts#L433) — 오케스트라 대시보드 |
| 10 | `vibezoo.openDropzone` | **KEEP** | [extension.ts#L440](extension/src/extension.ts#L440) — 드롭존 |
| 11 | `vibezoo.showSessionResume` | **KEEP** | [extension.ts#L518](extension/src/extension.ts#L518) — 세션 복원 |
| 12 | `vibezoo.toggleGuardGit` | **KEEP** | [extension.ts#L577](extension/src/extension.ts#L577) — Guard.git |
| 13 | `vibezoo.openErrorDashboard` | **KEEP** | [extension.ts#L447](extension/src/extension.ts#L447) — 에러 대시보드 |
| 14 | `vibezoo.configureErrorDashboard` | **KEEP** | [extension.ts#L455](extension/src/extension.ts#L455) — 에러 대시보드 설정 |
| 15 | `vibezoo.startWatching` | **KEEP** | [extension.ts#L654](extension/src/extension.ts#L654) — CIM 시작 |
| 16 | `vibezoo.stopWatching` | **KEEP** | [extension.ts#L662](extension/src/extension.ts#L662) — CIM 중지 |
| 17 | `vibezoo.pauseFixLoop` | **KEEP** | [extension.ts#L735](extension/src/extension.ts#L735) — FixLoop 일시중지 |
| 18 | `vibezoo.resumeFixLoop` | **KEEP** | [extension.ts#L742](extension/src/extension.ts#L742) — FixLoop 재개 |
| 19 | `vibezoo.abortFixLoop` | **KEEP** | [extension.ts#L749](extension/src/extension.ts#L749) — FixLoop 중단 |
| 20 | `vibezoo.showAgentInfo` | **KEEP** | [extension.ts#L506](extension/src/extension.ts#L506) — 에이전트 정보 |
| 21 | `vibezoo.showHelp` | **KEEP** | [extension.ts#L528](extension/src/extension.ts#L528) — 도움말 |

## 2.2 "채팅 안내" 커맨드 (showInformationMessage만, MCP 툴 안내)

| # | 커맨드 ID | 판정 | 근거 |
|---|-----------|------|------|
| 22 | `vibezoo.reviewProject` | **DELETE** | [extension.ts#L386](extension/src/extension.ts#L386) — "Please type \"review project\" in chat" |
| 23 | `vibezoo.findBugs` | **DELETE** | [extension.ts#L391](extension/src/extension.ts#L391) — "Please type \"find bugs\" in chat" |
| 24 | `vibezoo.suggestRefactor` | **DELETE** | [extension.ts#L396](extension/src/extension.ts#L396) — "Please type \"refactor\" in chat" |
| 25 | `vibezoo.generateDocs` | **DELETE** | [extension.ts#L401](extension/src/extension.ts#L401) — "Please type \"generate docs\" in chat" |
| 26 | `vibezoo.explainCode` | **DELETE** | [extension.ts#L670](extension/src/extension.ts#L670) — "Please type \"explain code\" in chat" |
| 27 | `vibezoo.analyzeChanges` | **DELETE** | [extension.ts#L677](extension/src/extension.ts#L677) — "Please type \"analyze changes\" in chat" |
| 28 | `vibezoo.reviewPR` | **DELETE** | [extension.ts#L684](extension/src/extension.ts#L684) — "Please type \"review PR\" in chat" |
| 29 | `vibezoo.refactorAcrossFiles` | **DELETE** | [extension.ts#L691](extension/src/extension.ts#L691) — "Please type \"refactor\" in chat" |
| 30 | `vibezoo.learnProject` | **DELETE** | [extension.ts#L698](extension/src/extension.ts#L698) — "Please type \"learn project\" in chat" |
| 31 | `vibezoo.recallProject` | **DELETE** | [extension.ts#L705](extension/src/extension.ts#L705) — "Please type \"recall project\" in chat" |
| 32 | `vibezoo.learnPreference` | **DELETE** | [extension.ts#L712](extension/src/extension.ts#L712) — "Please type \"learn preference\" in chat" |
| 33 | `vibezoo.getPreferences` | **DELETE** | [extension.ts#L719](extension/src/extension.ts#L719) — "Please type \"show preferences\" in chat" |
| 34 | `vibezoo.rebuildCodeIndex` | **DELETE** | [extension.ts#L726](extension/src/extension.ts#L726) — "Please type \"rebuild\" in chat" |

---

# Part 3: UI 표면 평가 (10개)

| # | UI 요소 | 판정 | 근거 |
|---|---------|------|------|
| 1 | Activity Bar 사이드바 | **KEEP** | VibeZoo 접근 메인 진입점. TreeView 3개 호스팅 |
| 2 | Active Subagents 트리뷰 | **KEEP** | 서브에이전트 상태 모니터링. AI 에이전트 워크플로우에 필수 |
| 3 | YOLO History 트리뷰 | **KEEP** | Instant Rewind 스냅샷 기록. 복원 메뉴 제공 |
| 4 | Session Resume 트리뷰 | **KEEP** | 세션 복원 정보. 실용적 기능 |
| 5 | StatusBar 아이템 | **KEEP** | Crow 연결 상태, CIM 모드, 상태 표시. 필수 피드백 채널 |
| 6 | Whiteboard Webview | **KEEP** | AI-사용자 간 시각적 협업 채널. 유니크 |
| 7 | UI Preview Webview | **KEEP** | React/Vue 미리보기. 개발 워크플로우 기여 |
| 8 | Error Dashboard Webview | **KEEP** | 에러 수집/시각화. 유틸리티 높음 |
| 9 | Editor Context 메뉴 (4개) | **DELETE** | [package.json#L384-L399](extension/package.json#L384-L399) — "채팅 안내" 커맨드 호출. 위 2.2 커맨드와 함께 삭제 대상 |
| 10 | Keybindings (3개) | **KEEP** | Ctrl+Shift+R/Z/B — 실용적 단축키 |

---

# Part 4: DELETE 목록 (영향파일 완전 명시)

## 4.1 MCP 툴 DELETE (9개)

### 1. `explain_code` (analysis.py)
- **파일**: [`mcp-servers/bridge/tools/analysis.py`](mcp-servers/bridge/tools/analysis.py) — `explain_code` 함수 전체 삭제 (L188-L422)
- **影響**: `extension/mcp-servers/bridge/tools/analysis.py` 동기화 필요
- **관련 보조 코드 삭제**: `_get_git_blame()`, `_find_related_tests()` (explain_code에서만 사용)

### 2. `analyze_changes` (analysis.py)
- **파일**: [`mcp-servers/bridge/tools/analysis.py`](mcp-servers/bridge/tools/analysis.py) — `analyze_changes` 함수 전체 삭제 (L424-L523)
- **影響**: `extension/mcp-servers/bridge/tools/analysis.py` 동기화
- **관련**: `_get_analyze_changes()` lazy getter in [`integrated.py`](mcp-servers/bridge/tools/integrated.py) (dead code로 이미 판정됨)

### 3. `generate_tests` (tester.py)
- **파일**: [`mcp-servers/bridge/tools/tester.py`](mcp-servers/bridge/tools/tester.py) — `generate_tests` 함수 전체 삭제 (L37-L307)
- **影響**: `extension/mcp-servers/bridge/tools/tester.py` 동기화
- **관련**: tester.py의 register()가 generate_tests만 등록하면, `__init__.py`에서 tester import 제거 가능

### 4. `analyze_coverage` (tester.py)
- **파일**: [`mcp-servers/bridge/tools/tester.py`](mcp-servers/bridge/tools/tester.py) — `analyze_coverage` 함수 전체 삭제 (L309-L427)
- **影響**: tester.py의 register()가 비어 있게 됨 → tester 모듈 자체를 `__init__.py`에서 제거

### 5. `ux_coordinator` (ux_coordinator.py)
- **파일**: [`mcp-servers/bridge/tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) — `ux_coordinator` 함수 전체 삭제 (L60-L134)
- **影響**: `extension/mcp-servers/bridge/tools/ux_coordinator.py` 동기화

### 6. `auto_analyze_after_drop` (ux_coordinator.py)
- **파일**: [`mcp-servers/bridge/tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) — `auto_analyze_after_drop` 함수 전체 삭제 (L136-L284)
- **影響**: `extension/mcp-servers/bridge/tools/ux_coordinator.py` 동기화

### 7. `auto_analyze_whiteboard` (ux_coordinator.py)
- **파일**: [`mcp-servers/bridge/tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) — `auto_analyze_whiteboard` 함수 전체 삭제 (L286-L308)
- **影響**: `extension/mcp-servers/bridge/tools/ux_coordinator.py` 동기화
- **우선순위**: 명시적 deprecated → 가장 먼저 삭제 대상

### 8. `apply_patch` (editor.py)
- **파일**: [`mcp-servers/bridge/tools/editor.py`](mcp-servers/bridge/tools/editor.py) — `apply_patch` 함수 + `_apply_patch_transactional` + 모든 헬퍼 삭제 (L1-L621, 파일 전체)
- **影響**: `extension/mcp-servers/bridge/tools/editor.py` 동기화
- **우선**: editor.py 모듈 자체를 `__init__.py`에서 제거

### 9. `explore_github` (github_diver.py)
- **파일**: [`mcp-servers/bridge/tools/github_diver.py`](mcp-servers/bridge/tools/github_diver.py) — 파일 전체 삭제
- **影響**: 없음 (이미 `__init__.py`에서 미등록)
- **우선순위**: DEAD CODE → 즉시 삭제 대상

## 4.2 VS Code 커맨드 DELETE (13개)

### "채팅 안내" 커맨드 13개
- **파일**: [`extension/src/extension.ts`](extension/src/extension.ts)
  - `vibezoo.reviewProject` — L386-L390
  - `vibezoo.findBugs` — L391-L393
  - `vibezoo.suggestRefactor` — L394-L398
  - `vibezoo.generateDocs` — L399-L401
  - `vibezoo.explainCode` — L668-L672
  - `vibezoo.analyzeChanges` — L675-L679
  - `vibezoo.reviewPR` — L682-L686
  - `vibezoo.refactorAcrossFiles` — L689-L693
  - `vibezoo.learnProject` — L696-L700
  - `vibezoo.recallProject` — L703-L707
  - `vibezoo.learnPreference` — L710-L714
  - `vibezoo.getPreferences` — L717-L721
  - `vibezoo.rebuildCodeIndex` — L724-L730

- **파일**: [`extension/package.json`](extension/package.json)
  - 커맨드 정의 13개 삭제 (menubar, menus section)
  - i18n 키 13개: package.nls.*.json, bundle.l10n.*.json

### Editor Context 메뉴 4개
- **파일**: [`extension/package.json`](extension/package.json) — `menus.editor/context` 내 vibezoo@1~4

## 4.3 UI DELETE (1개)

### Editor Context 메뉴 (4개 메뉴 항목)
- 위 4.2와 동일

## 4.4 ASSOCIATED FILES DELETE

### github_diver.py 삭제 시 영향:
- 없음 (다른 모듈에서 import 안 함)

### tester.py 삭제 시 영향:
- [`mcp-servers/bridge/tools/__init__.py`](mcp-servers/bridge/tools/__init__.py) — tester import 제거 (L60, L73)
- `extension/mcp-servers/bridge/tools/__init__.py` 동기화

### editor.py 삭제 시 영향:
- [`mcp-servers/bridge/tools/__init__.py`](mcp-servers/bridge/tools/__init__.py) — editor import 제거 (L69, L75)
- `extension/mcp-servers/bridge/tools/__init__.py` 동기화

### ux_coordinator.py 3개 도구 삭제 시:
- [`mcp-servers/bridge/tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) — 파일 자체를 `__init__.py`에서 제거 (3개 도구 모두 삭제되므로)
- `extension/mcp-servers/bridge/tools/__init__.py` 동기화
- [`mcp-servers/bridge/intent_detector.py`](mcp-servers/bridge/intent_detector.py) — ux_coordinator에서만 사용. DELETE 후 dead code

### analysis.py에서 2개 도구 삭제 시:
- register()에 2개 도구 제거 (explain_code, analyze_changes)
- 나머지 2개(review_pr, refactor_across_files) 유지

---

# Part 5: 예상 커밋 파장

| 구분 | 파일 수 | 설명 |
|------|---------|------|
| MCP 툴 Python 파일 | 11 | github_diver.py 삭제(1) + editor.py 삭제(1) + tester.py 삭제(1) + ux_coordinator.py 삭제(1) + analysis.py 수정(1) + intent_detector.py 삭제(1) + __init__.py 수정(1) + extension 복사본 4개 |
| VS Code extension | ~22 | extension.ts(1) + package.json(1) + package.nls.*/20개 번역 파일 |
| **총 파일 수** | **~33** | |

## 번역 파일 영향 (i18n)
- `extension/package.nls.*.json` (20개 언어) — 13개 커맨드 키 삭제
- `extension/l10n/bundle.l10n.*.json` (20개 언어) — 13개 런타임 키 삭제
- `mcp-servers/bridge/i18n/translations/*.json` (20개 언어) — ux_coordinator 관련 키 삭제 (해당 시)

---

# Part 6: 추가 발견

## 6.1 죽은 코드 (Dead Code)
- [`integrated.py` L337-L343](mcp-servers/bridge/tools/integrated.py#L337) — `_lazy_tool()` 함수: 호출 없음
- [`integrated.py` L40-L108](mcp-servers/bridge/tools/integrated.py#L40) — `_tool_registry` dict: 12/20개 lazy getter 없음 (dead entry)
- [`_base.py` L27-L31](mcp-servers/bridge/tools/_base.py#L27) — `BaseTool.partial_result()`: 호출 없음 (stub)
- [`deep_analyzer.py` L7](mcp-servers/bridge/tools/deep_analyzer.py#L7) — `import subprocess`: 미사용 import

## 6.2 사용하지 않는 설정 (package.json)
- `vibezoo.scout.port` (9022) — MCP 서버는 단일 브릿지(9027) 사용. 미사용
- `vibezoo.reviewer.port` (9023) — 동일. 미사용
- `vibezoo.tester.port` (9024) — 동일. 미사용
- `vibezoo.deepAnalyzer.port` (9026) — 동일. 미사용
- `vibezoo.emotion.detectionEnabled` — 감정 감지 기능 미구현 또는 미사용

## 6.3 MERGE 기회 (기록만, 이번 세션 미실행)
- `summarize_architecture` → `review_project(mode="summary")`에 통합 가능
- `review_pr` → GitHub MCP의 PR 리뷰 기능과 통합 가능 (단, git diff 분석은 VibeZoo 고유)

---

## Affected File List

| 파일 | 작업 | 상태 |
|------|------|------|
| [`mcp-servers/bridge/tools/__init__.py`](mcp-servers/bridge/tools/__init__.py) | tester/editor/ux_coordinator import 제거 | DELETE 대상 |
| [`mcp-servers/bridge/tools/github_diver.py`](mcp-servers/bridge/tools/github_diver.py) | 파일 전체 삭제 | DELETE 대상 |
| [`mcp-servers/bridge/tools/editor.py`](mcp-servers/bridge/tools/editor.py) | 파일 전체 삭제 | DELETE 대상 |
| [`mcp-servers/bridge/tools/tester.py`](mcp-servers/bridge/tools/tester.py) | 파일 전체 삭제 | DELETE 대상 |
| [`mcp-servers/bridge/tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) | 파일 전체 삭제 | DELETE 대상 |
| [`mcp-servers/bridge/tools/analysis.py`](mcp-servers/bridge/tools/analysis.py) | explain_code + analyze_changes 삭제 | 수정 대상 |
| [`mcp-servers/bridge/intent_detector.py`](mcp-servers/bridge/intent_detector.py) | ux_coordinator 삭제 시 dead code → 삭제 | DELETE 대상 |
| [`extension/src/extension.ts`](extension/src/extension.ts) | 13개 커맨드 등록 삭제 | 수정 대상 |
| [`extension/package.json`](extension/package.json) | 커맨드 정의 + menu + i18n 키 삭제 | 수정 대상 |
| [`extension/package.nls.*.json`] (20개) | 커맨드 i18n 키 삭제 | 수정 대상 |
| [`extension/l10n/bundle.l10n.*.json`] (20개) | 런타임 i18n 키 삭제 | 수정 대상 |
| `extension/mcp-servers/bridge/tools/*.py` (복사본 4개) | 위 Python 파일과 동기화 | DELETE 대상 |
