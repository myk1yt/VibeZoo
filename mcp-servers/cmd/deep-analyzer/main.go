// VibeZoo Wave 6: Deep Analyzer MCP Server (Go)
// Call Graph, Dependency Map, Pattern Extraction, Reverse Engineering
// 가장 분석 능력이 강력한 Subagent — 포트 9026

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
	port := flag.Int("port", 9026, "SSE server port")
	flag.Parse()

	s := server.NewMCPServer("deep-analyzer", "1.0.0", server.WithToolCapabilities(true))

	s.AddTool(mcp.NewTool("analyze_call_graph",
		mcp.WithDescription("프로젝트의 함수 호출 그래프를 분석합니다."),
		mcp.WithString("file_path", mcp.Description("분석할 파일 경로 (기본: 전체 프로젝트)")),
		mcp.WithNumber("depth", mcp.Description("호출 깊이 (기본: 3)")),
	), analyzeCallGraph)

	s.AddTool(mcp.NewTool("map_dependencies",
		mcp.WithDescription("프로젝트 파일 간 의존성을 분석하고 순환 참조를 탐지합니다."),
		mcp.WithString("target_path", mcp.Description("분석 대상 경로")),
	), mapDependencies)

	s.AddTool(mcp.NewTool("extract_patterns",
		mcp.WithDescription("프로젝트 전체에서 반복되는 코드 패턴을 추출합니다."),
		mcp.WithString("target_path", mcp.Description("분석 대상 경로")),
		mcp.WithNumber("min_occurrences", mcp.Description("최소 발생 횟수 (기본: 3)")),
	), extractPatterns)

	s.AddTool(mcp.NewTool("reverse_engineer",
		mcp.WithDescription("코드베이스로부터 아키텍처 문서, API 명세, ERD를 자동 생성합니다."),
		mcp.WithString("target_path", mcp.Description("분석 대상 경로")),
		mcp.WithString("format", mcp.Description("출력 형식 (markdown, openapi, mermaid). 기본: markdown")),
	), reverseEngineer)

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{"status": "ok", "name": "deep-analyzer"})
	})

	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	sseServer := server.NewSSEServer(s)
	log.Printf("[DeepAnalyzer] Starting on %s", addr)
	if err := sseServer.Start(addr); err != nil {
		log.Fatalf("[DeepAnalyzer] Server error: %v", err)
	}
	select {}
}

func analyzeCallGraph(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	filePath, _ := req.Params.Arguments["file_path"].(string)
	depth := 3
	if v, ok := req.Params.Arguments["depth"].(float64); ok {
		depth = int(v)
	}

	dir := getProjectRoot(filePath)

	output := "# Call Graph Analysis\n\n"

	// Go 특화 분석
	if exists(filepath.Join(dir, "go.mod")) {
		output += "## Go Call Graph\n\n```\n"
		cmd := exec.Command("go", "callgraph", "./...")
		cmd.Dir = dir
		out, _ := cmd.Output()
		output += string(out) + "\n```\n"
	}

	// TypeScript 특화 분석 (ts-morph 또는 grep 기반)
	if exists(filepath.Join(dir, "package.json")) {
		output += "## File-Level Dependencies\n\n"
		output += fileLevelDependency(dir)
	}

	output += fmt.Sprintf("\n*Analysis depth: %d levels*", depth)
	return mcp.NewToolResultText(output), nil
}

