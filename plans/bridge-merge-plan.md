# VibeZoo MCP Bridge 병합 계획

> 연구 분석 결과 기반 | 2026-06-02

## 결정: v1 모듈형 아키텍처 유지, v2 아카이브

v1(`0.14.1`)이 v2(`0.12.0`)보다 모든 면에서 우수:
- 더 최신 버전 (0.14.1 > 0.12.0)
- 7개 ghost tool 없음
- capture_screen source 파라미터 지원
- WhiteboardDataConverter, IntentDetector 등 고급 기능

## 액션 플랜

| Phase | 작업 | 파일 | 설명 |
|-------|------|------|------|
| 1 | v2 아카이브 이동 | `vibezoo_mcp_bridge_v2.py` → `_archive/vibezoo_mcp_bridge_v2.py` | 더 이상 사용하지 않음 |
| 2 | Extension 업데이트 | [`SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts) | `_v2.py` → `.py` 참조 변경 |
| 3 | v1 브릿지 capture_screen 최신화 (이미 완료) | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) | source 파라미터 지원, `check_uploaded_files` 도구 포함 |
| 4 | 구 VSIX 파일 삭제 | `extension/vibezoo-*.vsix` | 모든 구버전 VSIX 제거 |
| 5 | VSIX 빌드 + 설치 | — | 수정된 Extension 코드 반영 |
| 6 | GitHub 커밋 + 푸시 | — | v0.14.1 유지 |

> 이 계획은 Code 모드에서 즉시 구현합니다.