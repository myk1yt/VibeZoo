// VibeZoo Wave 3: Context Intelligence
// Crow Memory freshness 표시, 세션 복원, 설명 패턴 감지, 감정 신호 분석

import * as vscode from 'vscode';

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
      const fs = require('fs');
      const path = require('path');
      const os = require('os');
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

    // 반복되는 키워드 감지
    const patterns = [
      { keywords: ['zustand', 'redux', '상태관리'], suggestion: '상태관리: Zustand 사용' },
      { keywords: ['try-catch', '에러', 'error handling'], suggestion: '에러 핸들링: try-catch 래핑' },
      { keywords: ['tailwind', 'css', '스타일'], suggestion: '스타일: Tailwind CSS 사용' },
      { keywords: ['async', 'await', '비동기'], suggestion: '비동기: async/await 패턴' },
    ];

    for (const pattern of patterns) {
      const count = this.recentMessages.filter((msg) =>
        pattern.keywords.some((kw) => msg.toLowerCase().includes(kw.toLowerCase()))
      ).length;

      if (count >= 3) {
        return `💡 반복 설명 감지: '${pattern.suggestion}'. system_prompt.md에 추가할까요?`;
      }
    }

    return null;
  }
}

export class SessionResume {
  private panel: vscode.WebviewPanel | null = null;

  /** 이전 세션 요약을 Webview로 표시 */
  async show(context: vscode.ExtensionContext): Promise<void> {
    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.Two);
      return;
    }

    this.panel = vscode.window.createWebviewPanel(
      'vibezoo-session-resume',
      'VibeZoo: Session Resume',
      vscode.ViewColumn.Two,
      {
        enableScripts: false,
        retainContextWhenHidden: true,
      }
    );

    this.panel.webview.html = this.buildHtml();

    this.panel.onDidDispose(() => {
      this.panel = null;
    });
  }

  private buildHtml(): string {
    return `<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); }
    h2 { color: var(--vscode-textLink-foreground); }
    .summary { background: var(--vscode-textCodeBlock-background); padding: 12px; border-radius: 6px; }
    .files { margin-top: 12px; }
    .file { padding: 4px 0; color: var(--vscode-textPreformat-foreground); }
  </style>
</head>
<body>
  <h2>🔄 VibeZoo Session Resume</h2>
  <p>이전 세션의 작업 맥락을 복원합니다.</p>
  <div class="summary">
    <p>Crow Memory가 기억하는 마지막 세션 정보가 여기에 표시됩니다.</p>
  </div>
  <div class="files">
    <p><em>Crow Memory에서 마지막 세션 요약을 불러오는 중...</em></p>
  </div>
</body>
</html>`;
  }

  dispose(): void {
    this.panel?.dispose();
  }
}

export class EmotionalDetector {
  private rejectionPatterns = [
    { keywords: ['아니', '아니야', '아닌데', 'no', 'nope'], weight: 0.6 },
    { keywords: ['그렇게 하지 마', '하지 마', "don't", 'stop'], weight: 0.8 },
    { keywords: ['다시 해', '다시', 'retry', 'again'], weight: 0.5 },
    { keywords: ['이건 아니야', '이게 아닌데', 'wrong', 'not this'], weight: 0.9 },
  ];

  private consecutiveRejections: number = 0;

  /** 사용자 메시지의 감정 신호 분석 */
  analyze(message: string): { tone: 'neutral' | 'frustrated' | 'satisfied' | 'urgent'; rejectionStreak: number } {
    const isRejection = this.rejectionPatterns.some((pattern) =>
      pattern.keywords.some((kw) => message.toLowerCase().includes(kw.toLowerCase()))
    );

    if (isRejection) {
      this.consecutiveRejections++;
    } else if (this.isPositive(message)) {
      this.consecutiveRejections = 0;
    } else {
      // 중립 메시지는 카운터 유지 (급격한 리셋 방지)
      if (this.consecutiveRejections > 0) {
        this.consecutiveRejections = Math.max(0, this.consecutiveRejections - 0.5);
      }
    }

    let tone: 'neutral' | 'frustrated' | 'satisfied' | 'urgent' = 'neutral';
    if (this.consecutiveRejections >= 3) tone = 'frustrated';
    else if (this.consecutiveRejections >= 1) tone = 'urgent';
    else if (this.isPositive(message)) tone = 'satisfied';

    return { tone, rejectionStreak: this.consecutiveRejections };
  }

  private isPositive(message: string): boolean {
    const positive = ['좋아', '굿', 'good', 'thanks', 'perfect', 'exactly', 'great', '감사', '고마워'];
    return positive.some((p) => message.toLowerCase().includes(p.toLowerCase()));
  }
}