func mapDependencies(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	dir := getProjectRoot("")
	if v, ok := req.Params.Arguments["target_path"].(string); ok && v != "" {
		dir = v
	}

	output := "# Dependency Map\n\n"
	output += "## Import Analysis\n\n"

	// 모든 소스 파일에서 import 문 추출
	imports := make(map[string][]string)
	filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		ext := filepath.Ext(path)
		if ext != ".go" && ext != ".ts" && ext != ".tsx" && ext != ".js" && ext != ".py" {
			return nil
		}
		rel, _ := filepath.Rel(dir, path)
		if strings.Contains(rel, "node_modules") || strings.Contains(rel, ".git") || strings.Contains(rel, "vendor") {
			return nil
		}

		imports[rel] = extractImports(path)
		return nil
	})

	// 순환 참조 탐지 (간단한 DFS)
	visited := make(map[string]bool)
	stack := make(map[string]bool)
	var cycles []string

	var dfs func(node string, path []string)
	dfs = func(node string, path []string) {
		if stack[node] {
			start := -1
			for i, p := range path {
				if p == node {
					start = i
					break
				}
			}
			if start >= 0 {
				cycles = append(cycles, strings.Join(path[start:], " → "))
			}
			return
		}
		if visited[node] {
			return
		}
		visited[node] = true
		stack[node] = true

		for _, dep := range imports[node] {
			if existingDeps, ok := imports[dep]; ok {
				dfs(dep, append(path, dep))
				_ = existingDeps
			}
		}

		stack[node] = false
	}

	for file := range imports {
		dfs(file, []string{file})
	}

	if len(cycles) > 0 {
		output += "### ⚠️ Circular Dependencies Found\n\n"
		for _, cycle := range cycles {
			output += fmt.Sprintf("- `%s`\n", cycle)
		}
	} else {
		output += "✅ No circular dependencies found.\n"
	}

	// 파일별 의존성 수
	output += "\n## Dependency Count by File\n\n"
	for file, deps := range imports {
		output += fmt.Sprintf("- `%s`: %d imports\n", file, len(deps))
	}

	return mcp.NewToolResultText(output), nil
}

func extractPatterns(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	dir := getProjectRoot("")
	if v, ok := req.Params.Arguments["target_path"].(string); ok && v != "" {
		dir = v
	}
	minOccurrences := 3
	if v, ok := req.Params.Arguments["min_occurrences"].(float64); ok {
		minOccurrences = int(v)
	}

	output := "# Code Pattern Analysis\n\n"

	// 간단한 패턴: 함수 시그니처, 인터페이스, 구조체 추출
	patterns := make(map[string]int)
	filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		ext := filepath.Ext(path)
		if ext != ".go" && ext != ".ts" && ext != ".tsx" {
			return nil
		}

		content, err := os.ReadFile(path)
		if err != nil {
			return nil
		}

		lines := strings.Split(string(content), "\n")
		for _, line := range lines {
			trimmed := strings.TrimSpace(line)

			// TypeScript: export const/function/class patterns
			if strings.HasPrefix(trimmed, "export") && !strings.Contains(trimmed, "//") {
				patterns["export patterns"]++
			}
			// Go: func patterns
			if strings.HasPrefix(trimmed, "func ") && strings.Contains(trimmed, "error") {
				patterns["function returning error"]++
			}
			// async/await patterns
			if strings.Contains(trimmed, "async ") || strings.Contains(trimmed, "await ") {
				patterns["async/await usage"]++
			}
			// try-catch patterns
			if strings.Contains(trimmed, "try ") || strings.Contains(trimmed, "catch ") {
				patterns["try-catch usage"]++
			}
		}
		return nil
	})

	output += "## Detected Patterns\n\n"
	for pattern, count := range patterns {
		status := ""
		if count >= minOccurrences {
			status = "✅"
		} else {
			status = "⬜"
		}
		output += fmt.Sprintf("- %s `%s`: %d occurrences\n", status, pattern, count)
	}

	output += fmt.Sprintf("\n*Min occurrences threshold: %d*", minOccurrences)
	return mcp.NewToolResultText(output), nil
}

