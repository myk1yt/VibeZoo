#!/usr/bin/env python
import sys
BASE = r'c:\Users\k1yt\OneDrive\문서\각종자료\공부자료들\파이썬_Python\VibeZoo_forZoocode'

# ── Fix 1: VisualVibePanels.ts ──
ts_path = BASE + r'\extension\src\visual\VisualVibePanels.ts'
with open(ts_path, 'r', encoding='utf-8') as f:
    ts = f.read()

old1 = "const UI_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-ui-action.json');\n\nconst FABRIC_CDN"
new1 = "const UI_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-ui-action.json');\n\nconst DROPZONE_CACHE_DIR = () => path.join(os.homedir(), '.vibezoo-cache');\nconst UPLOADED_IMAGE_PATH = () => path.join(DROPZONE_CACHE_DIR(), 'dropped_image.png');\n\nconst FABRIC_CDN"
ts = ts.replace(old1, new1)

old2 = "  private diagramPanel: vscode.WebviewPanel | null = null;\n  private readonly homedir: string;"
new2 = "  private diagramPanel: vscode.WebviewPanel | null = null;\n  private dropzonePanel: vscode.WebviewPanel | null = null;\n  private readonly homedir: string;"
ts = ts.replace(old2, new2)

# Add methods after openWhiteboard()
old3 = "    return this.whiteboardPanel;\n  }\n\n  /** 사용자 캔버스 상태 저장"
new3 = "    return this.whiteboardPanel;\n  }\n\n  /** 드롭존 Webview 열기 */\n  openDropzone(htmlB64: string, title: string): void {\n    this.startWatching();\n    if (this.dropzonePanel) {\n      this.dropzonePanel.reveal(vscode.ViewColumn.Two);\n      return;\n    }\n    this.dropzonePanel = vscode.window.createWebviewPanel(\n      'vibezoo-dropzone',\n      '📸 ' + title,\n      vscode.ViewColumn.Two,\n      { enableScripts: true, retainContextWhenHidden: true },\n    );\n    const html = Buffer.from(htmlB64, 'base64').toString('utf-8');\n    this.dropzonePanel.webview.html = html;\n    this.dropzonePanel.webview.onDidReceiveMessage((message) => {\n      if (message.type === 'uploadImage') {\n        this.handleImageUpload(message);\n      }\n    });\n    this.dropzonePanel.onDidDispose(() => { this.dropzonePanel = null; });\n  }\n\n  private async handleImageUpload(message: {\n    dataUrl: string;\n    fileName?: string;\n    mimeType?: string;\n  }): Promise<void> {\n    try {\n      const matches = message.dataUrl.match(/^data:([^;]+);base64,(.+)$/);\n      if (!matches) {\n        this.dropzonePanel?.webview.postMessage({ type: 'uploadResult', success: false, error: 'Invalid data URL' });\n        return;\n      }\n      const base64Data = matches[2];\n      const ext = message.mimeType?.split('/')[1] || 'png';\n      const cacheDir = DROPZONE_CACHE_DIR();\n      fs.mkdirSync(cacheDir, { recursive: true });\n      const filePath = path.join(cacheDir, 'dropped_image.' + ext);\n      fs.writeFileSync(filePath, Buffer.from(base64Data, 'base64'));\n      if (ext !== 'png') {\n        try { fs.copyFileSync(filePath, UPLOADED_IMAGE_PATH()); } catch {}\n      }\n      log('Image saved to ' + filePath);\n      this.dropzonePanel?.webview.postMessage({ type: 'uploadResult', success: true, dataUrl: message.dataUrl, path: filePath });\n    } catch (err) {\n      log('Image upload error:', err.message);\n      this.dropzonePanel?.webview.postMessage({ type: 'uploadResult', success: false, error: err.message });\n    }\n  }\n\n  private async openFilePicker(): Promise<void> {\n    const result = await vscode.window.showOpenDialog({\n      canSelectFiles: true,\n      canSelectFolders: false,\n      canSelectMany: false,\n      filters: { 'Images': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'] },\n    });\n    if (result && result.length > 0) {\n      const srcPath = result[0].fsPath;\n      const cacheDir = DROPZONE_CACHE_DIR();\n      fs.mkdirSync(cacheDir, { recursive: true });\n      const destPath = UPLOADED_IMAGE_PATH();\n      try {\n        fs.copyFileSync(srcPath, destPath);\n        vscode.window.showInformationMessage('Image saved to ' + destPath);\n      } catch (err) {\n        vscode.window.showErrorMessage('Failed to copy image: ' + err.message);\n      }\n    }\n  }\n\n  /** 사용자 캔버스 상태 저장"
ts = ts.replace(old3, new3)

