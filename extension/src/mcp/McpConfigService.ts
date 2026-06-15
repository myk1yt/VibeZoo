// VibeZoo: MCP 설정 읽기/쓰기 전담 서비스
// Task 4 — global MCP 설정과 무관하게 항상 .roo/mcp.json을 최신 상태로 유지

import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { ConfigService } from '../config/ConfigService';
import { getGlobalMcpSettingsPath } from '../platform/VscodePaths';
import type { McpServerDefinition, McpSettings } from '../types';

export class McpConfigService {
  /**
   * OS별 Zoo Code global MCP 설정 파일 경로 반환.
   * 참고 전용 — 이 파일을 수정하지는 않음.
   */
  getGlobalMcpSettingsPath(): string {
    return getGlobalMcpSettingsPath();
  }

  /**
   * Global MCP 설정 파일 읽기 (읽기 전용, 참고 목적).
   * 파일이 없거나 파싱 실패 시 null 반환.
   */
  readGlobalMcp(): McpSettings | null {
    try {
      const globalPath = this.getGlobalMcpSettingsPath();
      if (!fs.existsSync(globalPath)) {
        return null;
      }
      const raw = fs.readFileSync(globalPath, 'utf-8');
      const parsed: McpSettings = JSON.parse(raw);
      return parsed;
    } catch (err: any) {
      console.warn(`[McpConfigService] Global MCP 설정 읽기 실패: ${err.message}`);
      return null;
    }
  }

  /**
   * 글로벌 Zoo Code `mcp_settings.json`에 지정된 서버 정의를 **항상** 작성.
   * writeProjectMcp()와 동일한 병합 로직으로, 기존 사용자 정의 MCP 서버 보존.
   *
   * @param serverKey - 서버 식별자 (기본: 'vibezoo')
   * @param definition - MCP 서버 정의
   */
  writeGlobalMcp(
    serverKey: string = 'vibezoo',
    definition?: McpServerDefinition,
  ): void {
    const globalPath = this.getGlobalMcpSettingsPath();
    const dir = path.dirname(globalPath);
    fs.mkdirSync(dir, { recursive: true });

    if (!definition) {
      definition = this.buildDefaultDefinition();
    }

    // 기존 글로벌 설정 읽기
    let existing: any = {};
    if (fs.existsSync(globalPath)) {
      try {
        const raw = fs.readFileSync(globalPath, 'utf-8');
        if (raw.trim()) existing = JSON.parse(raw);
      } catch { existing = {}; }
    }

    const existingServers: Record<string, any> = existing.mcpServers || {};

    // 기존 서버 정의가 있으면 병합
    // 기존 설정(url, autoStartCommand 등)을 모두 우선 보존
    // — url/autoStartCommand를 강제 덮어쓰지 않음 (사용자 설정 보호)
    if (existingServers[serverKey]) {
      const existingDef = { ...existingServers[serverKey] };
      delete existingDef.autoStart;
      delete existingDef.autoStartCommand;
      definition = {
        ...definition,                   // 새 기본값 먼저 (alwaysAllow 등 추가분)
        ...existingDef,                  // 기존 사용자 설정이 모두 우선
      };
    }

    // vibezoo 키만 병합 (다른 사용자 정의 서버 보존)
    const merged: McpSettings = {
      mcpServers: { ...existingServers, [serverKey]: definition },
    };

    // 파일 쓰기
    fs.writeFileSync(globalPath, JSON.stringify(merged, null, 2), 'utf-8');

    // mtime 갱신 → Zoo Code file watcher 강제 트리거
    try {
      const now = Date.now() / 1000;
      fs.utimesSync(globalPath, now, now);
    } catch { /* 비치명적 */ }

    console.log(`[McpConfigService] ✅ Global MCP ${serverKey} 업데이트 완료: ${globalPath}`);
  }

  /**
   * 프로젝트 `.roo/mcp.json`에 지정된 서버 정의를 **항상** 작성.
   * global 설정 존재 여부와 무관하게 강제 기록.
   *
   * @param root   - 프로젝트 루트 경로
   * @param serverKey - 서버 식별자 (기본: 'vibezoo')
   * @param definition - MCP 서버 정의
   */
  writeProjectMcp(
    root: string,
    serverKey: string = 'vibezoo',
    definition?: McpServerDefinition,
  ): void {
    const zooMCPDir = path.join(root, '.roo');
    const zooMCPPath = path.join(zooMCPDir, 'mcp.json');

    // 디렉토리 생성
    fs.mkdirSync(zooMCPDir, { recursive: true });

    // 서버 정의가 없으면 ConfigService에서 URL 생성
    if (!definition) {
      definition = this.buildDefaultDefinition();
    }

    // 기존 설정 읽기 (파일이 없거나 깨졌으면 빈 객체)
    let existing: any = {};
    if (fs.existsSync(zooMCPPath)) {
      try {
        const raw = fs.readFileSync(zooMCPPath, 'utf-8');
        if (raw.trim()) {
          existing = JSON.parse(raw);
        }
      } catch (err: any) {
        console.warn(`[McpConfigService] 기존 mcp.json 파싱 실패 (덮어쓰기): ${err.message}`);
        existing = {};
      }
    }

    const existingServers: Record<string, any> = existing.mcpServers || {};

    // 기존 서버 정의가 있으면 병합
    // 사용자 설정(autoStart, autoStartCommand, alwaysAllow 등)은 보존하고
    // url/transport만 새 정의로 갱신
    if (existingServers[serverKey]) {
      const existingDef = { ...existingServers[serverKey] };
      delete existingDef.autoStart;
      delete existingDef.autoStartCommand;
      definition = {
        ...definition,                   // 새 기본값 먼저
        ...existingDef,                  // 기존 사용자 설정이 우선
        url: definition.url,             // url은 항상 새 정의로
        transport: definition.transport, // transport도 항상 새 정의로
      };
    }

    // vibezoo 키만 병합 (다른 사용자 정의 서버 보존)
    const merged: McpSettings = {
      mcpServers: {
        ...existingServers,
        [serverKey]: definition,
      },
    };

    // 파일 쓰기
    fs.writeFileSync(zooMCPPath, JSON.stringify(merged, null, 2), 'utf-8');

    // mtime 갱신 → Zoo Code file watcher 강제 트리거
    try {
      const now = Date.now() / 1000;
      fs.utimesSync(zooMCPPath, now, now);
    } catch {
      // utimes 실패는 치명적이지 않음
    }

    console.log(`[McpConfigService] ✅ .roo/mcp.json ${serverKey} 업데이트 완료: ${zooMCPPath}`);
  }

