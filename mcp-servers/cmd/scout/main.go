// VibeZoo: Scout MCP Server (Go)
// 코드 탐색 전문 Subagent. 포트 9022에서 SSE transport로 대기.
// 가장 가볍고 빠른 단일 바이너리로 컴파일된다.

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
	"time"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

var (
	port       = flag.Int("port", 9022, "SSE server port")
	projectDir = flag.String("dir", "", "Project directory (default: CWD)")
)

func main() {
	flag.Parse()

	dir := *projectDir
	if dir == "" {
		var err error
		dir, err = os.Getwd()
		if err != nil {
			log.Fatalf("Failed to get working directory: %v", err)
		}
	}

	s := server.NewMCPServer(
		"scout",
		"1.0.0",
		server.WithToolCapabilities(true),
	)

	// Tool: search_codebase — 프로젝트 코드베이스 검색
	s.AddTool(mcp.NewTool("search_codebase",
		mcp.WithDescription("프로젝트 코드베이스에서 주어진 쿼리와 관련된 코드를 검색합니다."),
		mcp.WithString("query", mcp.Required(), mcp.Description("검색할 내용 (자연어 또는 코드 스니펫)")),
		mcp.WithString("file_patterns", mcp.Description("검색 대상 파일 패턴 (예: *.ts,*.tsx). 쉼표로 구분.")),
		mcp.WithNumber("max_results", mcp.Description("최대 결과 수 (기본: 10)")),
	), searchCodebase(dir))

	// Tool: find_references — 심볼 참조 찾기
	s.AddTool(mcp.NewTool("find_references",
		mcp.WithDescription("주어진 심볼(함수, 클래스, 변수)의 모든 참조를 찾습니다."),
		mcp.WithString("symbol", mcp.Required(), mcp.Description("찾을 심볼 이름")),
		mcp.WithBoolean("include_tests", mcp.Description("테스트 파일 포함 여부")),
	), findReferences(dir))

	// Tool: summarize_architecture — 아키텍처 요약
	s.AddTool(mcp.NewTool("summarize_architecture",
		mcp.WithDescription("주어진 경로의 프로젝트 아키텍처를 분석하여 요약합니다."),
		mcp.WithString("target_path", mcp.Description("분석 대상 디렉토리 경로 (기본: 프로젝트 루트)")),
	), summarizeArchitecture(dir))

	// Tool: list_files — 파일 목록 조회
	s.AddTool(mcp.NewTool("list_files",
		mcp.WithDescription("지정된 디렉토리의 파일 목록을 반환합니다."),
		mcp.WithString("target_path", mcp.Description("대상 디렉토리 경로")),
		mcp.WithNumber("depth", mcp.Description("탐색 깊이 (기본: 2)")),
	), listFiles(dir))

	// Health check endpoint
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"status":  "ok",
			"name":    "scout",
			"version": "1.0.0",
		})
	})

	// SSE transport
	sseServer := server.NewSSEServer(s)
	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	log.Printf("[Scout] Starting on %s (project: %s)", addr, dir)

	go func() {
		if err := sseServer.Start(addr); err != nil {
			log.Fatalf("[Scout] Server error: %v", err)
		}
	}()

	// 대기
	select {}
}

// ── Tool Handlers ─────────────────────────────────────────────

func searchCodebase(dir string) func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	return func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		query, _ := req.Params.Arguments["query"].(string)
		filePatterns, _ := req.Params.Arguments["file_patterns"].(string)
		maxResults := 10
		if v, ok := req.Params.Arguments["max_results"].(float64); ok {
			maxResults = int(v)
		}

		var patterns []string
		if filePatterns != "" {
			patterns = strings.Split(filePatterns, ",")
		} else {
			patterns = []string{"*.ts", "*.tsx", "*.js", "*.jsx", "*.py", "*.go", "*.rs", "*.java"}
		}

		results := grepSearch(dir, query, patterns, maxResults)

		output := fmt.Sprintf("# Search Results for: %s\n\n", query)
		output += fmt.Sprintf("Found %d results in %s\n\n", len(results), dir)
		for _, r := range results {
			output += fmt.Sprintf("- **%s**:%d\n  ```\n  %s\n  ```\n\n", r.File, r.Line, r.Snippet)
		}

		return mcp.NewToolResultText(output), nil
	}
}

func findReferences(dir string) func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	return func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		symbol, _ := req.Params.Arguments["symbol"].(string)

		results := grepSearch(dir, symbol, []string{"*.ts", "*.tsx", "*.js", "*.jsx", "*.py", "*.go", "*.rs"}, 20)

		output := fmt.Sprintf("# References for: %s\n\n", symbol)
		output += fmt.Sprintf("Found %d references\n\n", len(results))
		for _, r := range results {
			output += fmt.Sprintf("- `%s:%d`\n", r.File, r.Line)
		}

		return mcp.NewToolResultText(output), nil
	}
}