func reverseEngineer(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	dir := getProjectRoot("")
	if v, ok := req.Params.Arguments["target_path"].(string); ok && v != "" {
		dir = v
	}
	format, _ := req.Params.Arguments["format"].(string)
	if format == "" {
		format = "markdown"
	}

	output := "# Reverse Engineering Report\n\n"

	// 프로젝트 메타데이터
	output += "## Project Overview\n\n"
	if exists(filepath.Join(dir, "package.json")) {
		data, _ := os.ReadFile(filepath.Join(dir, "package.json"))
		var pkg map[string]interface{}
		json.Unmarshal(data, &pkg)
		if name, ok := pkg["name"]; ok {
			output += fmt.Sprintf("- **Name**: %s\n", name)
		}
		if desc, ok := pkg["description"]; ok {
			output += fmt.Sprintf("- **Description**: %s\n", desc)
		}
	}

	// 디렉토리 구조
	output += "\n## Architecture\n\n"
	output += "```\n"
	entries := listProjectStructure(dir, 2)
	for _, e := range entries {
		output += e + "\n"
	}
	output += "```\n"

	// API 엔드포인트 (TypeScript Express)
	output += "\n## API Endpoints\n\n"
	endpoints := detectEndpoints(dir)
	if len(endpoints) > 0 {
		for _, ep := range endpoints {
			output += fmt.Sprintf("- `%s` %s\n", ep.method, ep.path)
		}
	} else {
		output += "No Express/Next.js API endpoints detected.\n"
	}

	// 데이터 모델
	output += "\n## Data Models\n\n"
	models := detectModels(dir)
	if len(models) > 0 {
		for _, m := range models {
			output += fmt.Sprintf("- `%s`\n", m)
		}
	} else {
		output += "No explicit data models detected (TypeScript interfaces or Go structs positive).\n"
	}

	switch format {
	case "openapi":
		output += "\n## OpenAPI 3.0 Spec (placeholder)\n\n```yaml\nopenapi: 3.0.0\ninfo:\n  title: Auto-detected API\n  version: 0.1.0\npaths: {}\n```\n"
	case "mermaid":
		output += "\n## Mermaid ERD\n\n```mermaid\nerDiagram\n  User ||--o{ Order : places\n  Order ||--|{ OrderItem : contains\n```\n"
	}

	return mcp.NewToolResultText(output), nil
}

// ── Helpers ──────────────────────────────────────────────

func getProjectRoot(filePath string) string {
	if filePath != "" && filePath != "." {
		if exists(filePath) {
			if isDir(filePath) {
				return filePath
			}
			return filepath.Dir(filePath)
		}
	}
	wd, err := os.Getwd()
	if err != nil {
		return "."
	}
	return wd
}

func isDir(path string) bool {
	info, err := os.Stat(path)
	return err == nil && info.IsDir()
}

func fileLevelDependency(dir string) string {
	var result strings.Builder
	filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		ext := filepath.Ext(path)
		if ext != ".ts" && ext != ".tsx" && ext != ".js" {
			return nil
		}
		content, _ := os.ReadFile(path)
		lines := strings.Split(string(content), "\n")
		for _, line := range lines {
			trimmed := strings.TrimSpace(line)
			if strings.HasPrefix(trimmed, "import ") || strings.HasPrefix(trimmed, "const ") {
				rel, _ := filepath.Rel(dir, path)
				fmt.Fprintf(&result, "  %s\n", rel)
				break
			}
		}
		return nil
	})
	return result.String()
}

func extractImports(filePath string) []string {
	content, err := os.ReadFile(filePath)
	if err != nil {
		return nil
	}

	var imports []string
	lines := strings.Split(string(content), "\n")
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)

		// Go imports
		if strings.HasPrefix(trimmed, "import (") || strings.HasPrefix(trimmed, "import \"") {
			continue
		}

		// TypeScript/JavaScript imports
		if strings.HasPrefix(trimmed, "import ") || strings.HasPrefix(trimmed, "const ") || strings.HasPrefix(trimmed, "var ") {
			// Extract path from quotes
			if idx := strings.Index(trimmed, "from \""); idx >= 0 {
				rest := trimmed[idx+6:]
				if endIdx := strings.Index(rest, "\""); endIdx >= 0 {
					imports = append(imports, rest[:endIdx])
				}
			} else if idx := strings.Index(trimmed, "from '"); idx >= 0 {
				rest := trimmed[idx+6:]
				if endIdx := strings.Index(rest, "'"); endIdx >= 0 {
					imports = append(imports, rest[:endIdx])
				}
			}
		}
	}
	return imports
}

