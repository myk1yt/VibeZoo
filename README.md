# VibeZoo — Intelligent Companion Extension for AI Coding Assistants

> **VibeZoo = [Crow Memory](#3-crow-memory-overview) (Synaptic Memory) + [VibeZoo MCP Bridge](#1-vibezoo-mcp-bridge--tool-overview-34-tools) (34 Tools)**

VibeZoo is a Companion Extension for Zoo Code. Without modifying a single line of Zoo Code's source code, it enables the LLM to search, analyze, review, and document code more intelligently. It remembers your habits and preferences, and enables real-time visual collaboration (Whiteboard, Dropzone, Vision AI).

---

## Support VibeZoo Development ☕

If you find VibeZoo and Crow Memory helpful for your productivity, consider supporting our development!
**[💖 Sponsor VibeZoo on Gumroad](https://teamsunplaza.gumroad.com/l/vibezoo)**

Your support helps us maintain the servers, develop new features, and keep the AI coding revolution moving forward.

---

## 1. VibeZoo MCP Bridge — Tool Overview (34 Tools)

The VibeZoo MCP Bridge operates based on FastMCP + SSE, communicating with the Zoo Code MCP client and `vibezoo_mcp_bridge_v2.py` at `localhost:9027/sse`. It provides a total of **34 MCP tools**.

### 1.1 UX (3 Tools) — Intent Detection + Auto Tool Chains
When you say "I'll show you a file", the Dropzone opens. Uploaded files are automatically analyzed through the SSA→OCR→MiniCPM pipeline.

### 1.2 Scout (3 Tools) — Code Search and Exploration
Quickly grasp the project structure and find symbols or functions accurately using tree-sitter AST.

### 1.3 Reviewer (2 Tools) — Code Quality Check
Automatically check code quality before submitting a PR. Integrates with ESLint and go vet.

### 1.4 Tester (2 Tools) — Test Generation and Coverage
Detects function signatures to automatically generate test templates and measure coverage.

### 1.5 Deep Analyzer (4 Tools) — Deep AST Analysis
Analyzes call graphs, dependencies, and recurring patterns using tree-sitter AST, and automatically generates documentation.

### 1.6 Whiteboard (4 Tools) — AI-Human Visual Collaboration
The AI draws on a Fabric.js canvas, reads user modifications, and can capture the screen.

### 1.7 Fix Loop (3 Tools) — Autonomous Build & Fix Loop
If a build fails, the LLM automatically analyzes the error, looks up past fix patterns in Crow Memory, and suggests fixes. Supports Human-in-the-Loop.

### 1.8 Integrated (4 Tools) — Unified Scenario Tools
Combines multiple tools into a single workflow. Just say "Review this", and it runs search → review → quality → patterns sequentially.

### 1.9 Analysis (4 Tools) — Code Explanation and Diff Analysis
Explains what specific code lines do, analyzes git diffs, supports PR reviews, and proposes bulk refactoring.

### 1.10 Knowledge (2 Tools) — Project Knowledge Memory
Saves project structures and patterns into Crow Memory and recalls them later.

### 1.11 Preferences (2 Tools) — User Preference Learning
Stores your coding style and preferences in Crow Memory to be recalled when needed.

### 1.12 Web (2 Tools) — Web Search and Page Analysis
Used to reference external documentation or search for the latest technical information.

### 1.13 SSA (1 Tool) — Spatial Statistical Analysis
Spatial Statistical Aggregator: OpenCV-based image pixel statistics analysis, including OCR.

### 1.14 Setup (1 Tool) — Automation
Installs VibeZoo dependencies and auto-configures MCP/Zoo settings.

---

## 2. Vision AI Pipeline

VibeZoo includes a built-in Vision AI pipeline for image analysis:
- **MiniCPM-V**: Lightweight Vision-Language Model. Performs image captioning and analysis locally (GGUF + llama-cpp-python).
- **OCR**: Tesseract / PaddleOCR for text extraction (supports Korean, English, Japanese, Chinese).
- **SSA**: OpenCV-based Spatial Statistical Aggregator for pixel statistics and spatial pattern analysis.

---

## 3. Crow Memory Overview

### 3.1 Philosophy — "Crow remembers not the code, but the hand that wrote it."

Transformer-based LLMs are fixed at training time. RAG or SQLite-based solutions stack information infinitely like a "100% accurate notepad," but the human brain doesn't work that way.
**Forgetting is not a bug.** Crow's fixed-size weight matrices and λ (decay rate) implement "Creative Forgetting." By giving up 100% accurate recall, the AI responding through Crow becomes biased toward **the current you**.

### 3.2 The 8 Registers
- **Code Domain**: `style`, `bug`, `arch`, `context`
- **Life Domain**: `life_pref`, `life_avoid`, `life_phil`, `life_context`

### 3.3 Hebbian EMA Update Rule
Crow updates weights using an Exponential Moving Average (EMA) based on Hebbian learning:
`W_new = λ · W_old + (1 - λ) · (key ⊗ value)`

All memories are compressed into a fixed-size `crow.bin` (140MB). When capacity is exceeded, old memories naturally fade.

### 3.4 10 Crow MCP Tools
Includes tools like `crow_recall`, `crow_ingest`, `crow_diagnostics`, `crow_manage_backup`, and more to interact with the synaptic memory.

---

## 4. Quick Start

### 4.1 Requirements
- **Python 3.10+**
- **Zoo Code** (or MCP-compatible AI Coding Agent)
- Git

### 4.2 Installation
**Windows (PowerShell):**
```powershell
git clone https://github.com/myk1yt/crowmemory.git
cd crowmemory
.\install.ps1
```

**macOS / Linux:**
```bash
git clone https://github.com/myk1yt/crowmemory.git
cd crowmemory
python install.py
```

### 4.3 Manual VibeZoo MCP Bridge Configuration
```json
// .roo/mcp.json
{
  "mcpServers": {
    "vibezoo": {
      "url": "http://localhost:9027/sse"
    }
  }
}
```

---

## 5. Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      VS Code Window                           │
│                                                               │
│  ┌──────────────────────┐    ┌────────────────────────────┐  │
│  │   Zoo Code (LLM)     │    │  VibeZoo Extension          │  │
│  │                      │    │                             │  │
│  │  • LLM Reasoning     │    │  • FixLoopManager          │  │
│  │  • Built-in Crow     │    │  • VisualVibePanels        │  │
│  │    (localhost:9020)  │    │  • Safety Net              │  │
│  │  • MCP Client        │    │                            │  │
│  └──────────┬───────────┘    └─────────────┬──────────────┘  │
│             │ MCP/SSE                      │ child_process    │
└─────────────┼──────────────────────────────┼──────────────────┘
              ▼                              ▼
┌─────────────────────────┐  ┌─────────────────────────────────┐
│ Crow Memory (9020)      │  │ VibeZoo MCP Bridge (9027)       │
└─────────────────────────┘  └─────────────────────────────────┘
```

---

## 6. License and Contact

MIT License — See [`LICENSE`](LICENSE).

### Commercial Services / Custom Development

Crow Memory is free to use under the MIT license. However, organizations have different needs—security, proprietary LLM integration, custom encoding, compliance, etc.

**We provide custom development services:**
- 🔒 **Secure Deployments** (Air-gapped, encrypted `crow.bin`, RBAC)
- 🏢 **Enterprise Customization** (Custom registers, industry-specific decay profiles)
- 🤖 **LLM-Specific Optimization** (Fine-tuned embeddings, optimized weight matrices)
- 🧩 **Software Integration** (Non-VS Code IDEs, CI/CD hooks)
- 📊 **Enterprise Analytics** (Memory usage dashboards, drift alerts)

> **Contact us for enterprise, secure, or custom-tailored Crow Memory development:**
📧 **myk1yt@gmail.com**

---
*VibeZoo v0.14.2 — June 2026*
*Co-designed by Stefano, Kim & AI*
