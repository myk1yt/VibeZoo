# Architecture Plan — VibeZoo 재설치 복구 + 품질 개선

> **Session**: `docs/260830_0001_session_reinstall-recovery-and-quality/`
> **Date**: 2026-08-30 (Asia/Seoul)
> **Author**: Architect mode
> **Source of truth**: [`requirement-checklist.md`](docs/260830_0001_session_reinstall-recovery-and-quality/requirement-checklist.md) (REQ-001~012) + [`093000_project-research-report.md`](docs/260830_0001_session_reinstall-recovery-and-quality/093000_project-research-report.md) + [`plans/bridge-merge-plan.md`](plans/bridge-merge-plan.md)
> **Scope**: D-1(i18n), D-2(코드베이스 검색 복구+영속화), D-3(이미지 붙여넣기 UX), D-4(이중 mcp-servers 병합), D-5(버전/텍스트 정합)
> **Constraint**: 설계만, 코드 수정 없음. `.rooignore` 대상(node_modules, .zoo-code, .zoo/yocto) 탐색 제외.

---

## [0. Executive Summary]

| 항목 | 목표 | 핵심 결정 | 위임 수 | 위험 |
|---|---|---|---|---|
| **D-1 i18n** | 20개 언어 키 100% 일치, en fallback 제거 | **Option B (Pragmatic)**: ja 6키 수동 번역 + 검증 스크립트 재사용 + 오염 키는 "유지(무해)" 판단 | 3 | 🟢 낮음 |
| **D-2 검색 복구+영속화** | 임베딩 서버 다운 시 우아한 복구 + 디스크 인덱스 캐시 | **Option B (Pragmatic)**: 명확한 에러 안내 + 지수 백오프 재시도 + 파일해시 기반 디스크 캐시(신규 모듈) + `vibezoo.rebuildCodeIndex` 커맨드 | 5 | 🟡 중간 |
| **D-3 이미지 붙여넣기** | 복사→Ctrl+V→AI 전달 완성도 | **Option B (Pragmatic)**: 기존 Dropzone paste 핸들러 강화(자동 분석 트리거) + vision 폭백을 파일 경로 안내로 | 3 | 🟡 중간 |
| **D-4 mcp-servers 병합** | 단일 소스 확정, 이중 유지 제거 | **Option A (Standard)**: extension/ 을 소스, 루트 mcp-servers/ 제거 + 활성화 시 동기화 스크립트 | 4 | 🔴 높음 |
| **D-5 버전 정합** | 단일 버전 소스 | **Option A (Standard)**: package.json이 유일 소스, config.py는 읽기 전용 주입 | 1 | 🟢 낮음 |

**총 위임**: 16개. 각 위임은 단일 파일/단일 주제 원칙, 파일 간 의존 순서 명시.

---

## [1. Technical Specification]

### 1.1 전체 데이터 흐름 (FE ↔ BE ↔ FFI/IPC)

VibeZoo는 3계층 구조다. 이 계획이 건드리는 경계를 명확히 한다.

```
┌─────────────────────────────────────────────────────────────────┐
│  VS Code Extension (TypeScript) — extension/src/                │
│  - extension.ts        : 커맨드 등록 (31개)                        │
│  - VisualVibePanels.ts : Dropzone/Whiteboard Webview (paste JS) │
│  - McpConfigService.ts : .roo/mcp.json, 글로벌 mcp_settings     │
│  - CrowServerManager.ts: Crow 9020 헬스체크                       │
└──────────────┬──────────────────────────────────┬───────────────┘
               │ vscode.env.clipboard / fs.watchFile│ stdio/SSE
               │ (DZ_ACTION_FILE 등 JSON 파일 IPC)  │ MCP protocol
┌──────────────▼──────────────────────────────────▼───────────────┐
│  MCP Bridge (Python) — mcp-servers/bridge/ + tools/             │
│  - embedding_client.py : localhost:8089 임베딩 (Ollama/OpenAI)  │
│  - search_engine.py    : ripgrep→git grep→os.walk 3단계 폭백     │
│  - scout.py            : search_codebase MCP 툴                  │
│  - ux_coordinator.py   : auto_analyze_after_drop                 │
│  - vision/minicpm.py   : GGUF 로컬 비전 (llama-cpp-python)      │
│  - config.py           : VERSION + 경로 상수                     │
└──────────────┬──────────────────────────────────┬───────────────┘
               │ HTTP localhost:8089               │ HTTP localhost:9020
┌──────────────▼──────────────┐  ┌────────────────▼──────────────┐
│  Embedding Server           │  │  Crow Memory Server (9020)    │
│  (LM Studio / nomic-embed)  │  │  crow_memory_server.py        │
└─────────────────────────────┘  └───────────────────────────────┘
```

**D-2가 건드리는 경계**: `embedding_client.py`(BE→임베딩서버 HTTP) + 신규 캐시 모듈(BE 낶 디스크) + `extension.ts`(FE 커맨드→MCP 툴 호출).
**D-3가 건드리는 경계**: `VisualVibePanels.ts` 웹뷰 JS(paste)→`handleDropzoneUpload`(TS)→`.vibezoo-uploads/latest.json`(파일)→MCP `auto_analyze_after_drop`(Python).
**D-4가 건드리는 경계**: `McpConfigService.ts`의 `autoStartCommand`가 가리키는 브릿지 경로.

### 1.2 핵심 타입/인터페이스 정의

#### D-2: 디스크 인덱스 캐시 (신규)
```python
# mcp-servers/bridge/index_cache.py (신규 파일)
class IndexCache:
    """파일해시 기반 디스크 벡터/파일목록 캐시."""
    cache_dir: str          # .zoo-code/index-cache/ (gitignore 대상)
    manifest_path: str      # manifest.json — {file_path: sha256, mtime}
    vectors_path: str       # vectors.npz (numpy savez) — 선택적

    def load_manifest(self) -> dict: ...
    def is_stale(self, file_path: str, current_hash: str) -> bool: ...
    def get_embedding(self, file_path: str) -> Optional[list[float]]: ...
    def store_embedding(self, file_path: str, vec: list[float]) -> None: ...
    def invalidate(self, file_path: str) -> None: ...
    def rebuild(self, root: Path) -> int: ...  # 원큐 리빌드, 처리 파일 수 반환
```

