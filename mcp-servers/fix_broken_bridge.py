#!/usr/bin/env python
# Fix broken bridge (missing main block) + add image dropzone
import os, sys

BRIDGE = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/vibezoo_mcp_bridge.py'

DROPZONE = r'''

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
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1e1e1e;color:#ccc;font-family:-apple-system,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
#dropzone{width:600px;height:400px;border:3px dashed #555;border-radius:16px;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:20px;cursor:pointer;transition:all .3s;text-align:center;padding:20px}
#dropzone:hover,#dropzone.dragover{border-color:#4ec9ff;background:rgba(78,201,255,.1)}
#dropzone.dragover{border-color:#6acb6a;background:rgba(106,203,106,.1)}
#dropzone img{max-width:90%;max-height:70%;border-radius:8px;display:none}
#dropzone.has-image img{display:block}
#dropzone.has-image .placeholder{display:none}
.icon{font-size:64px;opacity:.5}
.hint{font-size:14px;color:#888}
.status{font-size:16px;color:#6acb6a;margin-top:12px}
input[type=file]{display:none}
</style></head><body>
<div id=dropzone onclick="document.getElementById('f').click()">
<div class=icon>&#128247;</div>
<div class=placeholder><h2>Drag & Drop Image Here</h2><p style="color:#888;margin-top:8px">or click to browse</p></div>
<img id=prev><div class=status id=sta></div></div>
<input type=file id=f accept=image/* onchange="u(this.files[0])">
<script>
function u(f){if(!f)return;var fd=new FormData();fd.append('image',f);document.getElementById('sta').textContent='Uploading...';var x=new XMLHttpRequest();x.open('POST','/upload',true);x.onload=function(){if(x.status==200){var d=JSON.parse(x.responseText);document.getElementById('sta').innerHTML='&#x2705; Uploaded! Path: <code>'+d.path+'</code>';var r=new FileReader();r.onload=function(e){document.getElementById('prev').src=e.target.result;document.getElementById('dropzone').classList.add('has-image')};r.readAsDataURL(f)}else{document.getElementById('sta').textContent='&#x274c; Upload failed'}};x.onerror=function(){document.getElementById('sta').textContent='&#x274c; Network error'};x.send(fd)}
document.getElementById('dropzone').addEventListener('dragover',function(e){e.preventDefault();this.classList.add('dragover')});
document.getElementById('dropzone').addEventListener('dragleave',function(e){this.classList.remove('dragover')});
document.getElementById('dropzone').addEventListener('drop',function(e){e.preventDefault();this.classList.remove('dragover');var f=e.dataTransfer.files[0];if(f&&f.type.startsWith('image/'))u(f)});
</script></body></html>"""
        return JSONResponse({"html": html})
    
    elif request.method == "POST":
        try:
            form = await request.form()
            file = form.get("image")
            if not file:
                return JSONResponse({"error": "No file"}, status_code=400)
            content_bytes = await file.read()
            with open(UPLOADED_IMAGE_PATH, "wb") as f:
                f.write(content_bytes)
            return JSONResponse({"status":"ok","path":UPLOADED_IMAGE_PATH,"size":len(content_bytes)})
        except Exception as e:
            return JSONResponse({"error":str(e)}, status_code=500)


@mcp.tool
def open_image_dropzone() -> str:
    """브라우저에서 이미지 드래그앤드롭 업로드 페이지를 엽니다.
    업로드된 이미지는 ~/.vibezoo-cache/dropped_image.png에 저장됩니다.
    이후 aggregate_spatial_pixels()로 분석할 수 있습니다.
    """
    try:
        from bridge.tools.whiteboard import _open_dropzone_in_webview
        return _open_dropzone_in_webview()
    except ImportError:
        return "Error: Cannot import _open_dropzone_in_webview."
    except Exception as e:
        from bridge.utils import _markdown_header, _markdown_footer
        return (_markdown_header("Drop Zone Error", "\\u274c")
                + f"**Error**: {e}\\n" + _markdown_footer())
'''

print("Reading bridge...")
with open(BRIDGE, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if main block exists
if 'if __name__ == "__main__":' in content:
    print("Main block exists")
    # Insert before main block
    marker = '# ═══════════════════════════════════════════════════════════\n# 메인 — SSE 서버 시작'
    if marker in content:
        content = content.replace(marker, DROPZONE + '\n\n' + marker)
        print("Dropzone inserted")
    else:
        print("Marker not found, appending")
        content += DROPZONE
else:
    print("Main block MISSING! Restoring...")
    content += DROPZONE + '\n\n'
    content += '\n# ═══════════════════════════════════════════════════════════\n# 메인 — SSE 서버 시작\n# ═══════════════════════════════════════════════════════════\n\n'
    content += 'if __name__ == "__main__":\n'
    content += '    parser = argparse.ArgumentParser(description="VibeZoo MCP Bridge Server")\n'
    content += '    parser.add_argument("--port", type=int, default=9027, help="SSE server port")\n'
    content += '    args = parser.parse_args()\n\n'
    content += '    print(f"\\U0001f680 VibeZoo MCP Bridge v{VERSION} starting on port {args.port}...")\n'
    content += '    print(f"   Crow Memory: {CROW_URL} (timeout: {CROW_TIMEOUT}s)")\n\n'
    content += '    mcp.run(transport="sse", host="127.0.0.1", port=args.port)\n'
    print("Bridge restored + dropzone added")

# Verify syntax
try:
    compile(content, BRIDGE, 'exec')
    print("Syntax: OK")
except SyntaxError as e:
    print(f"Syntax error at line {e.lineno}: {e.msg}")
    sys.exit(1)

# Atomic write
tmp = BRIDGE + '.fx'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, BRIDGE)
print(f"Written: {len(content)} chars, {content.count(chr(10))+1} lines")
print(f"Has open_image_dropzone: {'open_image_dropzone' in content}")
print(f"Has /upload route: {'/upload' in content}")
print("Bridge fixed!")