# Update action watcher
old4 = "    fs.watchFile(wbAction, { interval: WATCH_INTERVAL_MS }, (curr) => {\n      if (curr.mtimeMs <= lastActionMtime.current) return;\n      lastActionMtime.current = curr.mtimeMs;\n      this.handleFileChange(wbAction, lastActionMtime, (content) => {\n        if (content.action === 'open') {\n          this.openWhiteboard();\n          if (content.message) {\n            log(`Whiteboard action: ${content.message}`);\n          }\n        }\n      });\n    });"
new4 = "    fs.watchFile(wbAction, { interval: WATCH_INTERVAL_MS }, (curr) => {\n      if (curr.mtimeMs <= lastActionMtime.current) return;\n      lastActionMtime.current = curr.mtimeMs;\n      this.handleFileChange(wbAction, lastActionMtime, (content) => {\n        if (content.action === 'open') {\n          this.openWhiteboard();\n          if (content.message) {\n            log(`Whiteboard action: ${content.message}`);\n          }\n        } else if (content.action === 'open_dropzone') {\n          this.openDropzone(content.html_b64, content.title || 'VibeZoo Image Drop Zone');\n        } else if (content.action === 'open_file_picker') {\n          this.openFilePicker();\n        }\n      });\n    });"
ts = ts.replace(old4, new4)

with open(ts_path, 'w', encoding='utf-8') as f:
    f.write(ts)

# Verify TS
with open(ts_path, 'r', encoding='utf-8') as f:
    v = f.read()
ok1 = 'DROPZONE_CACHE_DIR' in v
ok2 = 'private dropzonePanel' in v
ok3 = 'openDropzone(htmlB64' in v
ok4 = 'handleImageUpload' in v
ok5 = 'openFilePicker' in v
ok6 = 'open_dropzone' in v
ok7 = 'open_file_picker' in v
print('TS: constants=' + str(ok1) + ' prop=' + str(ok2) + ' openDropzone=' + str(ok3) + ' handleUpload=' + str(ok4) + ' filePicker=' + str(ok5) + ' dropzone_action=' + str(ok6) + ' picker_action=' + str(ok7))

# ── Fix 2: whiteboard.py ──
wb_path = BASE + r'\mcp-servers\bridge\tools\whiteboard.py'
with open(wb_path, 'r', encoding='utf-8') as f:
    wb = f.read()

old_js = "<script>\nconst dz=document.getElementById('dropzone');\nconst preview=document.getElementById('preview');\nconst status=document.getElementById('status');\ndz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('dragover')});\ndz.addEventListener('dragleave',()=>dz.classList.remove('dragover'));\ndz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('dragover');handleFile(e.dataTransfer.files[0])});\nasync function handleFile(file){if(!file)return;if(!file.type.startsWith('image/')){showStatus('Not an image file','error');return}\nconst form=new FormData();form.append('image',file);\ntry{const r=await fetch('/upload',{method:'POST',body:form});const t=await r.text();showStatus('Uploaded! Use aggregate_spatial_pixels() to analyze.','success');preview.src=URL.createObjectURL(file);preview.style.display='block';dz.classList.add('has-image')}\ncatch(e){showStatus('Upload failed. Save manually to ~/.vibezoo-cache/dropped_image.png','error')}}\nfunction showStatus(msg,type){status.textContent=msg;status.className=type}\n</script>"

new_js = "<script>\n(function() {\n  var vscode = null;\n  try { vscode = acquireVsCodeApi(); } catch(e) {}\n  var dz=document.getElementById('dropzone');\n  var preview=document.getElementById('preview');\n  var statusEl=document.getElementById('status');\n  dz.addEventListener('dragover',function(e){e.preventDefault();dz.classList.add('dragover')});\n  dz.addEventListener('dragleave',function(){dz.classList.remove('dragover')});\n  dz.addEventListener('drop',function(e){\n    e.preventDefault();dz.classList.remove('dragover');handleFile(e.dataTransfer.files[0]);\n  });\n  function handleFile(file){\n    if(!file)return;\n    if(!file.type.startsWith('image/')){showStatus('Not an image file','error');return}\n    showStatus('Uploading...','');\n    var reader=new FileReader();\n    reader.onload=function(ev){\n      var dataUrl=ev.target.result;\n      if(vscode){\n        vscode.postMessage({type:'uploadImage',dataUrl:dataUrl,fileName:file.name,mimeType:file.type});\n        showStatus('Uploading... (sending to extension)','');\n      } else { showStatus('VS Code API unavailable. Save manually.','error'); }\n    };\n    reader.onerror=function(){showStatus('Failed to read file','error')};\n    reader.readAsDataURL(file);\n  }\n  window.addEventListener('message',function(e){\n    if(e.data&&e.data.type==='uploadResult'){\n      if(e.data.success){\n        showStatus('Uploaded! Use aggregate_spatial_pixels() to analyze.','success');\n        if(preview&&e.data.dataUrl){preview.src=e.data.dataUrl;preview.style.display='block';dz.classList.add('has-image');}\n      } else { showStatus('Upload failed: '+(e.data.error||'unknown error'),'error'); }\n    }\n  });\n  function showStatus(msg,type){statusEl.textContent=msg;statusEl.className=type||'';}\n})();\n</script>"

if old_js in wb:
    wb = wb.replace(old_js, new_js)
    with open(wb_path, 'w', encoding='utf-8') as f:
        f.write(wb)
    with open(wb_path, 'r', encoding='utf-8') as f:
        wv = f.read()
    print('WB: acquireVsCodeApi=' + str('acquireVsCodeApi' in wv) + ' old_fetch=' + str('fetch(' in wv and '/upload' in wv))
else:
    print('WB: old_js NOT FOUND')
    idx = wb.find('<script>')
    if idx >= 0:
        print('  Found <script> at', idx)
        print('  Context:', repr(wb[idx:idx+120]))
