// VibeZoo: Tester MCP Server (Go) — 테스트 생성 Subagent (:9024)
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func main() {
	port := flag.Int("port", 9024, "SSE server port")
	flag.Parse()

	s := server.NewMCPServer("tester", "1.0.0", server.WithToolCapabilities(true))

	s.AddTool(mcp.NewTool("generate_tests",
		mcp.WithDescription("지정된 소스 파일에 대한 단위 테스트를 생성합니다."),
		mcp.WithString("source_path", mcp.Required(), mcp.Description("테스트 대상 소스 파일 경로")),
		mcp.WithString("framework", mcp.Description("테스트 프레임워크 (jest, vitest, pytest, go test). 자동 감지됨.")),
	), generateTests)

	s.AddTool(mcp.NewTool("analyze_coverage",
		mcp.WithDescription("테스트 커버리지를 분석합니다."),
		mcp.WithString("target_path", mcp.Description("분석 대상 경로")),
	), analyzeCoverage)

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{"status": "ok", "name": "tester"})
	})

	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	sseServer := server.NewSSEServer(s)
	log.Printf("[Tester] Starting on %s", addr)
	if err := sseServer.Start(addr); err != nil {
		log.Fatalf("[Tester] Server error: %v", err)
	}
	select {}
}

func generateTests(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	sourcePath, _ := req.Params.Arguments["source_path"].(string)

	output := "# Test Generation\n\n"
	output += fmt.Sprintf("Source: %s\n\n", sourcePath)
	output += "테스트 생성은 LLM에 의해 수행됩니다. Scout의 검색 결과와 Crow Memory의 " +
		"프로젝트 컨텍스트를 참조하여 적절한 테스트를 생성하세요.\n"

	return mcp.NewToolResultText(output), nil
}

func analyzeCoverage(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	output := "# Coverage Analysis\n\n"
	output += "커버리지 분석 결과가 여기에 표시됩니다.\n"

	return mcp.NewToolResultText(output), nil
}
