import json
with open('extension/l10n/bundle.l10n.json', 'r', encoding='utf-8') as f:
    en_bundle = json.load(f)

with open('extension/l10n/bundle.l10n.ko.json', 'r', encoding='utf-8') as f:
    ko_bundle = json.load(f)

new_translations = {
  "# 🔍 VibeZoo Foundation Diagnostics": "# 🔍 VibeZoo Foundation 진단",
  "✅ Zoo Code Crow Memory: Connected": "✅ Zoo Code Crow Memory: 연결됨",
  "❌ Zoo Code Crow Memory: Connection failed": "❌ Zoo Code Crow Memory: 연결 실패",
  "✅ VibeZoo Extension: Active": "✅ VibeZoo Extension: 활성화됨",
  "✅ yocto directory: Exists": "✅ yocto 디렉토리: 존재함",
  "⚠️ yocto directory: Missing": "⚠️ yocto 디렉토리: 없음",
  "✅ .zoo/ directory: Exists": "✅ .zoo/ 디렉토리: 존재함",
  "⚠️ .zoo/ directory: Missing": "⚠️ .zoo/ 디렉토리: 없음",
  "## Settings": "## 설정",
  "# 🔍 VibeZoo Self Check": "# 🔍 VibeZoo 자가진단",
  "## System Status": "## 시스템 상태",
  "✅ MCP Bridge: Normal": "✅ MCP Bridge: 정상",
  "⚠️ MCP Bridge: Abnormal response": "⚠️ MCP Bridge: 비정상 응답",
  "❌ MCP Bridge: Connection failed": "❌ MCP Bridge: 연결 실패",
  "⚠️ Crow Memory: Disconnected": "⚠️ Crow Memory: 연결 안 됨",
  "✅ yocto directory": "✅ yocto 디렉토리",
  "⚠️ no yocto directory": "⚠️ yocto 디렉토리 없음",
  "✅ vibezoo_mcp_bridge.py": "✅ vibezoo_mcp_bridge.py",
  "❌ vibezoo_mcp_bridge.py not found": "❌ vibezoo_mcp_bridge.py 없음",
  "## Shortcuts": "## 단축키",
  "| Key | Function |": "| 키 | 기능 |",
  "| **Ctrl+Shift+Z** | Instant Rewind |": "| **Ctrl+Shift+Z** | Instant Rewind (YOLO 복구) |",
  "| **Ctrl+Shift+R** | Session Resume |": "| **Ctrl+Shift+R** | Session Resume (이전 세션) |",
  "## Commands (`Ctrl+Shift+P`)": "## 명령어 (`Ctrl+Shift+P`)",
  "| Command | Function |": "| 명령어 | 기능 |",
  "| `VibeZoo: Open Whiteboard` | 🎨 Collaborate with AI drawing |": "| `VibeZoo: Open Whiteboard` | 🎨 AI와 그림 그리며 협업 |",
  "| `VibeZoo: Open UI Preview` | 🖼️ React/Vue Live Preview |": "| `VibeZoo: Open UI Preview` | 🖼️ React/Vue 실시간 미리보기 |",
  "| `VibeZoo: Instant Rewind` | ⏪ YOLO Instant Recovery |": "| `VibeZoo: Instant Rewind` | ⏪ YOLO 즉시 복구 |",
  "| `VibeZoo: Verify Foundation` | 🔍 State Diagnostics |": "| `VibeZoo: Verify Foundation` | 🔍 상태 진단 |",
  "## MCP Tools (Zoo Code Chat)": "## MCP 도구 (Zoo Code 채팅)",
  "| \"search code\" | Scout: search_codebase |": "| \"코드 검색해줘\" | Scout: search_codebase |",
  "| \"review code\" | Reviewer: review_code |": "| \"코드 리뷰해줘\" | Reviewer: review_code |",
  "| \"analyze dependencies\" | DeepAnalyzer: map_dependencies |": "| \"의존성 분석해줘\" | DeepAnalyzer: map_dependencies |",
  "| \"draw a picture\" | Whiteboard: draw_on_whiteboard |": "| \"그림 그려줘\" | Whiteboard: draw_on_whiteboard |",
  "## Auto Features": "## 자동 기능",
  "- 🤫 Silent Build (Save build errors to Crow)": "- 🤫 Silent Build (빌드 에러 Crow 저장)",
  "- 📸 yocto Backup (Real-time save of file changes)": "- 📸 yocto 백업 (모든 파일 변경 실시간 저장)",
  "- 🔧 AutoBuildFix (Auto-fix build failures)": "- 🔧 AutoBuildFix (빌드 실패 자동 수정)",
  "VibeZoo: Active": "VibeZoo: 활성화됨",
  "VibeZoo Bridge: Connected (:{0})": "VibeZoo Bridge: 연결됨 (:{0})",
  " | Crow: Connected": " | Crow: 연결됨",
  " | Crow: Disconnected": " | Crow: 없음",
  "$(gear) Suggested: {0}": "$(gear) 권장: {0}",
  "Waiting for VibeZoo...": "VibeZoo 대기 중...",
  "Automatically shown when Bridge connects": "브릿지 연결 시 자동 표시됩니다",
  "$(sync~spin) Waiting for VibeZoo...": "$(sync~spin) VibeZoo 대기 중...",
  "Agent Info": "에이전트 정보",
  "No YOLO history": "YOLO 기록 없음",
  "Automatically recorded when working in YOLO mode": "YOLO 모드로 작업 시 자동 기록됩니다",
  "$(history) No YOLO history": "$(history) YOLO 기록 없음",
  "No previous session": "이전 세션 없음",
  "Loading session info from Crow Memory...": "Crow Memory에서 세션 정보를 불러오는 중...",
  "$(empty) No loaded session": "$(empty) 불러온 세션 없음",
  "📋 {0}": "📋 {0}",
  "No summary": "요약 없음",
  "📁 {0}": "📁 {0}",
  "No project path": "프로젝트 경로 없음",
  "📌 Key Decisions ({0})": "📌 주요 결정 ({0})",
  "📄 Modified Files ({0})": "📄 수정 파일 ({0})",
  "⏳ Pending Tasks ({0})": "⏳ 미완료 작업 ({0})",
  "**Session Summary**\\n\\n{0}\\n\\n**Project**: {1}\\n**Mode**: {2}\\n**Started**: {3}{4}{5}{6}": "**세션 요약**\n\n{0}\n\n**프로젝트**: {1}\n**모드**: {2}\n**시작**: {3}{4}{5}{6}",
  "\\n**Key Decisions**: {0}": "\n**주요 결정**: {0}",
  "\\n**Modified Files**: {0}": "\n**수정 파일**: {0}",
  "\\n**Pending Tasks**: {0}": "\n**미완료 작업**: {0}"
}

for k, v in new_translations.items():
    ko_bundle[k] = v

final_ko_bundle = {}
for k in en_bundle.keys():
    final_ko_bundle[k] = ko_bundle.get(k, k)

with open('extension/l10n/bundle.l10n.ko.json', 'w', encoding='utf-8') as f:
    json.dump(final_ko_bundle, f, indent=2, ensure_ascii=False)

print("Done")
