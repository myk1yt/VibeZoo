// VibeZoo Wave 7: Extension 측 에러 수집 및 알림 관리
// 단일 watcher 전략: ErrorDashboard가 registry.json을 감시.
// Extension은 ErrorDashboard의 데이터를 수신하거나,
// activate 시에만 registry.json을 확인하여 StatusBar 업데이트 + Critical 알림을 수행.
//
// 2026-07-28 개선:
// - globalState/workspaceState 기반 에러 열람 상태 지속성 도입 (창 재시작 시 자동 팝업 방지)
// - vibezoo.errorCollection.autoOpenDashboard (never | onCritical | always) 설정 연동
// - vibezoo.errorCollection.notifyOnCritical 설정 연동

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { StatusBarManager, NotificationThrottle } from '../ui/StatusBarManager';

const REGISTRY_PATH = path.join(os.homedir(), '.vibezoo-errors', 'registry.json');
const POLL_INTERVAL_MS = 5000; // 5초마다 registry.json 확인

let _pollTimer: NodeJS.Timeout | null = null;
let _lastCriticalCount = 0;
let _lastSeenTimestamp = 0;
let _enabled = true;
let _extensionContext: vscode.ExtensionContext | null = null;

/**
 * Extension 측 에러 수집 활성화.
 * activate()에서 호출된다.
 * - registry.json 폴링 (POLL_INTERVAL_MS 간격)
 * - Critical 에러 감지 시 showErrorMessage 표시 및 autoOpenDashboard 설정 준수
 * - context.subscriptions에 dispose 등록
 */
export function activateErrorCollection(
  context: vscode.ExtensionContext,
  statusBar: StatusBarManager
): void {
  _extensionContext = context;
  _enabled = vscode.workspace.getConfiguration('vibezoo')
    .get('errorCollection.enabled', true);

  if (!_enabled) {
    console.log('[VibeZoo:ErrorCollection] Disabled by config');
    return;
  }

  // 이전 세션에서 확인한 State 복원 (창 개별 재시작 시 반복 알림/팝업 방지)
  _lastCriticalCount = context.workspaceState.get<number>('vibezoo.lastCriticalCount')
    ?? context.globalState.get<number>('vibezoo.lastCriticalCount')
    ?? 0;
  _lastSeenTimestamp = context.workspaceState.get<number>('vibezoo.lastSeenErrorTimestamp')
    ?? context.globalState.get<number>('vibezoo.lastSeenErrorTimestamp')
    ?? 0;

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

  console.log('[VibeZoo:ErrorCollection] Activated (poll interval: %dms, lastCritical: %d)', POLL_INTERVAL_MS, _lastCriticalCount);
}

/**
 * 이미 열람했음을 기록
 */
export function markErrorsAsSeen(maxTimestamp?: number, criticalCount?: number): void {
  if (_extensionContext) {
    if (typeof criticalCount === 'number') {
      _lastCriticalCount = criticalCount;
      _extensionContext.workspaceState.update('vibezoo.lastCriticalCount', criticalCount);
      _extensionContext.globalState.update('vibezoo.lastCriticalCount', criticalCount);
    }
    if (typeof maxTimestamp === 'number') {
      _lastSeenTimestamp = maxTimestamp;
      _extensionContext.workspaceState.update('vibezoo.lastSeenErrorTimestamp', maxTimestamp);
      _extensionContext.globalState.update('vibezoo.lastSeenErrorTimestamp', maxTimestamp);
    }
  }
}

/**
 * 에러 레지스트리 및 지속 상태 리셋
 */
export function resetErrorRegistry(statusBar?: StatusBarManager): void {
  try {
    fs.writeFileSync(REGISTRY_PATH, '[]', 'utf-8');
    _lastCriticalCount = 0;
    _lastSeenTimestamp = 0;
    if (_extensionContext) {
      _extensionContext.workspaceState.update('vibezoo.lastCriticalCount', 0);
      _extensionContext.globalState.update('vibezoo.lastCriticalCount', 0);
      _extensionContext.workspaceState.update('vibezoo.lastSeenErrorTimestamp', 0);
      _extensionContext.globalState.update('vibezoo.lastSeenErrorTimestamp', 0);
    }
    if (statusBar) {
      statusBar.setErrorCount(0, 0);
    }
    vscode.window.showInformationMessage('✅ VibeZoo: 에러 레지스트리가 리셋되었습니다.');
  } catch (e) {
    vscode.window.showErrorMessage(`❌ VibeZoo: 에러 레지스트리 리셋 실패: ${e}`);
  }
}

