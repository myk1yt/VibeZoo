import sys
import os
import time
import base64
import urllib.request
import urllib.error
import json

print("\033[96m[VibeZoo Vision Analyzer] Initializing...\033[0m")
time.sleep(0.5)

image_path = sys.argv[1] if len(sys.argv) > 1 else None

if not image_path or not os.path.exists(image_path):
    print(f"\033[91m[Error] Image file not found: {image_path}\033[0m")
    time.sleep(10)
    sys.exit(1)

print(f"\033[94m[System] Processing image at: {image_path}\033[0m")

try:
    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
except Exception as e:
    print(f"\033[91m[Error] Failed to read image: {e}\033[0m")
    time.sleep(10)
    sys.exit(1)

# Ollama API settings
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "minicpm-v"
PROMPT = "You are a professional Vision AI assistant for software developers. Analyze this screenshot in detail. Identify any code errors, UI components, or relevant information. Be concise and precise."

payload = {
    "model": MODEL_NAME,
    "prompt": PROMPT,
    "images": [img_base64],
    "stream": True,
    "options": {
        "temperature": 0.1
    }
}

req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})

print("\033[93m[MiniCPM-V Output]\033[0m")
print("-" * 50)

try:
    with urllib.request.urlopen(req) as response:
        for line in response:
            if line:
                data = json.loads(line.decode('utf-8'))
                if "response" in data:
                    print(data["response"], end="", flush=True)
                if data.get("done"):
                    break
    print("\n" + "-" * 50)
    print("\n\033[96m[VibeZoo Analyzer] Analysis complete. Data is ready for LLM Context.\033[0m")
except urllib.error.URLError as e:
    print(f"\n\033[91m[Error] Could not connect to Ollama server ({e.reason}).\033[0m")
    print("\033[93mPlease ensure Ollama is running and you have pulled the model:\n> ollama run minicpm-v\033[0m")
except Exception as e:
    print(f"\n\033[91m[Error] Vision analysis failed: {e}\033[0m")

print("\n\033[90m(This terminal will auto-close in 30 seconds...)\033[0m")
time.sleep(30)