  /**
   * 기존 사용자 정의 서버를 보존하며 vibezoo 키만 병합.
   * writeProjectMcp와 동일한 동작 (별칭).
   */
  mergeProjectMcp(
    root: string,
    serverKey: string = 'vibezoo',
    definition?: McpServerDefinition,
  ): void {
    this.writeProjectMcp(root, serverKey, definition);
  }

  /**
   * 프로젝트 .roo/mcp.json에서 vibezoo 키를 제거.
   * mcpServers가 빈 객체가 되면 파일 자체를 삭제.
   *
   * @param root      - 프로젝트 루트 경로
   * @param serverKey - 제거할 서버 식별자 (기본: 'vibezoo')
   */
  cleanProjectMcp(root: string, serverKey: string = 'vibezoo'): void {
    const mcpPath = path.join(root, '.roo', 'mcp.json');
    if (!fs.existsSync(mcpPath)) return;

    try {
      const raw = fs.readFileSync(mcpPath, 'utf-8');
      const config = JSON.parse(raw);
      if (config.mcpServers?.[serverKey]) {
        delete config.mcpServers[serverKey];
        // Zoo Code는 mcpServers 키가 비어있어도 반드시 존재해야 함
        if (Object.keys(config.mcpServers).length === 0) {
          config.mcpServers = {};  // delete 대신 빈 객체 유지
        }
        fs.writeFileSync(mcpPath, JSON.stringify(config, null, 2), 'utf-8');
        console.log(`[McpConfigService] ✅ .roo/mcp.json에서 ${serverKey} 제거 완료`);
      } else if (!config.mcpServers) {
        // 파일이 {}로 시작하는 경우 mcpServers 키 초기화
        config.mcpServers = {};
        fs.writeFileSync(mcpPath, JSON.stringify(config, null, 2), 'utf-8');
        console.log(`[McpConfigService] ✅ .roo/mcp.json에 빈 mcpServers 초기화`);
      }
    } catch (err: any) {
      console.warn(`[McpConfigService] cleanProjectMcp 실패: ${err.message}`);
    }
  }

  /**
   * ConfigService에서 host/port를 읽어 기본 MCP 서버 정의 생성.
   */
  private buildDefaultDefinition(): McpServerDefinition {
    const host = ConfigService.getHost();
    const port = ConfigService.getBridgePort();
    return {
      url: `http://${host}:${port}/sse`,
      global: true,
      alwaysAllow: [
        'search_codebase', 'find_references', 'summarize_architecture',
        'review_code', 'explain_code', 'analyze_changes', 'review_pr', 'refactor_across_files',
        'generate_tests', 'analyze_coverage', 'analyze_call_graph', 'map_dependencies',
        'extract_patterns', 'reverse_engineer', 'analyze_uploaded_file', 'check_uploaded_files',
        'draw_on_whiteboard', 'get_whiteboard_state',
        'auto_fix_status', 'retry_build', 'check_intervention',
        'review_project', 'find_bugs', 'suggest_refactor', 'generate_docs',
        'learn_project', 'recall_project', 'learn_preference', 'get_preferences',
        'apply_patch', 'read_project_file',
        'ux_coordinator', 'auto_analyze_after_drop', 'auto_analyze_whiteboard',
        'vibezoo_feedback', 'vibezoo_setup',
        'capture_screen', 'fetch_page', 'web_search', 'aggregate_spatial_pixels',
      ],
    };
  }

  /**
   * 현재 설정 기반 URL이 유효한지 로깅과 함께 확인.
   * SelfCheck 등에서 사용.
   */
  logGlobalStatus(): void {
    const global = this.readGlobalMcp();
    if (global?.mcpServers?.vibezoo) {
      const existing = global.mcpServers.vibezoo;
      console.log(
        `[McpConfigService] Global MCP에 vibezoo 등록됨: ${existing.url} (참고 전용 — 프로젝트 설정에도 기록)`,
      );
    } else {
      console.log('[McpConfigService] Global MCP에 vibezoo 미등록 (프로젝트 설정에 기록)');
    }
  }
}
