# Code Task Report (D2-4: VS Code 커맨드 vibezoo.rebuildCodeIndex 추가 및 i18n 동기화)

> **Session Folder**: [`docs/260830_0001_session_reinstall-recovery-and-quality/`](docs/260830_0001_session_reinstall-recovery-and-quality/)  
> **Task**: D2-4 (VibeZoo 검색 복구 — VS Code 커맨드 `vibezoo.rebuildCodeIndex` 추가)  
> **Author**: Code mode (Dev Lead)  
> **Date**: 2026-08-30 (Asia/Seoul)  

---

## Task Summary
[`docs/260830_0001_session_reinstall-recovery-and-quality/architecture-plan.md`](docs/260830_0001_session_reinstall-recovery-and-quality/architecture-plan.md:394)의 D2-4 명세에 따라, VS Code 확장 내에서 코드 인덱스 수동 재구축을 트리거할 수 있는 [`vibezoo.rebuildCodeIndex`](extension/src/extension.ts:725) 커맨드를 등록하고, [`extension/package.json`](extension/package.json:137)에 커맨드 메타데이터를 추가하였으며, 20개 언어의 [`package.nls.*.json`](extension/package.nls.json:32) 및 [`bundle.l10n.*.json`](extension/l10n/bundle.l10n.json:60) 파일에 다국어 리소스를 100% 동기화 완료했습니다.

---

## Actions Taken

1. **[`extension/package.json`](extension/package.json:137) 커맨드 등록**:
   - `contributes.commands` 배열에 [`vibezoo.rebuildCodeIndex`](extension/package.json:137) 등록:
     - `command`: `"vibezoo.rebuildCodeIndex"`
     - `title`: `"%vibezoo.rebuildCodeIndex.title%"`
2. **20개 언어 [`package.nls.*.json`](extension/package.nls.json:32) 타이틀 키 추가**:
   - `en` ([`extension/package.nls.json`](extension/package.nls.json:32)): `"VibeZoo: Rebuild Code Index"`
   - `ko` ([`extension/package.nls.ko.json`](extension/package.nls.ko.json:32)): `"VibeZoo: 코드 인덱스 재구축"`
   - `ja` ([`extension/package.nls.ja.json`](extension/package.nls.ja.json:32)): `"VibeZoo: Rebuild Code Index (コードインデックス再構築)"` (기존 명령 팔레트 명명 규칙 일치)
   - 기타 17개 언어 (`ar`, `bg`, `cs`, `de`, `es`, `fr`, `he`, `hu`, `it`, `pl`, `pt-BR`, `ru`, `th`, `tr`, `vi`, `zh-CN`, `zh-TW`): 영문 fallback 적용.
3. **[`extension/src/extension.ts`](extension/src/extension.ts:724) 커맨드 핸들러 구현**:
   - 기존 MCP-의존 커맨드([`extension.ts#L670`](extension/src/extension.ts:670) `vibezoo.explainCode` 등)와 동일한 아키텍처 패턴을 따라 [`vibezoo.rebuildCodeIndex`](extension/src/extension.ts:725) 등록.
   - Zoo Code 채팅 안내 및 MCP 도구 매핑 메시지 출력:
     [`vscode.commands.registerCommand('vibezoo.rebuildCodeIndex')`](extension/src/extension.ts:725) → [`vscode.window.showInformationMessage()`](extension/src/extension.ts:726)
4. **20개 언어 [`bundle.l10n.*.json`](extension/l10n/bundle.l10n.json:60) 런타임 안내 메시지 보완**:
   - `VibeZoo: Please type "rebuild code index" in Zoo Code chat. (rebuild_code_index MCP tool)` 키를 20개 언어에 전수 번역/배치하여 다국어 환경에서 자연스럽게 안내되도록 구현.
5. **[`.gitignore`](.gitignore:48) 검증**:
   - `.zoo-code/` 캐시 디렉터리 ignore 설정 존재 여부 확인 (48행 기등록 확인).

---

## 커맨드 및 번역 등록 위치 명세

