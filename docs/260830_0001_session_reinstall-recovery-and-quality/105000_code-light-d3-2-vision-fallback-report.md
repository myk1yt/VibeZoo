# Code Light Task Report — D3-2 Vision Fallback

## Task Summary
MiniCPM vision 모델 미설치/로드 불가 시 사용자에게 Dropzone 폴백 안내 메시지를 반환하도록 [`minicpm.py`](mcp-servers/bridge/vision/minicpm.py) 수정 + i18n 키 20개 언어 추가 + 루트/extension 미러 동기화.

## Actions Taken

### 1. minicpm.py 수정
- [`mcp-servers/bridge/vision/minicpm.py`](mcp-servers/bridge/vision/minicpm.py) 에 `from bridge.i18n import t` import 추가
- `describe_image()` model None 경로 (L82): 기존 하드코딩 `"⚠️ Vision model not loaded. Check model files."` → `t("⚠️ MiniCPM vision model is not installed or failed to load. Image: {0}. Alternatives: ...", image_path)` 로 변경
- `describe_image()` except 경로 (L112): 기존 `f"⚠️ Analysis failed: {e}"` → 동일 i18n 키 + image_path 포함으로 변경
- 양쪽 경로 모두 `{0}`에 image_path 삽입하여 사용자가 이미지 위치를 파악 가능

### 2. i18n translations 추가 (20개 언어)
- 신규 키: `"⚠️ MiniCPM vision model is not installed or failed to load. Image: {0}. Alternatives: (1) Paste image into Dropzone (Ctrl+V) — file path copied as Markdown to clipboard for AI chat. (2) See README Vision section for model setup."`
- ko.json: 한국어 번역 ("드롭존", "클립보드", "마크다운" 포함)
- 나머지 18개 언어 (ar, bg, cs, de, es, fr, he, hu, it, ja, pl, pt-BR, ru, th, tr, vi, zh-CN, zh-TW): en 문구 임시 복사
- en.json 포함 전체 20개 파일: 각 173개 키 (기존 172 + 신규 1)

### 3. 미러 동기화
- `mcp-servers/bridge/vision/minicpm.py` → `extension/mcp-servers/bridge/vision/minicpm.py` 복사 (SHA-256 일치)
- `mcp-servers/bridge/i18n/translations/*.json` (20개) → `extension/mcp-servers/bridge/i18n/translations/*.json` 복사 (SHA-256 20/20 일치)

## Result
**Success** — 모든 검증 통과

### 검증 결과 요약

| 검증 항목 | 결과 | 증거 |
|---|---|---|
| AST parse | ✅ PASS | `py_compile` 통과 |
| verify_translations.py | ✅ PASS | Missing: 0, Empty: 0, Sync: 20/20 SHA-256 |
| English fallback 테스트 | ✅ PASS | image_path(`test_sample.png`) + `Dropzone` 포함 |
| Korean locale 테스트 | ✅ PASS | image_path(`sample_image.jpg`) + `드롭존` 포함 |
| Exception path 테스트 | ✅ PASS | image_path(`/nonexistent/path.png`) 포함 |

## Issues Discovered
- Windows cp949 console 인코딩으로 인해 inline Python에서 유니코드 이스케이프 한글 번역이 깨지는 문제 발견 → UTF-8 텍스트 파일 경유 우회

## Next Step Recommendations
- D3-3 (VisualVibePanels autoAnalyze) 진행 가능
- 미번역 키 5개 (ko 제외 19개 언어)는 기존 Keys in code missing in en.json 204개와 동일 범위로, D-1에서 "유지(무해)" 판단한 기존 미번역과 동일

## Affected File List
| 파일 | 변경 유형 |
|---|---|
| `mcp-servers/bridge/vision/minicpm.py` | 수정 (i18n import + fallback 메시지) |
| `extension/mcp-servers/bridge/vision/minicpm.py` | 미러 복사 |
| `mcp-servers/bridge/i18n/translations/en.json` | 키 1개 추가 |
| `mcp-servers/bridge/i18n/translations/ko.json` | 키 1개 추가 (한국어 번역) |
| `mcp-servers/bridge/i18n/translations/{ar,bg,cs,de,es,fr,he,hu,it,ja,pl,pt-BR,ru,th,tr,vi,zh-CN,zh-TW}.json` | 키 1개 추가 (en 임시) |
| `extension/mcp-servers/bridge/i18n/translations/*.json` (20개) | 미러 복사 |
