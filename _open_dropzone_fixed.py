#!/usr/bin/env python
"""VibeZoo 드랍존 열기 - 올바른 action 값으로 파일 작성"""
import json, time, os, sys

action_file = os.path.join(os.path.expanduser('~'), '.vibezoo-dropzone-action.json')
data = {
    "action": "open",  # Extension이 확인하는 action 값
    "title": "VibeZoo Image Drop Zone",
    "timestamp": time.time(),
}
with open(action_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Written: {action_file}")
print(f"   action: {data['action']}")
print()
print("📸 VibeZoo Drop Zone opened in VS Code Webview!")
print()
print("1. Drag & drop an image into the Webview panel")
print("2. The file will be saved to ~/.vibezoo-uploads/<date>/")
print("3. Then call `aggregate_spatial_pixels()` to analyze")
print()
print("🌐 Browser alternative: http://localhost:9027/upload")