#### D-2: 헬스체크 결과 (FE 표시용)
```typescript
// extension/src — MCP 툴 embedding_health_check() 반환 JSON
interface EmbeddingHealth {
  available: boolean;
  api_style?: "ollama" | "openai";
  url: string;              // http://localhost:8089
  model: string;            // nomic-embed-text
  hint?: string;            // 서버 켜는 법 안내 (i18n 키)
  retry_after_ms?: number;
}
```

#### D-3: 업로드 레지스트리 엔트리 (기존 확장)
```json
// ~/.vibezoo-uploads/latest.json — 기존 구조에 auto_analyze 플래그 추가
{ "path": "...", "fileName": "...", "size": 0, "mimeType": "...",
  "timestamp": 0, "autoAnalyze": true, "analysisStatus": "pending|done|failed" }
```

---

## [2. Architecture Decisions]

각 D 항목별로 **목표 / 설계안(선택+이유) / 대안 기각 / 영향 파일 / 리스크**를 기술한다.
모든 코드 인용은 연구보고서 + 이번 검증에서 확인한 `[파일#L행]` 기준.

---

### D-1: i18n 마무리 (REQ-003)

#### 목표
- ja.json nls 누락 6키를 **일본어로 번역**해 보완 (en 기본문 복사 금지).
- Python translations 169키 기준 20개 언어 재검증.
- bundle.l10n.json의 package.nls 키 오염 6건 처리 여부 판단.

#### 현황 (사실)
- [`extension/package.nls.ja.json`](extension/package.nls.ja.json) 누락 6키: `vibezoo.configureErrorDashboard.title`(en [#L60](extension/package.nls.json#L60)), `vibezoo.errorCollection.autoOpenDashboard.description`/`never`/`onCritical`/`always`([#L62-65](extension/package.nls.json#L62-L65)), `vibezoo.errorCollection.notifyOnCritical.description`([#L66](extension/package.nls.json#L66)).
- 나머지 18개 언어 nls는 70키 일치(누락 0).
- bundle.l10n.json 마지막 6키([#L119-124](extension/l10n/bundle.l10n.json#L119-L124))가 package.nls 전용 키로 오염. `vscode.l10n.t()` 호출부 51건은 모두 번들 내 정상 키 사용 → **오염은 런타임 무해**.
- Python [`en.json`](mcp-servers/bridge/i18n/translations/en.json) = 169키. 이전 검증([`-p/i18n_verify_result.json`](-p/i18n_verify_result.json))은 168키 → **이전 검증 이후 1키 추가됨**.

#### 설계안 선택: **Option B (Pragmatic)** ✅
1. **ja 6키 수동 번역**: 6개뿐이므로 기계번역 파이프라인 없이 직접 번역. 에러 대시보드 도메인 용어(대시보드 자동 열기/중요 알림)는 기존 ja.json의 어조(です/ます調)와 일치시킨다.
2. **검증 스크립트 재사용**: 기존 [`-p/i18n_verify.py`](-p/i18n_verify.py)를 세션 폴터 `tools/verify_i18n.py`로 **이동**(일회성 도구). en.json 169키 기준 20개 언어의 키 집합·누락·초과를 출력. 실행 결과에 따라 보완.
3. **오염 키는 "유지" 판단**: bundle.l10n의 package.nls 키 6건은 런타임 무해하며, 20개 언어 번들 모두 동일하게 존재. 제거 시 20개 파일 동시 수정 + 회귀 리스크만 커지고 사용자 가치는 0. **제거하지 않고 문서화**(KNOWN_ISSUE로 기록) → P4.5 기능 평가에서 에러 대시보드가 삭제되면 그때 함께 정리.

#### 대안 기각
- **Option A (자동 번역 파이프라인)**: 6키에 과도한 공수. 기계번역 품질 검증 비용이 수동 번역보다 큼. 기각.
- **Option C (en fallback 허용)**: REQ-003이 "en fallback 의존 금지"를 명시. 기각.
- **오염 키 즉시 제거 (A적 접근)**: 20개 언어 번들 동시 수정 + l10n-dev 재생성 필요. 무해한 오염 제거에 회귀 리스크를 걸 이유가 없음. 기각하되 문서화.

#### 영향 파일
| 파일 | 변경 | 행 |
|---|---|---|
| [`extension/package.nls.ja.json`](extension/package.nls.ja.json) | 6키 추가(일본어) | 파일 끝 append |
| `tools/verify_i18n.py` (신규, 세션 폴터) | `-p/i18n_verify.py` 이동+169키 기준 갱신 | 전체 |
| `docs/260830_0001_session_reinstall-recovery-and-quality/i18n-known-issues.md` (신규) | 오염 6건 문서화 | 전체 |

#### 리스크
- 🟢 Python translations 1키 불일치(168→169)는 검증 스크립트 실행으로 즉시 확정 가능. 실패 시 해당 언어에 번역 추가.
- 🟡 일본어 번역 품질: `ask` 게이트에서 사용자 검토 필요(번역 6건을 감안하면 소규모).

---

### D-2: 코드베이스 검색 복구 + 영속화 (REQ-005) — 핵심

#### 목표
a) 임베딩 서버(8089) 다운 시 **명확한 사용자 안내 에러** 반환(어떻게 켜는지).
b) 자동 헬스체크 + 재시도 정책.
c) 디스크 기반 인덱스 영속화(파일해시 무효화) + 재설치 후 원큐 리빌드.
d) `vibezoo.rebuildCodeIndex` VS Code 커맨드 연계.

