## VibeZoo 설치 및 실행 가이드

### 1. VibeZoo VS Code Extension 설치

```bash
cd extension
npm install
npm run compile
```

VS Code에서 `extension/` 폴더를 열고 `F5`를 눌러 Extension Development Host에서 실행.

### 2. Go MCP 서버 빌드

```powershell
cd mcp-servers
go mod tidy
.\build.ps1
```

또는 수동으로:
```bash
go build -o bin/scout ./cmd/scout
go build -o bin/reviewer ./cmd/reviewer
go build -o bin/tester ./cmd/tester
```

### 3. Crow Memory 연결 (외부 시스템)

Crow Memory가 이미 설치되어 실행 중이어야 합니다.
VibeZoo는 Crow를 자동으로 찾아서 연결합니다.
- Crow 기본 포트: 9020
- 설정: `vibezoo.crow.port`

### 4. Zoo Code에 VibeZoo 통합

Zoo Code 채팅창에 다음과 같이 입력하세요:

```
"VibeZoo를 설치해줘. 확장 ID는 vibezoo야."
```

또는 수동으로:
1. VS Code Extensions 패널 열기
2. "VibeZoo" 검색
3. 설치

### 5. Zoo Code MCP 설정

Zoo Code가 VibeZoo의 MCP 서버들을 사용할 수 있도록 `.roo/mcp.json`에 추가:

```json
{
  "mcpServers": {
    "crow": {
      "url": "http://localhost:9020",
      "transport": "sse"
    },
    "scout": {
      "url": "http://localhost:9022",
      "transport": "sse"
    },
    "reviewer": {
      "url": "http://localhost:9023",
      "transport": "sse"
    },
    "tester": {
      "url": "http://localhost:9024",
      "transport": "sse"
    }
  }
}
```

### 6. Zoo Code에 "VibeZoo 설치해줘" 라고 말하기

Zoo Code가 위 설정을 자동으로 구성합니다.
