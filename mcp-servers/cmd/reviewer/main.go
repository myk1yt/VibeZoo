// VibeZoo: Reviewer MCP Server (Go) — 코드 리뷰 Subagent (:9023)
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func main() {
	port := flag.Int("port", 9023, "SSE server port")
	flag.Parse()

	s := server.NewMCPServer("reviewer", "1.0.0", server.WithToolCapabilities(true))

	s.AddTool(mcp.NewTool("review_code",
		mcp.WithDescription("지정된 파일의 코드 리뷰를 수행합니다."),
		mcp.WithString("file_path", mcp.Required(), mcp.Description("리뷰할 파일 경로")),
	), reviewCode)

	s.AddTool(mcp.NewTool("check_quality",
		mcp.WithDescription("프로젝트의 코드 품질을 검사합니다 (ESLint, go vet, cargo check 등)."),
		mcp.WithString("target_path", mcp.Description("검사 대상 경로")),
	), checkQuality)

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{"status": "ok", "name": "reviewer"})
	})

	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	sseServer := server.NewSSEServer(s)
	log.Printf("[Reviewer] Starting on %s", addr)
	if err := sseServer.Start(addr); err != nil {
		log.Fatalf("[Reviewer] Server error: %v", err)
	}
	select {}
}

func reviewCode(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	filePath, _ := req.Params.Arguments["file_path"].(string)

	content, err := os.ReadFile(filePath)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Cannot read file: %v", err)), nil
	}

	lines := strings.Split(string(content), "\n")
	output := fmt.Sprintf("# Code Review: %s\n\n", filepath.Base(filePath))
	output += fmt.Sprintf("- **Lines**: %d\n", len(lines))
	output += fmt.Sprintf("- **Size**: %d bytes\n", len(content))

	// 기본 검사
	issues := 0
	for i, line := range lines {
		if len(line) > 120 {
			output += fmt.Sprintf("- ⚠️ Line %d: Too long (%d chars)\n", i+1, len(line))
			issues++
		}
		if strings.Contains(line, "TODO") || strings.Contains(line, "FIXME") {
			output += fmt.Sprintf("- 📝 Line %d: TODO/FIXME: %s\n", i+1, strings.TrimSpace(line))
			issues++
		}
	}

	if issues == 0 {
		output += "\n✅ No obvious issues found.\n"
	}

	return mcp.NewToolResultText(output), nil
}

func checkQuality(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	dir := "."
	if v, ok := req.Params.Arguments["target_path"].(string); ok && v != "" {
		dir = v
	}

	output := "# Code Quality Check\n\n"

	// 프로젝트 타입별 검사
	switch {
	case exists(filepath.Join(dir, "package.json")):
		cmd := exec.Command("npx", "eslint", "--ext", ".ts,.tsx,.js,.jsx", dir, "--format", "compact")
		out, _ := cmd.Output()
		output += "## ESLint\n\n```\n" + string(out) + "\n```\n"

	case exists(filepath.Join(dir, "go.mod")):
		cmd := exec.Command("go", "vet", "./...")
		cmd.Dir = dir
		out, err := cmd.CombinedOutput()
		if err != nil {
			output += "## go vet\n\n```\n" + string(out) + "\n```\n"
		} else {
			output += "## go vet\n\n✅ No issues found.\n"
		}

	default:
		output += "지원되는 프로젝트 타입을 찾을 수 없습니다.\n"
	}

	return mcp.NewToolResultText(output), nil
}

func exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}
