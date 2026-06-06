# Dropzone Problem Resolution Plan

> Based on Debug Results | Date: 2026-06-02

## Debug Diagnosis Summary

| # | Problem | Root Cause | File |
|---|---------|-----------|------|
| 1 | Uploaded file not found | Storage location `~/.vibezoo-uploads/` vs my search `~/.vibezoo-cache/` | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts:34) |
| 2 | LLM doesn't recognize file after upload | Path only copied to **clipboard**, not passed to MCP bridge | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts:462) |
| 3 | MCP tools don't know uploaded file list | No upload registry | New required |

## Solution Design

### Architecture Change

```
User file drag & drop
  → Webview → vscodeApi.postMessage
  → Extension: handleDropzoneUpload()
  → File save (~/.vibezoo-uploads/{date}/)
  → Upload registry record (~/.vibezoo-uploads/latest.json)
  → Zoo: check_uploaded_files() MCP tool call
  → Analysis request
```

### Files to Modify

| Phase | File | Change | Description |
|-------|------|--------|-------------|
| 1 | [`VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts) | Modify 5 lines | Record file path in `~/.vibezoo-uploads/latest.json` in `handleDropzoneUpload()` |
| 2 | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) | Modify 2 lines | Update `_open_dropzone_in_webview()` message with correct upload path guidance |
| 3 | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) | New 20 lines | Add `check_uploaded_files()` MCP tool — returns list of recently uploaded files |

### Phase 1: VisualVibePanels.ts (Extension)

Add at the end of `handleDropzoneUpload()` function (lines 487-537):

```typescript
// Upload registry record (so LLM knows file path)
const registryPath = path.join(os.homedir(), '.vibezoo-uploads', 'latest.json');
const registry = {
  path: destPath,
  fileName: safeName,
  size: buffer.length,
  mimeType: mimeType,
  timestamp: Date.now(),
};
try {
  // Read existing registry → add → save (keep max 10)
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

Modify `_open_dropzone_in_webview()` return message (lines 815-835):

```python
return (_markdown_header("File Drop Zone", "📎")
    + "Drop zone opened. Upload a file and I'll check it.\n\n"
    + "Files saved to: `~/.vibezoo-uploads/{date}/`\n"
    + "After upload, call `check_uploaded_files()` to see the latest uploads.\n"
    + _markdown_footer())
```

### Phase 3: whiteboard.py (MCP Bridge)

Add new MCP tool to `register()` function:

```python
@mcp.tool
def check_uploaded_files() -> str:
    """Check the list of recently uploaded files in the dropzone.
    
    Returns:
        List of uploaded file paths and metadata
    """
    import json as _json
    registry_path = os.path.expanduser("~/.vibezoo-uploads/latest.json")
    
    if not os.path.exists(registry_path):
        return "📂 No files have been uploaded yet."
    
    try:
        with open(registry_path, 'r') as f:
            entries = _json.load(f)
        
        lines = ["## 📎 Recently Uploaded Files", ""]
        for i, entry in enumerate(entries):
            path = entry.get("path", "?")
            name = entry.get("fileName", "?")
            size = entry.get("size", 0)
            mime = entry.get("mimeType", "?")
            ts = entry.get("timestamp", 0)
            
            size_str = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
            lines.append(f"### {i+1}. {name}")
            lines.append(f"- **Path**: `{path}`")
            lines.append(f"- **Size**: {size_str}")
            lines.append(f"- **Type**: {mime}")
            lines.append("")
        
        lines.append(f"**Analysis example**: `analyze_uploaded_file(file_path='{entries[0]['path']}')`")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Failed to read upload registry: {e}"
```

### Impact

| Item | Impact | Risk |
|------|--------|------|
| Extension Change | 10 lines added at end of `handleDropzoneUpload()` | None (simple file I/O) |
| MCP Bridge Change | Description update + 1 new tool | None |
| Existing Functionality | Clipboard copy + notification maintained | None |

---

> **Implementation**: Switch to Code mode and proceed with Phase 1~3 in order.
