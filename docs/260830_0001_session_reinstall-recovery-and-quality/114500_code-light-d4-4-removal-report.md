# Code Light Task Report — D4-4 Root mcp-servers/ Removal

## Task Summary
루트 `mcp-servers/` 폴더 및 잘못 위치한 루트 `.bat` 파일들을 Recycle Bin으로 삭제하고, git 인덱스에서 정리. 문서 참조 검사 완료.

## Actions Taken

### 1. Filesystem Deletion (Recycle Bin)
- `mcp-servers/` — Recycle Bin 삭제 (56+ 파일, 디렉토리 전체)
- `start_vibezoo_bridge.bat` (루트) — Recycle Bin 삭제
- `start_vibezoo_servers.bat` (루트) — Recycle Bin 삭제
- **삭제 방법**: `[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory/DeleteFile(..., 'SendToRecycleBin')`

### 2. Git Staging
- `git rm -r --cached mcp-servers/ start_vibezoo_bridge.bat start_vibezoo_servers.bat` 실행
- **59파일** staging 완료 (57개 mcp-servers/* + 2개 루트 .bat)
- git status 확인: 모두 `D` (deleted) 상태
- `git add -A` 미사용, 명시 경로만 지정

### 3. Mirror Comparison Verification
- 루트 `mcp-servers/` filesystem 확인: **DELETED**
- `extension/mcp-servers/` filesystem 확인: **EXISTS** (58 git-tracked files)
- `only_mir = 0` 충족: 루트 미러 파일 이제 존재하지 않음
- `only_ext = 정상`: extension 소스만 존재 (예상대로)
- p5_mirror_compare.py 스크립트는 별도 파일 없음 (114000 보고서에서 diff=0 확인됨)

### 4. Document Reference Scan
루트 `mcp-servers/` 경로를 참조하는 문서 278개 매치 탐지 (아래 목록 참조)

## Result
**✅ Success** — 루트 mcp-servers/ 완전 제거, git staging 완료 (commit 대기), 문서 참조 목록 확보

## Issues Discovered

### 🔴 `watch_vibezoo_bridge.bat` — 루트에 잔존
- git 추적 중 (`git ls-files` 확인)
- 이번 작업 범위 밖이었으나, 루트 `.bat` 정리 맥락에서 주목
- **P6-γ에서 검토 필요**

### 🟡 `tools/mirror_sync.py` — 참조 경로 깨질 수 있음
- `tools/mirror_sync.py`의 `root_base = 'mcp-servers'`가 이제 없는 디렉토리를 참조
- 기능상 문제 없음 (미러 불필요), 향후 정리 대상

## Affected File List
- `mcp-servers/*` — 57개 파일 git에서 제거 (filesystem은 Recycle Bin)
- `start_vibezoo_bridge.bat` (루트) — filesystem + git 제거
- `start_vibezoo_servers.bat` (루트) — filesystem + git 제거

## Next Step Recommendations
- VP가 `git commit` 실행 (커밋 메시지는 별도 txt 참조)
- **P6-γ README 단계**에서 아래 문서 참조 업데이트 필요

## Remaining Root `mcp-servers/` References in Docs (P6-γ 대상)

### 🔴 Active Docs (즉시 업데이트 필요)

| 문서 | 파일 경로 | 주요 참조 라인 |
|------|-----------|---------------|
| **README.md** | `README.md` | L37-38 (설치경로), L64 (실행), L89-93 (모듈소개), L101-103 (UX Coordinator), L106 (Scout), L114-116 (검색모드), L129 (Deep Analyzer), L134 (Whiteboard), L138 (deprecated), L143 (fix_loop), L169 (Editor), L232 (PythonResolver), L265-266 (경로변경), L272 (VSIX) |
| **docs/PROJECT_CONTEXT.md** | `docs/PROJECT_CONTEXT.md` | L158 (Layer 2 경로), L294-315 (모듈상세표), L365-366 (legacy mirror), L436 (config 경로), L460-475 (도구표), L481 (apply_patch), L523-527 (Fallback 체인), L546-554 (Caching), L558-561 (Singleton), L576 (error capture), L584 (Security), L594-604 (Known Issues) |
| **docs/ARCHITECTURE_CORE.md** | `docs/ARCHITECTURE_CORE.md` | L79-82 (Bridge entry/tools/config 경로) |
| **docs/ACTIVE_STATE.md** | `docs/ACTIVE_STATE.md` | L16 (Dual mcp-servers mention), L32 (merge plan reference) |

### 🟡 fromscratch/ (과거 기록, 선택적 업데이트)

| 문서 | 파일 경로 | 비고 |
|------|-----------|------|
| `fromscratch/Architecture.md` | L17-36, L175, L307-331 | 구조 비교 테이블 |
| `fromscratch/ROADMAP.md` | L26-27, L101-110, L275-277, L662 | 로드맵 타임라인 |
| `fromscratch/CHANGELOG.md` | L38, L65-74 | v0.15.0 changelog |
| `fromscratch/JOURNAL.md` | L81-83, L92-94, L107, L155 | 저널 기록 |
| `fromscratch/PLAN.md` | L13-14, L36, L82-83, L171-183, L228-233 | 계획 |
| `fromscratch/RELEASENOTES.md` | L38, L42, L78-83, L108-114, L130, L139-140 | 릴리즈노트 |

### 🟡 plans/ (설계 문서, P6-γ에서 검토)

| 문서 | 주요 참조 |
|------|-----------|
| `plans/bridge-merge-plan.md` | L18-19 (merge plan) |
| `plans/dropzone-fix-plan.md` | L32-34 (whiteboard.py 경로) |
| `plans/error-collection-system.md` | L31, L42-45, L65-67, L100-102, L154, L416, L814, L1130-1142, L1152, L1159-1167, L1186-1188 |
| `plans/error-collection-system-threat-analysis.md` | L22, L415-418 |
| `plans/multilang-analysis-engine-advancement.md` | L2-4, L57-63, L133, L192, L254, L729, L975, L1081 |
| `plans/vibezoo-auto-connect-fundamental-fix.md` | L3, L36, L144-146, L186-193, L212-232, L330-355 |
| `plans/vibezoo-reinstall-plan.md` | L32-36, L91-93 |
| `plans/vibezoo-ux-upgrade-plan.md` | L6, L27-35, L40, L72, L94, L110, L118, L243-244, L336, L494, L562-610, L955-1071, L1128-1130, L1349-1378, L1579-1588 |
| `plans/vibezoo-v2-upgrade.md` | L280-286 |

### 🟢 feedbacks/ (피드백 문서, 선택적)

| 문서 | 주요 참조 |
|------|-----------|
| `feedbacks/multilang_analysis_improvement.md` | L9, L12, L18, L61, L119-120 |
| `feedbacks/vibezoo_ux_llm_upgrade_proposal.md` | L9, L70-71, L91, L130, L205, L265-267, L287, L325-327 |

### 🟢 docs/ 과거 세션 보고서 (이력, 수정 불필요)

`docs/260725_*` 및 `docs/260830_*` 내 세션 보고서들의 `mcp-servers/` 참조는 **이력 기록**으로 유효. 현재 삭제된 경로를 기술한 것은 정확한 역사 기록이므로 변경 불필요.

**총 참조 문서 수**: 활성 4 + fromscratch 6 + plans 9 + feedbacks 2 + 과거 보고서 ~20 = **~41개 문서**
