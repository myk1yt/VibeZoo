# VibeZoo — 원큐 설치 및 환경 설정 가이드 (Installation Guide)

VibeZoo는 Zoo Code 및 AI 코딩 어시스턴트의 기능을 극대화하는 컴패니언 확장 프로그램(Companion Extension)입니다.  
컴퓨터에 익숙하지 않은 사용자도 **3단계만 따라 하면 원클릭으로 모든 MCP 서버 연결과 확장 설치를 완료**할 수 있도록 완전히 자동화되었습니다.

---

## 📋 목차
1. [시스템 요구사항](#-시스템-요구사항)
2. [Windows 환경 원샷 3단계 설치](#-windows-환경-원샷-3단계-설치)
3. [macOS / Linux 환경 원샷 3단계 설치](#-macos--linux-환경-원샷-3단계-설치)
4. [추가 환경 설정 (선택 사항)](#-추가-환경-설정-선택-사항)
5. [설치 후 정상 동작 확인 (Self Check)](#-설치-후-정상-동작-확인-self-check)
6. [자주 묻는 질문 및 트러블슈팅 (6선)](#-자주-묻는-질문-및-트러블슈팅-6선)

---

## 💻 시스템 요구사항

- **OS**: Windows 10/11 (64-bit), macOS 12+ (Apple Silicon / Intel), Linux (Ubuntu 20.04+)
- **Python**: Python 3.10 이상 (Python 3.11/3.12 권장, **Add python.exe to PATH** 필수)
- **Node.js**: Node.js 18.x 또는 20.x LTS 이상
- **IDE**: [Visual Studio Code](https://code.visualstudio.com/) 최신 버전
- **어시스턴트**: VS Code 내 **Zoo Code** 확장 (또는 Roo Code / Cline 등 MCP 지원 확장)
- **권한**: 관리자 권한 없이 일반 사용자 권한으로 설치 가능

---

## 🪟 Windows 환경 원샷 3단계 설치

### 1단계: 필수 런타임 준비 및 저장소 복제
1. **Python 3.10+ 설치**: [Python 공식 홈페이지](https://www.python.org/downloads/)에서 인스톨러 다운로드 후, 설치 첫 화면에서 반드시 **`[x] Add python.exe to PATH`**를 체크하고 설치합니다.
2. **Node.js LTS 설치**: [Node.js 공식 홈페이지](https://nodejs.org/)에서 LTS 버전을 설치합니다.
3. **VS Code & Zoo Code 설치**: VS Code 설치 후 확장 마켓플레이스(`Ctrl+Shift+X`)에서 **Zoo Code**를 설치합니다.
4. **저장소 복제(Clone)**: 명령 프롬프트(cmd)에서 아래 명령을 실행합니다:
   ```cmd
   git clone https://github.com/vibezoo/VibeZoo_forZoocode.git
   cd VibeZoo_forZoocode
   ```

### 2단계: `init_vibezoo.bat` 원샷 부트스트래퍼 실행
`VibeZoo_forZoocode` 폴더의 **`init_vibezoo.bat`** 파일을 더블 클릭하여 실행합니다. (또는 cmd에서 `init_vibezoo.bat` 입력)

스크립트가 다음 전 과정을 원스톱으로 자동 처리합니다:
- 표준 런타임 디렉터리(`%USERPROFILE%\mcp-servers\vibezoo`) 생성 및 모듈 복사
- 독립 Python 가상환경(`venv`) 구축 및 패키지(`fastmcp`, `starlette`, `requests`, `tree_sitter_languages`) 설치
- 확장 빌드 및 VSIX 패키징 (`vsce package`)
- **VS Code 확장 CLI 자동 설치** (`code --install-extension vibezoo-*.vsix`)
- **글로벌 MCP 설정 자동 등록** (`%APPDATA%\...\mcp_settings.json`에 `vibezoo`, `crow-memory` 자동 등록)
- **백그라운드 서버 자동 기동** (VibeZoo Bridge 포트 `9027`, Crow Memory 포트 `9021`)

### 3단계: VS Code 실행 및 동작 확인
1. VS Code를 실행합니다.
2. `Ctrl + Shift + P`로 커맨드 팔레트를 열고 **`VibeZoo: Self Check`**를 실행하여 모든 서버 연결이 정상인지 확인합니다.

---

## 🍎 macOS / Linux 환경 원샷 3단계 설치

### 1단계: 런타임 설치 및 저장소 복제
```bash
# macOS (Homebrew)
brew install git python@3.11 node
# Ubuntu / Debian
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip nodejs npm

# 저장소 복제
git clone https://github.com/vibezoo/VibeZoo_forZoocode.git
cd VibeZoo_forZoocode
```

### 2단계: `init_vibezoo.sh` 실행 및 확장 설치
```bash
chmod +x init_vibezoo.sh
./init_vibezoo.sh

# VSIX 빌드 및 설치
cd extension
npx vsce package
code --install-extension vibezoo-*.vsix
```

### 3단계: 백그라운드 서버 구동 및 확인
```bash
cd ~/mcp-servers/vibezoo
source venv/bin/activate
python vibezoo_mcp_bridge.py --port 9027 &
python crow_memory_server.py --port 9021 &
```
VS Code를 열고 `Cmd + Shift + P` -> **`VibeZoo: Self Check`**를 실행합니다.

---

## ⚙️ 추가 환경 설정 (선택 사항)

### 1. Crow Memory 서버 연동
- VibeZoo는 장기 시냅스 메모리 서버인 **Crow Memory**를 지원합니다.
- `init_vibezoo.bat`에 의해 포트 `9021`에서 Streamable HTTP MCP 모드로 자동 구동되며, 외부 전용 서버가 있을 경우 포트 `9020`으로 자동 프록시됩니다.

### 2. Exa 신경망 웹 검색 (`EXA_API_KEY`)
- `web_search` 도구는 고정밀 AI 검색 엔진인 **Exa API**를 지원합니다.
- [Exa AI](https://exa.ai)에서 API 키를 발급받은 후 시스템 환경변수에 등록하세요:
  - **Windows (cmd)**: `setx EXA_API_KEY "your_api_key_here"`
  - **macOS / Linux**: `export EXA_API_KEY="your_api_key_here"`
- *참고: `EXA_API_KEY`가 없어도 DuckDuckGo 검색으로 자동 폴백되어 웹 검색이 정상 동작합니다.*

### 3. 로컬 시맨틱 임베딩 서버 (포트 `8089`)
- [LM Studio](https://lmstudio.ai/) 또는 [Ollama](https://ollama.com/)에서 `nomic-embed-text` 모델을 로드하고 로컬 서버 포트를 `8089`로 설정하면 고속 벡터 시맨틱 검색이 활성화됩니다.
- *참고: 임베딩 서버가 없어도 내장 BM25 키워드 랭킹 엔진으로 자동 폴백됩니다.*

---

## ✅ 설치 후 정상 동작 확인 (Self Check)

1. VS Code를 실행합니다.
2. **커맨드 팔레트**를 엽니다:
   - Windows/Linux: `Ctrl + Shift + P`
   - macOS: `Cmd + Shift + P`
3. **`VibeZoo: Self Check`** 를 입력하고 실행합니다.
4. 알림창에 아래와 같이 표시되면 완벽하게 설치된 것입니다:
   ```text
   VibeZoo Self Check: All systems operational.
   - Python Bridge (Port 9027): Connected
   - Crow Memory (Port 9021/9020): Ready
   - Guard.git Protection: Active
   ```

---

## 🔧 자주 묻는 질문 및 트러블슈팅 (6선)

### 1. 포트 충돌 오류 (Port Conflict: 9027, 9021, 9020, 8089)
- **증상**: `WinError 10048` 또는 `Address already in use` 에러가 발생하며 서버가 켜지지 않습니다.
- **해결책**:
  - **Windows**:
    ```cmd
    netstat -ano | findstr :9027
    taskkill /F /PID <조회된PID>
    ```
  - **macOS/Linux**:
    ```bash
    lsof -i :9027
    kill -9 <조회된PID>
    ```

### 2. 임베딩 서버 미구동 ("Local embedding server not found at port 8089")
- **증상**: 코드 검색 시 안내 문구가 나타납니다.
- **해결책**:
  - VibeZoo는 LM Studio / Ollama의 `nomic-embed-text` 모델을 포트 `8089`에서 기본 탐색합니다.
  - 임베딩 서버가 켜져 있지 않아도 **내장 BM25 키워드 랭킹 엔진으로 자동 폴백**되어 정상 동작합니다.

### 3. VSIX 수동 설치 방법
- **증상**: `code` 명령어가 환경변수에 없어서 확장이 자동 설치되지 않았습니다.
- **해결책**:
  - VS Code를 열고 확장(Extensions) 탭(`Ctrl+Shift+X`) 상단 메뉴 `...` -> **Install from VSIX...** 를 선택하여 `extension/` 폴더에 생성된 `vibezoo-*.vsix` 파일을 선택해 설치합니다.

### 4. Windows OneDrive 동기화 파일 잠금 현상
- **증상**: `init_vibezoo.bat` 실행 시 `Access is denied` (액세스 거부) 또는 파일 잠금 에러가 발생합니다.
- **해결책**:
  - VibeZoo 프로젝트 폴더가 `OneDrive` 동기화 폴더 내에 있는 경우 동기화를 일시 중지하거나, `C:\Projects\VibeZoo`와 같은 순수 로컬 드라이브 경로로 이동하여 작업하세요.

### 5. MCP 설정 파일 위치 및 수동 등록
- **글로벌 MCP 설정 위치**:
  - **Windows**: `%APPDATA%\Code\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json`
  - **macOS**: `~/Library/Application Support/Code/User/globalStorage/zoocodeorganization.zoo-code/settings/mcp_settings.json`
  - **Linux**: `~/.config/Code/User/globalStorage/zoocodeorganization.zoo-code/settings/mcp_settings.json`
- `init_vibezoo.bat`가 자동으로 생성하지만, 수동 설정이 필요한 경우 위 경로의 `mcp_settings.json`에 `vibezoo` (url: `http://127.0.0.1:9027/sse`) 및 `crow-memory` (url: `http://127.0.0.1:9021/mcp`)를 등록할 수 있습니다.

### 6. 이미지 붙여넣기 및 비전 분석 (Dropzone & Vision)
- **사용법**:
  1. 커맨드 팔레트(`Ctrl+Shift+P` / `Cmd+Shift+P`)에서 **`VibeZoo: Open Image Dropzone`**을 실행합니다.
  2. 스크린샷이나 이미지를 복사(`Ctrl+C`)한 후 드롭존 창에서 붙여넣기(`Ctrl+V`)합니다.
  3. 설정 `vibezoo.image.autoAnalyze`가 활성화되어 있으면 자동으로 OCR, SSA 공간 통계 분석이 수행되어 AI에게 컨텍스트가 전달됩니다.
