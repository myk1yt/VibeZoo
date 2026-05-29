# 9020 단일 포트 통합 — 멀티 윈도우 근본 해결

> 진단일: 2026-05-28 | 대상: vibezoo_mcp_bridge.py + SubagentManager.ts + extension.ts

## 문제 요약

VS Code 창 2개 → 각 확장이 포트 9027로 브릿지 spawn → 두 번째 프로세스 포트 충돌 크래시 → `waitForReady()`가 첫 번째 브릿지의 `/health`를 보고 거짓 성공 → Zoo Code MCP 연결 시 404 또는 "project" 폴백

## 원인

현재 아키텍처는 Crow Memory(9020)와 VibeZoo Bridge(9027)가 **별도 포트, 별도 프로세스**로 분리되어 있음. 원래 설계 의도는 **9020 하나의 포트**에서 Crow + VibeZoo를 모두 제공하는 것.

## 해결 전략

```
변경 전:                           변경 후:
Zoo Code ──► :9020 (Crow)         Zoo Code ──► :9020 (Crow + VibeZoo 통합)
         ──► :9027 (VibeZoo)                   단일 FastMCP 서버
         2개 포트, 2개 프로세스               1개 포트, 1개 프로세스
```