| 항목 | 대상 파일 | 위치/행 번호 | 등록 내용 |
|---|---|---|---|
| Command 메타데이터 | [`extension/package.json`](extension/package.json:137) | [#L137-140](extension/package.json#L137-L140) | `vibezoo.rebuildCodeIndex` command 및 `%vibezoo.rebuildCodeIndex.title%` |
| Command 구현 | [`extension/src/extension.ts`](extension/src/extension.ts:724) | [#L724-731](extension/src/extension.ts#L724-L731) | `vscode.commands.registerCommand('vibezoo.rebuildCodeIndex', ...)` |
| NLS EN | [`extension/package.nls.json`](extension/package.nls.json:32) | [#L32](extension/package.nls.json#L32) | `"vibezoo.rebuildCodeIndex.title": "VibeZoo: Rebuild Code Index"` |
| NLS KO | [`extension/package.nls.ko.json`](extension/package.nls.ko.json:32) | [#L32](extension/package.nls.ko.json#L32) | `"vibezoo.rebuildCodeIndex.title": "VibeZoo: 코드 인덱스 재구축"` |
| NLS JA | [`extension/package.nls.ja.json`](extension/package.nls.ja.json:32) | [#L32](extension/package.nls.ja.json#L32) | `"vibezoo.rebuildCodeIndex.title": "VibeZoo: Rebuild Code Index (コードインデックス再構築)"` |
| NLS 17개 언어 | [`extension/package.nls.*.json`](extension/package.nls.de.json:32) | [#L32](extension/package.nls.de.json#L32) | 17개 언어 동일 키 영문 fallback 완비 |
| l10n 20개 언어 | [`extension/l10n/bundle.l10n.*.json`](extension/l10n/bundle.l10n.json:60) | [#L60](extension/l10n/bundle.l10n.json#L60) | `rebuild_code_index` 안내 20개 언어 번역 완비 |

---

## Result
- **상태**: ✅ **COMPLETE (100% 검증 통과)**
- **검증 증거**:
  1. **종합 자동화 검증 스크립트 실행** ([`tools/test_d2_4_verification.py`](tools/test_d2_4_verification.py)):
     ```text
     --- 1. Checking extension/package.json ---
     rebuildCodeIndex in package.json contributes.commands: {'command': 'vibezoo.rebuildCodeIndex', 'title': '%vibezoo.rebuildCodeIndex.title%'}

     --- 2. Checking 20 package.nls files ---
     Total nls files: 20

     --- 3. Checking 20 bundle.l10n files ---
     Total bundle.l10n files: 20

     --- 4. Checking extension/src/extension.ts ---

     --- 5. Checking .gitignore ---

     --- 6. Running TypeScript Compiler Check ---
     TS Output: Using TypeScript version: 5.9.3
     Files to compile count: 26
     ✅ TypeScript type check passed with 0 errors!

     === SUMMARY ===
       package.json: PASS
       package.nls (20 files): PASS
       bundle.l10n (20 files): PASS
       extension.ts: PASS
       .gitignore: PASS
       TypeScript tsc --noEmit: PASS

     ALL D2-4 CHECKS PASSED SUCCESSFULLY!
     ```
  2. **i18n 브릿지 번역 전수 일치 확인** ([`verify_translations.py`](docs/260830_0001_session_reinstall-recovery-and-quality/tools/verify_translations.py)):
     - `Total Missing: 0, Total Empty: 0`
     - `Root vs Extension Sync: ✅ 100% SHA-256 IDENTICAL (20/20)`

---

## Issues Discovered
- 특이사항 없음. 모든 20개 언어 `package.nls` 및 `bundle.l10n` 파일의 구조 정합성이 유지되었으며, TypeScript 타입 체크에서도 오류 0건이 확인되었습니다.

---

## Next Step Recommendations
- D-2 마일스톤의 `vibezoo.rebuildCodeIndex` 커맨드 및 i18n 동기화(D2-4)가 완료되었으므로, 다음 마일스톤인 D-3 (이미지 붙여넣기 및 Drag & Drop 안정화) 단계로 원활히 진행할 것을 권장합니다.

---

## Affected File List
- [`extension/package.json`](extension/package.json)
- [`extension/src/extension.ts`](extension/src/extension.ts)
- [`extension/package.nls.json`](extension/package.nls.json)
- [`extension/package.nls.ko.json`](extension/package.nls.ko.json)
- [`extension/package.nls.ja.json`](extension/package.nls.ja.json)
- [`extension/package.nls.ar.json`](extension/package.nls.ar.json)
- [`extension/package.nls.bg.json`](extension/package.nls.bg.json)
- [`extension/package.nls.cs.json`](extension/package.nls.cs.json)
- [`extension/package.nls.de.json`](extension/package.nls.de.json)
- [`extension/package.nls.es.json`](extension/package.nls.es.json)
- [`extension/package.nls.fr.json`](extension/package.nls.fr.json)
- [`extension/package.nls.he.json`](extension/package.nls.he.json)
- [`extension/package.nls.hu.json`](extension/package.nls.hu.json)
- [`extension/package.nls.it.json`](extension/package.nls.it.json)
- [`extension/package.nls.pl.json`](extension/package.nls.pl.json)
- [`extension/package.nls.pt-BR.json`](extension/package.nls.pt-BR.json)
- [`extension/package.nls.ru.json`](extension/package.nls.ru.json)
- [`extension/package.nls.th.json`](extension/package.nls.th.json)
- [`extension/package.nls.tr.json`](extension/package.nls.tr.json)
- [`extension/package.nls.vi.json`](extension/package.nls.vi.json)
- [`extension/package.nls.zh-CN.json`](extension/package.nls.zh-CN.json)
- [`extension/package.nls.zh-TW.json`](extension/package.nls.zh-TW.json)
- [`extension/l10n/bundle.l10n.json`](extension/l10n/bundle.l10n.json)
- [`extension/l10n/bundle.l10n.ko.json`](extension/l10n/bundle.l10n.ko.json)
- [`extension/l10n/bundle.l10n.ja.json`](extension/l10n/bundle.l10n.ja.json)
- [`extension/l10n/bundle.l10n.ar.json`](extension/l10n/bundle.l10n.ar.json)
- [`extension/l10n/bundle.l10n.bg.json`](extension/l10n/bundle.l10n.bg.json)
- [`extension/l10n/bundle.l10n.cs.json`](extension/l10n/bundle.l10n.cs.json)
- [`extension/l10n/bundle.l10n.de.json`](extension/l10n/bundle.l10n.de.json)
- [`extension/l10n/bundle.l10n.es.json`](extension/l10n/bundle.l10n.es.json)
- [`extension/l10n/bundle.l10n.fr.json`](extension/l10n/bundle.l10n.fr.json)
- [`extension/l10n/bundle.l10n.he.json`](extension/l10n/bundle.l10n.he.json)
- [`extension/l10n/bundle.l10n.hu.json`](extension/l10n/bundle.l10n.hu.json)
- [`extension/l10n/bundle.l10n.it.json`](extension/l10n/bundle.l10n.it.json)
- [`extension/l10n/bundle.l10n.pl.json`](extension/l10n/bundle.l10n.pl.json)
- [`extension/l10n/bundle.l10n.pt-BR.json`](extension/l10n/bundle.l10n.pt-BR.json)
- [`extension/l10n/bundle.l10n.ru.json`](extension/l10n/bundle.l10n.ru.json)
- [`extension/l10n/bundle.l10n.th.json`](extension/l10n/bundle.l10n.th.json)
- [`extension/l10n/bundle.l10n.tr.json`](extension/l10n/bundle.l10n.tr.json)
- [`extension/l10n/bundle.l10n.vi.json`](extension/l10n/bundle.l10n.vi.json)
- [`extension/l10n/bundle.l10n.zh-CN.json`](extension/l10n/bundle.l10n.zh-CN.json)
- [`extension/l10n/bundle.l10n.zh-TW.json`](extension/l10n/bundle.l10n.zh-TW.json)
- [`.gitignore`](.gitignore)
- [`tools/test_d2_4_verification.py`](tools/test_d2_4_verification.py)
- [`tools/check_tsc.js`](tools/check_tsc.js)
- [`tools/update_nls_d2_4.py`](tools/update_nls_d2_4.py)
- [`tools/update_bundle_l10n_d2_4.py`](tools/update_bundle_l10n_d2_4.py)
- [`docs/260830_0001_session_reinstall-recovery-and-quality/103500_code-d2-4-rebuild-command-report.md`](docs/260830_0001_session_reinstall-recovery-and-quality/103500_code-d2-4-rebuild-command-report.md)