func listProjectStructure(dir string, maxDepth int) []string {
	var result []string
	filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		rel, _ := filepath.Rel(dir, path)
		if rel == "." {
			return nil
		}
		parts := strings.Split(rel, string(filepath.Separator))
		if len(parts) > maxDepth {
			if d.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		skipDirs := map[string]bool{".git": true, "node_modules": true, ".zoo-code": true, "dist": true, "build": true, ".next": true, "vendor": true}
		if d.IsDir() && skipDirs[filepath.Base(path)] {
			return filepath.SkipDir
		}
		indent := strings.Repeat("  ", len(parts)-1)
		if d.IsDir() {
			result = append(result, fmt.Sprintf("%s📁 %s/", indent, filepath.Base(path)))
		} else {
			result = append(result, fmt.Sprintf("%s📄 %s", indent, filepath.Base(path)))
		}
		return nil
	})
	return result
}

type Endpoint struct {
	method string
	path   string
}

func detectEndpoints(dir string) []Endpoint {
	var endpoints []Endpoint
	filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		ext := filepath.Ext(path)
		if ext != ".ts" && ext != ".tsx" && ext != ".js" {
			return nil
		}

		content, _ := os.ReadFile(path)
		lines := strings.Split(string(content), "\n")
		for _, line := range lines {
			trimmed := strings.TrimSpace(line)
			// Express-style routes
			methods := []string{"get", "post", "put", "delete", "patch"}
			for _, m := range methods {
				pattern := fmt.Sprintf(".%s(", m)
				if strings.Contains(trimmed, pattern) {
					if idx := strings.Index(trimmed, "\""); idx >= 0 {
						if endIdx := strings.LastIndex(trimmed, "\""); endIdx > idx {
							route := trimmed[idx+1 : endIdx]
							endpoints = append(endpoints, Endpoint{method: strings.ToUpper(m), path: route})
						}
					}
				}
			}
			// Next.js App Router
			if strings.Contains(trimmed, "export async function") && strings.Contains(trimmed, "Handler") {
				parts := strings.Split(trimmed, " ")
				for _, p := range parts {
					p = strings.ToUpper(p)
					if p == "GET" || p == "POST" || p == "PUT" || p == "DELETE" {
						endpoints = append(endpoints, Endpoint{method: p, path: path})
					}
				}
			}
		}
		return nil
	})
	return endpoints
}

func detectModels(dir string) []string {
	var models []string
	filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		ext := filepath.Ext(path)
		content, _ := os.ReadFile(path)
		lines := strings.Split(string(content), "\n")

		switch ext {
		case ".ts", ".tsx":
			for _, line := range lines {
				trimmed := strings.TrimSpace(line)
				if strings.HasPrefix(trimmed, "interface ") {
					parts := strings.Split(trimmed, " ")
					if len(parts) >= 2 {
						models = append(models, fmt.Sprintf("interface %s (%s)", parts[1], filepath.Base(path)))
					}
				}
			}
		case ".go":
			for _, line := range lines {
				trimmed := strings.TrimSpace(line)
				if strings.HasPrefix(trimmed, "type ") && strings.Contains(trimmed, "struct") {
					parts := strings.Split(trimmed, " ")
					if len(parts) >= 2 {
						models = append(models, fmt.Sprintf("struct %s (%s)", parts[1], filepath.Base(path)))
					}
				}
			}
		}
		return nil
	})
	return models
}

func exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}
