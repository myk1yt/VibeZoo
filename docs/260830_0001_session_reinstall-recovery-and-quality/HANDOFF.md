# VibeZoo 핸즈오프 문서 — 새 세션용

> **작성일**: 2026-08-30 | **세션**: 260830_0001_session_reinstall-recovery-and-quality
> **최종 커밋**: `ad69d39` (ef18b1f..ad69d39, 18커밋) | **push 상태**: 원격 반영 완료

---

## 1. 현재 상태 요약

### ✅ 완료된 것
| 항목 | 상태 | 근거 |
|------|:----:|------|
| Git 연결 (HTTPS+GCM) | ✅ | `git push origin main` 성공 (ad69d39) |
| i18n 20개 언어 완전 지원 | ✅ | translations 212키×20 Missing=0 |
| web_search Exa 설명 | ✅ | 이미 교정 완료 상태 |
| 코드베이스 검색 정상화 | ✅ | embedding TTL/백오프 + index_cache + rebuild 툴 |
| 기능 쓸모 평가+정리 | ✅ | 9툴+13커맨드 삭제, 33툴/20커맨드 유지 |
| 이미지 붙여넣기 UX | ✅ | Dropzone 개편 + vision 폴백 |
| 일회성 파일/문서 정리 | ✅ | -p/, docs/archive 이동, 경로 교정 |
| 설치 가이드 | ✅ | docs/INSTALLATION.md (Win/Mac 8단계+트러블슈팅) |
| README 전수 갱신 | ✅ | 33툴/20커맨드/0 broken links |
| 커밋+push | ✅ | 18커밋 원격 반영 |

### ❌ 미해결: VibeZoo MCP 브릿지 연결

**원인**: 글로벌 MCP 설정(`mcp_settings.json`)에는 `vibezoo: http://127.0.0.1:9027/sse`가 등록되어 있지만, 브릿지 서버 프로세스가 실행되고 있지 않습니다. Windows 재설치 후 자동 시작 스크립트가 재구동되지 않은 상태입니다.

**크로우 메모리와 비교**:
- Crow Memory: `http://127.0.0.1:9021/mcp` → 정상 동작 (이 세션에서 recall/ingest 사용 확인)
- VibeZoo: `http://127.0.0.1:9027/sse` → 미실행 (port 9027 연결 불가)

**해결 방향**: 브릿지 서버를 시작하는 방법은 다음 중 하나:
1. `extension/mcp-servers/start_vibezoo_bridge.bat` 실행
2. VSIX 확장 설치 시 VS Code가 자동으로 브릿지를 기동
3. 수동: `python extension/mcp-servers/vibezoo_mcp_bridge.py` 직접 실행

---

## 2. 글로벌 MCP 설정 위치

```
%APPDATA%\Code\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json
```

현재 등록된 MCP 서버:
| 서버 | URL | 상태 |
|------|-----|:----:|
| vibezoo | `http://127.0.0.1:9027/sse` | ❌ 미실행 |
| crow-memory | `http://127.0.0.1:9021/mcp` | ✅ 동작 |
| github | `https://api.githubcopilot.com/mcp/` | ✅ 동작 |
| hf-mcp-server | `https://huggingface.co/mcp` | ✅ 동작 |

---

## 3. 새 세션에서 해야 할 것

### 긴급: VibeZoo 연결 복구 (새 세션이 가장 먼저 할 일)

```bash
# 1) 브릿지 서버 시작 (VibeZoo 워크스페이스에서)
cd %USERPROFILE%/OneDrive/Projects/VibeZoo
python extension/mcp-servers/vibezoo_mcp_bridge.py

# 2) 또는 배치파일로
extension/mcp-servers/start_vibezoo_bridge.bat

# 3) 연결 확인 (포트 9027이 리스닝되는지)
netstat -ano | findstr 9027
```

**브릿지가 시작되면 Zoo Code에서 자동으로 MCP 서버를 감지하고 연결됩니다.**

### 우선순위

