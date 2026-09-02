# -*- coding: utf-8 -*-
"""Update translations across all 20 language files in both extension and root mcp-servers.
Adds D2-3 serverdown guidance message and health/rebuild keys.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent

NEW_ENTRIES = {
    "Cannot connect to embedding server (localhost:8089, nomic-embed-text). Recovery: [1] Load nomic-embed-text model in LM Studio/Ollama and run on port 8089. [2] Retry the same request after server starts (auto-reprobes). Manual code index rebuild: VS Code command 'VibeZoo: Rebuild Code Index'.": {
        "ko": "Embedding 서버(localhost:8089, nomic-embed-text)에 연결할 수 없습니다. 복구: [1] LM Studio/Ollama에서 nomic-embed-text 모델 로드 및 8089 포트 구동 [2] 서버 구동 후 동일 요청 재시도(자동 재probe). 코드 인덱스 수동 리빌드: VS Code 커맨드 'VibeZoo: Rebuild Code Index'.",
        "default": "Cannot connect to embedding server (localhost:8089, nomic-embed-text). Recovery: [1] Load nomic-embed-text model in LM Studio/Ollama and run on port 8089. [2] Retry the same request after server starts (auto-reprobes). Manual code index rebuild: VS Code command 'VibeZoo: Rebuild Code Index'."
    },
    "Code Index Rebuild": {
        "ko": "코드 인덱스 리빌드",
        "default": "Code Index Rebuild"
    },
    "Code index rebuilt successfully ({0} files indexed).": {
        "ko": "코드 인덱스가 성공적으로 리빌드되었습니다 ({0}개 파일 인덱싱됨).",
        "default": "Code index rebuilt successfully ({0} files indexed)."
    },
    "Embedding Health Check": {
        "ko": "임베딩 서버 상태 점검",
        "default": "Embedding Health Check"
    }
}

target_dirs = [
    ROOT / "extension" / "mcp-servers" / "bridge" / "i18n" / "translations",
    ROOT / "mcp-servers" / "bridge" / "i18n" / "translations",
]

languages = [
    "en", "ko", "ja", "zh-CN", "zh-TW", "fr", "de", "es", "it", "ru",
    "pt-BR", "ar", "bg", "cs", "he", "hu", "pl", "th", "tr", "vi"
]

for tdir in target_dirs:
    for lang in languages:
        json_path = tdir / f"{lang}.json"
        if not json_path.exists():
            print(f"Warning: {json_path} does not exist!")
            continue
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for key, translations in NEW_ENTRIES.items():
            if lang == "ko":
                data[key] = translations["ko"]
            else:
                data[key] = translations["default"]
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Updated {json_path.relative_to(ROOT)} ({len(data)} keys)")

print("All translations updated successfully.")
