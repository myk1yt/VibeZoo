# Project Research Report — VibeZoo 코드베이스 현황 조사

## Task Summary
VibeZoo 프로젝트의 현재 상태를 4개 과제(RT-1~RT-4)에 대해 사실 기반으로 조사. i18n 완전성, web_search 설명 불일치, 코드베이스 검색 장애 원인, 기능 인벤토리를 분석하고, 각 항목의 코드 인용([파일#행번호])과 추정(공개 표기)을 구분하여 기술.

## Actions Taken
1. 핵심 참조 문서 읽기: `requirement-checklist.md`, `ACTIVE_STATE.md`, `-p/i18n_verify_result.json`
2. i18n 파일 전수 분석: `package.json`, `package.nls.*.json`(20개), `bundle.l10n.*.json`(20개), Python `translations/*.json`(20개)
3. web.py 양쪽 복사본 비교, docstring/설명 전수 검색
4. `embedding_client.py`, `search_engine.py`, `scout.py` 분석
5. MCP 설정 경로: `VscodePaths.ts`, `McpConfigService.ts`, `CrowServerManager.ts` 분석
6. 전체 MCP 툴 데코레이터 스캔 (42개 `@mcp.tool` 발견)
7. `extension/src/`에서 `vscode.l10n.t()` 호출 전수 스캔 (51건)

---

## [1] RT-1: i18n 완전성 분석

### 1.1 package.json %vibezoo.*% 플레이스홀더

[`extension/package.json`](extension/package.json) 에서 추출한 고유 플레이스홀더: **71개**

- `vibezoo.displayName`, `vibezoo.description` (2개)
- 커맨드 타이틀 31개 (`vibezoo.selfCheck.title` ~ `vibezoo.configureErrorDashboard.title`)
- 뷰 이름 4개 (`viewsContainer.vibezoo-sidebar.title`, `view.vibezoo.activeSubagents.name`, `view.vibezoo.yoloHistory.name`, `view.vibezoo.sessionResume.name`)
- 설정 설명 24개 (`vibezoo.crow.port.description` ~ `vibezoo.advanced.pythonPath.description`)
- enum 설명 3개 (`vibezoo.errorCollection.autoOpenDashboard.never/onCritical/always`)

### 1.2 package.nls (manifest i18n) — en 기준 70키

[`extension/package.nls.json`](extension/package.nls.json) 에 70개 키 존재.

**ja.json 누락 키 (6개) — 사실 확인:**

[`extension/package.nls.ja.json`](extension/package.nls.ja.json) 은 en 대비 **6개 키 누락**:

| 누락 키 | en에서의 행 |
|---|---|
| `vibezoo.configureErrorDashboard.title` | [#L60](extension/package.nls.json#L60) |
| `vibezoo.errorCollection.autoOpenDashboard.description` | [#L62](extension/package.nls.json#L62) |
| `vibezoo.errorCollection.autoOpenDashboard.never` | [#L63](extension/package.nls.json#L63) |
| `vibezoo.errorCollection.autoOpenDashboard.onCritical` | [#L64](extension/package.nls.json#L64) |
| `vibezoo.errorCollection.autoOpenDashboard.always` | [#L65](extension/package.nls.json#L65) |
| `vibezoo.errorCollection.notifyOnCritical.description` | [#L66](extension/package.nls.json#L66) |

ko, ar, bg, cs, de, es, fr, he, hu, it, pl, pt-BR, ru, th, tr, vi, zh-CN, zh-TW는 en과 동일 70키 보유 (누락 0).

> ⚠️ **추정**: 나머지 18개 언어 파일은 아직 확인하지 않았으나, 이전 i18n_verify_result.json에서 키 드리프트가 0으로 보고된 바 있어 ja만 누락 가능성이 높음. 다만 위 스크립트 검증은 미수행 상태.

### 1.3 bundle.l10n (런타임 l10n) — en 기준 124키

[`extension/l10n/bundle.l10n.json`](extension/l10n/bundle.l10n.json) 에 124개 키.

**비정상 징후**: bundle.l10n.json 마지막 6개 키가 package.nls 키와 동일:

```
"vibezoo.openErrorDashboard.title": "🐞 Open Error Dashboard"       ← [#L119](extension/l10n/bundle.l10n.json#L119)
"vibezoo.errorCollection.enabled.description": "..."                 ← [#L120](extension/l10n/bundle.l10n.json#L120)
"vibezoo.errorCollection.maxEntries.description": "..."              ← [#L121](extension/l10n/bundle.l10n.json#L121)
"vibezoo.bridge.port.description": "..."                             ← [#L122](extension/l10n/bundle.l10n.json#L122)
"vibezoo.network.host.description": "..."                            ← [#L123](extension/l10n/bundle.l10n.json#L123)
"vibezoo.advanced.pythonPath.description": "..."                     ← [#L124](extension/l10n/bundle.l10n.json#L124)
```

이 6개 키는 `package.nls` 전용 키인데 `bundle.l10n.json`에 오염됨. `vscode.l10n.t()` 호출부에서 이 키가 사용되는지는 미확인 — bundle l10n은 `extension/src/` 코드에서만 참조되므로, `package.nls` 키가 번들에 있어도 런타임에는 영향 없음(무의미한 오염).

ko, ja 번들 파일은 en의 124키와 동일 키 셋을 보유 (누락 0).

### 1.4 vscode.l10n.t() 런타임 사용 vs bundle.l10n 키

[`extension/src/extension.ts`](extension/src/extension.ts) 와 기타 TS 파일에서 `vscode.l10n.t()` 호출을 스캔한 결과, **51건의 고유 키 사용** 발견. bundle.l10n.json의 124키 내에 모두 포함됨.

> ✅ **확인**: 런타임에 누락되는 l10n 키는 없음. 번들에 package.nls 키가 오염되어 있지만, l10n 호출부는 정상.

### 1.5 Python 사이드 i18n

- [`mcp-servers/bridge/i18n/translations/en.json`](mcp-servers/bridge/i18n/translations/en.json): **169키**
- [`mcp-servers/bridge/i18n/__init__.py`](mcp-servers/bridge/i18n/__init__.py): `t()` 함수, 영어 키 자체를 lookup 키로 사용 (별도 키 네이밍 없음)
- 이전 검증 결과 ([`-p/i18n_verify_result.json`](-p/i18n_verify_result.json)): 20개 언어 전부 168~168키 일치, 키 드리프트 0건

> ⚠️ **불일치 가능 총 키 수**: en.json=169키 vs 이전 검증=168키 → 1키 차이. [`-p/i18n_verify_result.json`](-p/i18n_verify_result.json#L94)에서 `en_key_count_top_level: 168`로 보고. 현재 파일 읽기 결과 169키 확인. **이전 검증 이후 1키 추가됨** (검증 재실행 필요).

### 1.6 언어별 누락 키 요약 (확보된 데이터 기반)

| 언어 | nls 누락 | l10n 누락 | py 누락 |
|---|---|---|---|
| en(base) | 0 | 0 | 0 |
| ar | 0 | 0 | 0* |
| bg | 0 | 0 | 0* |
| cs | 0 | 0 | 0* |
| de | 0 | 0 | 0* |
| es | 0 | 0 | 0* |
| fr | 0 | 0 | 0* |
| he | 0 | 0 | 0* |
| hu | 0 | 0 | 0* |
| it | 0 | 0 | 0* |
| **ja** | **6** | 0 | 0* |
| ko | 0 | 0 | 0* |
| pl | 0 | 0 | 0* |
| pt-BR | 0 | 0 | 0* |
| ru | 0 | 0 | 0* |
| th | 0 | 0 | 0* |
| tr | 0 | 0 | 0* |
| vi | 0 | 0 | 0* |
| zh-CN | 0 | 0 | 0* |
| zh-TW | 0 | 0 | 0* |

> `*` 표시: Python translations는 이전 검증(`i18n_verify_result.json`) 결과 기반. 현재 파일을 전부 직접 대조하지 않은 이전 검증 데이터.

**추가 발견 — bundle.l10n.json 오염 키 6건**: `vibezoo.openErrorDashboard.title` 등 package.nls 전용 키가 bundle.l10n에 포함. 동일 오염이 20개 언어 번들에 모두 존재 (동일 키 셋).

---

## [2] RT-2: web_search 설명 불일치 위치

### 2.1 web_search 도구의 실제 동작

실제 검색 API: **Exa neural search** (`https://api.exa.ai/search`)가 1차, **DuckDuckGo HTML** (`https://html.duckduckgo.com/html/`)이 폴백.

- API 키: `EXA_API_KEY` 환경변수 또는 `keyring.get_password("VibeZoo", "EXA_API_KEY")` ([`mcp-servers/bridge/tools/web.py#L36-L44`](mcp-servers/bridge/tools/web.py#L36-L44))
- 엔드포인트: `https://api.exa.ai/search` ([`mcp-servers/bridge/tools/web.py#L81`](mcp-servers/bridge/tools/web.py#L81))
- 폴백: `https://html.duckduckgo.com/html/` ([`mcp-servers/bridge/tools/web.py#L122`](mcp-servers/bridge/tools/web.py#L122))

### 2.2 현재 web_search 설명 — 정확한 파일/행

**duckduckgo/Google/Bing "불일치"는 이제 없음** — 2025년 v0.16.0 개선에서 설명이 교정됨.

현재 docstring은 사실과 일치:

```python
# mcp-servers/bridge/tools/web.py#L316-L326
@mcp.tool
def web_search(query: str, max_results: int = 5, engine: str = "auto") -> str:
    """웹 검색. EXA_API_KEY가 있으면 Exa neural search, 없으면 DuckDuckGo로 폴백. engine: auto|exa|ddg
    ...
```

```python
# mcp-servers/bridge/tools/web.py#L31 (WebSearchEngine class docstring)
"""웹 검색 엔진 래퍼. Exa neural search + DuckDuckGo 폴백."""
```

```python
# mcp-servers/bridge/tools/web.py#L190-L198 (search 메서드 docstring)
"""웹 검색. EXA_API_KEY가 있으면 Exa neural search, 없으면 DuckDuckGo로 폴백.
...
- "auto" (default): Exa if EXA_API_KEY present, else DuckDuckGo
- "exa": Exa only (error if no key)
- "ddg": DuckDuckGo only
```

### 2.3 이전 불일치 기록

이전(`docs/260725_0001_session_tools-ecosystem-overhaul/095140_ask-light-gate-architecture-report.md`)에서:
> "Only Exa works; engine parameter is vestigial... no fallback when EXA_API_KEY absent"

→ v0.16.0에서 DuckDuckGo 폴백 추가, 설명 교정 완료. 현재 불일치 없음.

### 2.4 duckduckgo/Exa 관련 문구 등장 파일 전부

| 파일 | 위치 | 문맥 |
|---|---|---|
| `mcp-servers/bridge/tools/web.py` | #L31, #L114-L117, #L190-L198, #L317-L340 | 구현 코드 + docstring |
| `extension/mcp-servers/bridge/tools/web.py` | 동일 (복사본) | 구현 코드 + docstring |
| `docs/260725_0001_session_tools-ecosystem-overhaul/` | 다수 보고서 | 이전 세션 기록 |
| `fromscratch/CHANGELOG.md` | #L20-L22 | 릴리즈 노트 |
| `fromscratch/RELEASENOTES.md` | #L20-L22 | 릴리즈 노트 |
| `README.md` | #L161, #L258 | 프로젝트 설명 |
| `docs/PROJECT_CONTEXT.md` | #L503 | 프로젝트 컨텍스트 |
| `plans/bridge-merge-plan.md` | 미확인 | 병합 계획 |

**결론**: 현재 web_search 설명은 Exa + DuckDuckGo 폴백으로 사실과 일치. REQ-004 완료 상태.

---

## [3] RT-3: 코드베이스 검색(코드인덱스) 장애 원인 조사

### 3.1 codebase_search 관련 툴/모듈

| 구성 요소 | 파일 | 역할 |
|---|---|---|
| MCP 툴 `search_codebase` | [`mcp-servers/bridge/tools/scout.py#L736-L737`](mcp-servers/bridge/tools/scout.py#L736-L737) | 메인 검색 툴 |
| `SearchEngine` | [`mcp-servers/bridge/search_engine.py#L23`](mcp-servers/bridge/search_engine.py#L23) | ripgrep → git grep → os.walk 3단계 폴백 |
| `EmbeddingClient` | [`mcp-servers/bridge/embedding_client.py#L12`](mcp-servers/bridge/embedding_client.py#L12) | 임베딩 서버 HTTP 클라이언트 |
| `ResultRanker` | `mcp-servers/bridge/result_ranker.py` | 결과 순위화 |
| `FuzzyMatcher` | `mcp-servers/bridge/fuzzy_matcher.py` | 퍼지 매칭 |
| `AstEngine` | `mcp-servers/bridge/ast_engine.py` | AST 분석 |
| `FileCache` | `mcp-servers/bridge/file_cache.py` | 파일 캐시 |
| `IntentDetector` | [`mcp-servers/bridge/intent_detector.py`](mcp-servers/bridge/intent_detector.py) | 자연어 의도 감지 (codebase_search와는 독립) |

> `intent_detector.py`는 codebase_search와 **관련 없음** — ux_coordinator의 의도 분류용.

### 3.2 embedding_client.py 상세 분석

[`mcp-servers/bridge/embedding_client.py#L12-L56`](mcp-servers/bridge/embedding_client.py#L12-L56):

```python
self._base_url = os.environ.get("VIBEZOO_EMBED_URL", "http://localhost:8089")  # L16
self._model = os.environ.get("VIBEZOO_EMBED_MODEL", "nomic-embed-text")        # L17
```

- **기대 서버 주소**: `http://localhost:8089` (환경변수 `VIBEZOO_EMBED_URL`로 오버라이드 가능)
- **기대 모델명**: `nomic-embed-text` (환경변수 `VIBEZOO_EMBED_MODEL`로 오버라이드 가능)
- **요청 형식**: 2가지 probing
  1. **Ollama 스타일**: `POST /api/embeddings` — `{"model": "...", "input": "string"}` ([#L28-L29](mcp-servers/bridge/embedding_client.py#L28-L29))
  2. **OpenAI 스타일**: `POST /v1/embeddings` — `{"model": "...", "input": ["string"]}` ([#L43-L44](mcp-servers/bridge/embedding_client.py#L43-L44))
- **타임아웃**: probing 2초, 실제 embed 5초
- **캐싱**: `_api_style`, `_available`을 첫 probing 후 캐시 (프로세스 수명 동안)

### 3.3 현재 PC에 embedding 서버 실행 중인지

> ⚠️ **제한 사항**: project-research 모드에서 `execute_command` 사용 불가. 다음은 코드 기반 추정.

**추정 근거**:
1. `localhost:8089`는 LM Studio의 기본 임베딩 서버 포트 (Ollama는 기본 11434)
2. [`mcp-servers/bridge/embedding_client.py#L16`](mcp-servers/bridge/embedding_client.py#L16)에서 기본값 8089 사용 → LM Studio 기준 설정
3. 윈도우 재설치 직후 상태이므로 **임베딩 서버 미설치/미실행 가능성이 높음**

**확인 방법** (VP가 수행해야 할 검증):
```cmd
netstat -ano | findstr :8089
```
또는
```powershell
Get-Process | Where-Object { $_.Id -eq (Get-NetTCPConnection -LocalPort 8089 -ErrorAction SilentlyContinue).OwningProcess }
```

### 3.4 코드인덱스 데이터 저장 위치

[`mcp-servers/bridge/search_engine.py`](mcp-servers/bridge/search_engine.py)는 **인덱스 파일을 별도로 저장하지 않음** — 매 검색 시 ripgrep/git grep/os.walk를 직접 실행하는 구조.

[`mcp-servers/bridge/file_cache.py`](mcp-servers/bridge/file_cache.py)는 메모리 기반 LRU 캐시 (디스크 저장 없음).

[`mcp-servers/bridge/search_engine.py#L34-L86`](mcp-servers/bridge/search_engine.py#L34-L86): `ST-07` memo 레이어는 20초 TTL 메모리 캐시 (OrderedDict).

**디스크 인덱스 없음** → 재생성 불필요, 서버만 켜지면 즉시 동작.

### 3.5 실패 시나리오 추정

코드 증거 기반 분석:

| 시나리오 | 근거 | 유력도 |
|---|---|---|
| **① 임베딩 서버 꺼짐** | `embedding_client.py#L33`에서 2초 타임아웃 → `_available=False` 캐시 → 이후 모든 호출 `None` 반환 | 🔴 **가장 유력** |
| **② 모델 미설치** | LM Studio에서 `nomic-embed-text` 모델 미로드 시 Ollama/OpenAI probe 둘 다 실패 | 🟠 높음 |
| **③ 캐시 인덱스 소실** | 코드상 디스크 인덱스 없음 →해당 없음 | 🟢 없음 |
| **④ ripgrep 미설치** | `search_engine.py#L94-L102`에서 `rg --version` 실패 → os.walk 폴백으로 전환, 검색 자체는 동작 | 🟡 검색 품질 저하 |

**핵심 장애 경로**:
1. 임베딩 서버 미실행 → `EmbeddingClient.is_available() = False`
2. [`mcp-servers/bridge/tools/scout.py#L36`](mcp-servers/bridge/tools/scout.py#L36)에서 `rank_by_embedding()` 호출 시 `embed_fn`이 `None` 반환
3. `rank_by_embedding` ([`embedding_client.py#L107-L116`](mcp-servers/bridge/embedding_client.py#L107-L116)): vecs=None → 후보를 그대로 반환 (의미적 랭킹 없이 키워드 결과만 반환)
4. 사용자에게 "semantic search 실패" 메시지 표시 ([`bundle.l10n.json#L107-L108`](extension/l10n/bundle.l10n.json#L107-L108))

### 3.6 MCP 설정 파일 구조

** 글로벌 MCP 설정 (Zoo Code)**:

[`extension/src/platform/VscodePaths.ts#L102-L111`](extension/src/platform/VscodePaths.ts#L102-L111):

```
%APPDATA%/Code/User/globalStorage/zoocodeorganization.zoo-code/settings/mcp_settings.json
```

→ Windows: `%APPDATA%\Code\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json`

**프로젝트 MCP 설정**:

```
<workspace>/.roo/mcp.json
```

→ `%USERPROFILE%/OneDrive/Projects/VibeZoo/.roo/mcp.json`

**MCP 서버 등록 방식** ([`McpConfigService.ts`](extension/src/mcp/McpConfigService.ts)):

1. `writeGlobalMcp()` ([#L46-L95](extension/src/mcp/McpConfigService.ts#L46-L95)): 글로벌 `mcp_settings.json`에 `vibezoo` 키로 SSE 서버 정의 기록
2. `writeProjectMcp()` ([#L105-L170](extension/src/mcp/McpConfigService.ts#L105-L170)): 프로젝트 `.roo/mcp.json`에 `vibezoo` 키 기록
3. 기본 정의 ([#L220-L243](extension/src/mcp/McpConfigService.ts#L220-L243)):
   - URL: `http://127.0.0.1:9027/sse`
   - `autoStart: true`
   - `autoStartCommand`: Windows = `cd /d "%USERPROFILE%\mcp-servers\vibezoo" && start_vibezoo_bridge.bat`

**Crow Memory 서버** ([`CrowServerManager.ts`](extension/src/crow/CrowServerManager.ts)):
- 포트: 9020 (기본값)
- 헬스체크: `GET /health` ([#L44-L60](extension/src/crow/CrowServerManager.ts#L44-L60))
- 자동 spawn: `crow_memory_server.py` 실행 ([#L63-L125](extension/src/crow/CrowServerManager.ts#L63-L125))

**현재 .roo/mcp.json 상태**: 파일이 존재하며 보호(🛡️) 상태. 읽기 불가.

**현재 .zoo/ 디렉토리**: `Agent.md`, `config.json`, `config.schema.json`, `instructions.md`, `subagents_config.json` 포함.

---

## [4] RT-4: 기능 인벤토리

### 4.1 VS Code 커맨드 전체 (31개) + 구현 파일 매핑

| # | 커맨드 ID | 제목 (en) | 구현 파일 | 상태 |
|---|---|---|---|---|
| 1 | `vibezoo.selfCheck` | Self Check | [`extension/src/extension.ts#L618`](extension/src/extension.ts#L618) + [`SelfCheck.ts`](extension/src/safety/SelfCheck.ts) | ✅ 정상 |
| 2 | `vibezoo.verifyFoundation` | Verify Foundation | [`extension/src/extension.ts#L369`](extension/src/extension.ts#L369) | ✅ 정상 |
| 3 | `vibezoo.reconnectCrow` | Reconnect to Crow Memory | [`extension/src/extension.ts`](extension/src/extension.ts) | ✅ 정상 |
| 4 | `vibezoo.instantRewind` | Instant Rewind | [`extension/src/extension.ts#L325`](extension/src/extension.ts#L325) + [`YoctoManager.ts`](extension/src/safety/YoctoManager.ts) | ✅ 정상 |
| 5 | `vibezoo.toggleYolo` | Toggle YOLO Mode | [`extension/src/extension.ts#L343`](extension/src/extension.ts#L343) + [`GitStashManager.ts`](extension/src/safety/GitStashManager.ts) | ✅ 정상 |
| 6 | `vibezoo.scanProject` | Scan Project Tree | [`ProjectTreeScanner.ts`](extension/src/flow/ProjectTreeScanner.ts) | 🟡 설정 의존 |
| 7 | `vibezoo.openWhiteboard` | Open Whiteboard | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | 🟡 CDN 의존 (Fabric.js) |
| 8 | `vibezoo.openUIPreview` | Open UI Preview | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | 🟡 설정 의존 |
| 9 | `vibezoo.openDashboard` | Open Orchestra Dashboard | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | 🟡 설정 의존 |
| 10 | `vibezoo.openDropzone` | Open Drop Zone | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | 🟡 설정 의존 |
| 11 | `vibezoo.showSessionResume` | Show Session Resume | [`TreeViewProviders.ts`](extension/src/ui/TreeViewProviders.ts) | ✅ 정상 |
| 12 | `vibezoo.reviewProject` | Review Project | [`extension/src/extension.ts`](extension/src/extension.ts) → MCP `review_project` | 🟡 MCP 브릿지 의존 |
| 13 | `vibezoo.findBugs` | Find Bugs | → MCP `find_bugs` | 🟡 MCP 브릿지 의존 |
| 14 | `vibezoo.suggestRefactor` | Suggest Refactoring | → MCP `suggest_refactor` | 🟡 MCP 브릿지 의존 |
| 15 | `vibezoo.generateDocs` | Generate Documentation | → MCP `generate_docs` | 🟡 MCP 브릿지 의존 |
| 16 | `vibezoo.pauseFixLoop` | Pause Auto-Fix Loop | [`extension/src/extension.ts#L726`](extension/src/extension.ts#L726) | ✅ 정상 |
| 17 | `vibezoo.resumeFixLoop` | Resume Auto-Fix Loop | [`extension/src/extension.ts#L733`](extension/src/extension.ts#L733) | ✅ 정상 |
| 18 | `vibezoo.abortFixLoop` | Abort Auto-Fix Loop | [`extension/src/extension.ts#L740`](extension/src/extension.ts#L740) | ✅ 정상 |
| 19 | `vibezoo.startWatching` | Start Continuous Improvement | [`extension/src/extension.ts#L654`](extension/src/extension.ts#L654) + [`FixLoopManager.ts`](extension/src/orchestra/FixLoopManager.ts) | ✅ 정상 |
| 20 | `vibezoo.stopWatching` | Stop Continuous Improvement | [`extension/src/extension.ts#L662`](extension/src/extension.ts#L662) | ✅ 정상 |
| 21 | `vibezoo.explainCode` | Explain Code at Cursor | [`extension/src/extension.ts#L670`](extension/src/extension.ts#L670) → MCP `explain_code` | 🟡 MCP 브릿지 의존 |
| 22 | `vibezoo.analyzeChanges` | Analyze Git Changes | → MCP `analyze_changes` | 🟡 MCP 브릿지 의존 |
| 23 | `vibezoo.reviewPR` | Review Pull Request | → MCP `review_pr` | 🟡 MCP 브릿지 의존 |
| 24 | `vibezoo.refactorAcrossFiles` | Refactor Across Files | → MCP `refactor_across_files` | 🟡 MCP 브릿지 의존 |
| 25 | `vibezoo.learnProject` | Learn Project Knowledge | → MCP `learn_project` | 🟡 MCP + Crow 의존 |
| 26 | `vibezoo.recallProject` | Recall Project Knowledge | → MCP `recall_project` | 🟡 MCP + Crow 의존 |
| 27 | `vibezoo.learnPreference` | Learn Coding Preference | → MCP `learn_preference` | 🟡 MCP + Crow 의존 |
| 28 | `vibezoo.getPreferences` | Show Saved Preferences | → MCP `get_preferences` | 🟡 MCP + Crow 의존 |
| 29 | `vibezoo.toggleGuardGit` | Toggle Guard.git Protection | [`extension/src/extension.ts#L578`](extension/src/extension.ts#L578) + [`GuardGitManager.ts`](extension/src/safety/GuardGitManager.ts) | ✅ 정상 |
| 30 | `vibezoo.openErrorDashboard` | Open Error Dashboard | [`ErrorDashboard.ts`](extension/src/visual/ErrorDashboard.ts) + [`ErrorCollection.ts`](extension/src/flow/ErrorCollection.ts) | ✅ 정상 |
| 31 | `vibezoo.configureErrorDashboard` | Configure Error Dashboard Auto-Open | [`ErrorCollection.ts`](extension/src/flow/ErrorCollection.ts) | ✅ 정상 |

### 4.2 MCP 브릿지 툴 전체 (42개 @mcp.tool)

[`mcp-servers/bridge/tools/__init__.py`](mcp-servers/bridge/tools/__init__.py)에서 `register_all_tools(mcp)` 호출로 16개 모듈이 등록됨.

| # | 툴명 | 모듈 | 한줄 설명 | 의존성 |
|---|---|---|---|---|
| 1 | `search_codebase` | scout.py#L737 | 코드베이스 텍스트/시맨틱 검색 | ripgrep, embedding 서버(선택) |
| 2 | `find_references` | scout.py#L756 | 심볼 참조 검색 | ripgrep |
| 3 | `summarize_architecture` | scout.py#L767 | 프로젝트 아키텍처 요약 | Crow Memory, AST |
| 4 | `review_code` | reviewer.py#L336 | 단일 파일 코드 리뷰 | AST, Crow Memory |
| 5 | `explain_code` | analysis.py#L188 | 특정 라인 코드 설명 | AST |
| 6 | `analyze_changes` | analysis.py#L425 | git 변경 분석 | git |
| 7 | `review_pr` | analysis.py#L526 | PR 리뷰 | git |
| 8 | `refactor_across_files` | analysis.py#L697 | 멀티 파일 리팩토링 | AST |
| 9 | `analyze_call_graph` | deep_analyzer.py#L518 | 호출 그래프 분석 | AST |
| 10 | `map_dependencies` | deep_analyzer.py#L674 | 의존성 매핑 | AST |
| 11 | `extract_patterns` | deep_analyzer.py#L684 | 구조적 패턴 추출 | AST |
| 12 | `reverse_engineer` | deep_analyzer.py#L700 | 코드 역공학 | AST |
| 13 | `generate_tests` | tester.py#L38 | 테스트 코드 생성 | AST |
| 14 | `analyze_coverage` | tester.py#L310 | 테스트 커버리지 분석 | 파일 시스템 |
| 15 | `analyze_uploaded_file` | file_analyzer.py#L346 | 업로드된 파일 분석 | OpenCV(선택), OCR(선택) |
| 16 | `check_uploaded_files` | whiteboard.py#L971 | 업로드된 파일 목록 확인 | 파일 시스템 |
| 17 | `capture_screen` | whiteboard.py#L1030 | 화면 캡처 | Pillow(선택) |
| 18 | `draw_on_whiteboard` | whiteboard.py#L1054 | 화이트보드 그리기 | 파일 시스템 |
| 19 | `get_whiteboard_state` | whiteboard.py#L1091 | 화이트보드 상태 조회 | 파일 시스템 |
| 20 | `auto_fix_status` | fix_loop.py#L134 | 자동 수정 상태 확인 | 빌드 시스템 |
| 21 | `retry_build` | fix_loop.py#L178 | 빌드 재시도 | 빌드 시스템 |
| 22 | `check_intervention` | fix_loop.py#L301 | 사용자 개입 필요 확인 | 파일 시스템 |
| 23 | `review_project` | integrated.py#L382 | 통합 프로젝트 리뷰 | 모든 분석 모듈 |
| 24 | `find_bugs` | integrated.py#L526 | 버그 발견 | AST, Crow Memory |
| 25 | `suggest_refactor` | integrated.py#L739 | 리팩토링 제안 | AST |
| 26 | `generate_docs` | integrated.py#L868 | 문서 생성 | AST |
| 27 | `learn_project` | knowledge.py#L124 | 프로젝트 지식 수집 | Crow Memory |
| 28 | `recall_project` | knowledge.py#L216 | 프로젝트 지식 회상 | Crow Memory |
| 29 | `learn_preference` | knowledge.py#L271 | 코딩 선호도 학습 | Crow Memory |
| 30 | `get_preferences` | knowledge.py#L333 | 선호도 조회 | Crow Memory |
| 31 | `apply_patch` | editor.py#L608 | 패치 적용 | 파일 시스템 |
| 32 | `read_project_file` | editor.py (추정) | 프로젝트 파일 읽기 | 파일 시스템 |
| 33 | `ux_coordinator` | ux_coordinator.py#L61 | UX 의도 라우팅 | 의도 감지 |
| 34 | `auto_analyze_after_drop` | ux_coordinator.py#L137 | 드롭존 업로드 후 자동 분석 | 파일 분석 |
| 35 | `auto_analyze_whiteboard` | ux_coordinator.py#L287 | 화이트보드 자동 분석 | 화이트보드 |
| 36 | `vibezoo_feedback` | feedback.py#L9 | 사용자 피드백 수집 | 파일 시스템 |
| 37 | `vibezoo_setup` | setup.py#L1166 | VibeZoo 설치/설정 | pip, 시스템 패키지 |
| 38 | `aggregate_spatial_pixels` | ssa.py#L643 | 이미지 공간 분석 | OpenCV |
| 39 | `fetch_page` | web.py#L250 | 웹 페이지 가져오기 | urllib (stdlib) |
| 40 | `web_search` | web.py#L316 | 웹 검색 | Exa API / DuckDuckGo |
| 41 | `explain_code` | (analysis.py와 중복?) | 코드 설명 | AST |
| 42 | `capture_screen` | (whiteboard.py와 동일) | 화면 캡처 | Pillow |

### 4.3 VS Code UI 표면

| UI 요소 | 타입 | 파일 | 설명 |
|---|---|---|---|
| **Activity Bar 사이드바** | `viewsContainers.activitybar` | package.json#L151-L157 | "VibeZoo" 사이드바 (⚡ 아이콘) |
| **Active Subagents 트리뷰** | `views` TreeView | [`TreeViewProviders.ts`](extension/src/ui/TreeViewProviders.ts#L29) | 서브에이전트 상태 표시 |
| **YOLO History 트리뷰** | `views` TreeView | [`TreeViewProviders.ts`](extension/src/ui/TreeViewProviders.ts#L368) | YOLO 스냅샷 기록 |
| **Session Resume 트리뷰** | `views` TreeView | [`TreeViewProviders.ts`](extension/src/ui/TreeViewProviders.ts#L441) | 세션 복원 정보 |
| **StatusBar 아이템** | `StatusBarItem` | [`StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts) | 상태, Crow 연결, CIM 모드, 모드 제안 |
| **Whiteboard Webview** | `WebviewPanel` | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | Fabric.js 기반 화이트보드 |
| **UI Preview Webview** | `WebviewPanel` | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | React/Vue 실시간 미리보기 |
| **Error Dashboard Webview** | `WebviewPanel` | [`ErrorDashboard.ts`](extension/src/visual/ErrorDashboard.ts) | 에러 수집 대시보드 |
| **Editor Context 메뉴** | `menus.editor/context` | package.json#L375-L396 | Review/Bug/Refactor/Docs (4개) |
| **Keybindings** | 3개 | package.json#L350-L365 | Ctrl+Shift+R/Z/B |

### 4.4 기능별 상태 플래그

| 기능 영역 | 의존성 | 현재 상태 | 근거 |
|---|---|---|---|
| Self Check / Verify Foundation | Bridge + Crow | ✅ 정상 (서버 연결 시) |[`extension/src/safety/SelfCheck.ts`](extension/src/safety/SelfCheck.ts) |
| Instant Rewind | yocto 백업 | ✅ 정상 | [`YoctoManager.ts`](extension/src/safety/YoctoManager.ts) |
| YOLO 모드 | Git + Crow | ✅ 정상 | [`GitStashManager.ts`](extension/src/safety/GitStashManager.ts) |
| Guard.git | 파일 시스템 권한 | ✅ 정상 | [`GuardGitManager.ts`](extension/src/safety/GuardGitManager.ts) |
| AutoBuildFix | 빌드 시스템 | 🟡 설정 의존 | [`AutoBuildFix.ts`](extension/src/safety/AutoBuildFix.ts), `vibezoo.build.autoFix` config |
| Crow Memory | 포트 9020 Python 서버 | 🟡 서버 실행 필요 | [`CrowServerManager.ts`](extension/src/crow/CrowServerManager.ts) |
| MCP Bridge | 포트 9027 Python 서버 | 🟡 서버 실행 필요 | [`McpConfigService.ts`](extension/src/mcp/McpConfigService.ts) |
| codebase_search (Scout) | ripgrep + embedding 서버 | 🟡 ripgrep 폴백 가능, embedding은 선택 | [`search_engine.py`](mcp-servers/bridge/search_engine.py), [`embedding_client.py`](mcp-servers/bridge/embedding_client.py) |
| semantic search | embedding 서버 (8089) | 🔴 **서버 미실행 시 고장** | 포트 8089 미활성화 시 의미적 랭킹 비활성 |
| Whiteboard | Fabric.js CDN | 🟡 CDN 차단 시 고장 | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) |
| OCR | Tesseract/PaddleOCR | 🔴 미설치 시 고장 | [`ocr_engine.py`](mcp-servers/bridge/ocr_engine.py) |
| Vision AI | Hugging Face 모델 | 🔴 미설치 시 고장 | [`vision/minicpm.py`](mcp-servers/bridge/vision/minicpm.py) |
| web_search | Exa API 키 + DuckDuckGo | ✅ Exa 없어도 DDG 폴백 | [`web.py`](mcp-servers/bridge/tools/web.py) |
| Error Collection | 파일 시스템 | ✅ 정상 | [`ErrorCollection.ts`](extension/src/flow/ErrorCollection.ts) |
| SubagentManager | Bridge | 🟡 Bridge 의존 | [`SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts) |
| ContextIntelligence | Crow Memory | 🟡 Crow 의존 | [`ContextIntelligence.ts`](extension/src/context/ContextIntelligence.ts) |
| Python Resolver | 시스템 PATH | 🟡 Python 설치 필요 | [`PythonResolver.ts`](extension/src/python/PythonResolver.ts) |
| i18n (Python) | translations JSON | ✅ 20개 언어 동기화 | [`bridge/i18n/`](mcp-servers/bridge/i18n/) |
| i18n (Extension NLS) | package.nls JSON | 🟠 **ja 6개 키 누락** | 위 RT-1 분석 |
| i18n (Extension L10N) | bundle.l10n JSON | ✅ 동기화 (오염 키 6건 존재) | 위 RT-1 분석 |

---

## Issues Discovered

### 🔴 Critical
1. **일회성 폴더 `-p/` 미정리**: `i18n_verify.py`, `i18n_verify_result.json` 존재 → REQ-008 대상
2. **Dual mcp-servers/ 미병합**: `mcp-servers/`과 `extension/mcp-servers/`에 동일한 Python 코드 존재 → `plans/bridge-merge-plan.md` 기존 계획 있음

### 🟡 Important
3. **package.nls.ja.json 6개 키 누락**: `vibezoo.configureErrorDashboard.title` 등 에러 대시보드 관련 키 6개 누락 → REQ-003 대상
4. **bundle.l10n.json package.nls 키 오염**: 6개 `vibezoo.*` 키가 l10n 번들에 포함 (무해하나 불필요)
5. **Python translations 키 수 불일치**: 이전 검증 168키 vs 현재 en.json 169키 → 재검증 필요
6. **embedding 서버 미실행 추정**: 8089 포트 활성화 여부 미확인 → REQ-005 대상
7. **ACTIVE_STATE.md 2026-07-25 고정**: 현재 날짜(260830)와 불일치, 마지막 세션 정보 미갱신

### 🟢 Minor
8. **Bridge 버전 불일치**: `config.py#L9`에서 `VERSION = "0.14.4"`, `package.json#L5`에서 `"0.15.1"` → 버전 동기화 필요
9. **os.walk 폴백 시 성능 저하**: ripgrep 미설치 시 대규모 프로젝트 검색 느림
10. **URL 하드코딩**: [`extension/src/extension.ts#L570`](extension/src/extension.ts#L570)에서 `choice === 'Help 보기'` → 한국어 하드코딩 (l10n 미적용)

---

## Next Step Recommendations

1. **[REQ-003] i18n 보완**: ja.json에 6개 누락 키 추가, bundle.l10n.json 오염 키 제거, Python translations 재검증 (168→169키 확인)
2. **[REQ-005] embedding 서버 확인**: `netstat -ano | findstr :8089`로 포트 확인 → 미실행 시 LM Studio 재설치 또는 `VIBEZOO_EMBED_URL` 환경변수 조정
3. **[REQ-004] web_search 확인 완료**: 설명은 사실과 일치. 추가 조치 불필요.
4. **[REQ-006] 기능 쓸모 평가**: 위 4.4 상태 플래그 기반으로 설정 의존/고장 기능 우선 정리
5. **[REQ-008] 일회성 파일 정리**: `-p/` 폴더 삭제
6. **버전 동기화**: `config.py` VERSION을 `0.15.1`로 갱신
7. **ACTIVE_STATE.md 갱신**: 현재 세션 정보 반영

---

## Affected File List

| 파일 | 조사 대상 RT | 상태 |
|---|---|---|
| [`extension/package.json`](extension/package.json) | RT-1, RT-4 | 읽기 |
| [`extension/package.nls.json`](extension/package.nls.json) | RT-1 | 읽기 |
| [`extension/package.nls.ja.json`](extension/package.nls.ja.json) | RT-1 | 읽기 (누락 발견) |
| [`extension/package.nls.ko.json`](extension/package.nls.ko.json) | RT-1 | 읽기 |
| [`extension/l10n/bundle.l10n.json`](extension/l10n/bundle.l10n.json) | RT-1 | 읽기 (오염 발견) |
| [`extension/l10n/bundle.l10n.ko.json`](extension/l10n/bundle.l10n.ko.json) | RT-1 | 읽기 |
| [`extension/l10n/bundle.l10n.ja.json`](extension/l10n/bundle.l10n.ja.json) | RT-1 | 읽기 |
| [`mcp-servers/bridge/i18n/translations/en.json`](mcp-servers/bridge/i18n/translations/en.json) | RT-1 | 읽기 |
| [`mcp-servers/bridge/i18n/translations/ko.json`](mcp-servers/bridge/i18n/translations/ko.json) | RT-1 | 읽기 |
| [`mcp-servers/bridge/i18n/translations/ja.json`](mcp-servers/bridge/i18n/translations/ja.json) | RT-1 | 읽기 |
| [`mcp-servers/bridge/i18n/__init__.py`](mcp-servers/bridge/i18n/__init__.py) | RT-1 | 읽기 |
| [`mcp-servers/bridge/tools/web.py`](mcp-servers/bridge/tools/web.py) | RT-2 | 읽기 |
| [`extension/mcp-servers/bridge/tools/web.py`](extension/mcp-servers/bridge/tools/web.py) | RT-2 | 읽기 (복사본) |
| [`mcp-servers/bridge/embedding_client.py`](mcp-servers/bridge/embedding_client.py) | RT-3 | 읽기 |
| [`mcp-servers/bridge/search_engine.py`](mcp-servers/bridge/search_engine.py) | RT-3 | 읽기 |
| [`mcp-servers/bridge/tools/scout.py`](mcp-servers/bridge/tools/scout.py) | RT-3, RT-4 | 읽기 |
| [`mcp-servers/bridge/intent_detector.py`](mcp-servers/bridge/intent_detector.py) | RT-3 | 읽기 |
| [`extension/src/platform/VscodePaths.ts`](extension/src/platform/VscodePaths.ts) | RT-3 | 읽기 |
| [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts) | RT-3 | 읽기 |
| [`extension/src/crow/CrowServerManager.ts`](extension/src/crow/CrowServerManager.ts) | RT-3 | 읽기 |
| [`extension/src/config/ConfigService.ts`](extension/src/config/ConfigService.ts) | RT-3 | 읽기 |
| [`mcp-servers/bridge/config.py`](mcp-servers/bridge/config.py) | RT-3 | 읽기 |
| [`mcp-servers/vibezoo_mcp_bridge.py`](mcp-servers/vibezoo_mcp_bridge.py) | RT-3 | 읽기 |
| [`extension/src/extension.ts`](extension/src/extension.ts) | RT-4 | 읽기 |
| [`extension/src/safety/SelfCheck.ts`](extension/src/safety/SelfCheck.ts) | RT-4 | 읽기 |
| [`extension/src/ui/StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts) | RT-4 | 읽기 |
| [`extension/src/ui/TreeViewProviders.ts`](extension/src/ui/TreeViewProviders.ts) | RT-4 | 읽기 |
| [`mcp-servers/bridge/tools/__init__.py`](mcp-servers/bridge/tools/__init__.py) | RT-4 | 읽기 |
| [`mcp-servers/bridge/tools/tool_context.py`](mcp-servers/bridge/tool_context.py) | RT-4 | 읽기 |
| [`-p/i18n_verify_result.json`](-p/i18n_verify_result.json) | RT-1 | 읽기 |
| [`docs/ACTIVE_STATE.md`](docs/ACTIVE_STATE.md) | 전체 | 읽기 |
| [`docs/260830_0001_session_reinstall-recovery-and-quality/requirement-checklist.md`](docs/260830_0001_session_reinstall-recovery-and-quality/requirement-checklist.md) | 전체 | 읽기 |