func summarizeArchitecture(dir string) func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	return func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		target := dir
		if v, ok := req.Params.Arguments["target_path"].(string); ok && v != "" {
			target = filepath.Join(dir, v)
		}

		output := "# Project Architecture Summary\n\n"

		// 디렉토리 구조 요약
		output += "## Directory Structure\n\n"
		entries := listTopLevel(target, 2)
		for _, e := range entries {
			output += fmt.Sprintf("- %s\n", e)
		}

		// 프로젝트 타입 감지
		output += "\n## Detected Technologies\n\n"
		if exists(filepath.Join(dir, "package.json")) {
			output += "- **Node.js/TypeScript** 프로젝트\n"
		}
		if exists(filepath.Join(dir, "go.mod")) {
			output += "- **Go** 프로젝트\n"
		}
		if exists(filepath.Join(dir, "Cargo.toml")) {
			output += "- **Rust** 프로젝트\n"
		}
		if exists(filepath.Join(dir, "pyproject.toml")) {
			output += "- **Python** 프로젝트\n"
		}

		// 파일 통계
		output += "\n## File Statistics\n\n"
		stats := countFiles(dir)
		for ext, count := range stats {
			output += fmt.Sprintf("- `%s`: %d files\n", ext, count)
		}

		return mcp.NewToolResultText(output), nil
	}
}

func listFiles(dir string) func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	return func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		target := dir
		if v, ok := req.Params.Arguments["target_path"].(string); ok && v != "" {
			target = filepath.Join(dir, v)
		}

		depth := 2
		if v, ok := req.Params.Arguments["depth"].(float64); ok {
			depth = int(v)
		}

		entries := listTopLevel(target, depth)
		return mcp.NewToolResultText(strings.Join(entries, "\n")), nil
	}
}

// ── Helpers ──────────────────────────────────────────────────

type SearchResult struct {
	File    string `json:"file"`
	Line    int    `json:"line"`
	Snippet string `json:"snippet"`
}

func grepSearch(dir, query string, patterns []string, maxResults int) []SearchResult {
	var results []SearchResult

	for _, pattern := range patterns {
		if len(results) >= maxResults {
			break
		}

		// ripgrep이 있으면 사용, 없으면 find+grep 폴백
		rgPath, _ := exec.LookPath("rg")
		var cmd *exec.Cmd
		if rgPath != "" {
			cmd = exec.Command("rg", "--line-number", "--max-count=1", "--max-filesize=1M",
				"-g", pattern, query, dir)
		} else {
			// grep 폴백
			cmd = exec.Command("grep", "-rn", "--include="+strings.ReplaceAll(pattern, "*", ""),
				query, dir)
		}

		cmd.Stderr = nil
		out, err := cmd.Output()
		if err != nil {
			continue
		}

		lines := strings.Split(string(out), "\n")
		for _, line := range lines {
			if len(results) >= maxResults {
				break
			}
			if line == "" {
				continue
			}

			parts := strings.SplitN(line, ":", 3)
			if len(parts) < 3 {
				continue
			}

			file := parts[0]
			relPath, _ := filepath.Rel(dir, file)
			if relPath == "" {
				relPath = file
			}

			results = append(results, SearchResult{
				File:    relPath,
				Line:    atoi(parts[1]),
				Snippet: strings.TrimSpace(parts[2]),
			})
		}
	}

	return results
}

func listTopLevel(dir string, depth int) []string {
	var entries []string
	filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}

		rel, _ := filepath.Rel(dir, path)
		if rel == "." {
			return nil
		}

		parts := strings.Split(rel, string(filepath.Separator))
		if len(parts) > depth {
			if d.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}

		// 제외 디렉토리
		if d.IsDir() {
			base := filepath.Base(path)
			switch base {
			case ".git", "node_modules", ".zoo-code", "dist", "build", ".next", "coverage", "target":
				return filepath.SkipDir
			}
			entries = append(entries, fmt.Sprintf("📁 %s/", rel))
		} else {
			entries = append(entries, fmt.Sprintf("📄 %s", rel))
		}

		return nil
	})
	return entries
}

func countFiles(dir string) map[string]int {
	stats := make(map[string]int)
	filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		ext := filepath.Ext(path)
		if ext == "" {
			ext = "(no ext)"
		}
		stats[ext]++
		return nil
	})
	return stats
}

func exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func atoi(s string) int {
	var n int
	fmt.Sscanf(s, "%d", &n)
	return n
}
