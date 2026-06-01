#!/usr/bin/env python
"""VibeZoo 드랍존 열기 - VS Code Webview 내장 드롭존"""
import base64, json, os, time

# _DROPZONE_HTML from whiteboard.py
_DROPZONE_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' data: vscode-resource: https:; script-src 'unsafe-inline' 'unsafe-eval'; style-src 'unsafe-inline';">
<title>VibeZoo Image Drop Zone</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#1e1e1e;color:#ccc;font-family:-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh}
  #dropzone{width:90%;max-width:500px;height:300px;border:3px dashed #4ec9ff;border-radius:16px;display:flex;flex-direction:column;align-items:center;justify-content:center;transition:.3s;cursor:pointer;text-align:center;padding:20px}
  #dropzone.dragover{border-color:#6acb6a;background:rgba(106,203,106,.1)}
  #dropzone.has-image{border-style:solid;border-color:#6acb6a}
  #dropzone .icon{font-size:64px;margin-bottom:16px;opacity:.6}
  #dropzone p{font-size:14px;line-height:1.6}
  #dropzone .hint{font-size:12px;color:#888;margin-top:8px}
  #preview{max-width:100%;max-height:200px;display:none;margin-bottom:12px;border-radius:8px}
  #status{font-size:13px;margin-top:12px;padding:8px 16px;border-radius:8px;display:none}
  #status.success{background:#1a3a1a;color:#6acb6a;display:block}
  #status.error{background:#3a1a1a;color:#ff6b6b;display:block}
  input[type=file]{display:none}
</style></head>
<body>
<div id="dropzone" onclick="document.getElementById('fileInput').click()">
  <div class="icon">📸</div>
  <p>Drag & drop an image here<br>or <strong>click to browse</strong></p>
  <p class="hint">Supports all file types: images, PDF, DOCX, TXT, code, etc.</p>
  <img id="preview" alt="Preview"/>
  <div id="status"></div>
</div>
<input type="file" id="fileInput" onchange="handleFile(this.files[0])"/>
<script>
(function(){
const dz=document.getElementById('dropzone');
const preview=document.getElementById('preview');
const status=document.getElementById('status');
let vscodeApi=null;try{vscodeApi=acquireVsCodeApi()}catch(e){}
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('dragover')});
dz.addEventListener('dragleave',()=>dz.classList.remove('dragover'));
dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('dragover');handleFile(e.dataTransfer.files[0])});
async function handleFile(file){if(!file||!vscodeApi)return;
showStatus('Uploading...','');
const reader=new FileReader();
reader.onload=function(e){vscodeApi.postMessage({type:'uploadImage',dataUrl:e.target.result,filename:file.name,fileSize:file.size})};
reader.readAsDataURL(file)}
window.handleFile=handleFile;
window.addEventListener('message',function(e){
  if(e.data.type==='uploadResult'){
    if(e.data.success){showStatus('Uploaded! Path: '+e.data.path,'success');preview.src=e.data.previewUrl||'';preview.style.display='block';dz.classList.add('has-image')}
    else{showStatus('Upload failed: '+(e.data.error||'unknown'),'error')}
  }
});
})();
function showStatus(msg,type){status.textContent=msg;status.className=type}
</script></body></html>"""

html_b64 = base64.b64encode(_DROPZONE_HTML.encode('utf-8')).decode('utf-8')
action_file = os.path.join(os.path.expanduser('~'), '.vibezoo-dropzone-action.json')

data = {
    "action": "open_dropzone",
    "html_b64": html_b64,
    "title": "VibeZoo Image Drop Zone",
    "timestamp": time.time(),
}

with open(action_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Dropzone action file written: {action_file}")
print(f"   HTML payload: {len(html_b64)} bytes base64")
print()
print("📸 VibeZoo Image Drop Zone opened in VS Code Webview.")
print()
print("1. Drag & drop an image into the Webview")
print("2. File will be saved to ~/.vibezoo-cache/dropped_image.png")
print("3. Then call `aggregate_spatial_pixels(image_path='...')` to analyze")
print()
print("💡 Tip: Use `capture_screen()` (without arguments) to capture your screen directly.")
print()
print("🌐 Or visit http://localhost:9027/upload for the browser-based dropzone.")
