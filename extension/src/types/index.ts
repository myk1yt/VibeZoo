// VibeZoo: 공통 타입 정의

// ── MCP Server (Task 4) ────────────────────────────────────

/**
 * Zoo Code MCP 서버 정의.
 * `.roo/mcp.json`의 개별 MCP 서버 엔트리 타입.
 */
export interface McpServerDefinition {
  /** SSE 연결 URL (e.g. http://127.0.0.1:9027/sse) */
  url: string;
  /** MCP 서버 타입 (sse, streamable-http 등) */
  type?: string;
  /** 전송 프로토콜 (현재는 sse만 지원) */
  transport?: string;
  /** Zoo Code 향후 호환: 비활성화 플래그 */
  disabled?: boolean;
  /** 글로벌 MCP 서버 플래그 (모든 워크스페이스에서 표시) */
  global?: boolean;
  /** 자동 시작 플래그 — VS Code 시작 시 MCP 서버 자동 실행 */
  autoStart?: boolean;
  /** 자동 시작 시 실행할 명령어 */
  autoStartCommand?: string;
  /** 항상 허용할 도구 목록 (사용자 확인 없이 실행) */
  alwaysAllow?: string[];
  /** 자동 승인 도구 목록 */
  autoApprove?: string[];
}

/**
 * Zoo Code MCP 설정 파일(mcp_settings.json / .roo/mcp.json)의 최상위 구조.
 */
export interface McpSettings {
  mcpServers: Record<string, McpServerDefinition>;
}

/**
 * Crow Memory 감지 설정.
 * VibeZoo는 Crow 서버를 직접 실행하지 않고, Zoo Code가 관리하는 Crow 서버를 감지만 한다.
 */
export interface CrowServerConfig {
  /** Crow HTTP 서버 포트 (기본 9020) */
  port: number;
  /** 헬스체크 주기 (ms) */
  healthCheckIntervalMs: number;
}

/**
 * Python 인터프리터 탐색 결과 (Task 1 — PythonResolver).
 * resolve()가 반환하는 candidate에는 command + source + version이 포함된다.
 */
export interface PythonCommandCandidate {
  /** 실제 spawn/exec에 사용할 명령어 (e.g. "python", "python3", "py", 또는 전체 경로) */
  command: string;
  /** 탐색 출처 (우선순위 순) */
  source: 'setting' | 'venv' | 'pyenv' | 'conda' | 'path' | 'fallback';
  /** 검증된 Python 버전 (e.g. "3.11.5"), 검증 실패 시 undefined */
  version?: string;
}

export interface YoctoSnapshot {
  id: string;
  sessionId: string;
  timestamp: number;
  trigger: 'manual' | 'auto' | 'yolo-enter' | 'pre-edit';
  files: YoctoFileEntry[];
  crowBackupId?: string;
  isBase?: boolean;
}

// ── SelfCheck (Phase 0) ───────────────────────────────────

export interface SelfCheckReport {
  overall: 'healthy' | 'degraded' | 'critical';
  checks: SelfCheckItem[];
  timestamp: number;
  version: string;
}

export interface SelfCheckItem {
  name: string;
  status: 'passed' | 'warning' | 'failed';
  message: string;
  detail?: string;
  autoRecoverable?: boolean;
}

// ── NotificationThrottle (Phase 0) ────────────────────────

export interface ThrottleEntry {
  key: string;
  lastShown: number;
  count: number;
}

export interface YoctoFileEntry {
  originalPath: string;
  backupPath: string;
  hash: string;
  size: number;
  mtime: number;
}

export interface BuildResult {
  taskName: string;
  exitCode: number;
  stderr: string;
  stdout: string;
  timestamp: number;
  diagnostics: Diagnostic[];
  projectRoot: string;
}

export interface Diagnostic {
  file: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  code: string;
  source: string;
}

// ── Error Collection (P3/P4) ─────────────────────────────

export type FixLoopSource = 'build' | 'mcp_error';

export interface McpErrorInfo {
  /** 에러가 발생한 MCP 도구 이름 */
  toolName: string;
  /** 예외 타입 (e.g. "TypeError") */
  exceptionType: string;
  /** 예외 메시지 */
  exceptionMessage: string;
  /** 도구 호출 시 사용된 파라미터 */
  parameters: Record<string, any>;
  /** ErrorRegistry에서 할당된 entry ID */
  entryId: string;
}

export interface ProjectInfo {
  type: 'node' | 'rust' | 'go' | 'python' | 'java' | 'unknown';
  rootPath: string;
  buildCommand: string;
  problemMatcher: string;
  framework?: string;
}

export interface SubagentNode {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  currentTask?: string;
  progress?: number;
  startTime?: number;
  elapsedMs?: number;
  port: number;
}

export interface SessionSummary {
  sessionId: string;
  projectPath: string;
  startedAt: number;
  endedAt: number;
  summary: string;
  keyDecisions: string[];
  touchedFiles: string[];
  pendingTasks: string[];
  mode: string;
}

export interface EmotionalState {
  tone: 'neutral' | 'frustrated' | 'satisfied' | 'urgent';
  confidence: number;
  rejectionStreak: number;
  lastUserMessage: string;
}

export interface PermissionLevel {
  read: 1 | 2 | 3 | 4 | 5;
  create: 1 | 2 | 3 | 4 | 5;
  modify: 1 | 2 | 3 | 4 | 5;
  execute: 1 | 2 | 3 | 4 | 5;
  delete: 1 | 2 | 3 | 4 | 5;
}

export type ActionType = 'read' | 'create' | 'modify' | 'execute' | 'delete';

export interface PermissionDecision {
  decision: 'allow' | 'deny' | 'ask';
  reason: string;
  requiresUserConfirm?: boolean;
}

// ── Guard.git (v0.14.3) ──────────────────────────────────

export type GuardGitState = 'active' | 'inactive' | 'error' | 'warning';

export interface GuardGitACLResult {
  success: boolean;
  error?: string;
  command?: string;
  stdout?: string;
  stderr?: string;
}

export interface GuardGitIntegrity {
  exists: boolean;
  protected: boolean;
  headRef: string | null;
  objectCount: number;
  refCount: number;
}
