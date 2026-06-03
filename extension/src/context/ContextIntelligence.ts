// VibeZoo Wave 3: Context Intelligence
// Crow Memory freshness 표시, 세션 복원, 설명 패턴 감지, 감정 신호 분석

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { SessionSummary } from '../types';
import { ConfigService } from '../config/ConfigService';

export class ContextIndicator {
  /** Crow Context 복합 지표 계산 및 StatusBar 표시 */
  async getFreshnessStatus(): Promise<{ percentage: number; icon: string }> {
    // Crow.bin 접근 가능 여부 + 최근 접근 시간 기반 추정
    const stat = await this.tryStatCrowBin();
    if (!stat) return { percentage: 0, icon: '$(error)' };

    const hoursSinceAccess = (Date.now() - stat.atimeMs) / 3600000;
    const recency = Math.max(0, 1 - hoursSinceAccess / 168); // 7일 후 0%
    const percentage = Math.round(recency * 100);

    const icon = percentage > 70 ? '$(check)' : percentage > 30 ? '$(warning)' : '$(error)';
    return { percentage, icon };
  }

  private async tryStatCrowBin(): Promise<{ atimeMs: number } | null> {
    try {
      const crowBinPath = path.join(os.homedir(), '.zoo-code', 'crow', 'crow.bin');
      return fs.statSync(crowBinPath);
    } catch {
      return null;
    }
  }
}

export class ExplainLessSuggestor {
  private recentMessages: string[] = [];
  private readonly MAX_HISTORY = 10;

  /** 사용자 입력에서 반복 설명 패턴 감지 */
  analyze(message: string): string | null {
    this.recentMessages.push(message);
    if (this.recentMessages.length > this.MAX_HISTORY) {
      this.recentMessages.shift();
    }

    // Detect recurring keywords
    const patterns = [
      { keywords: ['zustand', 'redux', 'state management'], suggestion: 'State management: use Zustand' },
      { keywords: ['try-catch', 'error', 'error handling'], suggestion: 'Error handling: try-catch wrapping' },
      { keywords: ['tailwind', 'css', 'style'], suggestion: 'Style: use Tailwind CSS' },
      { keywords: ['async', 'await', 'asynchronous'], suggestion: 'Async: use async/await pattern' },
    ];

    for (const pattern of patterns) {
      const count = this.recentMessages.filter((msg) =>
        pattern.keywords.some((kw) => msg.toLowerCase().includes(kw.toLowerCase()))
      ).length;

      if (count >= 3) {
        return `💡 Repetitive explanation detected: '${pattern.suggestion}'. Should we add this to system_prompt.md?`;
      }
    }

    return null;
  }
}

/**
 * SessionResume — WebviewPanel 대신 TreeView 데이터 제공을 위한 클래스
 * Crow Memory 또는 로컬 파일에서 이전 세션 요약 정보를 가져온다.
 */
export class SessionResume {
  private sessions: SessionSummary[] = [];

  /** 세션 요약을 불러온다 (Crow recall 또는 로컬 파일에서) */
  async refresh(): Promise<SessionSummary[]> {
    const loaded: SessionSummary[] = [];

    // 1) Crow Memory recall 시도
    try {
      const resp = await fetch(ConfigService.getCrowUrl('/recall?query=session+summary&register=context&limit=10'));
      if (resp.ok) {
        const data: any = await resp.json();
        if (Array.isArray(data)) {
          loaded.push(...data.map((item: any) => this.toSessionSummary(item)));
        } else if (data.results && Array.isArray(data.results)) {
          loaded.push(...data.results.map((item: any) => this.toSessionSummary(item)));
        } else if (data.summary) {
          loaded.push(this.toSessionSummary(data));
        }
      }
    } catch {
      // Crow 연결 실패 — 로컬 파일로 fallback
    }

    // 2) 로컬 세션 히스토리 파일
    if (loaded.length === 0) {
      try {
        const historyPath = path.join(os.homedir(), '.zoo-code', 'session-history.json');
        if (fs.existsSync(historyPath)) {
          const raw = fs.readFileSync(historyPath, 'utf-8');
          const parsed: any = JSON.parse(raw);
          if (Array.isArray(parsed)) {
            loaded.push(...parsed.map((item: any) => this.toSessionSummary(item)));
          } else if (parsed.sessionId) {
            loaded.push(this.toSessionSummary(parsed));
          }
        }
      } catch {
        // 파일 읽기 실패
      }
    }

    // 3) YOLO yocto 디렉토리에서 세션 폴더 스캔 (fallback)
    if (loaded.length === 0) {
      try {
        const yoctoDir = path.join(os.homedir(), '.zoo-code', 'yocto');
        if (fs.existsSync(yoctoDir)) {
          const entries = fs.readdirSync(yoctoDir, { withFileTypes: true });
          for (const entry of entries.sort((a, b) => b.name.localeCompare(a.name)).slice(0, 10)) {
            if (entry.isDirectory()) {
              loaded.push({
                sessionId: entry.name,
                projectPath: '',
                startedAt: this.parseTimestampFromName(entry.name),
                endedAt: this.parseTimestampFromName(entry.name),
                summary: 'YOLO 백업 세션',
                keyDecisions: [],
                touchedFiles: [],
                pendingTasks: [],
                mode: 'unknown',
              });
            }
          }
        }
      } catch {
        // 무시
      }
    }

    this.sessions = loaded;
    return this.sessions;
  }

