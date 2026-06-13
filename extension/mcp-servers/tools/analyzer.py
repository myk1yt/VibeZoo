import sys
import os
import time
import base64
import urllib.request
import urllib.error
import json
import mimetypes

print("\033[96m[VibeZoo Vision Analyzer] Initializing (llama.cpp backend)...\033[0m")
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
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"
        data_url = f"data:{mime_type};base64,{img_base64}"
except Exception as e:
    print(f"\033[91m[Error] Failed to read image: {e}\033[0m")
    time.sleep(10)
    sys.exit(1)

# llama.cpp server (OpenAI compatible API)
LLAMA_CPP_URL = "http://localhost:8080/v1/chat/completions"
PROMPT = "You are a professional Vision AI assistant for software developers. Analyze this screenshot in detail. Identify any code errors, UI components, or relevant information. Be concise and precise."

payload = {
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": data_url
                    }
                },
                {
                    "type": "text",
                    "text": PROMPT
                }
            ]
        }
    ],
    "stream": True,
    "temperature": 0.1,
    "max_tokens": 1024
}

req = urllib.request.Request(
    LLAMA_CPP_URL, 
    data=json.dumps(payload).encode('utf-8'), 
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer no-key'
    }
)

print("\033[93m[MiniCPM-V Output (llama.cpp)]\033[0m")
print("-" * 50)

try:
    with urllib.request.urlopen(req) as response:
        for line in response:
            line_str = line.decode('utf-8').strip()
            if not line_str or not line_str.startswith("data: "):
                continue
            
            json_str = line_str[6:]
            if json_str == "[DONE]":
                break
                
            try:
                data = json.loads(json_str)
                if "choices" in data and len(data["choices"]) > 0:
                    delta = data["choices"][0].get("delta", {})
                    if "content" in delta:
                        print(delta["content"], end="", flush=True)
            except json.JSONDecodeError:
                pass

    print("\n" + "-" * 50)
    print("\n\033[96m[VibeZoo Analyzer] Analysis complete. Data is ready for LLM Context.\033[0m")
except urllib.error.URLError as e:
    print(f"\n\033[91m[Error] Could not connect to llama.cpp server ({e.reason}).\033[0m")
    print("\033[93mPlease ensure your llama.cpp server is running on port 8080.\nExample:\n> server.exe -m minicpm-v.gguf --port 8080 --host 127.0.0.1\033[0m")
except urllib.error.HTTPError as e:
    print(f"\n\033[91m[Error] HTTP Error {e.code}: {e.reason}\033[0m")
except Exception as e:
    print(f"\n\033[91m[Error] Vision analysis failed: {e}\033[0m")

print("\n\033[90m(This terminal will auto-close in 30 seconds...)\033[0m")
time.sleep(30)
