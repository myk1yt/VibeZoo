# -*- coding: utf-8 -*-
"""Update translations across all 20 language files in package.nls and bundle.l10n for D3-1 Dropzone UX."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent

LANGUAGES = [
    "en", "ko", "ja", "zh-CN", "zh-TW", "fr", "de", "es", "it", "ru",
    "pt-BR", "ar", "bg", "cs", "he", "hu", "pl", "th", "tr", "vi"
]

# 1. package.nls.*.json entries
PACKAGE_NLS_ENTRIES = {
    "vibezoo.image.autoAnalyze.description": {
        "en": "Automatically copy markdown image reference to clipboard and prepare analysis when an image is pasted into Dropzone",
        "ko": "Dropzone에 이미지를 붙여넣었을 때 마크다운 이미지 참조를 클립보드에 자동 복사하고 분석을 준비합니다",
        "ja": "Dropzoneに画像を貼り付けた際に、Markdown画像参照をクリップボードに自動コピーし、分析を準備します",
    }
}

# 2. bundle.l10n.*.json entries
BUNDLE_L10N_ENTRIES = {
    "VibeZoo Drop Zone": {
        "en": "VibeZoo Drop Zone",
        "ko": "VibeZoo 드롭존",
        "ja": "VibeZoo ドロップゾーン"
    },
    "Paste image (Ctrl+V) or drag & drop files here": {
        "en": "Paste image (Ctrl+V) or drag & drop files here",
        "ko": "이미지 붙여넣기(Ctrl+V) 또는 파일을 여기로 드래그하세요",
        "ja": "画像を貼り付け (Ctrl+V) またはここにファイルをドラッグ＆ドロップ"
    },
    "Click to browse files": {
        "en": "Click to browse files",
        "ko": "클릭하여 파일 찾아보기",
        "ja": "クリックしてファイルを参照"
    },
    "Drop Zone": {
        "en": "Drop Zone",
        "ko": "드롭존",
        "ja": "ドロップゾーン"
    },
    "Browse Files": {
        "en": "Browse Files",
        "ko": "파일 찾아보기",
        "ja": "ファイルを参照"
    },
    "Clear": {
        "en": "Clear",
        "ko": "지우기",
        "ja": "クリア"
    },
    "Copy Markdown": {
        "en": "Copy Markdown",
        "ko": "마크다운 복사",
        "ja": "Markdownをコピー"
    },
    "Copy Path": {
        "en": "Copy Path",
        "ko": "경로 복사",
        "ja": "パスをコピー"
    },
    "Open in VS Code": {
        "en": "Open in VS Code",
        "ko": "VS Code에서 열기",
        "ja": "VS Codeで開く"
    },
    "Recent Uploads": {
        "en": "Recent Uploads",
        "ko": "최근 업로드",
        "ja": "最近のアップロード"
    },
    "Clear History": {
        "en": "Clear History",
        "ko": "기록 지우기",
        "ja": "履歴をクリア"
    },
    "No recent uploads": {
        "en": "No recent uploads",
        "ko": "최근 업로드 내역이 없습니다",
        "ja": "最近のアップロードはありません"
    },
    "Saved & Markdown copied to clipboard!": {
        "en": "Saved & Markdown copied to clipboard!",
        "ko": "저장 완료 및 마크다운이 클립보드에 복사되었습니다!",
        "ja": "保存され、Markdownがクリップボードにコピーされました！"
    },
    "Upload failed: {0}": {
        "en": "Upload failed: {0}",
        "ko": "업로드 실패: {0}",
        "ja": "アップロードに失敗しました: {0}"
    },
    "copied to clipboard!": {
        "en": "copied to clipboard!",
        "ko": "클립보드에 복사되었습니다!",
        "ja": "クリップボードにコピーされました！"
    },
    "Markdown": {
        "en": "Markdown",
        "ko": "마크다운",
        "ja": "Markdown"
    },
    "Path": {
        "en": "Path",
        "ko": "경로",
        "ja": "パス"
    },
    "Uploading...": {
        "en": "Uploading...",
        "ko": "업로드 중...",
        "ja": "アップロード中..."
    },
    "Image file": {
        "en": "Image file",
        "ko": "이미지 파일",
        "ja": "画像ファイル"
    },
    "Document file": {
        "en": "Document file",
        "ko": "문서 파일",
        "ja": "ドキュメントファイル"
    },
    "Content": {
        "en": "Content",
        "ko": "내용",
        "ja": "コンテンツ"
    },
    "📋 {0} copied to clipboard!": {
        "en": "📋 {0} copied to clipboard!",
        "ko": "📋 {0}이(가) 클립보드에 복사되었습니다!",
        "ja": "📋 {0}をクリップボードにコピーしました！"
    },
    "🗑️ Upload history cleared.": {
        "en": "🗑️ Upload history cleared.",
        "ko": "🗑️ 업로드 기록이 삭제되었습니다.",
        "ja": "🗑️ アップロード履歴をクリアしました。"
    },
    "✅ {0} saved & Markdown copied to clipboard! Paste it in AI chat.": {
        "en": "✅ {0} saved & Markdown copied to clipboard! Paste it in AI chat.",
        "ko": "✅ {0}이(가) 저장되었으며 마크다운이 클립보드에 복사되었습니다! AI 채팅창에 바로 붙여넣으세요.",
        "ja": "✅ {0}が保存され、Markdownがクリップボードにコピーされました！AIチャットに貼り付けてください。"
    }
}


def update_package_nls():
    ext_dir = ROOT / "extension"
    for lang in LANGUAGES:
        if lang == "en":
            nls_path = ext_dir / "package.nls.json"
        else:
            nls_path = ext_dir / f"package.nls.{lang}.json"
        
        if not nls_path.exists():
            print(f"Warning: {nls_path} not found")
            continue
        
        with open(nls_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for key, trans in PACKAGE_NLS_ENTRIES.items():
            if lang in trans:
                data[key] = trans[lang]
            else:
                data[key] = trans["en"]
        
        with open(nls_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Updated package.nls: {nls_path.name}")


def update_bundle_l10n():
    l10n_dir = ROOT / "extension" / "l10n"
    for lang in LANGUAGES:
        if lang == "en":
            bundle_path = l10n_dir / "bundle.l10n.json"
        else:
            bundle_path = l10n_dir / f"bundle.l10n.{lang}.json"
        
        if not bundle_path.exists():
            print(f"Warning: {bundle_path} not found")
            continue
        
        with open(bundle_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for key, trans in BUNDLE_L10N_ENTRIES.items():
            if lang in trans:
                data[key] = trans[lang]
            else:
                data[key] = trans["en"]
        
        with open(bundle_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Updated bundle.l10n: {bundle_path.name}")


if __name__ == "__main__":
    print("=== Updating package.nls files ===")
    update_package_nls()
    print("\n=== Updating bundle.l10n files ===")
    update_bundle_l10n()
    print("\nDone!")
