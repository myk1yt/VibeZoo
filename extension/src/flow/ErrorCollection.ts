// VibeZoo Wave 7: Extension 측 에러 수집 및 알림 관리
// 단일 watcher 전략: ErrorDashboard가 registry.json을 감시.
// Extension은 ErrorDashboard의 데이터를 수신하거나,
// activate 시에만 registry.json을 확인하여 StatusBar 업데이트 + Critical 알림을 수행.
//
// 설계: ErrorDashboard만 fs.watchFile 사용, ErrorCollection은
// activate() 시점에 1회 확인 + 주기적 폴링 (간소화) 또는
// Dashboard를 통해 데이터를 수신하는 구조.

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { StatusBarManager, NotificationThrottle } from '../ui/StatusBarManager';

const REGISTRY_PATH = path.join(os.homedir(), '.vibezoo-errors', 'registry.json');
const POLL_INTERVAL_MS = 5000; // 5초마다 registry.json 확인

let _pollTimer: NodeJS.Timeout | null = null;
let _lastCriticalCount = 0;
let _enabled = true;

/**
 * Extension 측 에러 수집 활성화.
 * activate()에서 호출된다.
 * - registry.json 폴링 (POLL_INTERVAL_MS 간격)
 * - Critical 에러 감지 시 showErrorMessage 표시
 * - context.subscriptions에 dispose 등록
 */
export function activateErrorCollection(
  context: vscode.ExtensionContext,
  statusBar: StatusBarManager
): void {
  _enabled = vscode.workspace.getConfiguration('vibezoo')
    .get('errorCollection.enabled', true);

  if (!_enabled) {
    console.log('[VibeZoo:ErrorCollection] Disabled by config');
    return;
  }

  // 1. 초기 1회 확인
  pollRegistry(statusBar);

  // 2. 주기적 폴링
  _pollTimer = setInterval(() => {
    pollRegistry(statusBar);
  }, POLL_INTERVAL_MS);

  // 3. dispose 등록
  context.subscriptions.push({
    dispose: () => {
      if (_pollTimer) {
        clearInterval(_pollTimer);
        _pollTimer = null;
      }
    },
  });

  console.log('[VibeZoo:ErrorCollection] Activated (poll interval: %dms)', POLL_INTERVAL_MS);
}

/**
 * registry.json 읽어서 StatusBar 업데이트 + Critical 알림
 */
function pollRegistry(statusBar: StatusBarManager): void {
  try {
    if (!fs.existsSync(REGISTRY_PATH)) {
      statusBar.setErrorCount(0, 0);
      _lastCriticalCount = 0;
      return;
    }

    const raw = fs.readFileSync(REGISTRY_PATH, 'utf-8');
    if (!raw.trim()) {
      statusBar.setErrorCount(0, 0);
      _lastCriticalCount = 0;
      return;
    }

    const errors: any[] = JSON.parse(raw);
    const total = errors.length;

    // Critical 에러 카운트 (동일 시그니처 5회 이상)
    const freq: Record<string, number> = {};
    errors.forEach((e: any) => {
      const sig = `${e.tool || ''}:${e.exception_type || ''}`;
      freq[sig] = (freq[sig] || 0) + 1;
    });
    const criticalSigCount = Object.values(freq).filter(c => c >= 5).length;

    statusBar.setErrorCount(total, criticalSigCount);

    // Critical 에러 증가 시 알림
    if (criticalSigCount > 0 && criticalSigCount > _lastCriticalCount) {
      NotificationThrottle.showError(
        `🐞 VibeZoo: ${criticalSigCount}개 Critical 에러 감지! Error Dashboard를 확인하세요.`,
        'Open Dashboard',
        'Reset Errors'
      ).then(choice => {
        if (choice === 'Open Dashboard') {
          vscode.commands.executeCommand('vibezoo.openErrorDashboard');
        } else if (choice === 'Reset Errors') {
          try {
            fs.writeFileSync(REGISTRY_PATH, '[]', 'utf-8');
            _lastCriticalCount = 0;
            statusBar.setErrorCount(0, 0);
            vscode.window.showInformationMessage('✅ VibeZoo: 에러 레지스트리가 리셋되었습니다.');
          } catch (e) {
            vscode.window.showErrorMessage(`❌ VibeZoo: 에러 레지스트리 리셋 실패: ${e}`);
          }
        }
      });
    }

    _lastCriticalCount = criticalSigCount;
  } catch {
    // registry.json 파싱 실패 시 silent
    statusBar.setErrorCount(0, 0);
    _lastCriticalCount = 0;
  }
}