| 순위 | 작업 | 세션 위임 모드 |
|:----:|------|:----------:|
| 1 | VibeZoo 브릿지 연결 복구 + VSIX 재설치 검토 | debug |
| 2 | 모든 기능 실제 동작 검증 (tsc, pytest, 브릿지 연결) | code |
| 3 | 남은 잔여 작업 (MERGE 기회, bundle.l10n 오염 키) | code-light |

---

## 4. 이번 세션의 핵심 아키텍처 결정

| 결정 | 내용 | 근거 |
|------|------|------|
| 소스 = extension | `extension/mcp-servers/`가 유일한 소스, 루트 `mcp-servers/` 제거 | 092600 보고서 (tools 38개 상위집합, config 0.15.1) |
| Embedding 캐시 | TTL 60s + 지수백오프 + reset_availability | 114000 (P5 수정) |
| 디스크 인덱스 | `.zoo-code/index-cache/` (numpy 벡터 캐시, 파일해시) | 101000 |
| 이미지 UX | Dropzone이 공식 입구, 채팅 직접 Ctrl+V 불가 | 104500, decisions.md |
| 재구축 커맨드 | `vibezoo.rebuildCodeIndex` (VS Code 커맨드 + MCP 툴) | 103500 |
| 기능 정리 | 9 MCP 툴 + 13 커맨드 DELETE | 112000 |

---

## 5. 중요 파일 위치

| 파일 | 경로 |
|------|------|
| 설치 가이드 | [`docs/INSTALLATION.md`](docs/INSTALLATION.md) |
| 요구사항 | [`docs/260830_0001_session_reinstall-recovery-and-quality/requirement-checklist.md`](docs/260830_0001_session_reinstall-recovery-and-quality/requirement-checklist.md) |
| 아키텍처 | [`docs/ARCHITECTURE_CORE.md`](docs/ARCHITECTURE_CORE.md) |
| 현재 상태 | [`docs/ACTIVE_STATE.md`](docs/ACTIVE_STATE.md) |
| 아키텍처 결정 | [`docs/260830_0001_session_reinstall-recovery-and-quality/architecture-plan.md`](docs/260830_0001_session_reinstall-recovery-and-quality/architecture-plan.md) |
| 사용자 결정 | [`docs/260830_0001_session_reinstall-recovery-and-quality/decisions.md`](docs/260830_0001_session_reinstall-recovery-and-quality/decisions.md) |
| 브릿지 소스 | [`extension/mcp-servers/vibezoo_mcp_bridge.py`](extension/mcp-servers/vibezoo_mcp_bridge.py) |
| MCP 글로벌 설정 | `%APPDATA%/Code/User/globalStorage/zoocodeorganization.zoo-code/settings/mcp_settings.json` |

---

## 6. 새 세션용 프롬프트

아래 프롬프트를 복사해서 새 세션에서 사용하세요:

```
## 세션 시작

VibeZoo 재설치 복구 세션의 후속입니다.

### 현재 상태
- Git 연결: HTTPS+GCM, push 완료 (ad69d39)
- Crow Memory MCP: 글로벌 정상 동작
- VibeZoo MCP 브릿지: 포트 9027 미실행 → 연결 불가

### 긴급 작업
1. VibeZoo 브릿지 서버를 시작해주세요:
   - 경로: extension/mcp-servers/vibezoo_mcp_bridge.py
   - 또는 start_vibezoo_bridge.bat
   - 포트 9027에서 SSE 서버 동작 확인
2. VSIX 재설치 검토 (vsce package → 확장 디렉토리 설치)
3. 모든 MCP 툴이 Zoo Code에서 호출 가능한지 검증

### 참조
- 핸즈오프: docs/260830_0001_session_reinstall-recovery-and-quality/HANDOFF.md
- 설치 가이드: docs/INSTALLATION.md
- 구현 보고서: docs/260830_0001_session_reinstall-recovery-and-quality/
- 아키텍처: docs/ARCHITECTURE_CORE.md
```

---

*이 문서는 260830 세션에서 자동 생성되었습니다.*
