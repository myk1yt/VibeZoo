## **소개**

소프트웨어 개발 환경에서 AI 에이전트의 역할은 단순한 코드 스니펫 생성을 넘어, 시스템 아키텍처를 설계하고 자율적으로 문제를 해결하는 주도적 동반자로 진화하고 있습니다. 현재 시장에는 AI 에이전트를 통합하는 두 가지 뚜렷한 철학적 패러다임이 대립하고 있습니다. 첫째는 Anthropic의 Claude Code로 대표되는 터미널 네이티브(Terminal-native) 방식이며, 둘째는 Roo Code 및 그 파생형인 Zoo Code로 대표되는 IDE 통합(IDE-integrated) 방식입니다.1  
Claude Code는 커맨드라인 인터페이스(CLI)를 기반으로 하여 강력한 자율성을 보장하며, 복잡한 Git 작업 처리, 헤드리스(Headless) 실행, CI/CD 파이프라인 연동, 그리고 병렬 하위 에이전트(Subagent) 실행 등에서 우위를 보입니다.2 그러나 시각적 피드백이 부족하고 IDE의 풍부한 컨텍스트와 단절된다는 태생적 한계가 존재합니다. 반면 Zoo Code는 VS Code 확장을 기반으로 동작하여 다중 모델 선택권과 시각적 피드백, 그리고 custom\_modes.yaml을 통한 직관적인 페르소나 시스템을 제공하지만, 복잡한 병렬 처리나 터미널 중심의 작업에서는 흐름이 자주 끊기는 약점을 노출해 왔습니다.1  
본 조사의 핵심 목적은 Zoo Code의 기존 아키텍처를 외부 서버(예: Go TUI, Bun)로 이전하지 않고, 오직 VS Code Extension Host, Task API, TreeView API, globalState 등의 내장 API 생태계 안에서 최적해를 도출하는 것입니다. IDE 종속성을 제약이 아닌 강력한 기능적 이점으로 역전시켜, "가장 흐름이 끊기지 않는 바이브코딩 환경"을 구축하는 것이 궁극적 목표입니다. 나아가 Crow Memory(SSE 서버, crow.bin, AGENTS.md)와의 유기적 결합을 통해 세션 간 지식 영속성과 병렬 에이전트 간 맥락 공유를 구현하는 기술적 메커니즘을 상세히 규명합니다.

## **주요 결과**

본 연구는 Zoo Code의 흐름 단절 요인을 분석하고 이를 해결하기 위한 기술적 구현 방안을 검증하여 다음과 같은 핵심 인사이트를 도출했습니다. 각 인사이트는 VS Code 내장 기능과 AI 에이전트 간의 상호작용 메커니즘에 기반합니다.

* VS Code Extension Host는 단일 스레드 구조로 동작하므로 과도한 백그라운드 작업은 UI 지연을 유발합니다. 이로 인해 worker\_threads를 무리하게 사용하기보다는 로컬 프로세스로 분리된 MCP 서버와 Extension 간의 비동기 메시지 패싱을 통해 병렬 에이전트를 구축하는 것이 안정적입니다.6  
* Claude Code의 스냅샷 복원 기능은 cmux와 같은 외부 멀티플렉서에 의존하여 시스템 재부팅 시 복구가 까다로운 반면, VS Code 환경에서는 workbench.localHistory 내장 설정과 WorkspaceEdit 트랜잭션을 통해 확장 프로그램 자체적으로 지연 시간 없는 즉각적인 롤백 레이어를 구축할 수 있습니다.10  
* 사용자가 터미널 오류를 수동으로 복사하여 챗봇에 붙여넣는 마찰을 제거하기 위해, VS Code의 vscode.tasks.onDidEndTaskProcess 이벤트에서 반환되는 exitCode를 감시하여 빌드 실패 시 자동으로 LLM에 에러 컨텍스트를 주입하는 무개입 피드백 루프 자동화가 가능합니다.15  
* 기존 Roo Code 환경에서 설정 파일이 IDE 전용 스토리지에 파편화되어 관리되던 문제는 프로젝트 루트의 .roo/mcp.json 및 custom\_modes.yaml을 확장 프로그램이 자동 감지하도록 튜닝함으로써 모드 전환 마찰을 완전히 해소할 수 있습니다.18  
* 파일 변경을 감시하는 vscode.workspace.onDidChangeTextDocument API는 과도한 이벤트를 발생시켜 CPU 스파이크를 유발할 수 있으므로, 500ms 수준의 디바운싱(Debouncing) 처리와 활성 텍스트 에디터 필터링을 통해서만 컨텍스트 자동 요약 기능의 성능 저하를 막을 수 있습니다.22

이러한 분석을 바탕으로, 주요 AI 코딩 에이전트의 현재 역량과 목표로 하는 궁극적인 업그레이드 방향을 비교한 결과는 다음 표와 같습니다.

