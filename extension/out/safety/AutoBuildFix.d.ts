export interface AutoBuildFixResult {
    status: 'success' | 'failed';
    attempt: number;
}
export declare class AutoBuildFix {
    run(_result: any): Promise<AutoBuildFixResult>;
}
//# sourceMappingURL=AutoBuildFix.d.ts.map