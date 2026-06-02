import json
with open('extension/l10n/bundle.l10n.json', 'r', encoding='utf-8') as f:
    en_bundle = json.load(f)

translations = {
  "VibeZoo: YOLO safety net is disabled.": "VibeZoo: YOLO 안전망이 비활성화되어 있습니다.",
  "YOLO Rewind complete: {0}/{1} files restored ({2}ms)": "YOLO Rewind 완료: {0}/{1} 파일 복구 ({2}ms)",
  "Rewind failed: {0}": "Rewind 실패: {0}",
  "✅ VibeZoo: Zoo Code Crow Memory connection verified!": "✅ VibeZoo: Zoo Code Crow Memory 연결 확인 성공!",
  "⚠️ VibeZoo: Cannot connect to Zoo Code Crow Memory.": "⚠️ VibeZoo: Zoo Code Crow Memory에 연결할 수 없습니다.",
  "❌ Crow connection failed: {0}": "❌ Crow 연결 실패: {0}",
  "🎉 VibeZoo ready! Ctrl+Shift+P → VibeZoo: Help": "🎉 VibeZoo 준비 완료! Ctrl+Shift+P → VibeZoo: Help",
  "View Help": "Help 보기",
  "Close": "닫기",
  "VibeZoo: Continuous Improvement Mode started": "VibeZoo: Continuous Improvement Mode 시작",
  "VibeZoo: Continuous Improvement Mode stopped": "VibeZoo: Continuous Improvement Mode 중지",
  "VibeZoo: Please type \"explain code\" in Zoo Code chat. (explain_code MCP tool)": "VibeZoo: Zoo Code 채팅에서 \"코드 설명해줘\" 라고 입력하세요. (explain_code MCP 도구)",
  "VibeZoo: Please type \"analyze changes\" in Zoo Code chat. (analyze_changes MCP tool)": "VibeZoo: Zoo Code 채팅에서 \"변경사항 분석해줘\" 라고 입력하세요. (analyze_changes MCP 도구)",
  "VibeZoo: Please type \"review PR\" in Zoo Code chat. (review_pr MCP tool)": "VibeZoo: Zoo Code 채팅에서 \"PR 리뷰해줘\" 라고 입력하세요. (review_pr MCP 도구)",
  "VibeZoo: Please type \"refactor\" in Zoo Code chat. (refactor_across_files MCP tool)": "VibeZoo: Zoo Code 채팅에서 \"리팩토링해줘\" 라고 입력하세요. (refactor_across_files MCP 도구)",
  "VibeZoo: Please type \"learn project\" in Zoo Code chat. (learn_project MCP tool)": "VibeZoo: Zoo Code 채팅에서 \"프로젝트 학습해줘\" 라고 입력하세요. (learn_project MCP 도구)",
  "VibeZoo: Please type \"recall project\" in Zoo Code chat. (recall_project MCP tool)": "VibeZoo: Zoo Code 채팅에서 \"프로젝트 기억해줘\" 라고 입력하세요. (recall_project MCP 도구)",
  "VibeZoo: Please type \"learn preference\" in Zoo Code chat. (learn_preference MCP tool)": "VibeZoo: Zoo Code 채팅에서 \"선호도 학습해줘\" 라고 입력하세요. (learn_preference MCP 도구)",
  "VibeZoo: Please type \"show preferences\" in Zoo Code chat. (get_preferences MCP tool)": "VibeZoo: Zoo Code 채팅에서 \"선호도 보여줘\" 라고 입력하세요. (get_preferences MCP 도구)",
  "VibeZoo: Auto-Fix Loop paused": "VibeZoo: Auto-Fix Loop 일시 중지됨",
  "VibeZoo: Auto-Fix Loop resumed": "VibeZoo: Auto-Fix Loop 재개됨",
  "VibeZoo: Auto-Fix Loop aborted": "VibeZoo: Auto-Fix Loop 중단됨",
  "✅ {0} uploaded. (Path copied to clipboard. Paste it in chat to instruct the LLM!)": "✅ {0}이 업로드되었습니다. (경로가 클립보드에 복사되었습니다. 채팅창에 붙여넣어 LLM에게 지시하세요!)",
  "Agent status will be displayed when VibeZoo MCP Bridge is connected.": "VibeZoo MCP Bridge가 연결되면 Agent 상태가 표시됩니다.",
  "YOLO session history will be displayed here when YOLO snapshots are created.": "YOLO(Yocto OnLine Offline) 모드로 YOCTO 스냅샷을 생성하면 여기에 기록이 표시됩니다.",
  "YOLO Session: {0}\nRight-click → Run Rewind": "YOLO 세션: {0}\n우클릭 → Rewind 실행",
  "Cannot load session resume from Crow Memory or local file.": "Crow Memory 또는 로컬 파일에서 세션 요약을 불러올 수 없습니다.",
  "VibeZoo: {0}\nClick to change mode": "VibeZoo: {0}\n클릭하여 모드 변경",
  "Auto tsc check on file save": "파일 저장 시 자동 tsc 검사",
  
  "⚠️ Cannot load Fabric.js": "⚠️ Fabric.js를 불러올 수 없습니다",
  "Please check your internet connection or if the CDN is blocked.": "인터넷 연결을 확인하거나 CDN이 차단되지 않았는지 확인하세요.",
  "✏️ Draw": "✏️ 그리기",
  "⬜ Rectangle": "⬜ 사각형",
  "📝 Text": "📝 텍스트",
  "🖱️ Select": "🖱️ 선택",
  "📸 Capture": "📸 캡처",
  "📷 Image": "📷 이미지",
  "🗑️ Delete Selected": "🗑️ 선택 삭제",
  "🧹 Clear All": "🧹 전체 삭제",
  "Text": "텍스트",
  "When AI generates React/Vue component code, it will be rendered here in real-time.": "AI가 React/Vue 컴포넌트 코드를 생성하면 이곳에 실시간 렌더링됩니다.",
  "Mermaid render error": "Mermaid 렌더링 오류"
}

ko_bundle = {}
for k, v in en_bundle.items():
    ko_bundle[k] = translations.get(k, k)

with open('extension/l10n/bundle.l10n.ko.json', 'w', encoding='utf-8') as f:
    json.dump(ko_bundle, f, indent=2, ensure_ascii=False)

print("Done")
