// VibeZoo: 공통 타입 정의

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

export interface YoctoSnapshot {
  id: string;
  sessionId: string;
  timestamp: number;
  trigger: 'manual' | 'auto' | 'yolo-enter' | 'pre-edit';
  files: YoctoFileEntry[];
  crowBackupId?: string;
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
