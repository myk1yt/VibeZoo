import * as vscode from 'vscode';

export class ConfigService {
    public static getHost(): string {
        return vscode.workspace.getConfiguration('vibezoo').get('network.host', '127.0.0.1');
    }

    public static getBridgePort(): number {
        return vscode.workspace.getConfiguration('vibezoo').get('bridge.port', 9027);
    }

    public static getBridgeUrl(path: string = ''): string {
        return `http://${this.getHost()}:${this.getBridgePort()}${path}`;
    }

    public static getCrowPort(): number {
        return vscode.workspace.getConfiguration('vibezoo').get('crow.port', 9020);
    }

    public static getCrowUrl(path: string = ''): string {
        return `http://${this.getHost()}:${this.getCrowPort()}${path}`;
    }

    public static getAgentUrl(port: number, path: string = ''): string {
        return `http://${this.getHost()}:${port}${path}`;
    }

    public static getAgentPorts(): Array<{ id: string; name: string; port: number }> {
        const config = vscode.workspace.getConfiguration('vibezoo');
        return [
            { id: 'scout', name: 'Scout', port: config.get('scout.port', 9022) },
            { id: 'reviewer', name: 'Reviewer', port: config.get('reviewer.port', 9023) },
            { id: 'tester', name: 'Tester', port: config.get('tester.port', 9024) },
            { id: 'deepAnalyzer', name: 'Deep Analyzer', port: config.get('deepAnalyzer.port', 9026) },
        ];
    }
}
