# VibeZoo UX 업그레이드 상세 아키텍처 설계
## Pillar 1: AST-Guided Smart Ellipsis & Transactional Patching + Pillar 2: Crow-Aware Contextual Intent Routing

> **버전**: 2.0 (디버그 수정 반영)
> **날짜**: 2026-06-06
> **대상**: VibeZoo Bridge (`mcp-servers/bridge/`)
> **상태**: 설계 완료, 디버그 이슈 해결됨

---

## 목차

1. [디버그 발견 이슈 요약 (v1.0 → v2.0 변경사항)](#0-디버그-발견-이슈-요약)
2. [사전 분석: 현재 코드베이스 구조](#1-사전-분석)
3. [Pillar 1 상세 설계: AST-Guided Smart Ellipsis & Transactional Patching](#2-pillar-1-상세-설계)
4. [Pillar 2 상세 설계: Crow-Aware Contextual Intent Routing](#3-pillar-2-상세-설계)
5. [모듈 간 데이터 흐름 다이어그램](#4-데이터-흐름-다이어그램)
6. [구현 순서 및 파일별 변경 목록](#5-구현-순서)
7. [엣지 케이스 분석 및 대응 방안](#6-엣지-케이스-분석)
8. [테스트 전략](#7-테스트-전략)

---

## 0. 디버그 발견 이슈 요약 (v1.0 → v2.0 변경사항)

| # | 심각도 | 이슈 | v1.0 문제 | v2.0 해결책 | 영향 파일 |
|---|--------|------|-----------|-------------|-----------|
| D1 | 🔴 CRITICAL | `dz_session.json` Writer 부재 | Pillar 2가 `dz_session.json`을 읽기만 하고 쓰는 코드가 없어 기능 무력화 | `_write_dz_session()` 신규 함수 → [`auto_analyze_after_drop()`](mcp-servers/bridge/tools/ux_coordinator.py:63) 시작 부분에서 호출 | [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) |
| D2 | 🔴 CRITICAL | `_resolve_file()` 함수 정의 누락 | 계획이 `_resolve_file()`을 참조하지만 구현되지 않아 `NameError` 발생 | `_resolve_file()` 제거. [`_preprocess_blocks()`](mcp-servers/bridge/tools/editor.py)에서 직접 `Path(file_path).read_text()` 호출 | [`editor.py`](mcp-servers/bridge/tools/editor.py) |
| D3 | 🔴 CRITICAL | `_resolve_ellipsis_ast()` 예외 미처리 | AST 파싱 중 예외(메모리 부족, 문법 오류 등) 발생 시 전체 패치 실패 | `_resolve_ellipsis_ast()` 전체를 try/except로 감싸고 실패 시 `None` 반환 → caller가 text 결과 사용 | [`editor.py`](mcp-servers/bridge/tools/editor.py) |
| D4 | 🟡 MEDIUM | 경로 검증 누락 | `apply_patch`에 path traversal 방어 없음 | `os.path.normpath()`로 경로 정규화 및 검증 추가 | [`editor.py`](mcp-servers/bridge/tools/editor.py) |
| D5 | 🟡 MEDIUM | 파일 인코딩 불명시 | `read_text()` 호출 시 인코딩 미지정 | 모든 `read_text()` 호출에 `encoding="utf-8", errors="replace"` 명시 | [`editor.py`](mcp-servers/bridge/tools/editor.py), [`intent_detector.py`](mcp-servers/bridge/intent_detector.py) |
| D6 | 🟡 MEDIUM | `fix_loop` 의도 누락 | `INTENT_SIGNATURES`와 `get_workflow_hints()`에 `fix_loop` 없음 | `fix_loop` 시그니처 및 워크플로우 힌트 추가 | [`intent_detector.py`](mcp-servers/bridge/intent_detector.py) |
| D7 | 🟡 MEDIUM | Crow 3중 순차 호출 지연 | [`_query_crow_for_bias()`](mcp-servers/bridge/intent_detector.py)에서 context/bug/arch 3회 개별 호출 → 네트워크 지연 누적 | 단일 호출로 통합: `try_crow_recall("recent_context", register="context", limit=3)` 1회 + 결과 파싱 | [`intent_detector.py`](mcp-servers/bridge/intent_detector.py) |

---

## 1. 사전 분석: 현재 코드베이스 구조

### 1.1 [`editor.py`](mcp-servers/bridge/tools/editor.py) — 현재 흐름

```
apply_patch(path?, diff, target_path?)
    │
    ├─ _parse_diff(diff)          → blocks: [{search, replace}, ...]
    │   ├─ <<<<<<< SEARCH / ------- / >>>>>>> REPLACE 파싱
    │   └─ ======= (apply_diff 호환) + :start_line: 메타데이터 무시
    │
    ├─ 파일 결정: path → 절대경로 변환 → 존재 확인
    │   └─ path 없으면 _find_file_by_content(search[:100]) 로 검색
    │
    ├─ _apply_patch_impl(path, diff, target_path)
    │   ├─ content = file_path.read_text(encoding="utf-8", errors="ignore")  # 읽기
    │   ├─ modified = content                         # (문자열이므로 실질적 복사)
    │   ├─ _backup_file(file_path)                    # 백업 생성
    │   ├─ for block in blocks:
    │   │   ├─ exact match: modified.replace(search, replace, 1)
    │   │   ├─ fuzzy match: _find_best_location(modified, search, cutoff=0.85)
    │   │   │   └─ difflib.SequenceMatcher + prefix heuristic
    │   │   └─ 실패 → errors.append(...)
    │   ├─ errors 있으면 → 오류 보고 (디스크 쓰기 안 함) ✅
    │   └─ errors 없으면 → file_path.write_text(modified, encoding="utf-8")
```

**핵심 발견사항:**
- 현재 코드는 이미 "부분적 트랜잭션" — 오류 발생 시 디스크에 쓰지 않음
- 그러나 `modified`는 블록이 실패해도 이전 블록들의 변경사항이 누적됨 (메모리상)
- `_find_best_location()`은 85% 유사도 cutoff → ellipsis(`// ...`) 포함 시 완전 실패
- 에러 보고가 빈약: "블록 N: SEARCH 내용을 찾을 수 없습니다" — 라인 번호 없음
- **v2.0**: `errors="ignore"` → `errors="replace"`로 변경 (디버그 D5)

### 1.2 [`intent_detector.py`](mcp-servers/bridge/intent_detector.py) — 현재 흐름

```
detect_intent(user_message)
    │
    ├─ message_lower = user_message.lower()
    ├─ for (intent_name, priority, keywords, _) in INTENT_SIGNATURES:
    │   ├─ matched = sum(1 for kw in keywords if kw in message_lower)
    │   ├─ confidence = matched / len(keywords) * 10.0
    │   ├─ intent별 패턴 보정 (+2~3점)
    │   └─ results.append((intent_name, priority, confidence))
    │
    ├─ sort by (-priority, -confidence)
    └─ 빈 결과 → [("general_question", 0, 1.0)]
```

**핵심 발견사항:**
- 5개 의도, 총 ~35개 키워드 → `"이거 분석해줘"` → 키워드 매칭 0 → `general_question`
- Crow Memory 연동 無, Dropzone 세션 확인 無
- 임계값(threshold) 개념 없음 — 매칭만 되면 무조건 결과 반환
- **v2.0**: `fix_loop` 의도 누락 확인 (디버그 D6)

### 1.3 [`ast_engine.py`](mcp-servers/bridge/ast_engine.py) — 가용 기능

```python
class AstEngine:
    LANGUAGES = {'.py': 'python', '.ts': 'typescript', '.js': 'javascript', ...}
    NODE_TYPES  = {lang: {function, class, import, call}, ...}

    # editor.py에서 활용 가능한 메서드:
    parse(content, file_ext) → {functions, classes, interfaces, ...}
    extract_functions(content, file_ext) → [{name, line, end_line, type}, ...]
    extract_classes(content, file_ext)   → [{name, line}, ...]
    extract_calls(content, file_ext)     → [{name, line}, ...]
    extract_imports(content, file_ext)   → [{module, type, line}, ...]
    is_available(lang) → bool
```

### 1.4 [`crow_client.py`](mcp-servers/bridge/crow_client.py) — 가용 함수

```python
try_crow_recall(query, register="context", limit=5) → list  # 실패 시 []
try_crow_ingest(content, register="context", **kwargs) → None  # 실패 무시
crow_health_check() → bool
```

### 1.5 [`config.py`](mcp-servers/bridge/config.py) — 관련 상수

```python
CROW_URL = "http://localhost:9020"
CROW_TIMEOUT = 3
DZ_SESSION_FILE = "~/.vibezoo-uploads/dz_session.json"
```

---

## 2. Pillar 1 상세 설계: AST-Guided Smart Ellipsis & Transactional Patching

### 2.1 전체 설계 개요

```
                    ┌──────────────────────────────────────┐
                    │         apply_patch(path, diff)       │
                    │   [v2.0] normpath() 경로 검증 추가     │
                    └──────────────────┬───────────────────┘
                                       │
                    ┌──────────────────▼───────────────────┐
                    │         _parse_diff(diff)             │
                    │         → blocks[{search, replace}]   │
                    └──────────────────┬───────────────────┘
                                       │
                    ┌──────────────────▼───────────────────┐
                    │     _preprocess_blocks(blocks, file)  │  ← [NEW]
                    │  ┌─────────────────────────────────┐ │
                    │  │ [v2.0] direct read_text() 사용  │ │
                    │  │ file_content = file_path.       │ │
                    │  │   read_text(encoding="utf-8",   │ │
                    │  │   errors="replace")             │ │
                    │  │ for each block:                  │ │
                    │  │   ell = _detect_ellipsis(search) │ │
                    │  │   if ell:                        │ │
                    │  │     resolved = _resolve_ellipsis │ │
                    │  │     block["search"] = resolved   │ │
                    │  │     block["_had_ellipsis"]=True  │ │
                    │  └─────────────────────────────────┘ │
                    └──────────────────┬───────────────────┘
                                       │
                    ┌──────────────────▼───────────────────┐
                    │   _apply_patch_transactional(...)     │  ← [REFACTORED]
                    │  ┌─────────────────────────────────┐ │
                    │  │ PHASE 1: DRY-RUN                │ │
                    │  │   virtual = content              │ │
                    │  │   for block in blocks:           │ │
                    │  │     loc = _find_best_location()  │ │
                    │  │     if loc: apply to virtual     │ │
                    │  │     else: record failure, BREAK  │ │
                    │  │                                  │ │
                    │  │ PHASE 2: COMMIT / ROLLBACK       │ │
                    │  │   if all_success:                │ │
                    │  │     write virtual to disk        │ │
                    │  │     create backup                │ │
                    │  │   else:                          │ │
                    │  │     discard virtual              │ │
                    │  │     return detailed error report  │ │
                    │  └─────────────────────────────────┘ │
                    └──────────────────────────────────────┘
```

### 2.2 변경될 함수별 Before/After

#### 2.2.1 신규 함수: `_detect_ellipsis(search_block: str) -> Optional[dict]`

**목적**: SEARCH 블록에서 ellipsis 패턴 감지 및 header/footer 분리

```
Before: (존재하지 않음)

After:
  Input: "def foo():\n    init()\n    # ... existing code ...\n    cleanup()"
  
  감지 패턴 (언어별):
    Python:   r'^\s*#\s*\.{2,}.*$'        # # ...
    JS/TS:    r'^\s*//\s*\.{2,}.*$'       # // ...
    C/Go/Rust: r'^\s*//\s*\.{2,}.*$'      # // ...
    블록 공통: r'/\*\s*\.{2,}.*\*/\s*$'    # /* ... */
  
  Output: {
      "pattern": "# ... existing code ...",
      "header": "def foo():\n    init()",
      "footer": "    cleanup()",
      "style": "line_comment",
      "header_lines": 2,
      "footer_lines": 1
  }
  
  None if no ellipsis detected.
```

**세부 알고리즘:**
1. 줄 단위로 SEARCH 블록 순회
2. 각 줄이 ellipsis 패턴과 매칭되는지 검사 (주석 + `...` 포함)
3. 첫 매칭 이전 줄들 → `header`
4. 마지막 매칭 이후 줄들 → `footer`
5. 여러 ellipsis 줄이 연속된 경우 하나로 병합
6. header나 footer가 비어있으면 None 반환 (의미 없는 ellipsis)

#### 2.2.2 신규 함수: `_resolve_ellipsis_text(file_content: str, ellipsis_info: dict) -> Optional[str]`

**목적**: 파일 내용에서 header/footer 사이의 실제 코드를 찾아 ellipsis를 대체

**v2.0 변경**: `_resolve_file()` 호출 제거 (D2). `_preprocess_blocks()`에서 이미 `file_content`를 읽어 전달함.

```
Before: (존재하지 않음)

After:
  Input:
    file_content = "def foo():\n    init()\n    do_work()\n    more_work()\n    cleanup()"
    ellipsis_info = {header: "def foo():\n    init()", footer: "    cleanup()"}
  
  알고리즘:
    1. header_text를 file_content에서 fuzzy 매칭 → header_pos
    2. footer_text를 file_content[header_pos+len(header):]에서 fuzzy 매칭 → footer_pos
    3. 중간 텍스트 추출: middle = file_content[header_end : footer_start]
    4. 재구성: resolved = header + "\n" + middle + "\n" + footer
    5. (선택) 재구성된 검색어가 file_content에 exact match되는지 검증
  
  Output: "def foo():\n    init()\n    do_work()\n    more_work()\n    cleanup()"
  또는 None (매칭 실패)
```

**매칭 전략:**
- [`_find_best_location()`](mcp-servers/bridge/tools/editor.py:107)의 fuzzy 매칭 로직 재사용
- header는 파일 앞쪽에서, footer는 header 이후에서만 검색 (순서 보장)
- header/footer 각각 70% cutoff (ellipsis 특성상 짧은 조각일 수 있음)
- header-end 와 footer-start 사이의 모든 텍스트를 "gap"으로 처리

#### 2.2.3 신규 함수: `_resolve_ellipsis_ast(file_path: Path, file_content: str, ellipsis_info: dict) -> Optional[str]`

**목적**: tree-sitter AST를 활용한 구조적 검증 및 정밀 gap 계산 (선택적 강화)

**v2.0 변경**: 전체 로직을 try/except로 감싸고 실패 시 `None` 반환 (D3). caller가 `_resolve_ellipsis_text()` 결과를 사용함.

```
Before: (존재하지 않음)

After (v2.0):
```python
def _resolve_ellipsis_ast(file_path, file_content, ellipsis_info) -> Optional[str]:
    try:
        ast_engine = _get_ast_engine()
        file_ext = Path(file_path).suffix
        ast = ast_engine.parse(file_content, file_ext)
        if not ast:
            return None  # tree-sitter 사용 불가 → text 결과로 폴백
        
        # header의 첫 줄 / footer의 마지막 줄에 해당하는 AST 노드 찾기
        header_node = _find_ast_node_for_line(ast, ellipsis_info["header_lines"])
        footer_node = _find_ast_node_for_line(ast, ellipsis_info["footer_lines"])
        
        if not header_node or not footer_node:
            return None
        
        # 두 노드가 동일한 부모 scope에 있는지 확인
        if not _same_scope(header_node, footer_node):
            return None  # 서로 다른 scope → text 결과로 폴백
        
        # gap 계산 및 재구성
        gap = file_content[header_node.end_byte : footer_node.start_byte]
        if len(gap.split('\n')) > 500:
            # gap이 너무 크면 경고 로그 (진행은 허용)
            print(f"[VibeZoo] Ellipsis gap > 500 lines in {file_path}")
        
        resolved = ellipsis_info["header"] + gap + ellipsis_info["footer"]
        return resolved
    except Exception as e:
        print(f"[VibeZoo] AST ellipsis resolution failed, using text fallback: {e}")
        return None  # caller가 text 결과 사용
```

**AST 활용의 가치:**
- header/footer가 주석이나 리터럴 내부가 아닌 실제 코드 구조에 해당하는지 검증
- 서로 다른 함수/클래스에 걸친 ellipsis는 의도적 스패닝으로 간주하고 허용
- gap 크기 제한으로 비정상적인 매칭 방지
- **v2.0**: 예외 발생 시 전체 실패가 아닌 text 폴백으로 정상 진행

#### 2.2.4 신규 함수: `_preprocess_blocks(blocks: list[dict], file_path: Path) -> list[dict]`

**목적**: 모든 블록을 순회하며 ellipsis 감지 및 해결

**v2.0 변경**: `_resolve_file()` 제거 → 직접 `file_path.read_text()` 호출 (D2). 인코딩 명시 (D5).

```python
def _preprocess_blocks(blocks, file_path):
    """SEARCH/REPLACE 블록 전처리: ellipsis 해결"""
    file_content = file_path.read_text(encoding="utf-8", errors="replace")
    
    for block in blocks:
        ell = _detect_ellipsis(block["search"])
        if not ell:
            block["_had_ellipsis"] = False
            continue
        
        # 1차: 텍스트 기반 해결 시도
        resolved = _resolve_ellipsis_text(file_content, ell)
        
        # 2차: AST 검증 (선택적, 실패 시 None → text 결과 유지)
        if resolved:
            ast_resolved = _resolve_ellipsis_ast(file_path, file_content, ell)
            if ast_resolved:
                resolved = ast_resolved
        
        if resolved:
            block["search"] = resolved
            block["_had_ellipsis"] = True
            block["_original_search"] = block.get("_original_search", block["search"])
        else:
            block["_ellipsis_failed"] = True
    
    return blocks
```

#### 2.2.5 리팩터링: `_apply_patch_impl()` → `_apply_patch_transactional()`

**Before** (현재 [`_apply_patch_impl`](mcp-servers/bridge/tools/editor.py:141)):

```python
def _apply_patch_impl(path, diff, target_path):
    blocks = _parse_diff(diff)
    # ... 파일 결정, 읽기, 백업 ...
    modified = content
    for block in blocks:
        if exact match:   modified = modified.replace(...)
        elif fuzzy match: modified = modified[:loc] + replace + modified[loc:]
        else: errors.append(...)
    if errors: return error report  # 디스크 쓰기 안 함
    file_path.write_text(modified)
```

**After** (새 `_apply_patch_transactional`, v2.0 개선사항 포함):

```python
def _apply_patch_transactional(path, diff, target_path):
    # ── Phase 0: 파싱 및 전처리 ──
    blocks = _parse_diff(diff)
    # ... 파일 결정 ...
    # [v2.0 D4] 경로 검증: normpath()로 path traversal 방지
    resolved_path = _resolve_and_validate_path(path, diff, target_path)
    if not resolved_path:
        return _markdown_header("Apply Patch Error", "❌") + \
            "**파일을 찾을 수 없습니다.**\n" + _markdown_footer()
    file_path = resolved_path
    
    # [v2.0 D5] 명시적 인코딩
    content = file_path.read_text(encoding="utf-8", errors="replace")
    
    # [NEW] ellipsis 전처리
    blocks = _preprocess_blocks(blocks, file_path)
    
    # 백업은 커밋 직전에만 (Phase 2)
    
    # ── Phase 1: Dry-Run (가상 버퍼) ──
    virtual = content
    results = []  # [(block_index, success, match_detail), ...]
    
    for i, block in enumerate(blocks):
        search_text = block["search"].strip()
        replace_text = block["replace"].strip()
        
        # 이미 ellipsis 실패한 블록은 건너뛰기
        if block.get("_ellipsis_failed"):
            results.append((i, False, "ellipsis_resolution_failed", {
                "error": "SEARCH 블록의 생략 기호(ellipsis)를 해결할 수 없습니다",
                "original_search_preview": block.get("_original_search", search_text)[:100]
            }))
            break
        
        loc = _find_best_location(virtual, search_text)
        if loc:
            virtual = virtual[:loc[0]] + replace_text + virtual[loc[1]:]
            # 매칭 위치 정보 계산 (라인 번호)
            line_no = virtual[:loc[0]].count('\n') + 1
            results.append((i, True, "applied", {
                "line": line_no,
                "had_ellipsis": block.get("_had_ellipsis", False)
            }))
        else:
            # 상세 실패 정보
            search_preview = search_text[:80].replace('\n', '\\n')
            results.append((i, False, "not_found", {
                "search_preview": search_preview,
                "similarity": _compute_best_similarity(virtual, search_text)
            }))
            break  # 첫 실패에서 중단
    
    # ── Phase 2: Commit or Rollback ──
    all_success = all(r[1] for r in results)
    
    if all_success:
        bak = _backup_file(file_path)
        file_path.write_text(virtual, encoding="utf-8")
        return _format_success_report(blocks, results, file_path, bak)
    else:
        # virtual 버퍼 폐기 (아무것도 쓰지 않음)
        return _format_failure_report(blocks, results, file_path, content)
```

#### 2.2.6 신규 함수: `_resolve_and_validate_path()` (v2.0 D4)

**목적**: 경로 검증 및 path traversal 방지

```python
def _resolve_and_validate_path(path, diff, target_path) -> Optional[Path]:
    """파일 경로 결정 + path traversal 검증"""
    # path가 명시된 경우
    if path:
        p = Path(os.path.normpath(path))  # [v2.0 D4] normpath로 경로 정규화
        if not p.is_absolute():
            root = Path(get_project_root(target_path))
            p = (root / p).resolve()
        
        # [v2.0 D4] path traversal 검증: 프로젝트 루트 바깥이면 거부
        project_root = Path(get_project_root(target_path)).resolve()
        try:
            p.resolve().relative_to(project_root)
        except ValueError:
            return None  # 프로젝트 루트 바깥 경로
        
        if p.exists() and p.is_file():
            return p
        return None
    
    # path가 없으면 내용으로 파일 찾기
    blocks = _parse_diff(diff)
    if not blocks:
        return None
    search_sample = blocks[0]["search"][:100]
    candidates = _find_file_by_content(search_sample, target_path or os.getcwd())
    if candidates:
        return candidates[0]
    return None
```

#### 2.2.7 신규 함수: `_format_failure_report()`

**목적**: 실패 시 상세한 진단 정보 제공

```python
def _format_failure_report(blocks, results, file_path, content):
    """실패한 블록에 대한 상세 보고서 생성"""
    output = _markdown_header("Apply Patch", "❌")
    
    success_count = sum(1 for r in results if r[1])
    fail_index = next((i for i, ok, _, _ in results if not ok), -1)
    
    output += f"**{success_count}/{len(blocks)}** 블록 적용 성공 "
    output += f"(블록 {fail_index+1} 실패로 롤백됨)\n\n"
    output += "⚠️ 파일은 수정되지 않았습니다 (원자적 롤백).\n\n"
    
    for i, ok, reason, detail in results:
        if ok:
            output += f"- ✅ 블록 {i+1}: 적용됨"
            if detail.get("had_ellipsis"):
                output += " (ellipsis 해결됨)"
            output += f" @ line {detail.get('line', '?')}\n"
        else:
            output += f"- ❌ 블록 {i+1}: 실패 — {reason}\n"
            if reason == "ellipsis_resolution_failed":
                output += f"  원본 검색어: `{detail.get('original_search_preview', '?')}`\n"
            elif reason == "not_found":
                output += f"  검색 미리보기: `{detail.get('search_preview', '?')}`\n"
                output += f"  최고 유사도: {detail.get('similarity', 0):.1%}\n"
    
    # Diff Suggestion
    if fail_index >= 0 and content:
        output += "\n### 💡 제안: 파일 현재 상태 기준 SEARCH 블록\n"
        output += "실패한 블록의 SEARCH 텍스트와 가장 유사한 실제 코드:\n\n"
        # ... fuzzy diff 제안 ...
    
    return output + _markdown_footer()
```

### 2.3 [`editor.py`](mcp-servers/bridge/tools/editor.py) 최종 함수 맵

| 함수 | 상태 | 설명 |
|------|------|------|
| `_parse_diff()` | 유지 | 기존 블록 파서 (변경 없음) |
| `_find_file_by_content()` | 유지 | 기존 파일 검색 |
| `_find_best_location()` | 유지 | 기존 fuzzy 매칭 |
| `_backup_file()` | 유지 | 기존 백업 |
| **`_resolve_and_validate_path()`** | **신규 (v2.0)** | 경로 검증 + path traversal 방지 (D4) |
| **`_detect_ellipsis()`** | **신규** | Ellipsis 패턴 감지 + header/footer 분리 |
| **`_resolve_ellipsis_text()`** | **신규** | 텍스트 기반 ellipsis 해결 (항상 실행) |
| **`_resolve_ellipsis_ast()`** | **신규 (v2.0 수정)** | AST 기반 검증 + try/except 보호 (D3) |
| **`_preprocess_blocks()`** | **신규 (v2.0 수정)** | 모든 블록의 ellipsis 전처리 + 직접 read_text (D2, D5) |
| **`_apply_patch_transactional()`** | **리팩터링 (v2.0 수정)** | 기존 `_apply_patch_impl()` 대체 + 경로 검증 (D4) |
| **`_format_success_report()`** | **신규** | 성공 보고서 포맷 |
| **`_format_failure_report()`** | **신규** | 상세 실패 보고서 + diff 제안 |
| **`_compute_best_similarity()`** | **신규** | 최고 유사도 계산 (진단용) |
| `apply_patch()` | 수정 (v2.0) | `_apply_patch_impl` → `_apply_patch_transactional` 호출 + normpath (D4) |

---

## 3. Pillar 2 상세 설계: Crow-Aware Contextual Intent Routing

### 3.1 전체 설계 개요

```
              ┌─────────────────────────────────────────┐
              │        ux_coordinator(user_message)      │
              └──────────────────┬──────────────────────┘
                                 │
              ┌──────────────────▼──────────────────────┐
              │     detect_intent_v2(user_message)       │  ← [REFACTORED]
              │                                          │
              │  ┌────────────────────────────────────┐  │
              │  │ STEP 1: Keyword Matching (기존)     │  │
              │  │   confidence = keyword_score        │  │
              │  │   [v2.0] fix_loop 시그니처 추가     │  │
              │  └──────────────┬─────────────────────┘  │
              │                 │                         │
              │        confidence < 3.0?                  │
              │         │          │                      │
              │        YES        NO                      │
              │         │          │                      │
              │  ┌──────▼──────┐   │                      │
              │  │ STEP 2:     │   │                      │
              │  │ Crow Bias   │   │                      │
              │  │ [v2.0 D7]   │   │                      │
              │  │ 단일 호출    │   │                      │
              │  └──────┬──────┘   │                      │
              │         │          │                      │
              │  ┌──────▼──────┐   │                      │
              │  │ STEP 3:     │   │                      │
              │  │ Dropzone    │   │                      │
              │  │ Temporal    │   │                      │
              │  └──────┬──────┘   │                      │
              │         │          │                      │
              │  ┌──────▼──────┐   │                      │
              │  │ STEP 4:     │   │                      │
              │  │ Merge &     │◄──┘                      │
              │  │ Adjust      │                          │
              │  └──────┬──────┘                          │
              │         │                                 │
              │  [(intent, priority, confidence), ...]    │
              │  + metadata: {file_path, dz_recent, ...}  │
              └──────────────────────────────────────────┘
```

### 3.2 변경될 함수별 Before/After

#### 3.2.1 [`intent_detector.py`](mcp-servers/bridge/intent_detector.py): `INTENT_SIGNATURES` 수정 (v2.0 D6)

**Before:**
```python
INTENT_SIGNATURES = [
    ("file_share", 10, [...], []),
    ("drawing_request", 9, [...], []),
    ("whiteboard_input", 8, [...], []),
    ("code_analysis", 7, [...], []),
    ("project_setup", 5, [...], []),
]
```

**After (v2.0):**
```python
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
        "고쳐줘", "버그", "fix", "bug", "수정", "에러",
        "오류", "디버그", "debug", "패치", "patch"
    ], []),
    ("code_analysis", 6, [  # priority 7→6 (fix_loop이 7을 차지)
        "코드", "분석", "리뷰", "리팩터", "검색",
        "code", "analyze", "review", "refactor", "search"
    ], []),
    ("project_setup", 5, [
        "설치", "설정", "셋업", "초기화",
        "install", "setup", "init", "configure"
    ], []),
]
```

#### 3.2.2 [`intent_detector.py`](mcp-servers/bridge/intent_detector.py): `detect_intent()` → `detect_intent_v2()`

**Before:**

```python
def detect_intent(user_message: str) -> list[tuple[str, int, float]]:
    results = []
    message_lower = user_message.lower()
    for intent_name, priority, keywords, _ in INTENT_SIGNATURES:
        matched = sum(1 for kw in keywords if kw.lower() in message_lower)
        if matched > 0:
            confidence = matched / max(len(keywords), 1) * 10.0
            # ... 패턴 보정 ...
            results.append((intent_name, priority, min(confidence, 10.0)))
    results.sort(key=lambda x: (-x[1], -x[2]))
    if not results:
        results.append(("general_question", 0, 1.0))
    return results
```

**After:**

```python
# 의도 바이어스 상수
CROW_BIAS_WEIGHT = 0.4       # Crow 컨텍스트 바이어스 가중치
DZ_BIAS_WEIGHT = 0.6         # Dropzone 시간적 바이어스 가중치
LOW_CONFIDENCE_THRESHOLD = 3.0  # 이 임계값 미만이면 Crow/DZ 보강
DZ_TIME_THRESHOLD_MINUTES = 3   # Dropzone 세션 유효 시간

def detect_intent_v2(user_message: str) -> dict:
    """
    Returns:
        {
            "intents": [(name, priority, confidence), ...],
            "metadata": {
                "crow_used": bool,
                "dz_recent": bool,
                "dz_file_path": str | None,
                "adjustments": [...]
            }
        }
    """
    # STEP 1: 기존 키워드 매칭
    results, max_confidence = _keyword_match(user_message)
    
    metadata = {
        "crow_used": False,
        "dz_recent": False,
        "dz_file_path": None,
        "adjustments": []
    }
    
    # STEP 2: 저신뢰도 → Crow Memory 보강 [v2.0 D7] 단일 호출로 통합
    if max_confidence < LOW_CONFIDENCE_THRESHOLD:
        crow_bias = _query_crow_for_bias(user_message)
        if crow_bias:
            metadata["crow_used"] = True
            results = _apply_crow_bias(results, crow_bias, user_message)
            metadata["adjustments"].append({
                "source": "crow_memory",
                "details": crow_bias
            })
    
    # STEP 3: Dropzone 시간적 바인딩
    dz_info = _check_dropzone_session(user_message)
    if dz_info:
        metadata["dz_recent"] = True
        metadata["dz_file_path"] = dz_info.get("file_path")
        results = _apply_dz_bias(results, dz_info, user_message)
        metadata["adjustments"].append({
            "source": "dropzone",
            "details": dz_info
        })
    
    # STEP 4: 병합 및 정렬
    results.sort(key=lambda x: (-x[1], -x[2]))
    if not results:
        results = [("general_question", 0, 1.0)]
    
    return {"intents": results, "metadata": metadata}
```

#### 3.2.3 신규 함수: `_keyword_match(user_message: str) -> tuple[list, float]`

기존 `detect_intent()`의 키워드 매칭 로직을 분리:

```python
def _keyword_match(user_message: str):
    """기존 키워드 매칭 로직 (분리) → (results, max_confidence)"""
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
```

**개선사항:** 지시 대명사(demonstrative) 감지:

```python
DEMONSTRATIVES_KO = ["이거", "그거", "저거", "이것", "그것", "저것", "방금", "아까", "이 파일", "그 파일"]
DEMONSTRATIVES_EN = ["this", "that", "just now", "recently", "the file", "this file"]
```

지시 대명사가 감지되면 `file_share` 의도에 최소 신호(confidence 0.5)를 추가 — 이후 Crow/DZ 바이어스로 증폭.

#### 3.2.4 신규 함수: `_query_crow_for_bias(user_message: str) -> Optional[dict]` (v2.0 D7)

**목적**: Crow Memory에서 최근 컨텍스트를 조회하여 의도 바이어스 계산

**v2.0 변경**: 3중 개별 호출 → 단일 `try_crow_recall("recent_context", register="context", limit=3)` 호출 후 결과 파싱. 네트워크 지연 1/3로 감소.

```python
def _query_crow_for_bias(user_message: str) -> Optional[dict]:
    """
    Crow Memory에서 recent_context 조회 → 활성 레지스터 기반 바이어스
    
    [v2.0 D7] 단일 호출로 통합: context/bug/arch 3회 호출 → 1회 호출

    Returns:
        {
            "active_registers": ["context"],
            "bias": {
                "code_analysis": +2.5,
                "file_share": +1.0,
                "fix_loop": +3.0
            }
        }
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
            "bias": bias
        }
    except Exception:
        return None
```

#### 3.2.5 신규 함수: `_check_dropzone_session(user_message: str) -> Optional[dict]`

**목적**: `dz_session.json` 파일을 확인하여 최근 업로드된 파일 정보 반환

```python
def _check_dropzone_session(user_message: str) -> Optional[dict]:
    """
    dz_session.json 확인 → 3분 이내 업로드 + 지시 대명사 → file_share 바이어스

    Returns:
        {
            "file_path": "/path/to/uploaded/file.png",
            "file_name": "file.png",
            "uploaded_at": "2026-06-06T18:50:00Z",
            "seconds_ago": 90,
            "has_demonstrative": True
        }
        또는 None
    """
    import json
    from bridge.config import DZ_SESSION_FILE
    
    dz_file = os.path.expanduser(DZ_SESSION_FILE)
    if not os.path.exists(dz_file):
        return None
    
    try:
        with open(dz_file, 'r', encoding='utf-8', errors='replace') as f:
            session = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    
    # 세션 데이터 구조:
    # {
    #   "last_upload": {"file_path": "...", "file_name": "...", "timestamp": 1234567890.123},
    #   "history": [...]
    # }
    
    last_upload = session.get("last_upload")
    if not last_upload:
        return None
    
    # Unix timestamp 기반 시간 확인 (v2.0: _write_dz_session이 timestamp를 float으로 기록)
    uploaded_ts = last_upload.get("timestamp")
    if not uploaded_ts:
        return None
    
    now = time.time()
    seconds_ago = now - uploaded_ts
    
    if seconds_ago > DZ_TIME_THRESHOLD_MINUTES * 60:
        return None  # 너무 오래됨
    
    # 지시 대명사 확인
    has_demonstrative = _has_demonstrative(user_message)
    
    return {
        "file_path": last_upload.get("file_path", ""),
        "file_name": last_upload.get("file_name", ""),
        "uploaded_at": uploaded_ts,
        "seconds_ago": int(seconds_ago),
        "has_demonstrative": has_demonstrative
    }
```

#### 3.2.6 신규 함수: `_has_demonstrative(user_message: str) -> bool`

```python
def _has_demonstrative(user_message: str) -> bool:
    """한국어/영어 지시 대명사 포함 여부 확인"""
    msg = user_message.lower()
    
    ko_patterns = ["이거", "그거", "저거", "이것", "그것", "저것",
                   "방금", "아까", "이 파일", "그 파일", "저 파일",
                   "올린", "올렸", "첨부", "업로드"]
    en_patterns = ["this file", "that file", "just now", "recently",
                   "uploaded", "attached", "the file"]
    
    return any(p in msg for p in ko_patterns + en_patterns)
```

#### 3.2.7 신규 함수: `_apply_crow_bias(results, crow_bias, user_message) -> list`

```python
def _apply_crow_bias(results, crow_bias, user_message):
    """Crow Memory 바이어스를 기존 결과에 적용"""
    bias_map = crow_bias.get("bias", {})
    
    # 기존 결과에 바이어스 추가
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
```

#### 3.2.8 신규 함수: `_apply_dz_bias(results, dz_info, user_message) -> list`

```python
def _apply_dz_bias(results, dz_info, user_message):
    """Dropzone 시간적 바인딩 바이어스 적용"""
    has_demonstrative = dz_info.get("has_demonstrative", False)
    seconds_ago = dz_info.get("seconds_ago", 999)
    
    # 바이어스 강도 계산: 최근 + 지시대명사 → 높은 바이어스
    recency_factor = max(0, 1.0 - (seconds_ago / (DZ_TIME_THRESHOLD_MINUTES * 60)))
    bias_strength = recency_factor * (0.8 if has_demonstrative else 0.4)
    bias_value = bias_strength * 10.0 * DZ_BIAS_WEIGHT
    
    if bias_value <= 0:
        return results
    
    # file_share 의도 증폭 또는 추가
    existing = {r[0]: i for i, r in enumerate(results)}
    if "file_share" in existing:
        idx = existing["file_share"]
        name, priority, confidence = results[idx]
        results[idx] = (name, priority, min(confidence + bias_value, 10.0))
    else:
        results.append(("file_share", 10, min(bias_value, 10.0)))
    
    return results
```

#### 3.2.9 [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py): `ux_coordinator()` 수정

**Before:**
```python
def ux_coordinator(intent="auto", user_message="", context=""):
    if intent == "auto" and user_message:
        detected = detect_intent(user_message)
        if detected:
            intent = detected[0][0]
    hints = get_workflow_hints(intent)
    # ... 응답 구성 ...
```

**After:**
```python
def ux_coordinator(intent="auto", user_message="", context=""):
    metadata = {}
    
    if intent == "auto" and user_message:
        result = detect_intent_v2(user_message)  # [NEW] v2 호출
        intents = result["intents"]
        metadata = result["metadata"]
        
        if intents:
            intent = intents[0][0]
            
            # [NEW] Dropzone 바인딩: file_path 자동 주입
            if intent == "file_share" and metadata.get("dz_file_path"):
                # 응답에 드롭존 파일 경로 힌트 포함
                pass
    
    hints = get_workflow_hints(intent)
    
    # 응답 구성 (기존 + 메타데이터 추가)
    response_parts = [f"## 🧠 의도 분석 결과"]
    response_parts.append(f"- **감지된 의도**: `{intent}`")
    
    if metadata.get("crow_used"):
        response_parts.append(f"- **Crow 컨텍스트**: 활성화됨")
    if metadata.get("dz_recent"):
        file_name = os.path.basename(metadata.get("dz_file_path", ""))
        response_parts.append(f"- **최근 업로드**: `{file_name}` (Dropzone 바인딩)")
    
    # ... 기존 hints 처리 ...
    
    # [NEW] file_share + dz_file_path → 자동 분석 제안
    if intent == "file_share" and metadata.get("dz_file_path"):
        dz_path = metadata["dz_file_path"]
        response_parts.append("")
        response_parts.append("### 📎 Dropzone 자동 바인딩")
        response_parts.append(f"최근 업로드된 파일이 감지되었습니다: `{os.path.basename(dz_path)}`")
        response_parts.append(f"`auto_analyze_after_drop(file_path=\"{dz_path}\")` 호출을 제안합니다.")
    
    return "\n".join(response_parts)
```

#### 3.2.10 [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py): `_write_dz_session()` 신규 (v2.0 D1)

**목적**: 드롭존 업로드 시 `dz_session.json`에 세션 정보 기록

```python
# config에서 DZ_SESSION_FILE import
from bridge.config import DZ_SESSION_FILE

def _write_dz_session(file_path: str):
    """드롭존 세션 정보를 dz_session.json에 기록
    
    [v2.0 D1] 이 함수가 없으면 Pillar 2의 _check_dropzone_session()이
    항상 None을 반환하여 Dropzone 시간적 바인딩이 완전히 무력화됨.
    """
    import time, json, os
    
    dz_file = os.path.expanduser(DZ_SESSION_FILE)
    dz_dir = os.path.dirname(dz_file)
    os.makedirs(dz_dir, exist_ok=True)
    
    session = {
        "last_upload": {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "timestamp": time.time(),
        }
    }
    
    # 기존 세션 유지 + 새 업로드 추가
    try:
        if os.path.exists(dz_file):
            with open(dz_file, 'r', encoding='utf-8', errors='replace') as f:
                existing = json.load(f)
            existing["last_upload"] = session["last_upload"]
            # 최대 10개 히스토리 유지
            history = existing.get("history", [])
            history.insert(0, session["last_upload"])
            existing["history"] = history[:10]
            session = existing
    except Exception:
        pass
    
    with open(dz_file, 'w', encoding='utf-8') as f:
        json.dump(session, f)
```

이 함수는 [`auto_analyze_after_drop()`](mcp-servers/bridge/tools/ux_coordinator.py:63)의 시작 부분에서 호출:

```python
@mcp.tool
def auto_analyze_after_drop(file_path: str, user_intent: str = "") -> str:
    # [v2.0 D1] 세션 기록 — Pillar 2가 이 파일을 읽어 최근 업로드 감지
    _write_dz_session(file_path)
    
    if not os.path.exists(file_path):
        return f"⚠️ 파일을 찾을 수 없습니다: {file_path}"
    # ... 기존 분석 로직 ...
```

#### 3.2.11 [`intent_detector.py`](mcp-servers/bridge/intent_detector.py): `get_workflow_hints()` 수정 (v2.0 D6)

```python
def get_workflow_hints(intent: str) -> dict:
    workflow_map = {
        "file_share": {
            "primary_tool": "capture_screen",
            "primary_args": {"source": "dropzone"},
            "next_tool": "auto_analyze_after_drop",
            "description": "드롭존을 열어 파일 업로드를 요청합니다.",
            "suggested_response": "파일을 여기로 드래그하거나 업로드해 주세요."
        },
        "drawing_request": {
            "primary_tool": "draw_on_whiteboard",
            "primary_args": {},
            "next_tool": None,
            "description": "화이트보드에 그림을 그립니다.",
            "suggested_response": "어떤 다이어그램이나 그림을 원하시나요?"
        },
        "whiteboard_input": {
            "primary_tool": "get_whiteboard_state",
            "primary_args": {},
            "next_tool": "auto_analyze_whiteboard",
            "description": "화이트보드의 현재 상태를 읽고 분석합니다.",
            "suggested_response": "화이트보드 내용을 분석해 보겠습니다."
        },
        # [v2.0 D6] fix_loop 워크플로우 힌트 추가
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
            "suggested_response": "VibeZoo 설정을 진행하겠습니다."
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
```

#### 3.2.12 [`intent_detector.py`](mcp-servers/bridge/intent_detector.py) 신규 추가 함수

| 함수 | 상태 | 설명 |
|------|------|------|
| `detect_intent()` | **래퍼 유지** | 기존 호환성을 위해 `detect_intent_v2()` 래핑 |
| **`detect_intent_v2()`** | **신규** | Crow+DZ 통합 의도 감지 |
| **`_keyword_match()`** | **리팩터링** | 기존 키워드 로직 분리 + 지시대명사 + fix_loop (D6) |
| **`_query_crow_for_bias()`** | **신규 (v2.0 D7)** | Crow Memory 단일 호출 컨텍스트 조회 |
| **`_check_dropzone_session()`** | **신규** | dz_session.json 확인 |
| **`_has_demonstrative()`** | **신규** | 지시 대명사 감지 |
| **`_apply_crow_bias()`** | **신규** | Crow 바이어스 적용 |
| **`_apply_dz_bias()`** | **신규** | Dropzone 바이어스 적용 |
| **`_get_default_priority()`** | **신규** | 알려지지 않은 의도의 기본 우선순위 |
| `get_workflow_hints()` | **수정 (v2.0 D6)** | `fix_loop` 의도 추가 |

---

## 4. 데이터 흐름 다이어그램

### 4.1 Pillar 1: Ellipsis + Transactional Patch Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│              apply_patch(path, diff)  [v2.0 D4: normpath 검증]          │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     _parse_diff(diff)        │
                    │  → blocks[{search, replace}] │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼─────────────────────────┐
                    │  _resolve_and_validate_path()           │  ← [v2.0 D4 NEW]
                    │  → normpath + 프로젝트 루트 검증       │
                    │  → file_path: Path                     │
                    └──────────────┬──────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────────────┐
                    │         _preprocess_blocks(blocks, file)     │  ← [v2.0 D2/D5]
                    │                                              │
                    │  file_content = file_path.read_text(         │
                    │    encoding="utf-8", errors="replace")       │  ← [v2.0 D5]
                    │                                              │
                    │  for each block:                             │
                    │    ┌──────────────────────────────────┐     │
                    │    │  _detect_ellipsis(search)         │     │
                    │    │  → None | {header, footer, ...}   │     │
                    │    └──────────────┬───────────────────┘     │
                    │                   │                          │
                    │              ellipsis found?                 │
                    │               │          │                   │
                    │              YES        NO                   │
                    │               │          │                   │
                    │    ┌──────────▼────┐     │                   │
                    │    │ _resolve_     │     │                   │
                    │    │ ellipsis_text │     │                   │
                    │    │ → resolved    │     │                   │
                    │    └──────┬────────┘     │                   │
                    │           │              │                   │
                    │    ┌──────▼────────┐     │                   │
                    │    │ _resolve_     │     │                   │
                    │    │ ellipsis_ast  │     │  ← [v2.0 D3]
                    │    │ (try/except)  │     │     예외 시 None
                    │    │ [선택적 검증]  │     │     → text 결과 유지
                    │    └──────┬────────┘     │                   │
                    │           │              │                   │
                    │    block["search"] = resolved                │
                    │    block["_had_ellipsis"] = True             │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │     _apply_patch_transactional(...)          │
                    │                                              │
                    │  ┌─── PHASE 1: DRY-RUN ──────────────────┐  │
                    │  │  virtual = content (복사본)             │  │
                    │  │  for block in blocks:                  │  │
                    │  │    loc = _find_best_location(virtual)   │  │
                    │  │    if loc:                              │  │
                    │  │      virtual = apply(virtual, block)    │  │
                    │  │      record success + line info         │  │
                    │  │    else:                                │  │
                    │  │      record failure + similarity        │  │
                    │  │      BREAK (더 이상 진행 안 함)         │  │
                    │  └────────────────────────────────────────┘  │
                    │                                              │
                    │  ┌─── PHASE 2: COMMIT ────────────────────┐  │
                    │  │  if all_success:                        │  │
                    │  │    _backup_file(file_path)              │  │
                    │  │    file_path.write_text(virtual,        │  │
                    │  │      encoding="utf-8")                  │  │
                    │  │    → success report                     │  │
                    │  │  else:                                  │  │
                    │  │    discard virtual                      │  │
                    │  │    → _format_failure_report()           │  │
                    │  └────────────────────────────────────────┘  │
                    └──────────────────────────────────────────────┘
```

### 4.2 Pillar 2: Crow-Aware Intent Routing Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ux_coordinator(user_message)                       │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
              ┌──────────────────▼──────────────────────┐
              │         detect_intent_v2(msg)            │
              │                                          │
              │  ┌──────────────────────────────────┐    │
              │  │ STEP 1: _keyword_match(msg)       │    │
              │  │  → [(intent, pri, conf), ...]     │    │
              │  │  → max_confidence                 │    │
              │  │  [v2.0 D6] fix_loop 시그니처 포함 │    │
              │  └──────────────┬───────────────────┘    │
              │                 │                         │
              │        max_conf < 3.0?                    │
              │         │          │                      │
              │        YES        NO                      │
              │         │          │                      │
              │  ┌──────▼───────────────────────────┐    │
              │  │ STEP 2: _query_crow_for_bias()    │    │
              │  │  [v2.0 D7] 단일 호출:             │    │
              │  │  try_crow_recall(                 │    │
              │  │    "recent_context",              │    │
              │  │    register="context",            │    │
              │  │    limit=3                        │    │
              │  │  )                                │    │
              │  │  → 결과 텍스트 파싱               │    │
              │  │  → crow_bias: {intent: +score}    │    │
              │  │  → _apply_crow_bias(results)      │    │
              │  └──────────────┬───────────────────┘    │
              │                 │                         │
              │  ┌──────────────▼───────────────────┐    │
              │  │ STEP 3: _check_dropzone_session() │    │
              │  │  ┌─────────────────────────────┐  │    │
              │  │  │ DZ_SESSION_FILE 읽기         │  │    │
              │  │  │ → last_upload.timestamp      │  │    │
              │  │  │ → now - timestamp < 180s?    │  │    │
              │  │  │ → _has_demonstrative(msg)?   │  │    │
              │  │  └─────────────────────────────┘  │    │
              │  │  → dz_info: {file_path, ...}      │    │
              │  │  → _apply_dz_bias(results)        │    │
              │  └──────────────┬───────────────────┘    │
              │                 │                         │
              │  ┌──────────────▼───────────────────┐    │
              │  │ STEP 4: 병합 및 정렬               │    │
              │  │  sort by (-priority, -confidence) │    │
              │  │  → {intents: [...], metadata: {}} │    │
              │  └──────────────────────────────────┘    │
              └──────────────────┬──────────────────────┘
                                 │
              ┌──────────────────▼──────────────────────┐
              │      ux_coordinator 응답 구성            │
              │  - 감지된 의도 + 신뢰도                   │
              │  - Crow 컨텍스트 정보                     │
              │  - Dropzone 바인딩 정보                   │
              │  - 자동 file_path 주입 (해당 시)          │
              └──────────────────────────────────────────┘
```

### 4.3 모듈 간 의존성

```
editor.py
  ├── ast_engine.py       (AstEngine — ellipsis AST 검증, try/except 보호)
  ├── config.py           (VERSION)
  └── utils.py            (_markdown_header, _normalize_path, etc.)

intent_detector.py
  ├── crow_client.py      (try_crow_recall — [v2.0 D7] 단일 호출)
  └── config.py           (DZ_SESSION_FILE)

ux_coordinator.py
  ├── intent_detector.py  (detect_intent_v2, get_workflow_hints)
  ├── config.py           (DZ_SESSION_FILE — [v2.0 D1] _write_dz_session)
  └── (기존 의존성 유지)
```

---

## 5. 구현 순서 및 파일별 변경 목록

### v2.0 수정된 구현 순서

```
Phase A: editor.py (Pillar 1)
  1. _detect_ellipsis() 신규
  2. _resolve_ellipsis_text() 신규
  3. _resolve_ellipsis_ast() 신규 [v2.0 D3: try/except 보호]
  4. _preprocess_blocks() 신규 [v2.0 D2: _resolve_file() 제거, D5: 인코딩 명시]
  5. _resolve_and_validate_path() 신규 [v2.0 D4: normpath 검증]
  6. _apply_patch_transactional() 리팩터링 [v2.0 D4/D5 통합]
  7. _format_success_report(), _format_failure_report(), _compute_best_similarity() 신규
  8. apply_patch() 수정 (내부 호출 변경)
  9. _apply_patch_impl() 보존 (하위 호환)

Phase B: intent_detector.py (Pillar 2)
  1. _has_demonstrative() 신규
  2. _query_crow_for_bias() 신규 [v2.0 D7: 단일 호출]
  3. _check_dropzone_session() 신규
  4. _keyword_match() 리팩터링 [v2.0 D6: fix_loop 추가]
  5. _apply_crow_bias(), _apply_dz_bias(), _get_default_priority() 신규
  6. detect_intent_v2() 신규 (통합)
  7. INTENT_SIGNATURES 수정 [v2.0 D6: fix_loop 추가]
  8. get_workflow_hints() 수정 [v2.0 D6: fix_loop 항목 추가]
  9. detect_intent() 래퍼 유지 (하위 호환)

Phase C: ux_coordinator.py (Pillar 2 통합)
  1. _write_dz_session() 신규 [v2.0 D1]
  2. auto_analyze_after_drop() 수정 (_write_dz_session 호출 추가)
  3. ux_coordinator() 수정 (detect_intent_v2 사용)

Phase D: 통합 테스트
  1. 단위 테스트 (각 신규 함수)
  2. 통합 테스트 (Ellipsis + Transactional + Intent)
  3. 하위 호환 검증
```

### 파일별 상세 변경 목록

#### Phase A: [`editor.py`](mcp-servers/bridge/tools/editor.py)

| 순서 | 작업 | 설명 | v2.0 디버그 |
|------|------|------|-------------|
| A1 | 신규 함수 | `_detect_ellipsis()` | - |
| A2 | 신규 함수 | `_resolve_ellipsis_text()` | D2: `_resolve_file()` 의존성 제거됨 |
| A3 | 신규 함수 | `_resolve_ellipsis_ast()` | **D3**: 전체 try/except 감싸기, 실패 시 None 반환 |
| A4 | 신규 함수 | `_preprocess_blocks()` | **D2**: `_resolve_file()` 제거, 직접 read_text; **D5**: `encoding="utf-8", errors="replace"` |
| A5 | 신규 함수 | `_resolve_and_validate_path()` | **D4**: `os.path.normpath()` + 프로젝트 루트 검증 |
| A6 | 리팩터링 | `_apply_patch_transactional()` | **D4**: 경로 검증 호출; **D5**: 인코딩 명시 |
| A7 | 신규 함수 | `_format_success_report()`, `_format_failure_report()`, `_compute_best_similarity()` | - |
| A8 | 수정 | `apply_patch()` → `_apply_patch_transactional()` 호출 | - |
| A9 | 보존 | `_apply_patch_impl()` → `_apply_patch_transactional()`로 위임 | - |

#### Phase B: [`intent_detector.py`](mcp-servers/bridge/intent_detector.py)

| 순서 | 작업 | 설명 | v2.0 디버그 |
|------|------|------|-------------|
| B1 | 신규 함수 | `_has_demonstrative()` | - |
| B2 | 신규 함수 | `_query_crow_for_bias()` | **D7**: 3중 호출 → 단일 `try_crow_recall("recent_context", register="context", limit=3)` |
| B3 | 신규 함수 | `_check_dropzone_session()` | timestamp 파싱을 Unix float에 맞춤 (D1과 연계) |
| B4 | 리팩터링 | `_keyword_match()` | **D6**: `fix_loop` 시그니처 매칭 로직 포함 |
| B5 | 신규 함수 | `_apply_crow_bias()`, `_apply_dz_bias()`, `_get_default_priority()` | - |
| B6 | 신규 함수 | `detect_intent_v2()` | 통합 감지 |
| B7 | 수정 | `INTENT_SIGNATURES` | **D6**: `fix_loop` 항목 추가, `code_analysis` priority 7→6 |
| B8 | 수정 | `get_workflow_hints()` | **D6**: `fix_loop` 워크플로우 추가 |
| B9 | 래퍼 | `detect_intent()` → `detect_intent_v2()` 호출 + list[intents] 반환 | 하위 호환 유지 |

#### Phase C: [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py)

| 순서 | 작업 | 설명 | v2.0 디버그 |
|------|------|------|-------------|
| C1 | 신규 함수 | `_write_dz_session()` | **D1**: `dz_session.json` Writer |
| C2 | 수정 | `auto_analyze_after_drop()` | **D1**: 시작 부분에서 `_write_dz_session(file_path)` 호출 |
| C3 | 수정 | `ux_coordinator()` | `detect_intent_v2()` 사용 + 메타데이터 표시 |

---

## 6. 엣지 케이스 분석 및 대응 방안

### 6.1 Pillar 1: Ellipsis Resolution

| # | 엣지 케이스 | 위험 | 대응 방안 |
|---|------------|------|-----------|
| E1 | **Ellipsis가 SEARCH 블록의 맨 처음 또는 맨 끝에 있는 경우** | header 또는 footer가 비어있어 매칭 불가 | `_detect_ellipsis()`에서 header/footer 중 하나라도 비어있으면 None 반환 → 기존 fuzzy matching으로 폴백 |
| E2 | **여러 개의 분리된 ellipsis (예: `# ... A ... # ... B ...`)** | 복잡한 다중 gap 처리 필요 | 첫 번째 ellipsis만 해결하고 나머지는 무시. LLM이 단일 ellipsis 사용을 권장하는 문서화 추가 |
| E3 | **Header/footer가 파일 내에서 여러 번 등장** | 잘못된 위치 매칭 | Header는 파일 앞쪽부터 검색, footer는 header 이후에서만 검색. AST 검증으로 동일 scope 확인 |
| E4 | **Ellipsis가 주석 내부가 아닌 문자열 리터럴 내 `...`** | 오탐지 | `_detect_ellipsis()` 패턴에 줄 시작 앵커(`^`)와 주석 구분자(`#`, `//`) 필수 포함 |
| E5 | **너무 큰 gap (>1000줄)** | 의도치 않은 대량 코드 포함 | `_resolve_ellipsis_text()`에서 gap > 1000줄이면 경고 로그 + 진행 (LLM이 의도한 것일 수 있음) |
| E6 | **Tree-sitter 미설치 환경** | AST 검증 불가 | `_resolve_ellipsis_ast()` 초기화 실패 → None 반환 → `_resolve_ellipsis_text()` 결과 사용 (D3 폴백) |
| E7 | **Ellipsis 해결 후에도 SEARCH 블록이 파일에 exact match 안 됨** | 전처리 실패 | `_apply_patch_transactional`의 dry-run 단계에서 `_find_best_location()` 검증 → 실패 시 상세 오류 보고 |
| E8 | **Ellipsis 패턴이 파일 확장자와 다른 주석 스타일** | 감지 실패 | 모든 주석 스타일(`#`, `//`, `/* */`)을 모든 파일에서 검사 → 언어별 필터링 안 함 |
| **E9** | **AST 파싱 중 MemoryError / SyntaxError** | **v2.0 D3** | `_resolve_ellipsis_ast()` try/except → None 반환 → text 결과 유지 |

### 6.2 Pillar 1: Transactional Patching

| # | 엣지 케이스 | 위험 | 대응 방안 |
|---|------------|------|-----------|
| T1 | **블록 3 실패 시 블록 1, 2의 변경사항이 메모리에 남음** | 메모리 낭비 (파일은 안전) | Dry-run 종료 후 virtual 버퍼 즉시 폐기. Python GC에 의존 |
| T2 | **디스크 쓰기 중 OS 레벨 장애 (부분 쓰기)** | 파일 손상 가능성 | 백업 먼저 생성 후 덮어쓰기 (현재 로직 유지) |
| T3 | **백업 디렉토리 생성 실패** | 백업 없이 파일 수정 | `_backup_file()` 실패 시 경고 플래그 설정. 그래도 쓰기 진행 |
| T4 | **빈 SEARCH 블록** | 의미 없는 패치 | `_parse_diff()`에서 이미 strip() → 빈 블록은 파싱 단계에서 제외됨 |
| T5 | **REPLACE가 SEARCH와 동일** | No-op 패치 | Dry-run에서 exact match로 감지 → applied=0으로 기록. 쓰기는 정상 진행 |
| T6 | **동일 파일에 대한 동시 패치 요청** | Race condition | MCP 요청이 순차적이므로 일반적으론 발생 안 함. 추후 파일 락 고려 |
| **T7** | **Path traversal 공격 (`../../etc/passwd`)** | **v2.0 D4** | `_resolve_and_validate_path()`에서 `os.path.normpath()` + 프로젝트 루트 `relative_to()` 검증 |
| **T8** | **파일 인코딩 불일치 (UTF-8 아닌 파일)** | **v2.0 D5** | `read_text(encoding="utf-8", errors="replace")`로 손상 문자 대체 |

### 6.3 Pillar 2: Intent Detection

| # | 엣지 케이스 | 위험 | 대응 방안 |
|---|------------|------|-----------|
| I1 | **Crow Memory 서버 비활성 (localhost:9020 다운)** | `try_crow_recall()` 실패 | 3초 타임아웃 + 빈 리스트 반환 → Crow 바이어스 없이 진행. `crow_used: False` |
| I2 | **`dz_session.json` 파일 없음** | Dropzone 바인딩 불가 | `_check_dropzone_session()` → 파일 없으면 None 반환. 정상 동작 |
| **I2a** | **`_write_dz_session()` 누락** | **v2.0 D1: dz_session.json이 영원히 생성되지 않아 Dropzone 바인딩 무력화** | `auto_analyze_after_drop()` 시작 부분에서 항상 `_write_dz_session()` 호출 |
| I3 | **`dz_session.json` JSON 파싱 오류** | corrupted 세션 파일 | try/except → None 반환. 로그만 남기고 무시 |
| I4 | **지시 대명사만 있고 실제 파일 업로드는 없는 경우** | False positive file_share | `_check_dropzone_session()`에서 세션 파일 미존재 → dz_info = None → 바이어스 없음 |
| I5 | **키워드 매칭은 높지만 Crow 컨텍스트와 충돌** | 의도 혼란 | 키워드 매칭 신뢰도 ≥ 3.0이면 Crow/DZ 보강 단계 스킵. 키워드 우선 |
| I6 | **`user_message`가 매우 짧음 ("이거")** | 모든 키워드 매칭 0 | 지시대명사 감지 → 약한 file_share 신호(0.5) → Crow+DZ 바이어스로 증폭 |
| I7 | **다중 레지스터에서 상충하는 바이어스** | 의도 충돌 | 모든 바이어스 합산. 우선순위(priority)는 원래 시그니처 값 유지. confidence만 조정 |
| I8 | **Dropzone 파일이 3분 1초 전 업로드** | Threshold 경계 | `seconds_ago > 180` → 제외. recency_factor가 0에 수렴하므로 자연스러운 감쇠 |
| **I9** | **Crow 3중 호출 지연 (최대 9초)** | **v2.0 D7** | 단일 `try_crow_recall("recent_context", register="context", limit=3)` 호출로 통합 (최대 3초) |
| **I10** | **`fix_loop` 의도 감지 불가** | **v2.0 D6** | `INTENT_SIGNATURES`에 `fix_loop` 추가 + `get_workflow_hints()`에 워크플로우 추가 |

---

## 7. 테스트 전략

### 7.1 Pillar 1 단위 테스트 시나리오

```python
# Test: _detect_ellipsis

# Python ellipsis
assert _detect_ellipsis("def foo():\n    pass\n# ... existing code ...\n    return x")
# → {"header": "def foo():\n    pass", "footer": "    return x", "style": "line_comment"}

# JS/TS ellipsis
assert _detect_ellipsis("function bar() {\n  init();\n  // ... rest ...\n  cleanup();\n}")
# → {"header": "function bar() {\n  init();", "footer": "  cleanup();\n}", "style": "line_comment"}

# Block ellipsis
assert _detect_ellipsis("start()\n/* ... middle ... */\nend()")
# → {"header": "start()", "footer": "end()", "style": "block_comment"}

# No ellipsis
assert _detect_ellipsis("exact_match_code") is None

# Empty header (ellipsis at start)
assert _detect_ellipsis("# ...\ndef foo(): pass") is None

# Test: _resolve_ellipsis_text
file_content = "def outer():\n    init()\n    do_work()\n    more_work()\n    cleanup()\n"
ell_info = {"header": "def outer():\n    init()", "footer": "    cleanup()"}
resolved = _resolve_ellipsis_text(file_content, ell_info)
assert "do_work" in resolved and "more_work" in resolved

# Test: _resolve_ellipsis_ast exception safety [v2.0 D3]
# AST 파싱 실패 시 None 반환 (Exception 발생 안 함)
result = _resolve_ellipsis_ast("bad_file.py", "invalid === content", ell_info)
assert result is None  # 예외 발생 안 하고 None 반환

# Test: _resolve_and_validate_path traversal prevention [v2.0 D4]
# 프로젝트 루트 바깥 경로는 None 반환
assert _resolve_and_validate_path("../../../etc/passwd", "", ".") is None

# Test: _apply_patch_transactional (no ellipsis, original behavior)
result = _apply_patch_transactional(path="test.py", diff="""
<<<<<<< SEARCH
old_code
-------
new_code
>>>>>>> REPLACE
""")
assert "✅" in result

# Test: _apply_patch_transactional (with ellipsis)
result = _apply_patch_transactional(path="test.py", diff="""
<<<<<<< SEARCH
def foo():
    init()
    # ... existing code ...
    cleanup()
-------
def foo():
    init()
    new_step()
    cleanup()
>>>>>>> REPLACE
""")
assert "✅" in result

# Test: Transactional rollback
result = _apply_patch_transactional(path="test.py", diff="""
<<<<<<< SEARCH
good_block
-------
replaced
>>>>>>> REPLACE
<<<<<<< SEARCH
nonexistent_block_xyz
-------
something
>>>>>>> REPLACE
""")
assert "❌" in result
assert "롤백" in result
```

### 7.2 Pillar 2 단위 테스트 시나리오

```python
# Test: _has_demonstrative
assert _has_demonstrative("이거 분석해줘") == True
assert _has_demonstrative("방금 올린 파일 확인해줘") == True
assert _has_demonstrative("this file please") == True
assert _has_demonstrative("코드 리뷰 해줘") == False

# Test: detect_intent_v2 (normal keyword match → no Crow/DZ)
result = detect_intent_v2("코드 분석해줘")
assert result["intents"][0][0] == "code_analysis"
assert result["metadata"]["crow_used"] == False
assert result["metadata"]["dz_recent"] == False

# Test: detect_intent_v2 fix_loop detection [v2.0 D6]
result = detect_intent_v2("버그 고쳐줘")
assert result["intents"][0][0] == "fix_loop"

# Test: detect_intent_v2 (ambiguous → Crow fallback)
# (Crow가 활성화된 환경에서)
result = detect_intent_v2("이거 확인해봐")
# intents 리스트 반환 (file_share 또는 code_analysis amplified)

# Test: detect_intent_v2 (dz_session present + demonstrative)
# (dz_session.json에 최근 업로드가 있는 환경에서)
result = detect_intent_v2("방금 올린 파일 분석해줘")
assert result["metadata"]["dz_recent"] == True
assert result["metadata"]["dz_file_path"] is not None

# Test: Backward compatibility
old_result = detect_intent("코드 분석해줘")
assert old_result[0][0] == "code_analysis"  # 기존 API 그대로 동작

# Test: _write_dz_session + _check_dropzone_session integration [v2.0 D1]
# 임시 파일로 dz_session 테스트
_write_dz_session("/tmp/test_upload.png")
dz_info = _check_dropzone_session("방금 올린 파일 분석해줘")
assert dz_info is not None
assert dz_info["file_name"] == "test_upload.png"
assert dz_info["has_demonstrative"] == True
```

### 7.3 통합 시나리오

| 시나리오 | 입력 | 기대 결과 |
|----------|------|-----------|
| S1 | Ellipsis 패치 + 성공 | 파일 수정됨, 백업 생성, "ellipsis 해결됨" 표시 |
| S2 | Ellipsis 패치 + 실패 | 파일 미수정, 상세 실패 보고서, 롤백 확인 |
| S3 | 일반 패치 (no ellipsis) | 기존과 동일하게 동작 |
| S4 | "이거 분석해줘" + Dropzone 파일 있음 | file_share 감지, auto_analyze_after_drop 제안 |
| S5 | "이거 분석해줘" + Dropzone 파일 없음 + Crow 디버깅 컨텍스트 | code_analysis 또는 fix_loop 감지 |
| S6 | "코드 리뷰해줘" (명확한 키워드) | Crow/DZ 무시, 키워드 매칭 우선 |
| S7 | "버그 고쳐줘" + 빌드 에러 있음 [v2.0 D6] | fix_loop 감지, auto_fix_status → retry_build 제안 |
| S8 | Path traversal 시도 [v2.0 D4] | `_resolve_and_validate_path()` → None → 오류 반환 |
| S9 | AST 파싱 실패 + ellipsis [v2.0 D3] | `_resolve_ellipsis_ast()` → None → text 결과로 폴백, 패치 성공 |

---

## 부록 A: 변경 파일 요약

| 파일 | 변경 유형 | 새 함수 수 | 수정 함수 수 | 총 라인 변화 (예상) | v2.0 디버그 영향 |
|------|----------|-----------|-------------|---------------------|------------------|
| [`editor.py`](mcp-servers/bridge/tools/editor.py) | 대규모 추가 + 리팩터링 | 9 | 1 | +280~340 | D2,D3,D4,D5 반영 |
| [`intent_detector.py`](mcp-servers/bridge/intent_detector.py) | 중규모 추가 + 리팩터링 | 8 | 3 | +200~250 | D6,D7 반영 |
| [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) | 소규모 수정 + 신규 함수 | 1 | 2 | +30~50 | D1 반영 |

## 부록 B: 제약 조건 준수 확인

| 제약 조건 | 준수 방법 |
|-----------|----------|
| VibeZoo 브릿지 내부만 변경 | 모든 변경은 `mcp-servers/bridge/` 내 |
| Crow Memory 서버 변경 없음 | `crow_client.py`의 기존 함수만 사용 (v2.0 D7: 단일 호출로 최적화) |
| Ellipsis 없는 경우 원래 로직 유지 | `_detect_ellipsis()` → None → 기존 `_find_best_location()` 경로 |
| Windows 환경 호환 | `Path`, `os.path`, `json` 표준 라이브러리만 사용 |
| PyYAML 등 새 외부 의존성 금지 | `json`, `re`, `difflib`, `pathlib`, `datetime`, `time`, `os` 등 표준 라이브러리만 |
| 기존 `detect_intent()` API 유지 | `detect_intent()` → 내부적으로 `detect_intent_v2()` 래핑, 반환 형식 유지 |
| 경로 검증 (v2.0 D4) | `os.path.normpath()` + `Path.resolve().relative_to(project_root)` |
| 예외 안전성 (v2.0 D3) | `_resolve_ellipsis_ast()` try/except → 실패 시 None → text 폴백 |

## 부록 C: v2.0 디버그 변경사항 추적 매트릭스

| 디버그 ID | 심각도 | 함수/영역 | 변경 내용 | 검증 방법 |
|-----------|--------|-----------|-----------|-----------|
| D1 | 🔴 CRITICAL | `ux_coordinator.py::_write_dz_session()` | 신규 함수 + `auto_analyze_after_drop()`에서 호출 | Dropzone 업로드 후 dz_session.json 생성 확인 |
| D2 | 🔴 CRITICAL | `editor.py::_preprocess_blocks()` | `_resolve_file()` 제거, 직접 `read_text()` 사용 | `NameError` 미발생 확인 |
| D3 | 🔴 CRITICAL | `editor.py::_resolve_ellipsis_ast()` | try/except 전체 감싸기, 실패 시 None | AST 예외 상황에서 패치 정상 동작 |
| D4 | 🟡 MEDIUM | `editor.py::_resolve_and_validate_path()` | `normpath()` + 루트 검증 | `../../../etc/passwd` 차단 확인 |
| D5 | 🟡 MEDIUM | `editor.py::_preprocess_blocks()` 외 | 모든 `read_text()`에 `encoding="utf-8", errors="replace"` | 비UTF-8 파일 처리 확인 |
| D6 | 🟡 MEDIUM | `intent_detector.py::INTENT_SIGNATURES`, `get_workflow_hints()` | `fix_loop` 시그니처 + 워크플로우 추가 | "버그 고쳐줘" → fix_loop 감지 확인 |
| D7 | 🟡 MEDIUM | `intent_detector.py::_query_crow_for_bias()` | 3회 호출 → 1회 `try_crow_recall("recent_context", register="context", limit=3)` | Crow 응답 시간 1/3 감소 확인 |
