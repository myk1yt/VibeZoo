"use strict";
// VibeZoo Wave 3: Context Intelligence
// Crow Memory freshness 표시, 세션 복원, 설명 패턴 감지, 감정 신호 분석
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.EmotionalDetector = exports.SessionResume = exports.ExplainLessSuggestor = exports.ContextIndicator = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
class ContextIndicator {
    /** Crow Context 복합 지표 계산 및 StatusBar 표시 */
    async getFreshnessStatus() {
        // Crow.bin 접근 가능 여부 + 최근 접근 시간 기반 추정
        const stat = await this.tryStatCrowBin();
        if (!stat)
            return { percentage: 0, icon: '$(error)' };
        const hoursSinceAccess = (Date.now() - stat.atimeMs) / 3600000;
        const recency = Math.max(0, 1 - hoursSinceAccess / 168); // 7일 후 0%
        const percentage = Math.round(recency * 100);
        const icon = percentage > 70 ? '$(check)' : percentage > 30 ? '$(warning)' : '$(error)';
        return { percentage, icon };
    }
    async tryStatCrowBin() {
        try {
            const crowBinPath = path.join(os.homedir(), '.zoo-code', 'crow', 'crow.bin');
            return fs.statSync(crowBinPath);
        }
        catch {
            return null;
        }
    }
}
exports.ContextIndicator = ContextIndicator;
class ExplainLessSuggestor {
    recentMessages = [];
    MAX_HISTORY = 10;
    /** 사용자 입력에서 반복 설명 패턴 감지 */
    analyze(message) {
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
            const count = this.recentMessages.filter((msg) => pattern.keywords.some((kw) => msg.toLowerCase().includes(kw.toLowerCase()))).length;
            if (count >= 3) {
                return `💡 반복 설명 감지: '${pattern.suggestion}'. system_prompt.md에 추가할까요?`;
            }
        }
        return null;
    }
}
exports.ExplainLessSuggestor = ExplainLessSuggestor;
/**
 * SessionResume — WebviewPanel 대신 TreeView 데이터 제공을 위한 클래스
 * Crow Memory 또는 로컬 파일에서 이전 세션 요약 정보를 가져온다.
 */
class SessionResume {
    sessions = [];
    /** 세션 요약을 불러온다 (Crow recall 또는 로컬 파일에서) */
    async refresh() {
        const loaded = [];
        // 1) Crow Memory recall 시도
        try {
            const crowPort = vscode.workspace.getConfiguration('vibezoo').get('crow.port', 9020);
            const resp = await fetch(`http://localhost:${crowPort}/recall?query=session+summary&register=context&limit=10`);
            if (resp.ok) {
                const data = await resp.json();
                if (Array.isArray(data)) {
                    loaded.push(...data.map((item) => this.toSessionSummary(item)));
                }
                else if (data.results && Array.isArray(data.results)) {
                    loaded.push(...data.results.map((item) => this.toSessionSummary(item)));
                }
                else if (data.summary) {
                    loaded.push(this.toSessionSummary(data));
                }
            }
        }
        catch {
            // Crow 연결 실패 — 로컬 파일로 fallback
        }
        // 2) 로컬 세션 히스토리 파일
        if (loaded.length === 0) {
            try {
                const historyPath = path.join(os.homedir(), '.zoo-code', 'session-history.json');
                if (fs.existsSync(historyPath)) {
                    const raw = fs.readFileSync(historyPath, 'utf-8');
                    const parsed = JSON.parse(raw);
                    if (Array.isArray(parsed)) {
                        loaded.push(...parsed.map((item) => this.toSessionSummary(item)));
                    }
                    else if (parsed.sessionId) {
                        loaded.push(this.toSessionSummary(parsed));
                    }
                }
            }
            catch {
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
            }
            catch {
                // 무시
            }
        }
        this.sessions = loaded;
        return this.sessions;
    }
    getSessions() {
        return this.sessions;
    }
    toSessionSummary(raw) {
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
    parseTimestampFromName(name) {
        const match = name.match(/(\d{13})/);
        if (match)
            return parseInt(match[1], 10);
        const match2 = name.match(/session[-_]?(\d+)/);
        if (match2)
            return parseInt(match2[1], 10);
        return Date.now();
    }
    dispose() {
        this.sessions = [];
    }
}
exports.SessionResume = SessionResume;
class EmotionalDetector {
    rejectionPatterns = [
        { keywords: ['아니', '아니야', '아닌데', 'no', 'nope'], weight: 0.6 },
        { keywords: ['그렇게 하지 마', '하지 마', "don't", 'stop'], weight: 0.8 },
        { keywords: ['다시 해', '다시', 'retry', 'again'], weight: 0.5 },
        { keywords: ['이건 아니야', '이게 아닌데', 'wrong', 'not this'], weight: 0.9 },
    ];
    consecutiveRejections = 0;
    /** 사용자 메시지의 감정 신호 분석 */
    analyze(message) {
        const isRejection = this.rejectionPatterns.some((pattern) => pattern.keywords.some((kw) => message.toLowerCase().includes(kw.toLowerCase())));
        // 긍정 키워드가 우선: 거절+긍정 중첩 시 긍정으로 분류
        if (this.isPositive(message)) {
            this.consecutiveRejections = 0;
        }
        else if (isRejection) {
            this.consecutiveRejections++;
        }
        else {
            // 중립 메시지는 카운터 유지 (급격한 리셋 방지)
            if (this.consecutiveRejections > 0) {
                this.consecutiveRejections = Math.max(0, this.consecutiveRejections - 1);
            }
        }
        let tone = 'neutral';
        if (this.consecutiveRejections >= 3)
            tone = 'frustrated';
        else if (this.consecutiveRejections >= 1)
            tone = 'urgent';
        else if (this.isPositive(message))
            tone = 'satisfied';
        return { tone, rejectionStreak: this.consecutiveRejections };
    }
    isPositive(message) {
        const positive = ['좋아', '굿', 'good', 'thanks', 'perfect', 'exactly', 'great', '감사', '고마워'];
        return positive.some((p) => message.toLowerCase().includes(p.toLowerCase()));
    }
}
exports.EmotionalDetector = EmotionalDetector;
//# sourceMappingURL=ContextIntelligence.js.map