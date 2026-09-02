"""SSE handshake + initialize + tools/list against local VibeZoo bridge (verification-only)."""
import json
import requests

BASE = "http://127.0.0.1:9027"

def handshake_and_call():
    with requests.get(BASE + "/sse", stream=True, timeout=60) as r:
        got_ep = None

        def gen():
            for line in r.iter_lines(decode_unicode=True):
                yield line

        g = gen()
        for line in g:
            if line and line.startswith("data:"):
                got_ep = line[5:].strip()
                break
        if not got_ep:
            print("HANDSHAKE_FAIL")
            return
        url = BASE + got_ep if got_ep.startswith("/") else got_ep

        init = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "vp-verify", "version": "1.0"},
            },
        }
        requests.post(url, json=init, timeout=15)

        initialized = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        requests.post(url, json=initialized, timeout=15)

        payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        requests.post(url, json=payload, timeout=15)

        for line in g:
            if not line or not line.startswith("data:"):
                continue
            try:
                obj = json.loads(line[5:].strip())
            except Exception:
                continue
            if obj.get("id") == 2 and "result" in obj and "tools" in obj["result"]:
                tools = obj["result"]["tools"]
                print("TOOL_COUNT=" + str(len(tools)))
                print("NAMES=" + ",".join(t["name"] for t in tools))
                return
        print("NO_RESPONSE")

handshake_and_call()