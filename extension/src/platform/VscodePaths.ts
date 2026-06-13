import * as os from 'os';
import * as path from 'path';
import * as vscode from 'vscode';

/**
 * VS Code distribution flavor enum.
 */
export type VSCodeFlavor = 'stable' | 'insiders';

/**
 * Detect whether the current VS Code instance is Insiders or Stable
 * by inspecting `vscode.env.appRoot`.
 */
function detectFlavor(): VSCodeFlavor {
  try {
    const appRoot = vscode.env.appRoot;
    if (/[Ii]nsiders/.test(appRoot)) {
      return 'insiders';
    }
  } catch {
    // vscode API not available — assume stable
  }
  return 'stable';
}

/**
 * Returns the Code directory name (e.g. "Code" or "Code - Insiders")
 * based on the detected flavor.
 */
function getCodeDirectoryName(): string {
  return detectFlavor() === 'insiders' ? 'Code - Insiders' : 'Code';
}

/**
 * Resolve the VS Code User configuration directory using platform branching.
 *
 * Priority:
 * 1. `vscode.env.appRoot` + platform branch (detects Stable vs Insiders)
 * 2. Fallback: `os.homedir()` + platform-specific path
 *
 * @returns Absolute path to the Code/User directory.
 *
 * @example
 * // Windows
 * getCodeUserPath() // → C:\Users\k1yt\AppData\Roaming\Code\User
 * // macOS
 * getCodeUserPath() // → /Users/k1yt/Library/Application Support/Code/User
 * // Linux
 * getCodeUserPath() // → /home/k1yt/.config/Code/User
 */
export function getCodeUserPath(): string {
  const codeDir = getCodeDirectoryName();
  const platform = process.platform;

  try {
    // Primary path: platform branching with APPDATA / homedir
    if (platform === 'win32') {
      const appData = process.env.APPDATA;
      if (appData) {
        return path.join(appData, codeDir, 'User');
      }
      // Fallback if APPDATA is somehow unset
      return path.join(os.homedir(), 'AppData', 'Roaming', codeDir, 'User');
    }

    if (platform === 'darwin') {
      return path.join(os.homedir(), 'Library', 'Application Support', codeDir, 'User');
    }

    // Linux / others
    return path.join(os.homedir(), '.config', codeDir, 'User');
  } catch {
    // Ultimate fallback: stable-only paths using os.homedir()
    return getFallbackCodeUserPath();
  }
}

/**
 * Last-resort fallback: always uses "Code" (stable) with os.homedir().
 */
function getFallbackCodeUserPath(): string {
  const platform = process.platform;
  if (platform === 'win32') {
    return path.join(os.homedir(), 'AppData', 'Roaming', 'Code', 'User');
  }
  if (platform === 'darwin') {
    return path.join(os.homedir(), 'Library', 'Application Support', 'Code', 'User');
  }
  return path.join(os.homedir(), '.config', 'Code', 'User');
}

/**
 * Resolve the absolute path to the Zoo Code global MCP settings file.
 *
 * @returns Absolute path to `mcp_settings.json`.
 *
 * @example
 * // Windows
 * getGlobalMcpSettingsPath()
 * // → C:\Users\k1yt\AppData\Roaming\Code\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json
 */
export function getGlobalMcpSettingsPath(): string {
  const codeUserPath = getCodeUserPath();
  return path.join(
    codeUserPath,
    'globalStorage',
    'zoocodeorganization.zoo-code',
    'settings',
    'mcp_settings.json',
  );
}