  getSessions(): SessionSummary[] {
    return this.sessions;
  }

  private toSessionSummary(raw: any): SessionSummary {
    return {
      sessionId: raw.sessionId || raw.id || `session-${Date.now()}`,
      projectPath: raw.projectPath || raw.project_path || '',
      startedAt: raw.startedAt || raw.started_at || Date.now(),
      endedAt: raw.endedAt || raw.ended_at || Date.now(),
      summary: raw.summary || raw.description || '',
      keyDecisions: raw.keyDecisions || raw.key_decisions || [],
      touchedFiles: raw.touchedFiles || raw.touched_files || [],
      pendingTasks: raw.pendingTasks || raw.pending_tasks || [],
      mode: raw.mode || 'unknown',
    };
  }

  private parseTimestampFromName(name: string): number {
    const match = name.match(/(\d{13})/);
    if (match) return parseInt(match[1], 10);
    const match2 = name.match(/session[-_]?(\d+)/);
    if (match2) return parseInt(match2[1], 10);
    return Date.now();
  }

  dispose(): void {
    this.sessions = [];
  }
}

export class EmotionalDetector {
  private rejectionPatterns = [
    { keywords: ['no', 'nope', 'incorrect', 'not what i meant'], weight: 0.6 },
    { keywords: ['don\'t do that', 'stop', "don't", 'halt'], weight: 0.8 },
    { keywords: ['do it again', 'retry', 'again', 'redo'], weight: 0.5 },
    { keywords: ['this is wrong', 'wrong', 'not this'], weight: 0.9 },
  ];

  private consecutiveRejections: number = 0;

  /** Analyze emotional signals in user message */
  analyze(message: string): { tone: 'neutral' | 'frustrated' | 'satisfied' | 'urgent'; rejectionStreak: number } {
    const isRejection = this.rejectionPatterns.some((pattern) =>
      pattern.keywords.some((kw) => message.toLowerCase().includes(kw.toLowerCase()))
    );

    // Positive keywords override rejections
    if (this.isPositive(message)) {
      this.consecutiveRejections = 0;
    } else if (isRejection) {
      this.consecutiveRejections++;
    } else {
      // Keep neutral messages from resetting streak instantly
      if (this.consecutiveRejections > 0) {
        this.consecutiveRejections = Math.max(0, this.consecutiveRejections - 1);
      }
    }

    let tone: 'neutral' | 'frustrated' | 'satisfied' | 'urgent' = 'neutral';
    if (this.consecutiveRejections >= 3) tone = 'frustrated';
    else if (this.consecutiveRejections >= 1) tone = 'urgent';
    else if (this.isPositive(message)) tone = 'satisfied';

    return { tone, rejectionStreak: this.consecutiveRejections };
  }

  private isPositive(message: string): boolean {
    const positive = ['good', 'thanks', 'perfect', 'exactly', 'great', 'awesome', 'thank you'];
    return positive.some((p) => message.toLowerCase().includes(p.toLowerCase()));
  }
}
