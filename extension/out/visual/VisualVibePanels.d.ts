import * as vscode from 'vscode';
export declare class VisualVibePanels {
    private whiteboardPanel;
    private uiPreviewPanel;
    private diagramPanel;
    private dropzonePanel;
    private readonly homedir;
    private _activated;
    private _watching;
    private _lastCommandsHash;
    /** Whiteboard가 아직 열리지 않았을 때 대기 중인 드로잉 명령 */
    private _pendingDrawCommands;
    constructor();
    activate(): void;
    dispose(): void;
    /**
     * action 파일의 변경을 감지하여 콜백 실행.
     * @param filePath 감시할 파일 경로
     * @param lastMtime 마지막 mtime 기록 (객체 참조로 유지)
     * @param onChange 파일 내용이 변경되었을 때 실행할 콜백
     */
    private handleFileChange;
    /** 현재 파일의 mtime 반환 (없으면 0) */
    private getCurrentMtime;
    /**
     * 파일 감시 시작 (fs.watchFile 기반).
     * activate()에서 최초 1회 호출.
     */
    private startWatching;
    /** 파일 감시 중단 */
    private stopWatching;
    /** AI 드로잉 명령을 Whiteboard Webview로 전달 */
    private sendToWhiteboard;
    /** Whiteboard 열기 — Fabric.js 기반 드로잉 캔버스 */
    openWhiteboard(): vscode.WebviewPanel;
    /** 사용자 캔버스 상태 저장 (무한 루프 방지를 위해 _source 마커 포함) */
    private handleCanvasState;
    /** 캡처 도구 실행 → 클립보드 이미지를 Whiteboard에 자동 로드 */
    private handleCaptureScreenshot;
    private cleanupTempFile;
    openUIPreview(initialCode?: string, _framework?: string): vscode.WebviewPanel;
    openDiagram(diagramType?: string): vscode.WebviewPanel;
    /** 드랍존 열기 — 드래그앤드롭 / 파일 선택으로 이미지 업로드 */
    openDropzone(): vscode.WebviewPanel;
    /** 드랍존 절대 경로 파일 복사 (VS Code 샌드박스 우회 근본 해결책) */
    private handleLocalFileDrop;
    /** 드랍존 파일 업로드 처리 — Temp 폴더에 저장 */
    private handleDropzoneUpload;
    private whiteboardHtml;
    private uiPreviewHtml;
    private diagramHtml;
    private dropzoneHtml;
}
//# sourceMappingURL=VisualVibePanels.d.ts.map