#### 현황 (사실)
- [`embedding_client.py#L16-17`](mcp-servers/bridge/embedding_client.py#L16-L17): `VIBEZOO_EMBED_URL`(기본 `http://localhost:8089`), `VIBEZOO_EMBED_MODEL`(기본 `nomic-embed-text`).
- [`embedding_client.py#L21-56`](mcp-servers/bridge/embedding_client.py#L21-L56): `is_available()`이 첫 probe(2초) 후 `_available`을 **프로세스 수명 동안 캐시**. 한 번 False면 서버가 켜져도 재시도 안 함 → **이것이 "재설치 후 계속 안 됨"의 코드상 근본 원인**.
- [`scout.py#L109-125`](mcp-servers/bridge/tools/scout.py#L109-L125): semantic 모드에서 서버 없으면 BM25 폭백 + "embedding server unavailable" 노트. 침묵적 저하.
- **디스크 인덱스 없음**: [`search_engine.py`](mcp-servers/bridge/search_engine.py)는 매 검색 시 ripgrep/git grep/os.walk 직접 실행. [`file_cache.py`](mcp-servers/bridge/file_cache.py)는 메모리 LRU만.
- 포트 8089 = LM Studio 기본 임베딩 포트. 재설치 직후 미실행 가능성 높음.

#### 설계안 선택: **Option B (Pragmatic)** ✅
"AI 에이전트가 실제로 쓸 때" 기준: 에이전트는 `search_codebase(mode="semantic")`을 호출했을 때 "왜 시맨틱이 안 되고, 지금 무엇을 해야 하는지"를 한 번에 알아야 한다.

1. **재시도 가능한 헬스체크** (`embedding_client.py` 수정):
   - `_available` 캐시에 **TTL(60초) + 실패 시 지수 백오프**(2s→4s→8s, 최대 30s) 도입.
   - `reset_availability()` 메서드 추가 → 서버가 켜지면 다음 호출에서 자동 재probe.
   - `EmbeddingClient`를 모듈 싱글톤화(현재는 scout.py#L110에서 매번 `EmbeddingClient()` 생성 → 캐시 무의미). `_get_embed_client()` 싱글톤 도입.
2. **명확한 안내 에러 + MCP 툴 `embedding_health_check()`** (신규):
   - 서버 다운 시 반환: `{available:false, url, model, hint}`. `hint`는 i18n 키로 "LM Studio에서 nomic-embed-text 로드 후 서버 시작, 또는 `VIBEZOO_EMBED_URL` 환경변수 설정" 안내.
   - semantic 검색 시 unavailable이면 기존 BM25 폭백은 유지하되, 노트에 `embedding_health_check()` 호출 유도 문구 추가.
3. **디스크 인덱스 캐시** (신규 `mcp-servers/bridge/index_cache.py`):
   - 위치: `<workspace>/.zoo-code/index-cache/` (이미 `.rooignore`/DEFAULT_EXCLUDE_DIRS의 `.zoo-code` 제외 대상과 일치, git 오염 없음).
   - `manifest.json`: `{relpath: {sha256, mtime}}`. 검색 시 변경된 파일만 재임베딩.
   - `vectors.npz`: numpy `savez`로 `{relpath: vector}`. numpy는 이미 SSA/vision 의존으로 존재.
   - 검색 플로우: 키워드 후보 → 캐시에서 벡터 조회 → 없는 것만 임베딩 → 코사인 랭킹. 서버 다운이면 캐시 벡터만으로 랭킹(쿼리 벡터는 못 만들므로 이 경우 BM25 폭백).
4. **원큐 리빌드 + 커맨드**:
   - MCP 툴 `rebuild_code_index(target_path)` (신규): `IndexCache.rebuild()` 호출, 처리 파일 수 반환.
   - VS Code 커맨드 `vibezoo.rebuildCodeIndex`: `extension.ts`에 등록, package.json commands/contributes 추가, MCP 툴 호출 안내(기존 MCP-의존 커맨드와 동일 패턴, 예: [`extension.ts#L670`](extension/src/extension.ts#L670)).

#### 대안 기각
- **Option A (완전한 벡터 DB: sqlite-vss/Chroma 도입)**: 신규 무거운 의존성 + 설치 가이드(REQ-009) 복잡화. "Boring Technology" 원칙 위배. numpy 파일 캐시로 충분. 기각.
- **Option C (에러 메시지만 개선, 영속화 없음)**: REQ-005의 "영속화" 요구 미충족. 기각. 다만 a+b(헬스체크/안내)만 먼저 배포하는 단계적 롤아웃은 허용(아래 구현 분할 D2-1→D2-2 순서).
- **클립보드 폭백으로 서버 없이 시맨틱 흉내**: 의미 없음. 기각.

#### 영향 파일
| 파일 | 변경 | 행 |
|---|---|---|
| [`mcp-servers/bridge/embedding_client.py`](mcp-servers/bridge/embedding_client.py) | TTL+백오프, `reset_availability()`, 싱글톤 팩토리 | [#L12-56](mcp-servers/bridge/embedding_client.py#L12-L56) 수정 + ~40행 추가 |
| `mcp-servers/bridge/index_cache.py` (신규) | `IndexCache` 클래스 | 전체(~150행) |
| `mcp-servers/bridge/tools/scout.py` (신규 툴 파일 아님, 기존 수정) | `embedding_health_check`, `rebuild_code_index` 툴 + 싱글톤 사용 | [#L736-753](mcp-servers/bridge/tools/scout.py#L736-L753) 영역 |
| [`extension/src/extension.ts`](extension/src/extension.ts) | `vibezoo.rebuildCodeIndex` 커맨드 등록 | [#L669](extension/src/extension.ts#L669) 부근 |
| [`extension/package.json`](extension/package.json) | commands + nls 키 추가 | commands 배열 |
| [`extension/package.nls.json`](extension/package.nls.json) + 20개 언어 | `vibezoo.rebuildCodeIndex.title` | append |
| `mcp-servers/bridge/i18n/translations/*.json` (20개) | health/rebuild 안내 키 | append |

#### 리스크
- 🟡 numpy `savez` 포맷은 모델 차원 변경 시 호환 문제 → manifest에 `model`+`dim` 기록, 불일치 시 전체 무효화로 방어.
- 🟡 `.zoo-code/`는 사용자 워크스페이스마다 생성 → 대용량 프로젝트에서 vectors.npz 크기. 파일 수 상한(기본 5000) + LRU eviction 명시.
- 🔴 embedding_client 싱글톤화는 scout.py 외 다른 호출부(있는지) 영향 → 구현 전 `EmbeddingClient()` 전수 검색 필수(테스트 프로토콜에 명시).

---

### D-3: 이미지 붙여넣기 UX 고도화 (REQ-007)

#### 목표 시나리오
"이미지 파일 복사 → VS Code 채팅 입력창에 Ctrl+V → 즉시 AI에게 전달 가능한 상태"

#### 현황 (사실)
- Dropzone 웹뷰에 **이미 paste 핸들러 존재**: [`VisualVibePanels.ts#L1137-1150`](extension/src/visual/VisualVibePanels.ts#L1137-L1150) — `document.addEventListener('paste')`에서 `item.kind === 'file'`이면 `uploadFile(file)` 호출.
- 업로드 후 흐름: [`handleDropzoneUpload`](extension/src/visual/VisualVibePanels.ts#L501) → `.vibezoo-uploads/`에 저장 → **클립보드에 LLM 프롬프트 텍스트 작성**([#L532-533](extension/src/visual/VisualVibePanels.ts#L532-L533)) → `latest.json` 레지스트리 기록([#L546-558](extension/src/visual/VisualVibePanels.ts#L546-L558)).
- 문제 1: **Dropzone 패널이 열리고 포커스된 상태에서만** paste가 동작. 채팅 입력창에 직접 Ctrl+V하면 VS Code 채팅이 처리 (Zoo Code 확장의 채팅은 이미지 paste를 자체 지원 여부 불명).
- 문제 2: 클립보드에 "경로 안내 텍스트"를 쓰는 방식은 사용자가 다시 채팅에 붙여넣어야 함 (2단계).
- vision 의존: [`minicpm.py#L23-31`](mcp-servers/bridge/vision/minicpm.py#L23-L31)은 GGUF+mmproj 파일 + `llama_cpp` import 필요. `models/` 디렉토리는 git에 없고 재설치 후 미존재 확실 → **현실적으로 vision은 대부분 환경에서 비가용**.

#### 설계안 선택: **Option B (Pragmatic)** ✅
"AI 에이전트가 실제로 쓸 때" 기준: 에이전트는 이미지 자체를 못 볼 수 있으므로, **(1) 파일을 확실히 저장하고 (2) 에이전트가 발견 가능한 레지스트리에 기록하고 (3) 분석 가능하면 자동 분석, 아니면 경로 안내**가 본질이다.

1. **채택: Dropzone 개편 (b안) + paste 자동 감지 강화 (a안 부분 채택)**
   - paste 핸들러는 유지하되, 업로드 완료 후 **자동 분석 트리거** 추가: `latest.json` 엔트리에 `autoAnalyze:true` 기록 + 웹뷰에 "분석 중" 상태 표시.
   - `handleDropzoneUpload`에서 이미지면 MCP `auto_analyze_after_drop` 경로를 사용자에게 원클릭 제안(기존 [`ux_coordinator.py#L137`](mcp-servers/bridge/tools/ux_coordinator.py#L137) 활용).
   - 클립보드 덮어쓰기는 유지하되, **이미지 마크다운(`![](path)`)도 함께 제공**해 채팅 붙여넣기 시 미리보기 가능하게.
2. **vision 폭백 설계**:
   - `auto_analyze_after_drop` 이미지 분기([`ux_coordinator.py#L178-211`](mcp-servers/bridge/tools/ux_coordinator.py#L178-L211))에서 `minicpm.is_available()` 선행 체크.
   - 비가용이면 "⚠️ Vision model unavailable. File saved at: {path}. Install GGUF model or describe manually" 안내로 폭백(현재는 try/except에서 실패 메시지만 출력).
   - `describe_image` 실패 시에도 파일 경로는 항상 응답에 포함.

#### 대안 기각
- **(a) 클립보드 폴륨 기반 자동 감지 (전역)**: VS Code 확장 호스트에서 OS 클립보드 이미지 폴륨은 `vscode.env.clipboard.readText()`만 가능(이미지 직접 읽기 API 없음). 네이티브 모듈/PowerShell 폴륨 필요 → CPU/배터리 낭비 + 플랫폼별 분기. 기각(단, Whiteboard 캡처는 기존 PowerShell 경로 [#L314](extension/src/visual/VisualVibePanels.ts#L314) 유지).
- **(c) 채팅 패널 직접 연동**: Zoo Code 채팅 webview는 VibeZoo 확장이 아닌 별도 확장(zoocodeorganization.zoo-code) 소유. VibeZoo가 주입 불가. 기각.
- **Option A (네이티브 클립보드 감시 데몬)**: 과도한 복잡성. 기각.

#### 영향 파일
| 파일 | 변경 | 행 |
|---|---|---|
| [`extension/src/visual/VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | `handleDropzoneUpload`에 autoAnalyze 플래그 + 이미지 마크다운 클립보드 + 웹뷰 상태 메시지 | [#L501-566](extension/src/visual/VisualVibePanels.ts#L501-L566) |
| [`mcp-servers/bridge/tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) | 이미지 분기에 `minicpm.is_available()` 선행 + 경로 폭박 안내 | [#L178-211](mcp-servers/bridge/tools/ux_coordinator.py#L178-L211) |
| [`mcp-servers/bridge/vision/minicpm.py`](mcp-servers/bridge/vision/minicpm.py) | `describe_image` 실패 시 경로 포함 폭박 메시지 | [#L80-112](mcp-servers/bridge/vision/minicpm.py#L80-L112) |

#### 리스크
- 🟡 웹뷰 paste는 포커스 필요 → "채팅에 직접 Ctrl+V" 시나리오는 Dropzone을 열어둬야 함. 이 제약은 문서화(README/가이드에 "Dropzone 패널에 붙여넣기" 명시).
- 🟡 vision 미설치 환경이 대부분 → 폭박 안내가 주 경로가 됨. UX가 "파일 저장 + 경로 안내"로 수렴하는 것은 의도된 동작.

---

### D-4: 이중 mcp-servers/ 병합 (plans/bridge-merge-plan.md 현실화)

#### 목표
루트 `mcp-servers/` vs `extension/mcp-servers/` 중 소스 확정, 중복 제거, 활성화 시 자동 동기화.

#### 현황 (사실 — 이번 검증에서 확정)
- **바이너리 다름**: `fc /b` 결과 `vibezoo_mcp_bridge.py` = **DIFF**, `crow_memory_server.py` = **DIFF**.
- **파일 수 다름**: 루트 `mcp-servers/bridge/tools/` = **19개 py**, `extension/mcp-servers/bridge/tools/` = **38개 py** → **extension 쪽이 상위 집합(더 완전)**.
- **버전 다름**: 루트 [`config.py#L9`](mcp-servers/bridge/config.py#L9) = `0.14.4`, extension [`config.py`](extension/mcp-servers/bridge/config.py) = `0.15.1` → **extension이 최신**.
- 루트에만 있는 것: `mcp-servers/bridge/i18n/`(translations 20개 — 연구보고서 기준 루트 경로로 인용됨), `mcp-servers/bridge/tools/`의 일부(`web.py` 등 — 단 extension에도 있음). **주의**: extension/mcp-servers에 i18n/translations가 있는지 구현 위임 시 반드시 확인 필요(연구보고서는 루트 경로만 인용).
- extension에만 있는 것: `start_vibezoo_bridge.bat`.
- [`McpConfigService.ts`](extension/src/mcp/McpConfigService.ts)의 기본 `autoStartCommand`는 `%USERPROFILE%\mcp-servers\vibezoo`를 가리킴(별도 설치 위치).

#### 설계안 선택: **Option A (Standard)** ✅
- **소스 = `extension/mcp-servers/`** (근거: 상위 집합 38>19, 최신 버전, VSIX 배포 단위와 일치).
- **루트 `mcp-servers/`는 제거**하되, 루트에만 있는 고유 파일(i18n/translations, 누락된 tools)을 extension으로 **먼저 병합**한 뒤 제거. 제거는 Recycle Bin(규칙 7).
- **단일 진실 공급원**: 이후 Python 브릿지는 `extension/mcp-servers/`만 편집. VSIX 빌드 시 포함.
- **활성화 시 동기화**: `McpConfigService`의 autoStartCommand가 가리키는 `%USERPROFILE%\mcp-servers\vibezoo`로 extension/mcp-servers를 복사하는 **설치/동기화 스크립트**를 제공(기존 `init_vibezoo.bat`/`vibezoo_setup` 툴과 연계). 중복 유지 필요성을 "런타임 배포본 1곳"으로 최소화.
- 기존 [`plans/bridge-merge-plan.md`](plans/bridge-merge-plan.md)는 v1/v2 병합(2026-06-02)이 목적이라 현재 이중 디렉토리 문제와는 별개 → 이 계획이 그 후속.

#### 대안 기각
- **소스 = 루트 mcp-servers/**: 파일 수 적고(19) 구버전(0.14.4). 기각.
- **Option B (심링크/정션으로 양쪽 유지)**: Windows OneDrive 환경에서 정션 불안정 + VSIX 패키징 혼란. 기각.
- **Option C (그대로 두고 문서화)**: REQ-008(정리)와 충돌, 지속적 드리프트. 기각.

#### 영향 파일
| 파일 | 변경 | 비고 |
|---|---|---|
| `extension/mcp-servers/` (전체) | 루트 고유 파일(i18n 등) 병합 | 소스로 승격 |
| `mcp-servers/` (루트) | 병합 후 제거(Recycle Bin) | 읽기 전용 보관 불필요 |
| [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts) | autoStartCommand 경로 검증/동기화 로직 | [#L220-243](extension/src/mcp/McpConfigService.ts#L220-L243) |
| `init_vibezoo.bat` / `init_vibezoo.sh` | 동기화 스크립트 반영 | 배포본 복사 |
| `.gitignore` | `extension/mcp-servers/__pycache__/` 등 확인 | — |

#### 리스크
- 🔴 **병합 시 누락 위험**: 루트에만 있는 파일(i18n/translations, 특정 tools)을 extension으로 옮기기 전 삭제하면 데이터 유실. → 구현 분할에서 "diff 인벤토리 → 병합 → 검증 → 제거" 순서를 강제.
- 🟡 `%USERPROFILE%\mcp-servers\vibezoo` 런타임 배포본은 사용자 환경 의존 → 설치 가이드(REQ-009)와 연계 필수.
- 🟡 `start_vibezoo_bridge.bat` 경로 참조가 다른 설정에 하드코딩돼 있을 수 있음 → 전수 검색 필요.

---

### D-5: 버전/텍스트 정합 (소규모)

#### 목표
`config.py 0.14.4` vs `package.json 0.15.1` → 단일 소스 기준 정합.
P4.5 기능 평가에서 삭제될 기능이 있을 수 있으므로 **제거 가능 범위를 파라미터화**.

#### 현황 (사실)
- [`extension/package.json#L5`](extension/package.json#L5) = `0.15.1` (VSIX 매니페스트 = 유일한 배포 버전).
- 루트 [`mcp-servers/bridge/config.py#L9`](mcp-servers/bridge/config.py#L9) = `0.14.4`.
- extension [`mcp-servers/bridge/config.py`](extension/mcp-servers/bridge/config.py) = `0.15.1` (이미 일치).
- `VERSION`은 scout.py 등에서 import해 사용([`scout.py#L20`](mcp-servers/bridge/tools/scout.py#L20)).

#### 설계안 선택: **Option A (Standard)** ✅
- **단일 소스 = `extension/package.json`**. D-4 병합으로 루트 config.py(0.14.4)는 제거되므로 자연 해소.
- Python 측 `config.py`의 `VERSION`은 package.json과 수동 동기화하는 대신, **릴리스 시점 주입**은 과도하므로 "package.json이 진실, config.py는 그 사본" 규칙을 문서화하고, D-4 병합으로 사본이 1개(extension)만 남게 해 드리프트 원천 제거.
- **제거 가능 범위 파라미터화**: P4.5에서 에러 대시보드 등이 삭제될 경우를 대비해, D-1의 nls/l10n 키와 D-5 버전은 특정 기능에 묶지 않고 **독립 상수**로 유지. 기능 삭제 시 해당 기능의 nls 키만 제거하면 되도록 설계(키 네임스페이스가 이미 기능별 접두어: `vibezoo.errorCollection.*`).

#### 대안 기각
- **Option B (config.py를 소스로)**: VSIX 버전은 package.json이 필수. 이중 소스 유지. 기각.
- **빌드 타임 자동 주입 스크립트**: 소규모 프로젝트에 과도. 문서화된 수동 동기화 + 단일 사본으로 충분. 기각(단, 검증 스크립트로 불일치 탐지는 D-1 verify_i18n.py에 버전 체크 추가로 대체 가능).

#### 영향 파일
| 파일 | 변경 |
|---|---|
| 루트 `mcp-servers/bridge/config.py` | D-4에서 제거 (0.14.4 소멸) |
| `extension/mcp-servers/bridge/config.py` | 0.15.1 유지 (package.json 사본임을 주석 명시) |
| `extension/package.json` | 0.15.1 유지 (단일 소스) |

#### 리스크
- 🟢 없음. D-4 완료 시 자동 해소. 향후 드리프트는 verify 스크립트에 버전 일치 체크 1줄로 방어.

---

## [3. Implementation Plan] — P3.5 Subdivision (단일 위임 크기)

> **규칙**: 한 위임 = 한 파일/한 주제 우선. 의존 순서 엄수. 각 위임에 [파일 경로] + [전제조건] + [검증/테스트 프로토콜] 명시.
> **공통 제약**: `.rooignore` 대상 탐색 금지. git commit/push는 VP 전용. 삭제는 Recycle Bin.
> **공통 Report Folder**: `docs/260830_0001_session_reinstall-recovery-and-quality/`

### 위임 의존 그래프
```
D1-1 (ja 번역) ──────────────┐
D1-2 (verify_i18n.py) ───────┼─→ D1-3 (오염 문서화)        [독립, 병렬 가능]
                             │
D4-1 (mcp-servers diff 인벤토리) → D4-2 (extension으로 병합) → D4-3 (검증) → D4-4 (루트 제거+동기화)
                                                                    │
                                              ┌─────────────────────┤
                                              ▼                     ▼
D2-1 (embedding_client 재시도) → D2-2 (index_cache.py) → D2-3 (scout 툴) → D2-4 (extension 커맨드) → D2-5 (nls/l10n 키)
                                              │
D3-1 (ux_coordinator vision 폭박) → D3-2 (minicpm 폭박) → D3-3 (VisualVibePanels autoAnalyze)
                                              │
D5-1 (config.py 사본 주석 + verify 버전체크) ──→ D4-4 이후 자동 해소 확인
```

### 권장 위임 순서 (의존 순서)
1. **D4-1 → D4-2 → D4-3 → D4-4** (병합이 다른 모든 Python 작업의 기반 경로를 확정하므로 최우선)
2. **D1-1, D1-2, D1-3** (독립, 병렬 가능)
3. **D2-1 → D2-2 → D2-3 → D2-4 → D2-5**
4. **D3-1 → D3-2 → D3-3**
5. **D5-1** (D4-4 완료 후)

---

### 위임 상세 (delegation-ready)

#### D1-1: package.nls.ja.json 6키 일본어 번역
- **파일**: [`extension/package.nls.ja.json`](extension/package.nls.ja.json) (수정)
- **전제**: 없음
- **내용**: en [#L60-66](extension/package.nls.json#L60-L66)의 6키를 일본어로 번역해 append. 기존 ja.json 어조(です/ます調) 일치. en 기본문 복사 금지.
- **검증**: `node -e "const a=require('./extension/package.nls.json'),b=require('./extension/package.nls.ja.json');const m=Object.keys(a).filter(k=>!Object.keys(b).includes(k));console.log(m.length===0?'PASS:0 missing':'FAIL:'+m)"`
- **테스트**: l10n 키 검증(위 CLI). 기존 테스트 스위트 없음 → 위 CLI가 게이트.

#### D1-2: tools/verify_i18n.py 작성 (일회성 검증 도구)
- **파일**: `docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_i18n.py` (신규)
- **전제**: 없음 (기존 [`-p/i18n_verify.py`](-p/i18n_verify.py) 참고)
- **내용**: (1) en.json 169키 기준 20개 언어 translations 키 집합 비교, (2) package.nls 20개 언어 70키 비교, (3) bundle.l10n 20개 언어 비교, (4) package.json vs extension/mcp-servers/bridge/config.py VERSION 일치 체크. 결과를 세션 폴터 `i18n_verify_result.json`으로 출력.
- **검증**: `python docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_i18n.py`
- **테스트**: 스크립트 실행 후 결과 JSON의 `missing_total == 0` 확인. 불일치 시 해당 언어 보완 위임 추가.

#### D1-3: bundle.l10n 오염 6건 문서화
- **파일**: `docs/260830_0001_session_reinstall-recovery-and-quality/i18n-known-issues.md` (신규)
- **전제**: 없음
- **내용**: bundle.l10n.json [#L119-124](extension/l10n/bundle.l10n.json#L119-L124)의 package.nls 오염 6건이 "런타임 무해 + 20개 언어 공통 + P4.5 에러 대시보드 삭제 시 함께 정리"임을 기록. 제거하지 않는 결정 근거 명시.
- **검증**: VP 문서 리뷰.
- **테스트**: 없음 (문서).

#### D2-1: embedding_client.py 재시도 + 싱글톤
- **파일**: `extension/mcp-servers/bridge/embedding_client.py` (수정) — ⚠️ D4-4 이후 경로 확정
- **전제**: **D4-4 완료** (단일 소스 extension/mcp-servers 확정 후)
- **내용**: (1) `_available` 캐시에 TTL 60초 + 지수 백오프(2→4→8→최대 30초), (2) `reset_availability()` 추가, (3) 모듈 싱글톤 `_get_embed_client()` 팩토리 추가. `is_available()`은 TTL 만료 시 재probe.
- **검증**: `python -c "from bridge.embedding_client import EmbeddingClient; c=EmbeddingClient(); print('probe ok', c.is_available() in (True,False))"`
- **테스트**: `extension/mcp-servers/tests/`에 `test_embedding_client.py` 신규 — mock HTTP로 서버 다운→False, TTL 후 재probe 호출 확인. 실행: `cd extension/mcp-servers && python -m pytest tests/test_embedding_client.py -v`

#### D2-2: index_cache.py 신규 (디스크 인덱스 영속화)
- **파일**: `extension/mcp-servers/bridge/index_cache.py` (신규)
- **전제**: D2-1
- **내용**: `IndexCache` 클래스 — `.zoo-code/index-cache/`에 manifest.json(파일해시 sha256+mtime) + vectors.npz(numpy). `is_stale`, `get/store_embedding`, `invalidate`, `rebuild(root)`. 모델+dim manifest 기록, 불일치 시 전체 무효화. 파일 수 상한 5000 + LRU eviction.
- **검증**: `python -c "from bridge.index_cache import IndexCache; c=IndexCache('.'); print('init ok', c.cache_dir)"`
- **테스트**: `extension/mcp-servers/tests/test_index_cache.py` 신규 — 임시 디렉토리에 파일 생성→store→get 일치, 파일 수정→is_stale True, rebuild 처리 수 반환. 실행: `cd extension/mcp-servers && python -m pytest tests/test_index_cache.py -v`

#### D2-3: scout.py에 embedding_health_check + rebuild_code_index 툴
- **파일**: `extension/mcp-servers/bridge/tools/scout.py` (수정)
- **전제**: D2-1, D2-2
- **내용**: (1) `@mcp.tool embedding_health_check()` → `{available, api_style, url, model, hint}` JSON 반환, hint는 i18n `t()` 사용, (2) `@mcp.tool rebuild_code_index(target_path)` → `IndexCache.rebuild()` 호출, (3) `_search_codebase_impl`이 `EmbeddingClient()` 직접 생성 대신 싱글톤 `_get_embed_client()` 사용 ([#L110](mcp-servers/bridge/tools/scout.py#L110)), semantic unavailable 시 노트에 `embedding_health_check()` 유도 추가. **구현 전 `EmbeddingClient()` 전수 검색으로 다른 호출부 확인**.
- **검증**: 브릿지 기동 후 MCP 툴 목록에 2개 툴 노출 확인.
- **테스트**: `extension/mcp-servers/tests/test_scout_health.py` 신규 — health_check가 dict 키 포함, rebuild_code_index가 int 반환. 실행: `cd extension/mcp-servers && python -m pytest tests/test_scout_health.py -v`

#### D2-4: extension.ts에 vibezoo.rebuildCodeIndex 커맨드
- **파일**: [`extension/src/extension.ts`](extension/src/extension.ts) (수정) + [`extension/package.json`](extension/package.json) (commands)
- **전제**: D2-3
- **내용**: 기존 MCP-의존 커맨드 패턴(예: [`extension.ts#L669-674`](extension/src/extension.ts#L669-L674))을 따라 `vibezoo.rebuildCodeIndex` 등록 → "Zoo Code 채팅에 'rebuild code index' 입력" 안내. package.json `contributes.commands`에 추가.
- **검증**: `cd extension && npx tsc --noEmit` (타입 체크)
- **테스트**: `npx tsc --noEmit` 통과. 커맨드 팔레트 수동 확인(VP).

#### D2-5: rebuildCodeIndex nls/l10n 키 20개 언어
- **파일**: [`extension/package.nls.json`](extension/package.nls.json) + 20개 nls 파일, 필요시 bundle.l10n 20개
- **전제**: D2-4
- **내용**: `vibezoo.rebuildCodeIndex.title`을 en 기준 작성 후 20개 언어 번역 추가. verify_i18n.py(D1-2)로 100% 일치 확인.
- **검증**: `python docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_i18n.py` → missing 0.
- **테스트**: verify_i18n.py 게이트.

#### D3-1: ux_coordinator.py vision 폭박 (이미지 분기)
- **파일**: `extension/mcp-servers/bridge/tools/ux_coordinator.py` (수정) — ⚠️ D4-4 이후
- **전제**: D4-4
- **내용**: 이미지 분기([`ux_coordinator.py#L178-211`](mcp-servers/bridge/tools/ux_coordinator.py#L178-L211))에서 `from bridge.vision.minicpm import is_available, describe_image` 후 `is_available()` False면 "⚠️ Vision model unavailable. File saved at: {path}. ..." 경로 안내 폭박. 가용이면 기존 describe_image 호출.
- **검증**: 비가용 환경에서 `auto_analyze_after_drop(이미지경로)` 호출 시 경로 포함 안내 반환.
- **테스트**: `extension/mcp-servers/tests/test_ux_vision_fallback.py` 신규 — is_available False mock 시 응답에 파일 경로 포함. 실행: `cd extension/mcp-servers && python -m pytest tests/test_ux_vision_fallback.py -v`

#### D3-2: minicpm.py describe_image 폭박 메시지
- **파일**: `extension/mcp-servers/bridge/vision/minicpm.py` (수정) — ⚠️ D4-4 이후
- **전제**: D4-4
- **내용**: `describe_image`([#L71-112](mcp-servers/bridge/vision/minicpm.py#L71-L112))의 model None 반환 및 except 경로에서 반환 문자열에 **항상 image_path 포함**. "⚠️ Vision model not loaded. Image saved at: {image_path}".
- **검증**: 모델 미설치 상태에서 `describe_image('x.png')` → 반환값에 'x.png' 포함.
- **테스트**: D3-1 테스트와 통합 가능. 실행: `cd extension/mcp-servers && python -m pytest tests/test_ux_vision_fallback.py -v`

#### D3-3: VisualVibePanels.ts autoAnalyze + 이미지 마크다운 클립보드
- **파일**: [`extension/src/visual/VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) (수정)
- **전제**: D3-1
- **내용**: `handleDropzoneUpload`([#L501-566](extension/src/visual/VisualVibePanels.ts#L501-L566))에서 (1) latest.json 엔트리에 `autoAnalyze:true, analysisStatus:'pending'` 추가, (2) 이미지면 클립보드 텍스트에 `![](destPath)` 마크다운 포함, (3) 웹뷰 postMessage에 `suggestAnalyze:true` 추가해 웹뷰가 "분석 제안" 표시. paste 핸들러([#L1137](extension/src/visual/VisualVibePanels.ts#L1137))는 유지.
- **검증**: `cd extension && npx tsc --noEmit`
- **테스트**: `npx tsc --noEmit` 통과 + Dropzone에 이미지 붙여넣기 수동 확인(VP). 제약(포커스 필요)은 README에 명시(REQ-011 범위).

#### D4-1: mcp-servers diff 인벤토리
- **파일**: `docs/260830_0001_session_reinstall-recovery-and-quality/mcp-merge-inventory.md` (신규)
- **전제**: 없음
- **내용**: 루트 `mcp-servers/` vs `extension/mcp-servers/` 재귀 비교. (1) 루트에만 있는 파일 목록, (2) extension에만 있는 파일, (3) 양쪽에 있으나 내용 다른 파일(fc /b DIFF 목록). 특히 `bridge/i18n/translations/` 20개와 `bridge/tools/` 19 vs 38의 차이 파일을 파일명으로 명시.
- **검증**: `fc /b /s mcp-servers extension\mcp-servers` (또는 git diff --no-index) 결과 첨부.
- **테스트**: 없음 (인벤토리 문서). 이후 모든 병합의 입력.

#### D4-2: 루트 고유 파일을 extension/mcp-servers로 병합
- **파일**: `extension/mcp-servers/` (다수 추가)
- **전제**: D4-1
- **내용**: D4-1 인벤토리의 "루트에만 있는 파일"을 extension 대응 경로로 복사. 양쪽 DIFF 파일은 extension(최신 0.15.1) 기준으로 유지하되, 루트에만 있는 로직이 있으면 수동 병합. **삭제는 이 단계에서 하지 않음**.
- **검증**: 병합 후 `python -c "import bridge.i18n"` 등 주요 모듈 import 성공.
- **테스트**: `cd extension/mcp-servers && python -m pytest tests/ -v` (기존 테스트 전수) + `python -m compileall bridge/ -q` (문법 검증).

#### D4-3: extension/mcp-servers 단일 소스 검증
- **파일**: 검증 보고서만 (코드 변경 없음)
- **전제**: D4-2
- **내용**: extension/mcp-servers가 독립적으로 완전한지 검증. 브릿지 기동(`start_vibezoo_bridge.bat` 또는 `python -m bridge`) → MCP 툴 목록(42개+) 노출 확인 → search_codebase 1회 호출.
- **검증**: `cd extension/mcp-servers && python -m compileall bridge/ -q && echo BUILD_OK`
- **테스트**: `cd extension/mcp-servers && python -m pytest tests/ -v`. 통과 못하면 D4-4 진행 금지.

#### D4-4: 루트 mcp-servers 제거 + 동기화 스크립트
- **파일**: 루트 `mcp-servers/` (Recycle Bin 제거), `init_vibezoo.bat`/`init_vibezoo.sh` (수정), [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts) (검토)
- **전제**: D4-3 통과
- **내용**: (1) 루트 mcp-servers를 Recycle Bin으로 이동, (2) init 스크립트가 extension/mcp-servers를 `%USERPROFILE%\mcp-servers\vibezoo`로 복사하는 동기화 로직 확인/추가, (3) McpConfigService autoStartCommand 경로 일치 확인. `.gitignore`에 `__pycache__` 확인.
- **검증**: 제거 후 `python -c "import sys; sys.path.insert(0,'extension/mcp-servers'); import bridge.config; print(bridge.config.VERSION)"` → 0.15.1.
- **테스트**: D4-3 테스트 재실행 + init 스크립트 드라이런. **삭제는 Irreversible에 준하므로 CPO(ask)+VP 승인 후 실행**(규칙 7 Escape Hatch).

#### D5-1: config.py 사본 주석 + verify 버전 체크
- **파일**: `extension/mcp-servers/bridge/config.py` (주석), `docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_i18n.py` (D1-2에서 이미 버전 체크 포함 시 생략)
- **전제**: D4-4
- **내용**: config.py [#L9](mcp-servers/bridge/config.py#L9) 상단에 "# VERSION은 extension/package.json의 사본. 릴리스 시 동기화 필수." 주석. verify_i18n.py의 버전 체크로 드리프트 탐지.
- **검증**: verify_i18n.py 실행 시 VERSION 일치 PASS.
- **테스트**: verify_i18n.py 게이트.

---

## [4. Cross-Cutting Concerns]

### 4.1 i18n 키 추가 총량 (D-2 신규 툴 + 커맨드)
- `vibezoo.rebuildCodeIndex.title` (nls, 20개 언어)
- embedding health/rebuild 안내 (Python translations, 20개 언어)
→ 모두 D1-2 verify_i18n.py로 100% 일치 게이트. **en fallback 금지**(REQ-003).

### 4.2 보안/Redaction
- D-2 캐시는 워크스페이스 로컬 파일 해시+벡터만 저장, PII 없음.
- D-3 업로드 경로는 `~/.vibezoo-uploads/` (홈 디렉토리), 저장소 외 → git 유출 없음.
- `.zoo-code/index-cache/`는 `.rooignore` 대상이나 **`.gitignore`에도 `.zoo-code/` 명시 권장**(D4-4에서 확인). 현재 `.gitignore`에 없음(검증됨) → 추가 위임 고려.

### 4.3 테스트 전략
- Python: `extension/mcp-servers/tests/`에 모듈별 `test_*.py` 신규(D2-1, D2-2, D2-3, D3-1). 실행은 각 위임의 `python -m pytest tests/test_X.py -v`.
- TS: `cd extension && npx tsc --noEmit` 타입 체크(D2-4, D3-3). 기존 단위 테스트 스위트 부재 시 타입 체크가 게이트.
- i18n: verify_i18n.py(D1-2)가 통합 게이트.
- 병합: D4-3의 `compileall` + `pytest tests/` 전수.

### 4.4 문서 권위 충돌
- [`plans/bridge-merge-plan.md`](plans/bridge-merge-plan.md)(2026-06-02, v1/v2 병합)은 현재 이중 디렉토리 문제와 목적이 다름. D-4는 그 후속으로 **arch/decisions/ ADR 없이 plans/ 수준에서 처리**하되, D-4-4(삭제)는 Irreversible하므로 `decisions.md`에 사용자 승인 기록 필수(Report Protocol §5).

---

## [5. Open Questions for VP / ask Gate]

1. **D-1 일본어 번역 품질**: 6키 번역문을 ask 게이트에서 사용자 검토할 것인가, 아니면 기존 ja.json 어조 준수로 충분한가. (권장: 6거이므로 번역문을 보고서에 첨부해 사용자 확인)
2. **D-4-4 루트 mcp-servers 삭제 승인**: Recycle Bin 이동이지만 저장소에서 제거되는 Irreversible 변경. CPO+VP 승인 필요. (권장: D4-3 검증 통과 후 승인)
3. **D-2 `.gitignore`에 `.zoo-code/` 추가 여부**: 캐시가 워크스페이스에 생기므로 git 오염 방지. (권장: 추가)
4. **D-3 채팅 직접 Ctrl+V 미지원 제약 수용**: Zoo Code 채팅 webview는 타 확장 소유라 VibeZoo가 주입 불가. "Dropzone 패널에 붙여넣기"로 문서화하는 것에 동의하는가. (권장: 수용 + README 명시)

---

*End of Architecture Plan — 16 delegations, dependency-ordered. Report Folder: `docs/260830_0001_session_reinstall-recovery-and-quality/`*