/**
 * registry.json 읽어서 StatusBar 업데이트 + Critical 알림
 */
function pollRegistry(statusBar: StatusBarManager): void {
  try {
    if (!fs.existsSync(REGISTRY_PATH)) {
      statusBar.setErrorCount(0, 0);
      return;
    }

    const raw = fs.readFileSync(REGISTRY_PATH, 'utf-8');
    if (!raw.trim()) {
      statusBar.setErrorCount(0, 0);
      return;
    }

    const errors: any[] = JSON.parse(raw);
    const total = errors.length;

    if (total === 0) {
      statusBar.setErrorCount(0, 0);
      return;
    }

    // Critical 에러 카운트 (동일 시그니처 5회 이상)
    const freq: Record<string, number> = {};
    let maxTimestamp = 0;
    errors.forEach((e: any) => {
      const sig = `${e.tool || ''}:${e.exception_type || ''}`;
      freq[sig] = (freq[sig] || 0) + 1;
      if (e.timestamp && typeof e.timestamp === 'number') {
        if (e.timestamp > maxTimestamp) maxTimestamp = e.timestamp;
      }
    });
    const criticalSigCount = Object.values(freq).filter(c => c >= 5).length;

    statusBar.setErrorCount(total, criticalSigCount);

    const config = vscode.workspace.getConfiguration('vibezoo');
    const autoOpenMode = config.get<'never' | 'onCritical' | 'always'>('errorCollection.autoOpenDashboard', 'never');
    const notifyOnCritical = config.get<boolean>('errorCollection.notifyOnCritical', true);

    const hasNewErrors = maxTimestamp > 0 && maxTimestamp > _lastSeenTimestamp;
    const hasNewCritical = criticalSigCount > _lastCriticalCount;

    // 신규 에러 또는 Critical 에러가 발생한 경우 처리
    if (hasNewCritical || (hasNewErrors && autoOpenMode === 'always')) {
      // 1. autoOpenDashboard 처리
      if (autoOpenMode === 'always' || (autoOpenMode === 'onCritical' && hasNewCritical)) {
        vscode.commands.executeCommand('vibezoo.openErrorDashboard');
        markErrorsAsSeen(maxTimestamp, criticalSigCount);
      }

      // 2. 알림 팝업 처리 (notifyOnCritical이 true일 경우)
      if (notifyOnCritical && hasNewCritical) {
        NotificationThrottle.showError(
          `🐞 VibeZoo: ${criticalSigCount}개 Critical 에러 감지! Error Dashboard를 확인하세요.`,
          'Open Dashboard',
          'Reset Errors',
          'Configure Auto-Open'
        ).then(choice => {
          if (choice === 'Open Dashboard') {
            vscode.commands.executeCommand('vibezoo.openErrorDashboard');
            markErrorsAsSeen(maxTimestamp, criticalSigCount);
          } else if (choice === 'Reset Errors') {
            resetErrorRegistry(statusBar);
          } else if (choice === 'Configure Auto-Open') {
            vscode.commands.executeCommand('vibezoo.configureErrorDashboard');
          }
        });
      }

      // 상태 갱신 및 저장
      _lastCriticalCount = criticalSigCount;
      if (maxTimestamp > 0) _lastSeenTimestamp = maxTimestamp;
      if (_extensionContext) {
        _extensionContext.workspaceState.update('vibezoo.lastCriticalCount', criticalSigCount);
        _extensionContext.globalState.update('vibezoo.lastCriticalCount', criticalSigCount);
        if (maxTimestamp > 0) {
          _extensionContext.workspaceState.update('vibezoo.lastSeenErrorTimestamp', maxTimestamp);
          _extensionContext.globalState.update('vibezoo.lastSeenErrorTimestamp', maxTimestamp);
        }
      }
    }
  } catch {
    // registry.json 파싱 실패 시 silent
    statusBar.setErrorCount(0, 0);
  }
}
