# VibeZoo i18n & l10n Master Plan

## 1. Overview
Currently, the VibeZoo extension has Korean and English hardcoded in the `package.json` command/setting names and TypeScript source code. For global expansion, the system will be completely reorganized to dynamically support all major UI languages supported by VS Code (i18n/l10n).

Aligning with VibeZoo's engine requirement (`"vscode": "^1.90.0"`), introducing **VS Code's latest built-in API `vscode.l10n`**, supported since VS Code 1.73, instead of the older `vscode-nls` module, is the most efficient and modern approach.

## 2. Architecture and Tech Stack
- **Extension Manifest (`package.json`)**: Use `%key_name%` tokens and separate into `package.nls.json` (default/English) and `package.nls.ko.json` (Korean) per language files.
- **Source Code (`TypeScript`)**: Use VS Code's built-in `vscode.l10n.t()` API.
- **Tools**: Use `@vscode/l10n-dev` CLI package to automatically extract translation keys from source code.

---

## 3. Detailed Execution Plan

### Step 1: `package.json` Internationalization (`package.nls.*.json`)
1. **JSON Structure Change**:
   Replace all user-facing text in `package.json` (`displayName`, `description`, `title`, configuration `description`) with tokens (`%vibezoo.command.selfCheck.title%`).
2. **Create `package.nls.json` (Default/English)**:
   ```json
   {
     "vibezoo.displayName": "VibeZoo (Local)",
     "vibezoo.description": "Zoo Code Companion Extension — The most seamless vibe coding environment",
     "vibezoo.command.selfCheck.title": "VibeZoo: Self Check"
   }
   ```
3. **Create `package.nls.ko.json` (Korean)**:
   ```json
   {
     "vibezoo.displayName": "VibeZoo (로컬)",
     "vibezoo.description": "Zoo Code Companion Extension — 세상에서 가장 흐름이 끊기지 않는 바이브코딩 환경",
     "vibezoo.command.selfCheck.title": "VibeZoo: Self Check (시스템 자가진단)"
   }
   ```
4. **Update `package.json` Metadata**:
   Add `"l10n": "./l10n"` field at the top level to specify runtime bundle location.

### Step 2: TypeScript Source Code Internationalization (`vscode.l10n`)
1. **Install Development Dependency**:
   Command: `npm install -D @vscode/l10n-dev`
2. **Add `package.json` Script**:
   ```json
   "scripts": {
     "l10n:export": "npx @vscode/l10n-dev export --outDir ./l10n ./src"
   }
   ```
3. **Replace Strings in Source Code**:
   Wrap hardcoded messages in `src/extension.ts`, `src/ui/StatusBarManager.ts`, `src/visual/VisualVibePanels.ts`, etc. with `vscode.l10n.t()`.
   *Tip: The default strings inside source code should be unified to **English** as a global open-source standard.*
   
   **Before:**
   ```typescript
   vscode.window.showInformationMessage('VibeZoo: Auto-Fix Loop 일시 중지됨');
   ```
   **After:**
   ```typescript
   import * as vscode from 'vscode';
   vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Auto-Fix Loop paused'));
   ```

   **When Variable Interpolation is Needed:**
   ```typescript
   vscode.l10n.t({
     message: '✅ {0} uploaded. (Path copied to clipboard!)',
     args: [fileTypeLabel],
     comment: ['Notification when a file is successfully uploaded']
   });
   ```

### Step 3: Create and Separate Translation Bundle Files (l10n)
1. **Run Extraction Script**:
   Execute `npm run l10n:export`.
   This automatically generates `./l10n/bundle.l10n.json` with all English default strings from source code registered as keys.
2. **Create Language-specific Translations**:
   Copy the generated `bundle.l10n.json` to create `./l10n/bundle.l10n.ko.json` and enter corresponding Korean translations for each key value.
   (VS Code runtime automatically loads the appropriate `bundle.l10n.*.json` according to the user's display language.)

### Step 4: Webview UI Internationalization (If Applicable)
Webviews rendering HTML in `src/visual/VisualVibePanels.ts` etc. have a separate context from Extension Host, so `vscode.l10n.t()` does not work directly.
- **Solution**: When generating Webview HTML, inject translated strings from Extension via `vscode.l10n.t()` into HTML, or pass them as configuration values via `postMessage` for use by Webview internal JS.

### Step 5: Distribution and Packaging Settings Check
1. **Check `.vscodeignore`**:
   Ensure `package.nls.json`, `package.nls.ko.json` files and `l10n/` directory are not ignored during packaging (i.e., included in the distribution file).

---

## 4. Summary (Action Items for Coder)
1. Run `npm install -D @vscode/l10n-dev` in the root path.
2. Replace all UI strings in `package.json` with `%...%` format and add `"l10n": "./l10n"`.
3. Create `package.nls.json`, `package.nls.ko.json`.
4. Replace all hardcoded Korean/English notifications (`showInformationMessage` etc.) in `src/**/*.ts` with `vscode.l10n.t()` English default messages.
5. Run `npm run l10n:export` to extract `l10n/bundle.l10n.json`, then write `l10n/bundle.l10n.ko.json`.
6. For Webview UI, modify to inject translated String map into HTML.
