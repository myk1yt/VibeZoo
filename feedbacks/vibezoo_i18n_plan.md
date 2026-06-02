# VibeZoo i18n & l10n Master Plan

## 1. 개요 (Overview)
현재 VibeZoo 익스텐션은 `package.json`의 명령어/설정 이름과 TypeScript 소스 코드 내에 한국어 및 영어가 하드코딩되어 있습니다. 글로벌 확장을 위해 VS Code가 지원하는 모든 주요 UI 언어를 동적으로 지원(i18n/l10n)할 수 있도록 시스템을 전면 개편합니다.

VibeZoo의 엔진 요구사항(`"vscode": "^1.90.0"`)에 맞추어, 구형 `vscode-nls` 모듈 대신 **VS Code 1.73부터 지원되는 최신 내장 API인 `vscode.l10n`**을 도입하는 것이 가장 효율적이고 현대적인 방식입니다.

## 2. 아키텍처 및 기술 스택
- **Extension Manifest (`package.json`)**: `%key_name%` 토큰을 사용하고 `package.nls.json` (기본/영어) 및 `package.nls.ko.json` (한국어) 등 언어별 파일로 분리.
- **Source Code (`TypeScript`)**: VS Code 내장 `vscode.l10n.t()` API 사용.
- **도구 (Tools)**: `@vscode/l10n-dev` CLI 패키지를 사용하여 소스 코드에서 번역 키를 자동 추출.

---

## 3. 세부 실행 계획

### Step 1: `package.json` 다국어화 (`package.nls.*.json`)
1. **JSON 구조 변경**:
   `package.json` 내 사용자 노출 텍스트(`displayName`, `description`, `title`, configuration `description`)를 모두 토큰(`%vibezoo.command.selfCheck.title%`)으로 치환.
2. **`package.nls.json` 생성 (Default/English)**:
   ```json
   {
     "vibezoo.displayName": "VibeZoo (Local)",
     "vibezoo.description": "Zoo Code Companion Extension — The most seamless vibe coding environment",
     "vibezoo.command.selfCheck.title": "VibeZoo: Self Check"
   }
   ```
3. **`package.nls.ko.json` 생성 (Korean)**:
   ```json
   {
     "vibezoo.displayName": "VibeZoo (로컬)",
     "vibezoo.description": "Zoo Code Companion Extension — 세상에서 가장 흐름이 끊기지 않는 바이브코딩 환경",
     "vibezoo.command.selfCheck.title": "VibeZoo: Self Check (시스템 자가진단)"
   }
   ```
4. **`package.json` 메타데이터 업데이트**:
   최상위에 `"l10n": "./l10n"` 필드를 추가하여 런타임 번들 위치를 명시.

### Step 2: TypeScript 소스 코드 다국어화 (`vscode.l10n`)
1. **개발 의존성 설치**:
   명령어: `npm install -D @vscode/l10n-dev`
2. **`package.json` Script 추가**:
   ```json
   "scripts": {
     "l10n:export": "npx @vscode/l10n-dev export --outDir ./l10n ./src"
   }
   ```
3. **소스 코드 내 문자열 치환**:
   `src/extension.ts`, `src/ui/StatusBarManager.ts`, `src/visual/VisualVibePanels.ts` 등에서 하드코딩된 메세지를 `vscode.l10n.t()`로 감쌉니다.
   *Tip: 소스 코드 내부의 기본 문자열은 **영어(English)**로 통일하는 것이 글로벌 오픈소스 표준입니다.*
   
   **Before:**
   ```typescript
   vscode.window.showInformationMessage('VibeZoo: Auto-Fix Loop 일시 중지됨');
   ```
   **After:**
   ```typescript
   import * as vscode from 'vscode';
   vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Auto-Fix Loop paused'));
   ```

   **변수 보간(Interpolation)이 필요한 경우:**
   ```typescript
   vscode.l10n.t({
     message: '✅ {0} uploaded. (Path copied to clipboard!)',
     args: [fileTypeLabel],
     comment: ['Notification when a file is successfully uploaded']
   });
   ```

### Step 3: 번역 번들 파일(l10n) 생성 및 분리
1. **추출 스크립트 실행**:
   `npm run l10n:export` 실행.
   결과물로 `./l10n/bundle.l10n.json` 파일이 자동 생성되며, 소스 코드 내 모든 영어 기본 문자열이 키로 등록됩니다.
2. **언어별 번역본 생성**:
   생성된 `bundle.l10n.json`을 복사하여 `./l10n/bundle.l10n.ko.json`을 만들고 각 키값에 대응하는 한국어 번역을 입력합니다.
   (VS Code 런타임은 사용자의 표시 언어에 맞춰 적절한 `bundle.l10n.*.json`을 자동으로 로드합니다.)

### Step 4: Webview UI 다국어화 (해당 시)
`src/visual/VisualVibePanels.ts` 등에서 HTML을 렌더링하는 Webview는 Extension Host와 컨텍스트가 분리되어 있으므로 `vscode.l10n.t()`가 직접 동작하지 않습니다.
- **해결책**: Webview HTML을 생성할 때, Extension에서 `vscode.l10n.t()`를 통해 번역된 문자열을 HTML 내부에 주입(Inject)하거나, `postMessage`를 통해 설정값으로 전달하여 Webview 내부 JS에서 활용하도록 구현합니다.

### Step 5: 배포 및 패키징 설정 점검
1. **`.vscodeignore` 점검**:
   `package.nls.json`, `package.nls.ko.json` 파일들과 `l10n/` 디렉터리가 패키징 시 무시되지 않도록(즉, 배포 파일에 포함되도록) `.vscodeignore`를 확인합니다.

---

## 4. 요약 (Action Items for Coder)
1. 루트 경로에서 `npm install -D @vscode/l10n-dev` 실행.
2. `package.json`의 모든 UI 문자열을 `%...%` 형식으로 치환 및 `"l10n": "./l10n"` 추가.
3. `package.nls.json`, `package.nls.ko.json` 생성.
4. `src/**/*.ts` 안의 모든 하드코딩 한글/영문 알림(`showInformationMessage` 등)을 `vscode.l10n.t()` 영문 기본 메시지로 교체.
5. `npm run l10n:export` 실행하여 `l10n/bundle.l10n.json` 추출 후, `l10n/bundle.l10n.ko.json` 작성.
6. Webview UI의 경우 번역된 String 맵을 HTML에 주입하도록 수정.
