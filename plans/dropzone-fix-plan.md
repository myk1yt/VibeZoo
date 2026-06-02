# 드랍존 문제 해결 계획

> 디버그 결과 기반 | 날짜: 2026-06-02

## 디버그 진단 요약

| # | 문제 | 근본 원인 | 파일 |
|---|------|-----------|------|
| 1 | 업로드된 파일을 찾을 수 없음 | 저장 위치 `~/.vibezoo-uploads/` vs 내 검색 `~/.vibezoo-cache/` | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts:34) |
| 2 | 파일 업로드 후 LLM이 인식 못 함 | 경로를 **클립보드에만** 복사, MCP 브릿지에 전달하지 않음 | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts:462) |
| 3 | MCP 도구가 업로드 파일 목록을 모름 | 업로드 레지스트리 없음 | 신규 필요 |

## 해결 설계

### 아키텍처 변경

```
사용자 파일 드래그&드롭
  → Webview → vscodeApi.postMessage
  → Extension: handleDropzoneUpload()
  → 파일 저장 (~/.vibezoo-uploads/{date}/)
  → 업로드 레지스트리 기록 (~/.vibezoo-uploads/latest.json)
  → Zoo: check_uploaded_files() MCP 도구 호출
  → 분석 요청
```

### 수정 파일

| Phase | 파일 | 변경 | 설명 |
|-------|------|------|------|
| 1 | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | 수정 5줄 | `handleDropzoneUpload()`에서 파일 경로를 `~/.vibezoo-uploads/latest.json`에 기록 |
| 2 | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) | 수정 2줄 | `_open_dropzone_in_webview()` 메시지에 올바른 업로드 경로 안내 |
| 3 | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) | 신규 20줄 | `check_uploaded_files()` MCP 도구 추가 — 최근 업로드된 파일 목록 반환 |

### Phase 1: VisualVibePanels.ts (Extension)

`handleDropzoneUpload()` 함수 (487-537행) 끝부분에 추가:

```typescript
// 업로드 레지스트리 기록 (LLM이 파일 경로를 알 수 있도록)
const registryPath = path.join(os.homedir(), '.vibezoo-uploads', 'latest.json');
const registry = {
  path: destPath,
  fileName: safeName,
  size: buffer.length,
  mimeType: mimeType,
  timestamp: Date.now(),
};
try {
  // 기존 레지스트리 읽기 → 추가 → 저장 (최대 10개 유지)
  let entries = [];
  if (fs.existsSync(registryPath)) {
    entries = JSON.parse(fs.readFileSync(registryPath, 'utf-8'));
  }
  entries.unshift(registry);
  if (entries.length > 10) entries = entries.slice(0, 10);
  fs.writeFileSync(registryPath, JSON.stringify(entries, null, 2));
} catch {}
```

### Phase 2: whiteboard.py (MCP Bridge)

`_open_dropzone_in_webview()` 반환 메시지 수정 (815-835행):

```python
return (_markdown_header("File Drop Zone", "📎")
    + "Drop zone opened. Upload a file and I'll check it.\n\n"
    + "Files saved to: `~/.vibezoo-uploads/{date}/`\n"
    + "After upload, call `check_uploaded_files()` to see the latest uploads.\n"
    + _markdown_footer())
```

### Phase 3: whiteboard.py (MCP Bridge)

`register()` 함수에 신규 MCP 도구 추가:

```python
@mcp.tool
def check_uploaded_files() -> str:
    """드랍존에 업로드된 최근 파일 목록을 확인합니다.
    
    Returns:
        업로드된 파일 경로와 메타데이터 목록
    """
    import json as _json
    registry_path = os.path.expanduser("~/.vibezoo-uploads/latest.json")
    
    if not os.path.exists(registry_path):
        return "📂 아직 업로드된 파일이 없습니다."
    
    try:
        with open(registry_path, 'r') as f:
            entries = _json.load(f)
        
        lines = ["## 📎 최근 업로드된 파일", ""]
        for i, entry in enumerate(entries):
            path = entry.get("path", "?")
            name = entry.get("fileName", "?")
            size = entry.get("size", 0)
            mime = entry.get("mimeType", "?")
            ts = entry.get("timestamp", 0)
            
            size_str = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
            lines.append(f"### {i+1}. {name}")
            lines.append(f"- **경로**: `{path}`")
            lines.append(f"- **크기**: {size_str}")
            lines.append(f"- **타입**: {mime}")
            lines.append("")
        
        lines.append(f"**분석 예시**: `analyze_uploaded_file(file_path='{entries[0]['path']}')`")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ 업로드 레지스트리 읽기 실패: {e}"
```

### 영향도

| 항목 | 영향 | 위험 |
|------|------|------|
| Extension 변경 | `handleDropzoneUpload()` 마지막에 10줄 추가 | 없음 (파일 I/O 단순) |
| MCP Bridge 변경 | 설명문 업데이트 + 신규 도구 1개 | 없음 |
| 기존 기능 | 클립보드 복사 + 알림 유지 | 없음 |

---

> **구현 시 Code 모드로 전환하여 Phase 1~3 순서대로 진행하세요.**