| 비교 차원 | Claude Code (CLI 네이티브) | Zoo Code (현재 VS Code 기반) | Zoo Code (목표: Ultimate Upgrade) |
| :---- | :---- | :---- | :---- |
| **세션 및 탭 복구** | cmux 등 외부 툴을 통한 텍스트 기반 스냅샷 관리 10 | IDE 재시작 시 메모리 상태 및 Custom Mode 소멸 | globalState 및 Task API를 통한 무중단 자동 복구 |
| **컨텍스트 피드백** | 파이프라인(\` | \`) 기반 터미널 명령어 체이닝 4 | 사용자의 수동 복사/붙여넣기에 전적으로 의존 |
| **롤백/체크포인트** | Git 트리 기반의 백업 및 복원 2 | Ctrl+Z 단축키 의존, 다중 파일 트랜잭션 관리 미흡 | localHistory 및 메모리 배열 기반 트랜잭션 단위 롤백 13 |
| **에이전트 확장성** | 내부 로직에 통합된 병렬 하위 에이전트 실행 4 | Boomerang 패턴을 활용한 순차적 단일 실행 모델 2 | TreeView API 대시보드 및 독립 MCP 기반 병렬화 25 |
| **컨텍스트 로딩** | CLAUDE.md 기반의 엄격한 중앙 집중식 컨텍스트 3 | 글로벌 스토리지에 숨겨진 custom\_modes.yaml 수동 적용 18 | 프로젝트 루트의 .zoo.md 및 AGENTS.md 자동 감지 및 로드 |

## **상세 분석**

본 섹션에서는 5명의 가상 바이브코더(Vibe Coder) 페르소나가 수행한 심층 분석 결과를 바탕으로, VS Code 생태계 내에서 인지적 마찰을 일으키는 원인들을 기술적으로 분해하고 해결책을 서술합니다.

### **\[바이버 1: Flow Keeper — 흐름 수호자\]**

개발자의 사고 흐름과 AI의 실행 사이의 간극을 최소화하고, 중단 없는 세션 지속성과 피드백 루프를 달성하기 위한 구조적 메커니즘을 분석합니다. 개발자가 IDE를 재시작하거나 모드를 변경할 때마다 설정이 초기화되거나 오류를 수동으로 전달해야 하는 상황은 바이브코딩의 몰입을 파괴하는 가장 큰 요인입니다.  
세션 지속성 측면에서 VS Code Extension Host가 재시작될 때 메모리 내의 임시 상태는 영구히 소멸됩니다. 이를 방지하기 위해 VS Code Extension API가 제공하는 상태 저장소인 ExtensionContext.globalState와 workspaceState의 적극적인 활용이 요구됩니다. 사용자가 마지막으로 선택한 Custom Mode나 현재 활성화된 세션 ID는 반드시 globalState에 JSON 형태로 저장되어야 하며, IDE가 로드되는 즉시 deactivate() 훅 이전의 상태를 복원하여 시각적으로 렌더링해야 합니다. 한편, 에이전트의 두뇌 역할을 하는 Crow Memory의 SSE 서버는 백그라운드에서 영구적으로 구동되어야 하므로, 확장 프로그램이 child\_process.spawn을 호출할 때 detached: true 옵션을 부여하여 서버 프로세스의 생명 주기를 Extension Host가 아닌 OS 레벨로 위임하는 아키텍처가 필수적입니다. 이 메커니즘이 완성될 경우, 세션 지속성의 바이브 점수는 현재의 4점에서 10점으로 수직 상승하며, 사용자는 IDE를 끄고 켤 때마다 AI가 초기화된다는 단절감을 느끼지 않게 됩니다.  
모드 전환 과정에서 발생하는 인지적 마찰 역시 기술적 튜닝으로 해소할 수 있습니다. 현재 사용자는 프로젝트를 열 때마다 custom\_modes.yaml에 기반한 모드 선택을 수동으로 진행해야 하는 번거로움을 겪고 있습니다.5 이를 자동화하기 위해 extension.ts 내에 vscode.workspace.onDidChangeWorkspaceFolders 이벤트를 리스닝하는 로직을 주입합니다. 프로젝트 루트에 .roo/mcp.json 20 또는 AGENTS.md가 존재하는지 스캔하고, 해당 파일의 메타데이터를 기반으로 기본 Custom Mode를 자동 활성화하는 방식입니다. 더 나아가 MCP 서버에 의존하지 않고 Zoo Code 자체의 FileSystemProvider 래퍼를 튜닝하여, 프로젝트 오픈 시 AGENTS.md를 읽어 시스템 프롬프트의 최상단(prepend)에 주입함으로써 모드 전환 클릭 수를 0회로 줄일 수 있습니다.  
가장 치명적인 흐름 단절 지점은 빌드-코드-피드백 루프에 존재합니다. 코드를 수정하고 터미널에서 npm run build를 실행한 뒤 발생하는 오류 메시지를 사용자가 직접 드래그하여 복사하고 대화창에 붙여넣는 행위는 뇌의 컨텍스트 스위칭을 강제합니다. 우리는 VS Code를 벗어나지 않으면서 이 과정을 자동화하기 위해 vscode.tasks.onDidEndTaskProcess 이벤트를 활용합니다.15 해당 API는 백그라운드에서 실행된 작업 프로세스가 종료될 때 exitCode를 반환하므로, 확장 프로그램은 exitCode가 0이 아닌 상황(빌드 실패)을 캡처할 수 있습니다.

TypeScript  
// \[튜닝\] vscode.tasks.onDidEndTaskProcess 기반 자동 에러 캡처 및 피드백 주입 의사코드  
vscode.tasks.onDidEndTaskProcess(async e \=\> {  
    if (e.exitCode\!== 0\) {  
        const errorTerminalOutput \= await fetchTerminalOutput(e.execution.task.name);  
        // 사용자 개입 없이 백그라운드에서 Crow Memory에 에러 패턴 전송  
        crowMcpClient.callTool("crow\_ingest\_from\_build", {   
            register: "bug",   
            log: errorTerminalOutput   
        });  
        // 채팅창 컨텍스트에 에러 자동 주입  
        injectContextToChat(\`빌드 오류가 감지되었습니다:\\n${errorTerminalOutput}\`);  
    }  
});

위의 의사코드와 같이 실패 감지 즉시 crow\_ingest\_from\_build MCP 도구를 백그라운드에서 호출하여 bug 레지스터에 기록하고, 요약된 진단 결과(Diagnostics)를 crow\_recall과 함께 다음 프롬프트 컨텍스트에 자동 주입합니다. 이 루프가 구축되면 현재 4점에 불과한 빌드-피드백 루프의 바이브 점수는 즉각적으로 10점에 도달합니다.  
컨텍스트 부패(Context Rot) 현상에 대한 대응도 중요한 과제입니다. 장시간 코딩 세션이 이어지면 프롬프트 컨텍스트가 비대해져 모델이 이전의 지시사항을 망각하게 됩니다. globalState의 제한된 용량 내에서 이를 관리하기 위해 Crow Memory의 단기 기억(λ=0.95 반감기) 모델을 활용합니다. 다만 너무 잦은 텍스트 감시와 파일 I/O는 CPU 부하를 일으키므로 23, 사용자의 타이핑이 멈춘 시점을 식별하는 vscode.workspace.onWillSaveTextDocument 이벤트 27를 트리거로 삼습니다. 파일 저장 시점에 10분 주기로 crow\_compact 도구를 백그라운드 호출하여 대화 내역을 압축 및 요약함으로써, 모델의 컨텍스트 창을 최적의 상태로 유지합니다.  
YOLO 모드(사용자 승인 없이 코드를 즉각적으로 수정하고 실행하는 자율 모드)의 핵심 가치는 에이전트의 '완벽한 성공'이 아니라 사용자의 '두려움 없는 회복(Fearless Recovery)'에 있습니다. AI의 대규모 코드 변경이 실패하더라도 인지적 부하 없이 단 1초 만에 이전 상태로 되돌릴 수 있는 3단계 안전망 레이어를 VS Code 내장 API를 활용하여 구축합니다.  
첫 번째 방어선은 즉각적 복원(Instant Rewind) 메커니즘입니다. Claude Code는 내부적으로 스냅샷을 구성하여 프로젝트 상태를 보호하지만, cmux나 외부 복구 도구에 의존해야 하는 한계를 지닙니다.10 이와 달리 우리는 VS Code의 내장 기능인 workbench.localHistory를 강제 활성화하는 방식을 채택합니다. settings.json에 "workbench.localHistory.enabled": true를 주입하고, 최대 파일 크기(maxFileSize)와 보관 개수(maxFileEntries)를 조율합니다.13 AI가 코드를 수정할 때마다 VS Code 자체 엔진이 백업을 생성하므로 확장 프로그램의 추가적인 성능 부하가 발생하지 않습니다. 더 넓은 범위의 복원을 위해 다중 파일 변경 전에는 VS Code 명령어 확장을 통해 git stash \-m "YOLO-before-{timestamp}"를 실행하는 백그라운드 태스크를 트리거하며 32, 문제 발생 시 git stash pop을 통해 작업 트리를 원상복구합니다.  
두 번째 방어선은 트랜잭션 처리(Transaction & Rollback) 레이어입니다. 현행 VS Code 확장 API에서 WorkspaceEdit를 통해 여러 파일을 갱신할 때 발생하는 치명적인 UX 문제는, AI가 적용한 수정 사항들이 Ctrl+Z를 누를 때마다 하나의 원자적(atomic) 트랜잭션으로 취소되지 않고 개별 편집 단계로 나뉘어 실행 취소된다는 점입니다.14 이 문제를 해결하기 위해 Zoo Code Extension 내부에 crow\_transaction이라는 논리적 레이어를 도입합니다. AI가 vscode.workspace.applyEdit를 호출하기 전에 모든 TextEdit 작업 객체를 pending\_edits 배열에 스택 형태로 저장하고, 적용 도중 실패하거나 사용자가 롤백을 요청할 경우 역순으로 새로운 WorkspaceEdit를 생성하여 되돌립니다.14 이 방식은 Git 기반 연산과 달리 오직 메모리 내에서 처리되므로 지연 시간(latency)이 사실상 존재하지 않습니다.  
세 번째 방어선은 점진적 권한 부여(Permission Gradation)를 통한 안전 구역 설정입니다. 무제한적인 YOLO 모드의 위험을 물리적으로 통제하기 위해 프로젝트 루트에 .yoloignore 파일을 도입합니다. 확장 프로그램은 vscode.workspace.createFileSystemWatcher를 사용하여 해당 파일의 룰셋을 메모리에 캐싱합니다. AI가 WorkspaceEdit 인스턴스를 빌드하여 수정을 시도할 때, 대상 파일의 URI가 ignore 패턴과 일치하면 즉각적으로 수정을 거부하고 사용자에게 프롬프트 피드백을 반환합니다. 이 과정에서 사용자가 특정 파일을 거부한 맥락은 Crow Memory의 life\_avoid 레지스터에 기록되어, 다음 세션부터는 AI가 스스로 해당 파일의 접근 경로를 회피하게 됩니다.  
이러한 메커니즘을 종합하여 각 스냅샷 생성 및 복원 방식을 비교하면 다음과 같습니다.

| 메커니즘 | 원리 및 기반 기술 | 평균 복구 지연 시간 | VS Code API 적합성 | 아키텍처 상의 장단점 |
| :---- | :---- | :---- | :---- | :---- |
| **Git Stash 기반** | git stash save / pop 래핑 32 | 중간 (\~500ms) | 높음 (명령어 래핑 활용) | 프로젝트 전체의 작업 공간 복원이 완벽하나, Git 히스토리 및 인덱스를 오염시킬 위험성 존재 |
| **VS Code localHistory** | workbench.localHistory 내장 엔진 활용 13 | 매우 낮음 (\~50ms) | 매우 높음 (순수 내장 기능) | 파일 단위의 세밀한 복원이 완벽하지만, 트랜잭션 단위로 묶어 다중 파일을 일괄 복원하기는 어려움 |
| **메모리 기반 WorkspaceEdit** | applyEdit 호출 전 TextEdit 객체 배열 캐싱 35 | 거의 없음 (\<10ms) | 매우 높음 (Ext API 조작) | 즉각적인 트랜잭션 롤백이 가능하여 인지적 마찰이 없으나, VS Code 비정상 종료 시 캐시 증발 위험 |

바이브코딩의 이상향은 사용자가 명시적으로 배경 상황을 설명하지 않아도("Zero-Explanation Coding"), AI가 사용자의 뉘앙스, 코딩 스타일, 프로젝트 특화 컨텍스트, 심지어 감정적 맥락까지 기저에서 인지하고 선제적으로 반응하는 것입니다. 이를 위해 Crow Memory를 VS Code 확장 프로그램의 신경망 깊숙이 이식하는 방안을 설계합니다.  
암묵적 컨텍스트(Implicit Context)를 주입하는 과정에서 현재 직면한 기술적 난관은, custom\_modes.yaml의 시스템 프롬프트에 crow\_recall을 지시하더라도 4B 수준의 경량 로컬 모델들은 지시사항을 무시하거나 툴 호출을 생략하는 경향이 있다는 것입니다. 이 문제를 해결하기 위해 Fallback Injection(강제 주입) 아키텍처를 도입해야 합니다. Zoo Code Extension이 LLM으로 프롬프트를 전송하기 직전에, 직접 crow.bin 파일이나 SSE 서버를 통해 최신 사용자 편향(User Bias) 데이터를 읽어옵니다. 읽어온 데이터를 원시 텍스트로 가공한 뒤, LLM에 전송되는 시스템 프롬프트 배열의 맨 앞에 \`\` 블록으로 물리적으로 강제 병합(prepend)합니다. 매 턴마다 파일 I/O를 수행하는 것은 성능 저하를 유발하므로, Extension 내부에 캐시 레이어를 두고 fs.watch로 crow.bin 파일의 변경이 감지될 때만 메모리 내 컨텍스트를 업데이트하는 최적화가 필수적입니다.  
다중 에이전트 간 맥락 공유(Multi-Agent Sync)는 Zoo Code 생태계를 넘어서는 일관성을 부여합니다. 사용자가 Kimi Code 등 다른 파생 도구를 통해 명시한 선호도가 Zoo Code에도 즉시 반영되어야만 흐름이 단절되지 않습니다.5 이를 위해 Crow SSE 서버는 crow\_evolve\_propose 도구를 통해 축적된 사용자 편향을 구체적이고 명시적인 규칙 텍스트로 컴파일하고, 이를 프로젝트 루트의 system\_prompt.md 파일로 저장합니다. Zoo Code는 vscode.workspace.onDidChangeTextDocument API를 통해 이 마크다운 파일의 변경을 실시간으로 감시합니다.22 파일 변경 이벤트가 발생하면 즉시 메모리 내 컨텍스트를 갱신하여, 상이한 에이전트 간 발생할 수 있는 '해석의 차이'를 텍스트 표준화를 통해 극복합니다.  
이 과정에서 텍스트 감시 API의 성능 최적화는 매우 중요합니다. onDidChangeTextDocument를 제어 없이 사용하면 타이핑마다 이벤트가 발생하여 분당 수백 건의 파일 시스템 호출을 유발, 심각한 CPU 스파이크를 초래합니다.23 따라서 500ms 수준의 스마트 디바운싱(Debouncing) 타이머를 적용하고, 현재 포커스된 활성 텍스트 에디터(vscode.window.activeTextEditor)에서 발생하는 이벤트로만 처리를 제한하여 백그라운드 리소스 소모를 최소화해야 합니다.  
프로젝트 특화 컨텍스트의 자동 로딩 측면에서는, 복잡한 .roo/mcp.json 설정 20 외에도 .zoo.md라는 직관적인 마크다운 파일 규격을 지원합니다. 이 파일에 팀의 규칙이나 기술 스택을 평문으로 작성해 두면, 확장 프로그램이 프로젝트 폴더 인식 시 자동으로 시스템 프롬프트에 병합합니다. 또한 감정 보정(Emotional Context) 로직을 추가하여, 사용자가 생성된 코드를 연속으로 취소하거나 "아니, 다시 해"라고 부정적인 텍스트를 입력할 경우 life\_avoid 레지스터의 polarity 값이 급감하도록 설계합니다. 이를 감지한 Zoo Code는 내부적으로 LLM의 온도(Temperature) 파라미터를 하향 조정하거나, 코드 생성 전 반드시 사용자의 승인을 요하는 'Architect 모드'로 임시 전환하여 감정적 마찰을 줄입니다.

### **\[바이버 4: Parallel Vibe Engineer — 병렬 바이브 엔지니어\]**

"Orchestra of One" 즉, 단일 사용자를 위한 AI 오케스트라의 구축은 단일 AI 모델의 순차적 처리를 넘어서는 패러다임 전환입니다. VS Code 내에서 다수의 서브 에이전트가 병렬로 독립적인 작업을 수행하고, 그 결과를 시각적으로 조율하며 충돌 없이 병합하는 아키텍처를 구현합니다.  
서브 에이전트 구현에 있어 가장 큰 제약은 VS Code Extension Host가 Node.js 기반의 단일 스레드(Single-threaded) 환경이라는 점입니다. 무거운 연산이나 백그라운드 작업을 처리하기 위해 내장된 worker\_threads를 활용하려는 시도는 빈번한 시스템 크래시를 유발합니다. 특히 과거 esbuild나 WASM 모듈을 워커 스레드로 구동하려던 시도들이 특정 OS 환경(예: macOS Big Sur)에서 호스트 다운을 일으킨 사례가 보고된 바 있습니다.6 이러한 치명적인 구조적 한계를 우회하기 위해, 무거운 병렬 작업과 외부 리소스 검색 등은 메인 Extension 프로세스와 완전히 분리된 별도의 Node 프로세스(MCP 서버, 예: scout\_mcp\_server.py)로 위임해야 합니다. Zoo Code 메인 확장은 복잡한 연산을 수행하지 않고, 단지 하위 MCP 프로세스와 통신하는 비동기 메시지 라우터(Message Router) 역할만을 수행하여 UI 스레드의 프리징을 완벽히 방어합니다.  
사용자가 메인 편집기에서 코드를 작성하는 동안, 서브 에이전트는 백그라운드에서 문서 검색이나 코드 리팩토링을 수행해야 합니다. 이때 작업의 진행 상태를 사용자에게 침해적이지 않게 전달하기 위해 VS Code의 TreeView API를 적극 활용합니다.25 확장 프로그램은 vscode.window.createTreeView와 TreeDataProvider 인터페이스를 사용하여 사이드바에 "Zoo Orchestra"라는 전용 대시보드 패널을 구축합니다. 각 하위 에이전트의 상태(대기 중, 실행 중, 오류 발생, 완료됨)는 TreeItem 객체로 매핑되어 실시간으로 표시됩니다. 작업이 완료되면 vscode.window.showInformationMessage를 통해 방해되지 않는 선에서 알림을 제공하며, 결과물은 자동으로 사용자의 작업 공간이나 컨텍스트에 주입됩니다.

TypeScript  
// \[튜닝\] vscode TreeView API를 활용한 병렬 에이전트 대시보드 상태 관리 의사코드 \[40, 42\]  
export class ZooOrchestraProvider implements vscode.TreeDataProvider\<AgentStatusItem\> {  
    private \_onDidChangeTreeData \= new vscode.EventEmitter\<AgentStatusItem | undefined\>();  
    readonly onDidChangeTreeData \= this.\_onDidChangeTreeData.event;

    // 트리 아이템의 UI 표현 (아이콘, 상태 텍스트 등) 결정  
    getTreeItem(element: AgentStatusItem): vscode.TreeItem {  
        const item \= new vscode.TreeItem(element.label);  
        item.description \= element.currentTask;  
        item.iconPath \= this.getIconForState(element.state); // 실행 중, 완료 등 아이콘 매핑  
        return item;  
    }

    // 최상위 및 하위 에이전트 목록을 SSE 서버로부터 비동기 조회  
    getChildren(element?: AgentStatusItem): Thenable\<AgentStatusItem\> {  
        return Promise.resolve(this.fetchActiveAgentsFromSSE());   
    }

    refresh(): void {  
        this.\_onDidChangeTreeData.fire(undefined);  
    }  
}

에이전트 라우팅은 채팅 입력창의 텍스트 파싱을 통해 이루어집니다. 사용자가 대화창에 @scout 최신 React 문서 찾아줘라고 입력하면, Zoo Code Extension은 문자열 선두의 @scout 접두어(Prefix)를 정규식으로 파싱하여 메인 LLM의 컨텍스트 창을 소모하지 않고 해당 텍스트를 직접 하위 MCP 클라이언트로 라우팅합니다. 만약 명시된 서브 에이전트가 존재하지 않을 경우, 메인 에이전트가 이를 이어받아 처리하는 유연한 폴백(Graceful Degradation) 로직을 갖춥니다.  
병렬 작업 시 발생할 수 있는 가장 심각한 문제는 복수의 에이전트가 동일한 파일을 동시에 수정하려 할 때 발생하는 충돌(Conflict)입니다. 이를 해결하기 위해 Crow SSE 서버 내부에 파일 경로 기반의 '중앙 잠금 관리자(Lock Manager)'를 도입합니다. 에이전트 A가 특정 파일에 대해 WorkspaceEdit 권한을 획득하려 할 때 Lock 테이블을 확인하고, 이미 선점된 경우 에이전트 B의 작업은 내부 큐(Queue)에 대기 상태로 전환됩니다.14 이 메커니즘을 통해 동시성 문제를 해결하고 파일 시스템의 무결성을 유지합니다.

### **\[바이버 5: Vibe Alchemist — 통합 설계자\]**

앞선 4개의 독립적 차원의 분석을 종합하여, VS Code Extension API의 엄격한 제약을 준수하면서 Zoo Code를 이상적인 바이브코딩 툴로 진화시키기 위한 4단계 통합 로드맵을 수립합니다. 본 로드맵은 '기술적 완벽함'보다 '흐름의 무결성'을 최우선으로 삼으며, 기존 설정 파일 체계(custom\_modes.yaml, .roo/mcp.json, .vscode/tasks.json)를 파괴하지 않고 기능을 확장하는 생태계 최적화(Ecological Niche Optimization) 전략을 취합니다.  
각 기능의 구현 가치를 평가하기 위해 '사용자 피로도 감소(y축)', '구현 난이도(x축)', 'VS Code API 적합성(z축)'을 기준으로 3차원 매트릭스를 구성하고 핵심 과제를 선별한 결과는 다음과 같습니다.

| 핵심 기능 제안 | 사용자 피로도 감소 (1-10) | 구현 난이도 (1-10) | VS Code API 적합성 (1-10) | 채택 여부 | 근거 및 분석 요약 |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **localHistory 기반 YOLO 롤백** | 9 | 3 | 10 | **채택 (Wave 2\)** | 내장된 workbench.localHistory 설정을 조작하여 인지 부하 없이 완벽한 파일 단위 롤백 구현 13 |
| **Worker Threads 기반 병렬화** | 8 | 8 | 2 | 기각 | Node 종속성 문제와 Extension Host의 메모리 크래시 위험성이 너무 높아 안정적인 바이브코딩 훼손 6 |
| **MCP 백그라운드 프로세스** | 8 | 6 | 9 | **채택 (Wave 4\)** | 스레드 분리 제약을 독립 프로세스와 SSE 기반 비동기 메시지 패싱으로 우회하여 UI 지연 방지 |
| **Task API 연동 에러 Ingest** | 10 | 4 | 10 | **채택 (Wave 1\)** | onDidEndTaskProcess API 완벽 지원으로 수동 복사/붙여넣기 마찰을 0으로 감소 15 |
| **TreeView 기반 상태 대시보드** | 7 | 5 | 10 | **채택 (Wave 4\)** | 커스텀 웹뷰의 무거움을 피하고 VS Code 네이티브 UI 경험을 유지하면서 진행 상태 시각화 25 |

#### **통합 로드맵 단계별 상세 설계**

**Phase 0: Foundation (Week 0-2) — 기반 구축**  
본 단계에서는 사용자가 프로젝트를 열고 닫을 때 발생하는 모든 초기화 마찰을 제거합니다. "사용자가 VS Code를 켰다. Zoo Code가 로딩되는 짧은 순간 동안 백그라운드에서는 OS 레벨 데몬으로 전환된 Crow SSE 서버가 자동으로 준비된다. 루트 디렉터리의 .roo/mcp.json과 .zoo.md가 즉시 감지되어 사용자는 모드 선택 버튼을 누를 필요조차 없이 어제 작성하던 코드를 곧바로 이어간다."는 사용자 경험 시나리오를 충족해야 합니다.  
기술적 구현 측면에서, extension.ts에 child\_process.spawn({ detached: true }) 속성을 적용하여 SSE 서버의 생명 주기를 OS로 위임하는 튜닝을 진행합니다. 동시에 ExtensionContext.globalState를 활용하여 lastCustomMode 및 sessionId 복원 로직을 작성하고, workspace.findFiles API를 사용하여 설정 파일들을 자동 스캔합니다. 이 단계가 완료되면 세션 지속성 부문에서 눈에 띄는 바이브 점수 향상이 이루어집니다.  
**Wave 1: Unbreakable Flow (Week 2-6) — 끊어지지 않는 흐름** 이 단계는 오류 발생 시 개발자의 인지적 문맥 전환을 차단하는 데 집중합니다. "사용자가 빌드를 실행 후 에러가 발생했다. 하지만 사용자는 에러 메시지를 복사하지 않는다. 1.5초 후, Zoo Code가 스스로 '타입 에러가 발생했습니다. 인터페이스 정의를 수정할까요?'라고 물어오며 대안 코드를 제시한다."는 시나리오를 달성합니다. 이를 위해 vscode.tasks.onDidEndTaskProcess를 구독하는 자체 튜닝을 통해 Task의 exitCode를 캡처하는 로직을 고도화합니다.15 에러 캡처 즉시 MCP 측면에 추가된 crow\_ingest\_from\_build 도구를 호출하여 에러 로그를 bug 레지스터에 영구 기록합니다. 더불어 vscode.languages.onDidChangeDiagnostics 이벤트를 리스닝하여 LSP 기반 경고(Warning)를 백그라운드에서 실시간으로 요약하고, 파일 저장 시점(onWillSaveTextDocument)을 기점으로 세션 요약 타이머를 자동 트리거하는 디바운싱 로직을 적용합니다.23  
**Wave 2: Fearless YOLO (Week 6-12) — 두려움 없는 질주** YOLO 모드의 심리적 장벽을 완전히 허무는 단계입니다. "AI가 15개의 파일을 한 번에 대대적으로 수정했다. 결과물이 마음에 들지 않은 사용자가 '되돌려'라고 입력하자, 단 0.1초 만에 수정 전 상태로 완벽히 원상 복구된다. 사전에 명시된 주요 설정 파일은 안전하게 보존되었다."는 경험을 제공합니다. VS Code 환경의 강점을 극대화하기 위해 workbench.localHistory.enabled 설정을 강제 주입하여 자체 스냅샷 엔진을 백그라운드에서 활성화합니다.13 또한 확장 프로그램의 튜닝을 통해 메모리 상의 WorkspaceEdit 객체들을 배열 형태로 임시 캐싱하여 트랜잭션 롤백 레이어(crow\_transaction)를 구현합니다.14 .yoloignore 감시 시스템은 vscode.workspace.createFileSystemWatcher 기반으로 동작하며, 에러 후 자동 복구를 위해 MCP 도구 단에서 재시도 횟수를 제한하는 max\_attempts=3 설정 논리를 포함합니다.  
**Wave 3: Zero-Explanation (Week 12-20) — 무설명 코딩** 이 단계에서는 사용자의 의도를 선제적으로 파악하는 지능형 컨텍스트 관리가 완성됩니다. "사용자가 새로운 프로젝트를 시작하며 '저번처럼 라우터 셋업해줘'라고만 말한다. AI는 이전에 다른 도구(Kimi Code)에서 학습했던 사용자의 선호 구조를 정확히 회상하여 일관된 코드 스캐폴딩을 완성한다."는 시나리오를 목표로 합니다. 구현을 위해 매 대화 턴 시작 시, 프롬프트 전송 전에 확장 프로그램이 crow.bin의 바이너리 또는 JSON 캐시를 직접 읽어 들여 \`\` 블록을 프롬프트 맨 앞에 강제 주입(Prepend)하는 하드코딩 튜닝을 적용합니다. 서버 측에서는 crow\_evolve\_propose를 통해 도출된 패턴을 system\_prompt.md 평문으로 추출하여 Git 연동이 가능하게 만듭니다. 또한 fs.watch를 통해 해당 텍스트 파일의 런타임 수정을 감지하고 즉각 리로드하는 로직을 결합합니다.22  
**Wave 4: Orchestra of One (Week 20-32) — 단일 사용자를 위한 오케스트라** 마지막으로 1인 개발자를 위한 병렬 에이전트 시스템을 완성합니다. "채팅창에 @scout 최신 React 문서 찾아줘라고 지시한 뒤 메인 창에서는 로직 수정을 계속한다. 사이드바의 대시보드에 검색 에이전트의 진행 상태가 나타나며, 완료 즉시 문서가 컨텍스트에 추가되어 메인 에이전트가 이를 활용해 코드를 작성한다."는 이상적 작업 흐름을 구현합니다. VS Code 네이티브 UI인 vscode.window.createTreeView를 사용하여 서브에이전트 패널을 구축하고 25, 채팅창의 입력 텍스트를 파싱하여 특정 MCP 서버로 컨텍스트를 분배하는 텍스트 라우터 로직을 튜닝합니다. 병렬 처리 중 발생할 수 있는 파일 시스템 충돌을 방지하기 위해 Crow SSE 서버 내에 'WorkspaceEdit Lock Manager' 로직을 통합하여 동기화를 보장합니다.

#### **종합 바이브 스코어카드 및 리스크 관리**

본 로드맵이 각 단계를 거치며 달성하게 될 사용자 경험의 정량적 평가 예측치(바이브 점수)는 다음과 같습니다. 궁극적으로 모든 차원에서 9점 이상을 획득하여 사용자가 도구의 존재 자체를 망각하는 수준에 도달하는 것이 목표입니다.

| 평가 축 (흐름 유지 항목) | 현재 점수 | Wave 1 후 | Wave 2 후 | Wave 3 후 | Wave 4 후 | 최종 목표치 |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **세션 지속성 및 무중단 복구** | 4.0 | 8.5 | 8.5 | 9.0 | 9.5 | 9.5 이상 |
| **모드 및 컨텍스트 전환 마찰** | 3.5 | 9.0 | 9.0 | 9.5 | 9.5 | 9.5 이상 |
| **YOLO 모드의 심리적 안전성** | 5.0 | 5.0 | 9.0 | 9.5 | 9.5 | 9.5 이상 |
| **장기 세션 컨텍스트 유지력** | 6.0 | 7.0 | 7.0 | 9.5 | 9.5 | 9.5 이상 |
| **백그라운드 병렬 작업성** | 2.0 | 2.0 | 2.0 | 3.0 | 8.5 | 8.5 이상 |
| **빌드 에러 자동 피드백 및 복구** | 4.0 | 9.0 | 9.5 | 9.5 | 9.5 | 9.5 이상 |
| **종합 바이브(Vibe) 점수** | **4.0** | **6.7** | **7.5** | **8.3** | **9.3** | **9.5 이상** |

프로젝트 진행 중 발생할 수 있는 주요 기술적 리스크와 그에 대한 완화 대책(Fallback) 매트릭스는 다음과 같이 구성됩니다.

| 기술적 리스크 항목 | 발생 확률 | 영향도 | 대응책 및 폴백(Fallback) 방안 |
| :---- | :---- | :---- | :---- |
| **Extension Host 성능 한계 직면** | 높음 | 높음 | 무거운 정적 분석 로직이나 웹 스크래핑 기능은 철저히 독립된 Node 프로세스 기반의 외부 MCP 도구로 100% 오프로딩하여 UI 스레드를 방어. 내장 worker\_threads 사용은 엄격히 금지.6 |
| **경량 로컬 모델의 툴 호출 실패** | 높음 | 중간 | LLM이 능동적으로 crow\_recall을 호출하지 않더라도, 프롬프트 생성 파이프라인에서 확장 프로그램이 바이너리 데이터를 원시 텍스트로 직접 파싱해 강제 주입(Prepend)하는 하드코딩 우회로 마련. |
| **Crow SSE 서버 연결 단절** | 중간 | 중간 | globalState 내부 로직에 서버 상태를 주기적으로 묻는 Health Polling을 추가하고, 응답 지연 시 즉각적인 재구동(Respawn) 스크립트 실행. 서버 재연결 전까지는 로컬 JSON 캐시 폴백 사용. |
| **병렬 에이전트 간 파일 수정 충돌** | 중간 | 높음 | SSE 서버에 중앙화된 Lock 레이블을 관리하고, 파일 접근 시 WorkspaceEdit 큐가 해소될 때까지 대기하도록 명시적인 동기화 지연 로직 구현.14 |
| **텍스트 감시 API로 인한 CPU 폭주** | 높음 | 높음 | onDidChangeTextDocument 및 onWillSaveTextDocument 이벤트 리스너에 반드시 500ms 이상의 디바운스(Debounce) 알고리즘을 적용하고, 비활성 윈도우의 이벤트를 무시하는 필터링 정책 엄수.22 |

Zoo Code를 '세상에서 가장 흐름이 끊기지 않는 바이브코딩 툴'로 진화시키기 위한 궁극적인 해답은 역설적이게도 VS Code를 벗어나는 거창한 아키텍처 혁신에 있지 않습니다. 생태계를 무리하게 이탈하여 별도의 클라우드 VM이나 무거운 독립 데스크톱 앱, 혹은 터미널 중심의 TUI 기반으로 전환하는 것은 사용자에게 새로운 형태의 인지적 마찰과 학습 곡선을 강요할 뿐입니다. 본 통합 설계안은 철저하게 VS Code Extension의 내장 API들이 지닌 잠재력을 극한으로 끌어올려 조립하는 생태계 내 최적화(Ecological Niche Optimization) 전략에 집중했습니다.  
빌드 실패를 스스로 인지하고 에러 로그를 주입하는 Task API의 비동기적 활용, 내장된 localHistory와 트랜잭션 메모리 배열을 융합하여 구현한 지연 시간 없는 즉각적 복구 레이어, 그리고 파일 시스템 변경 감지를 최적화하여 암묵적 맥락을 주입하는 기술적 기교들은 모두 이미 존재하는 VS Code 생태계의 기어들을 정교하게 맞물려 놓은 결과물입니다. 이 탄탄한 로컬 기반 위에 Crow Memory의 전역적이고 영속적인 학습 능력을 덧입힘으로써, 개발자는 더 이상 도구의 한계와 타협하거나 챗봇과 소모적인 대화를 나누지 않고 오로지 자신의 코드와만 깊이 호흡할 수 있게 될 것입니다. 이 로드맵은 파편화된 기술 스택의 단순한 기능적 나열이 아니라, '완벽한 흐름(Unbreakable Flow)'을 창조하기 위해 기획된 확장 프로그램(Extension) 단위의 가장 완벽한 인지적 신경계 연장 설계입니다.

#### **참고 자료**

1. 5월 27, 2026에 액세스, [https://www.lowcode.agency/blog/claude-code-vs-roo-code\#:\~:text=Roo%20Code%20is%20the%20right,constraint%20rather%20than%20a%20feature.](https://www.lowcode.agency/blog/claude-code-vs-roo-code#:~:text=Roo%20Code%20is%20the%20right,constraint%20rather%20than%20a%20feature.)  
2. Claude Code vs Roo Code: Feature-by-Feature Comparison \- LowCode Agency, 5월 27, 2026에 액세스, [https://www.lowcode.agency/blog/claude-code-vs-roo-code](https://www.lowcode.agency/blog/claude-code-vs-roo-code)  
3. Official Authority vs. Community Creativity: Claude Code vs. Roo Code (2026 Edition), 5월 27, 2026에 액세스, [https://medium.com/@p123456dan.mse99/official-authority-vs-community-creativity-claude-code-vs-roo-code-2026-edition-df84f2bdfa00](https://medium.com/@p123456dan.mse99/official-authority-vs-community-creativity-claude-code-vs-roo-code-2026-edition-df84f2bdfa00)  
4. Claude code vs roocode \- Reddit, 5월 27, 2026에 액세스, [https://www.reddit.com/r/RooCode/comments/1lc0t4g/claude\_code\_vs\_roocode/](https://www.reddit.com/r/RooCode/comments/1lc0t4g/claude_code_vs_roocode/)  
5. Roo Code to Kilo Code Migration Guide (2026), 5월 27, 2026에 액세스, [https://kilo.ai/articles/roo-to-kilo-migration-guide](https://kilo.ai/articles/roo-to-kilo-migration-guide)  
6. Command-line API | Node.js v26.2.0 Documentation, 5월 27, 2026에 액세스, [https://nodejs.org/api/cli.html](https://nodejs.org/api/cli.html)  
7. esbuild/CHANGELOG-2021.md at main \- GitHub, 5월 27, 2026에 액세스, [https://github.com/evanw/esbuild/blob/main/CHANGELOG-2021.md](https://github.com/evanw/esbuild/blob/main/CHANGELOG-2021.md)  
8. January 2021 (version 1.53) \- Visual Studio Code, 5월 27, 2026에 액세스, [https://code.visualstudio.com/updates/v1\_53](https://code.visualstudio.com/updates/v1_53)  
9. Modern Node.js Patterns \- Hacker News, 5월 27, 2026에 액세스, [https://news.ycombinator.com/item?id=44778936](https://news.ycombinator.com/item?id=44778936)  
10. Feature: Workspace-level session save/restore (multi-session persistence) · Issue \#43262 · anthropics/claude-code \- GitHub, 5월 27, 2026에 액세스, [https://github.com/anthropics/claude-code/issues/43262](https://github.com/anthropics/claude-code/issues/43262)  
11. GitHub \- REMvisual/claude-workspace-snapshot: Never lose your, 5월 27, 2026에 액세스, [https://github.com/REMvisual/claude-workspace-snapshot](https://github.com/REMvisual/claude-workspace-snapshot)  
12. Cmux session manager \- snapshot and restore for workspaces and claude sessions \- Reddit, 5월 27, 2026에 액세스, [https://www.reddit.com/r/ClaudeCode/comments/1sdjoly/cmux\_session\_manager\_snapshot\_and\_restore\_for/](https://www.reddit.com/r/ClaudeCode/comments/1sdjoly/cmux_session_manager_snapshot_and_restore_for/)  
13. User interface \- Visual Studio Code, 5월 27, 2026에 액세스, [https://code.visualstudio.com/docs/getstarted/userinterface](https://code.visualstudio.com/docs/getstarted/userinterface)  
14. Allow LSP servers to apply edits without polluting the undo stack \#55276 \- GitHub, 5월 27, 2026에 액세스, [https://github.com/zed-industries/zed/discussions/55276](https://github.com/zed-industries/zed/discussions/55276)  
15. The exitCode in onDidEndTaskProcess event callback is 0 when, 5월 27, 2026에 액세스, [https://github.com/microsoft/vscode/issues/125824](https://github.com/microsoft/vscode/issues/125824)  
16. Task started with vscode.tasks.executeTask doesn't generate any completition notification if dependency task fails, preventing its execution. · Issue \#97475 \- GitHub, 5월 27, 2026에 액세스, [https://github.com/microsoft/vscode/issues/97475](https://github.com/microsoft/vscode/issues/97475)  
17. How to detect failure of task execution from a vscode extension? \- Stack Overflow, 5월 27, 2026에 액세스, [https://stackoverflow.com/questions/61678941/how-to-detect-failure-of-task-execution-from-a-vscode-extension](https://stackoverflow.com/questions/61678941/how-to-detect-failure-of-task-execution-from-a-vscode-extension)  
18. \[ENHANCEMENT\] Move global custom\_modes.yaml to \~/.roo/modes/ for cross-editor consistency · Issue \#10750 · RooCodeInc/Roo-Code \- GitHub, 5월 27, 2026에 액세스, [https://github.com/RooCodeInc/Roo-Code/issues/10750](https://github.com/RooCodeInc/Roo-Code/issues/10750)  
19. Managing .roo/, modes, & rules, between projects : r/RooCode \- Reddit, 5월 27, 2026에 액세스, [https://www.reddit.com/r/RooCode/comments/1l7v23t/managing\_roo\_modes\_rules\_between\_projects/](https://www.reddit.com/r/RooCode/comments/1l7v23t/managing_roo_modes_rules_between_projects/)  
20. Shadcn MCP for Roo Code, 5월 27, 2026에 액세스, [https://www.shadcn.io/mcp/roo-code](https://www.shadcn.io/mcp/roo-code)  
21. Roo Code 3.11.0 Release Notes \- Project Level MCP Config, Fast Edits and MOREEEEEEE..... : r/ChatGPTCoding \- Reddit, 5월 27, 2026에 액세스, [https://www.reddit.com/r/ChatGPTCoding/comments/1joi2n1/roo\_code\_3110\_release\_notes\_project\_level\_mcp/](https://www.reddit.com/r/ChatGPTCoding/comments/1joi2n1/roo_code_3110_release_notes_project_level_mcp/)  
22. March 2021 (version 1.55) \- Visual Studio Code, 5월 27, 2026에 액세스, [https://code.visualstudio.com/updates/v1\_55](https://code.visualstudio.com/updates/v1_55)  
23. 5 File Insights Performance Secrets That Will Blow Your Mind \- DEV Community, 5월 27, 2026에 액세스, [https://dev.to/vijay431/5-file-insights-performance-secrets-that-will-blow-your-mind-5a2p](https://dev.to/vijay431/5-file-insights-performance-secrets-that-will-blow-your-mind-5a2p)  
24. x/tools/gopls: gopls causes bad vscode performance on large projects due to excessive LSP traffic · Issue \#74876 · golang/go \- GitHub, 5월 27, 2026에 액세스, [https://github.com/golang/go/issues/74876](https://github.com/golang/go/issues/74876)  
25. Views | Visual Studio Code Extension API, 5월 27, 2026에 액세스, [https://code.visualstudio.com/api/ux-guidelines/views](https://code.visualstudio.com/api/ux-guidelines/views)  
26. Tasks (and TaskExecutions) are not \=== in the onDid(Start|End)Task callbacks. · Issue \#96643 · microsoft/vscode \- GitHub, 5월 27, 2026에 액세스, [https://github.com/microsoft/vscode/issues/96643](https://github.com/microsoft/vscode/issues/96643)  
27. September 2016 (version 1.6) \- Visual Studio Code, 5월 27, 2026에 액세스, [https://code.visualstudio.com/updates/v1\_6](https://code.visualstudio.com/updates/v1_6)  
28. VS Code API | Visual Studio Code Extension API, 5월 27, 2026에 액세스, [https://code.visualstudio.com/api/references/vscode-api](https://code.visualstudio.com/api/references/vscode-api)  
29. Druva Claude Backup: Your Safety Net for AI-Powered Work, 5월 27, 2026에 액세스, [https://www.druva.com/blog/druva-claude-backup-for-ai-work](https://www.druva.com/blog/druva-claude-backup-for-ai-work)  
30. July 2024 (version 1.92) \- Visual Studio Code, 5월 27, 2026에 액세스, [https://code.visualstudio.com/updates/v1\_92](https://code.visualstudio.com/updates/v1_92)  
31. How can I see local history changes in Visual Studio Code? \- Stack Overflow, 5월 27, 2026에 액세스, [https://stackoverflow.com/questions/46446901/how-can-i-see-local-history-changes-in-visual-studio-code](https://stackoverflow.com/questions/46446901/how-can-i-see-local-history-changes-in-visual-studio-code)  
32. Stashing and Cleaning \- Git, 5월 27, 2026에 액세스, [https://git-scm.com/book/en/v2/Git-Tools-Stashing-and-Cleaning](https://git-scm.com/book/en/v2/Git-Tools-Stashing-and-Cleaning)  
33. Git Stash for Newbies. \- The Tidy Trekker, 5월 27, 2026에 액세스, [https://thetidytrekker.com/post/git-stash-for-newbies/git-stash-for-newbies.html](https://thetidytrekker.com/post/git-stash-for-newbies/git-stash-for-newbies.html)  
34. January 2023 (version 1.75) \- Visual Studio Code, 5월 27, 2026에 액세스, [https://code.visualstudio.com/updates/v1\_75](https://code.visualstudio.com/updates/v1_75)  
35. Vscode api, 5월 27, 2026에 액세스, [https://vscode-docs.readthedocs.io/en/stable/extensionAPI/vscode-api/](https://vscode-docs.readthedocs.io/en/stable/extensionAPI/vscode-api/)  
36. visual studio code \- VSCode extension \- how to alter file's text \- Stack Overflow, 5월 27, 2026에 액세스, [https://stackoverflow.com/questions/53585737/vscode-extension-how-to-alter-files-text](https://stackoverflow.com/questions/53585737/vscode-extension-how-to-alter-files-text)  
37. Custom modes for Roo Code VS Code extension \- Enhanced AI coding assistance configurations \- GitHub, 5월 27, 2026에 액세스, [https://github.com/jtgsystems/Custom-Modes-Roo-Code](https://github.com/jtgsystems/Custom-Modes-Roo-Code)  
38. Modern VS Code extension development tutorial: Building a secure extension \- Snyk, 5월 27, 2026에 액세스, [https://snyk.io/blog/modern-vs-code-extension-development-tutorial/](https://snyk.io/blog/modern-vs-code-extension-development-tutorial/)  
39. Roo Code \- Cognee Documentation, 5월 27, 2026에 액세스, [https://docs.cognee.ai/cognee-mcp/integrations/roo-code](https://docs.cognee.ai/cognee-mcp/integrations/roo-code)  
40. Tree View API \- Visual Studio Code, 5월 27, 2026에 액세스, [https://code.visualstudio.com/api/extension-guides/tree-view](https://code.visualstudio.com/api/extension-guides/tree-view)  
41. vscode-extension-samples/tree-view-sample/USAGE.md at main \- GitHub, 5월 27, 2026에 액세스, [https://github.com/microsoft/vscode-extension-samples/blob/master/tree-view-sample/USAGE.md](https://github.com/microsoft/vscode-extension-samples/blob/master/tree-view-sample/USAGE.md)  
42. VS-Code API: Let's Create A Tree-View In TypeScript (Part 1\) \- Coding With Thomas, 5월 27, 2026에 액세스, [https://www.codingwiththomas.com/blog/typescript-vs-code-api-lets-create-a-tree-view-part-1](https://www.codingwiththomas.com/blog/typescript-vs-code-api-lets-create-a-tree-view-part-1)  
43. Simple Example to implement VS Code TreeDataProvider with JSON data \- Stack Overflow, 5월 27, 2026에 액세스, [https://stackoverflow.com/questions/56534723/simple-example-to-implement-vs-code-treedataprovider-with-json-data](https://stackoverflow.com/questions/56534723/simple-example-to-implement-vs-code-treedataprovider-with-json-data)  
44. VSCode Extension API \- event for "text document became dirty/unsaved" \- Stack Overflow, 5월 27, 2026에 액세스, [https://stackoverflow.com/questions/65934171/vscode-extension-api-event-for-text-document-became-dirty-unsaved](https://stackoverflow.com/questions/65934171/vscode-extension-api-event-for-text-document-became-dirty-unsaved)  
45. \[vscode\] workspace.onWillSaveTextDocument is not triggered anymore since 1.62 \#15770, 5월 27, 2026에 액세스, [https://github.com/eclipse-theia/theia/issues/15770](https://github.com/eclipse-theia/theia/issues/15770)