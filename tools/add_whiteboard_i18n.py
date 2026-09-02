import json
import os
from pathlib import Path

WHITEBOARD_TRANSLATIONS = {
    'After upload, call `check_uploaded_files()` to see the latest uploads.': {
        'ko': '업로드 후 `check_uploaded_files()`를 호출하여 최신 업로드 파일을 확인하세요.',
        'ja': 'アップロード後、`check_uploaded_files()`を呼び出して最新のアップロードを確認してください。',
    },
    'Analysis Suggestions': {
        'ko': '분석 제안',
        'ja': '分析の提案',
    },
    'Analysis example': {
        'ko': '분석 예시',
        'ja': '分析例',
    },
    'Based on the whiteboard content, you can:': {
        'ko': '화이트보드 내용을 바탕으로 다음 작업을 수행할 수 있습니다:',
        'ja': 'ホワイトボードの内容に基づいて以下を実行できます:',
    },
    'Capture failed:': {
        'ko': '캡처 실패:',
        'ja': 'キャプチャ失敗:',
    },
    'Code Generation': {
        'ko': '코드 생성',
        'ja': 'コード生成',
    },
    'Convert whiteboard content to a Mermaid diagram': {
        'ko': '화이트보드 내용을 Mermaid 다이어그램으로 변환',
        'ja': 'ホワイトボードの内容をMermaidダイアグラムに変換',
    },
    'Description Generation': {
        'ko': '설명 생성',
        'ja': '説明生成',
    },
    'Diagram Conversion': {
        'ko': '다이어그램 변환',
        'ja': 'ダイアグラム変換',
    },
    'Drop zone opened. Upload a file and I will check it.': {
        'ko': '드롭존이 열렸습니다. 파일을 업로드하면 확인하겠습니다.',
        'ja': 'ドロップゾーンが開きました。ファイルをアップロードすると確認します。',
    },
    'Failed to draw:': {
        'ko': '그리기 실패:',
        'ja': '描画失敗:',
    },
    'Failed:': {
        'ko': '실패:',
        'ja': '失敗:',
    },
    'File Drop Zone': {
        'ko': '파일 드롭존',
        'ja': 'ファイルドロップゾーン',
    },
    'File Picker': {
        'ko': '파일 선택기',
        'ja': 'ファイルピッカー',
    },
    'File saved to:': {
        'ko': '파일 저장 위치:',
        'ja': 'ファイルの保存先:',
    },
    'File will be saved to': {
        'ko': '파일이 저장될 위치:',
        'ja': 'ファイルの保存先:',
    },
    'Generate code based on the whiteboard design': {
        'ko': '화이트보드 디자인을 기반으로 코드 생성',
        'ja': 'ホワイトボードのデザインに基づいてコードを生成',
    },
    'Improvement Suggestions': {
        'ko': '개선 제안',
        'ja': '改善提案',
    },
    'Install Pillow:': {
        'ko': 'Pillow 설치 필요:',
        'ja': 'Pillowのインストールが必要:',
    },
    'Invalid JSON:': {
        'ko': '유효하지 않은 JSON:',
        'ja': '無効なJSON:',
    },
    'No files uploaded in the current session. Please upload a file to the dropzone.': {
        'ko': '현재 세션에 업로드된 파일이 없습니다. 드롭존에 파일을 업로드해 주세요.',
        'ja': '現在のセッションでアップロードされたファイルはありません。ドロップゾーンにファイルをアップロードしてください。',
    },
    'No files uploaded yet.': {
        'ko': '아직 업로드된 파일이 없습니다.',
        'ja': 'まだアップロードされたファイルはありません。',
    },
    'Path': {
        'ko': '경로',
        'ja': 'パス',
    },
    'Provide a description of the whiteboard content': {
        'ko': '화이트보드 내용에 대한 설명 제공',
        'ja': 'ホワイトボードの内容の説明を提供',
    },
    'Provide feedback on the design': {
        'ko': '디자인에 대한 피드백 및 개선안 제공',
        'ja': 'デザインに関するフィードバックを提供',
    },
    'Raw JSON (truncated):': {
        'ko': 'Raw JSON (일부 생략):',
        'ja': 'Raw JSON (一部省略):',
    },
    'Recently Uploaded Files': {
        'ko': '최근 업로드된 파일',
        'ja': '最近アップロードされたファイル',
    },
    'Screen Capture': {
        'ko': '화면 캡처',
        'ja': '画面キャプチャ',
    },
    'Screen Capture Error': {
        'ko': '화면 캡처 오류',
        'ja': '画面キャプチャエラー',
    },
    'Screenshot': {
        'ko': '스크린샷',
        'ja': 'スクリーンショット',
    },
    'Select an image file from the file picker': {
        'ko': '파일 선택기에서 이미지 파일을 선택하세요',
        'ja': 'ファイルピッカーから画像ファイルを選択してください',
    },
    'Size': {
        'ko': '크기',
        'ja': 'サイズ',
    },
    'Then call `aggregate_spatial_pixels(image_path=...` to analyze': {
        'ko': '그 후 `aggregate_spatial_pixels(image_path=...`를 호출하여 분석하세요',
        'ja': 'その後、`aggregate_spatial_pixels(image_path=...`を呼び出して分析してください',
    },
    'To auto-analyze whiteboard content, call `get_whiteboard_state(analyze=True)`.': {
        'ko': '화이트보드 내용을 자동 분석하려면 `get_whiteboard_state(analyze=True)`를 호출하세요.',
        'ja': 'ホワイトボードの内容を自動分析するには、`get_whiteboard_state(analyze=True)`を呼び出してください。',
    },
    'Type': {
        'ko': '유형',
        'ja': 'タイプ',
    },
    'Use `aggregate_spatial_pixels()` with the saved image path for detailed spatial analysis.': {
        'ko': '저장된 이미지 경로로 `aggregate_spatial_pixels()`를 호출하여 상세 공간 분석을 수행하세요.',
        'ja': '保存された画像パスで`aggregate_spatial_pixels()`を呼び出して、詳細な空間分析を実行してください。',
    },
    'Whiteboard Drawing': {
        'ko': '화이트보드 그리기',
        'ja': 'ホワイトボード描画',
    },
    'Whiteboard Error': {
        'ko': '화이트보드 오류',
        'ja': 'ホワイトボードエラー',
    },
    'Whiteboard State': {
        'ko': '화이트보드 상태',
        'ja': 'ホワイトボード状態',
    },
}

def update_translations_directory(dir_path: Path):
    all_json_files = sorted(dir_path.glob("*.json"))
    for f in all_json_files:
        lang = f.stem
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            
        for k, translations in WHITEBOARD_TRANSLATIONS.items():
            if lang == "en":
                data[k] = k
            elif lang in translations:
                data[k] = translations[lang]
            else:
                # English fallback for other languages
                data[k] = k
                
        # Sort keys to keep json neat and consistent
        sorted_data = {k: data[k] for k in sorted(data.keys())}
        
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(sorted_data, fp, ensure_ascii=False, indent=2)
            fp.write("\n")
            
    print(f"Updated {len(all_json_files)} files in {dir_path}")

def main():
    ext_dir = Path("extension/mcp-servers/bridge/i18n/translations")
    root_dir = Path("mcp-servers/bridge/i18n/translations")
    
    update_translations_directory(ext_dir)
    update_translations_directory(root_dir)
    print("All translations updated successfully.")

if __name__ == "__main__":
    main()
