# VibeZoo 로컬 재설치 계획 (간소화)

## 진단 결과

| 항목 | 상태 |
|------|------|
| **Global MCP 설정** (`mcp_settings.json`) | ✅ `vibezoo` 이미 등록됨 (`http://localhost:9027/sse`) |
| **브릿지** (port 9027) | ❌ 미실행 또는 구버전 |
| **Global mcp-servers** (`%USERPROFILE%\.vscode\extensions\mcp-servers\`) | ⚠️ 구버전 코드일 가능성 - 업데이트 필요 |
| **Python deps** (fastmcp, uvicorn, starlette) | ⚠️ 미확인 |
| **mcp_settings.json 툴 목록** | ⚠️ `learn_project` 누락, `open_image_dropzone`/`open_dropzone` (폐기됨) 잔존 |

`.roo/mcp.json`은 프로젝트 레벨 설정이므로 **건드릴 필요 없음**. 확장 재컴파일/재설치도 불필요.

---

## 실행 계획 (4단계)

### Step 1: 구 브릿지 종료 & Python 환경 확인

```powershell
# 1-a. 9027 포트 점유 프로세스 kill
netstat -ano | findstr ":9027.*LISTENING"
taskkill /F /PID <PID> /T

# 1-b. fastmcp, uvicorn, starlette 설치 확인 및 설치
pip install fastmcp uvicorn starlette
```

### Step 2: Global mcp-servers 최신화

워크스페이스의 최신 `mcp-servers/` → Global 경로로 복사:

```powershell
# 소스: 워크스페이스 mcp-servers/
# 대상: %USERPROFILE%\.vscode\extensions\mcp-servers\
robocopy "mcp-servers" "%USERPROFILE%\.vscode\extensions\mcp-servers" /E /XO /NFL /NDL
```

`/XO` = 대상보다 최신 파일만 덮어쓰기.

### Step 3: Global MCP 설정 툴 목록 동기화

파일: `%APPDATA%\Code\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json`

현재 `vibezoo.alwaysAllow` 배열에서:
- **추가**: `"learn_project"` (신규 Knowledge 툴)
- **제거**: `"open_image_dropzone"`, `"open_dropzone"` (브릿지 v0.14.4에서 폐기, `capture_screen`으로 통합)

```diff
  "alwaysAllow": [
    ...
    "recall_project",
+   "learn_project",
    "learn_preference",
    "get_preferences",
    ...
-   "open_image_dropzone",
-   "open_dropzone",
    "analyze_uploaded_file",
    ...
  ]
```

### Step 4: 새 브릿지 실행 & 검증

```powershell
# 4-a. 브릿지 시작 (백그라운드)
start /B python "%USERPROFILE%\.vscode\extensions\mcp-servers\vibezoo_mcp_bridge.py" --port 9027

# 4-b. 헬스체크
curl http://127.0.0.1:9027/health
# → {"status":"ok","crow":...,"timestamp":...,"version":"0.14.4"}

# 4-c. SSE 엔드포인트 확인
curl http://127.0.0.1:9027/sse
# → SSE 스트림 응답
```

### Step 5: Zoo Code에서 확인

1. Zoo Code 재시작 (또는 MCP 재연결)
2. 채팅에서 VibeZoo 도구 호출 가능 확인 (`search_codebase`, `review_code` 등)

---

## 요약

| 단계 | 작업 | 파일/대상 |
|------|------|-----------|
| 1 | 구 브릿지 kill | port 9027 프로세스 |
| 2 | 최신 코드 복사 | `mcp-servers/` → Global `mcp-servers/` |
| 3 | 툴 목록 동기화 | `mcp_settings.json` (add `learn_project`, remove deprecated) |
| 4 | 새 브릿지 실행 | `vibezoo_mcp_bridge.py --port 9027` |
| 5 | 검증 | `/health` → `0.14.4`, Zoo Code 도구 확인 |

**불필요한 작업 제거:**
- ~~TypeScript 컴파일~~ (확장은 그대로 사용)
- ~~VS Code 확장 재설치~~ (v0.14.3 → v0.14.4 변경은 Extension TypeScript 코드 변경사항이 있을 때만 필요)
- ~~`.roo/mcp.json` 수정~~ (프로젝트 레벨, Global 설정으로 충분)
- ~~`.vscode/settings.json` 생성~~ (VibeZoo 동작과 무관)
- ~~`.zoo/config.json` 수정~~ (확장이 자동 관리)
