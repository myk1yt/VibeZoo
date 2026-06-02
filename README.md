<div align="center">
  <img src="https://github.com/myk1yt/VibeZoo/raw/main/Logo/logo.png" alt="VibeZoo Logo" width="128">
  <h1>VibeZoo 🐾</h1>
  <p><strong>A Next-Generation Coding Assistant Extension for Zoo Code (VS Code)</strong></p>
  <a href="https://teamsunplaza.gumroad.com/l/vibezoo"><img src="https://img.shields.io/badge/Sponsor-☕_Buy_me_a_coffee-FFDD00?style=for-the-badge&logo=gumroad&logoColor=black" alt="Sponsor VibeZoo"></a>
</div>

![VibeZoo Demo](https://raw.githubusercontent.com/myk1yt/VibeZoo/main/test_output.png)

## What is VibeZoo?

**VibeZoo** is a next-generation multimodal extension bridge designed specifically for AI coding assistants like Zoo Code (VS Code). 
While most AI agents can only read text, VibeZoo equips your LLM (DeepSeek, Claude, etc.) with **"Eyes" (Multimodal Vision)**, **"Hands" (32+ MCP Tools)**, and an intelligent **"Radar" (GitHub Deep Diver)** to interact with your local environment seamlessly.

---

## 🌟 Core Features

### 1. Universal Drop Zone & Multimodal Vision
No more describing UI bugs with words. Just drag and drop!
- **Drop Zone Webview**: Drop images, screenshots, or PDF files directly into the VS Code panel.
- **Auto-Triggered Pipeline**: Uploading an image automatically opens the `VibeZoo Analyzer` terminal.
- **MiniCPM-V 4.6 (578MB)**: We utilize an ultra-lightweight, blazing-fast local vision model. It loads into memory in 1 second and infers in 0.5 seconds to describe exactly what's in the image.
- **3-Layer Engine**: Integrates **MiniCPM-V** (Vision), **PaddleOCR** (Text Extraction), and **SSA** (Statistical Spatial Aggregator) to give the LLM 100% spatial awareness.

### 2. GitHub Deep Diver (`explore_github`)
Why write code from scratch when you can borrow from the best?
- **All-in-One OpenSource Search**: A single, intelligent MCP tool (`explore_github`) that functions as a deep-sea diver for open-source code.
- **Smart Routing**: The LLM autonomously inputs a `query` to search repositories, a `repo` to scan tree skeletons, or a `file_path` to snipe and extract specific raw code.
- **Zero Config**: Completely free, anonymous REST API usage out of the box. No tokens or login required.

### 3. Visual Collaboration Suite
- **Whiteboard**: An interactive canvas where you and the AI can draw architectures and share ideas.
- **Diagram Engine**: Automatically generate Mermaid diagrams or UI layouts based on the active codebase.

### 4. 32+ Powerful MCP Tools
A massive arsenal of Model Context Protocol (MCP) tools:
- Tree-sitter AST-based code search and reverse engineering
- Automated tests and bug hunting
- Web Search integration
- Self-healing build loops (Autonomous Fix)

---

## 🧠 Perfect Synergy with Crow Memory

VibeZoo is designed to work in perfect harmony with **[Crow Memory](https://github.com/myk1yt/crowmemory)**.
While VibeZoo provides the sensory inputs (vision, tools, searches), Crow Memory acts as the long-term hippocampus. 

- **How it works together**: When you upload an image of a bug via VibeZoo's Drop Zone, the AI fixes it. Crow Memory then passively observes your preferred coding style and architectural decisions during the fix, storing them in its `crow.bin` weight matrices.
- **Result**: Your AI agent not only sees what you see, but it remembers *how you like things done* across different projects and sessions.

---

## 🚀 Quick Start (Zero Config Auto-Setup)

VibeZoo embraces the "Zero Configuration" philosophy. The LLM can bootstrap itself!

1. **Clone & Open**:
   ```bash
   git clone https://github.com/myk1yt/VibeZoo.git
   cd VibeZoo
   # Open this folder in VS Code / Zoo Code
   ```
2. **Ask your AI**: Simply open the chat and say: *"Setup VibeZoo for me."*
3. **The LLM takes over**: It reads the `.zoo/instructions.md` guide and autonomously:
   - Starts the background MCP Bridge (`vibezoo_mcp_bridge.py`)
   - Registers the SSE port
   - Calls the `vibezoo_setup(target="full")` tool to download the 578MB GGUF models and Python dependencies
   - Compiles the TypeScript UI Webviews

*(You can also run these steps manually if you prefer.)*

---

## ❤️ Community & Support

- **Bug Reports**: Open an issue on GitHub
- **Sponsor & Support**: If you love VibeZoo and want to support its continuous development, please consider becoming a sponsor! ❤️ [**Support VibeZoo on Gumroad**](https://teamsunplaza.gumroad.com/l/vibezoo)
- **Contributions**: Pull requests are warmly welcomed for new MCP tools or UI enhancements!

---
*VibeZoo — Bridging the gap between local AI reasoning and visual coding.*
