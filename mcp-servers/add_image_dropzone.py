#!/usr/bin/env python
# Add image drag-and-drop upload + SSA analysis tool to bridge
import os, sys, re

BRIDGE = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/vibezoo_mcp_bridge.py'

print("📖 Reading bridge...")
with open(BRIDGE, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"   Current: {len(content)} chars")

# New tool + route code
dropzone_code = r'''

# ── 이미지 업로드 캐시 ──────────────────────────────
IMAGE_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".vibezoo-cache")
os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
UPLOADED_IMAGE_PATH = os.path.join(IMAGE_CACHE_DIR, "dropped_image.png")


@mcp.custom_route("/upload", methods=["GET", "POST"])
async def image_upload_handler(request: Request) -> JSONResponse:
    """이미지 드래그앤드롭 업로드 엔드포인트"""
    if request.method == "GET":
        html = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>VibeZoo Image Upload</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #1e1e1e; color: #ccc; font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
#dropzone { width: 600px; height: 400px; border: 3px dashed #555; border-radius: 16px; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 20px; cursor: pointer; transition: all 0.3s; text-align: center; padding: 20px; }
#dropzone:hover, #dropzone.dragover { border-color: #4ec9ff; background: rgba(78,201,255,0.1); }
#dropzone.dragover { border-color: #6acb6a; background: rgba(106,203,106,0.1); }
#dropzone img { max-width: 90%; max-height: 70%; border-radius: 8px; display: none; }
#dropzone.has-image img { display: block; }
#dropzone.has-image .placeholder { display: none; }
.icon { font-size: 64px; opacity: 0.5; }
.hint { font-size: 14px; color: #888; }
.status { font-size: 16px; color: #6acb6a; margin-top: 12px; }
input[type=file] { display: none; }
</style>
</head><body>
<div id="dropzone" onclick="document.getElementById('fileInput').click()">
<div class="icon">&#128247;</div>
<div class="placeholder">
<h2>Drag & Drop Image Here</h2>
<p style="color:#888;margin-top:8px;">or click to browse</p>
</div>
<img id="preview">
<div class="status" id="status"></div>
</div>
<input type="file" id="fileInput" accept="image/*" onchange="uploadFile(this.files[0])">
<script>
function uploadFile(file) {
    if (!file) return;
    var formData = new FormData();
    formData.append('image', file);
    document.getElementById('status').textContent = 'Uploading...';
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            var data = JSON.parse(xhr.responseText);
            document.getElementById('status').innerHTML = '✅ Uploaded! Path: <code>' + data.path + '</code>';
            var reader = new FileReader();
            reader.onload = function(e) {
                var img = document.getElementById('preview');
                img.src = e.target.result;
                img.style.display = 'block';
                document.getElementById('dropzone').classList.add('has-image');
            };
            reader.readAsDataURL(file);
        } else {
            document.getElementById('status').textContent = '❌ Upload failed';
        }
    };
    xhr.onerror = function() { document.getElementById('status').textContent = '❌ Network error'; };
    xhr.send(formData);
}
document.getElementById('dropzone').addEventListener('dragover', function(e) {
    e.preventDefault();
    this.classList.add('dragover');
});
document.getElementById('dropzone').addEventListener('dragleave', function(e) {
    this.classList.remove('dragover');
});
document.getElementById('dropzone').addEventListener('drop', function(e) {
    e.preventDefault();
    this.classList.remove('dragover');
    var file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) uploadFile(file);
});
</script>
</body></html>"""
        return JSONResponse({"html": html}, status_code=200)
    
    elif request.method == "POST":
        try:
            from starlette.datastructures import UploadFile
            form = await request.form()
            file: UploadFile = form.get("image")
            if not file:
                return JSONResponse({"error": "No file uploaded"}, status_code=400)
            
            content_bytes = await file.read()
            with open(UPLOADED_IMAGE_PATH, "wb") as f:
                f.write(content_bytes)
            
            return JSONResponse({
                "status": "ok",
                "path": UPLOADED_IMAGE_PATH,
                "size": len(content_bytes),
            }, status_code=200)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)


@mcp.tool
def open_image_dropzone() -> str:
    """브라우저에서 이미지 드래그앤드롭 업로드 페이지를 엽니다.
    업로드된 이미지는 ~/.vibezoo-cache/dropped_image.png에 저장됩니다.
    이후 aggregate_spatial_pixels()로 분석할 수 있습니다.
    
    Returns:
        업로드 페이지 URL 및 사용법 안내
    """
    try:
        import webbrowser
        port = vscode_workspace_get_configuration_get('vibezoo').get('bridge.port', 9027) \
               if 'vscode_workspace_get_configuration_get' in dir() else 9027
        
        # 실제 브릿지 포트 찾기
        import subprocess as _sp
        try:
            from starlette.routing import Route
            # read the actual port from a simple heuristic
            port = 9027  # default
        except:
            pass
        
        url = f"http://localhost:{port}/upload"
        
        try:
            webbrowser.open(url)
            browser_msg = "✅ Browser opened automatically."
        except:
            browser_msg = "🔗 Open this URL in your browser:"
        
        return (_markdown_header("Image Drop Zone", "📸")
                + f"{browser_msg}\n\n"
                + f"**URL**: `{url}`\n\n"
                + f"### Usage\n"
                + f"1. Open the URL in your browser\n"
                + f"2. Drag & drop an image file onto the drop zone\n"
                + f"3. Wait for '✅ Uploaded' confirmation\n"
                + f"4. Then call `aggregate_spatial_pixels(image_path=\"~/.vibezoo-cache/dropped_image.png\")`\n\n"
                + f"### Cached file location\n"
                + f"`{UPLOADED_IMAGE_PATH}`\n"
                + _markdown_footer())
    except Exception as e:
        return (_markdown_header("Drop Zone Error", "❌")
                + f"**Failed to open drop zone**: {e}\n"
                + _markdown_footer())
'''

# Find insertion point: before the main block
marker = "# ═══════════════════════════════════════════════════════════\n# 메인 — SSE 서버 시작"
if marker in content:
    content = content.replace(marker, dropzone_code + '\n\n' + marker)
    print("✅ Image drop zone code inserted")
else:
    print("❌ Main marker not found!")
    sys.exit(1)

# Verify syntax
try:
    compile(content, BRIDGE, 'exec')
    print("✅ Syntax: OK")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
    sys.exit(1)

# Atomic write
print(f"\n📝 Writing {len(content)} chars...")
tmp = BRIDGE + '.dz_tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, BRIDGE)
print("✅ Write complete!")

# Verify
with open(BRIDGE, 'r', encoding='utf-8') as f:
    final = f.read()
print(f"📊 Final: {len(final)} chars, {final.count(chr(10))+1} lines")
print(f"   Has open_image_dropzone: {'open_image_dropzone' in final}")
print(f"   Has /upload route: {'/upload' in final}")
print(f"   Has drag-drop HTML: {'dragover' in final}")
print("\n✅ Image drop zone added! Bridge restart required.")
print("   Visit http://localhost:9027/upload to use it.")
