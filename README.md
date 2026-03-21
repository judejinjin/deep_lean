# DeepLean

An agentic deep-research system that autonomously investigates mathematics and physics problems. It combines LLM-driven reasoning (Google Gemini, OpenAI, Anthropic Claude) with the **Lean 4** theorem prover to produce formally verified proofs and derivations.

## What It Does

- **Autonomous research** — takes a math/physics question, searches literature, constructs proofs, and verifies them
- **Formal verification** — translates reasoning into Lean 4 code and iteratively refines until it compiles against Mathlib4
- **Multi-agent architecture** — Orchestrator, Research, Formalization, Verification, Report, and Notebook agents coordinated via LangGraph
- **Notebook generation** — produces interactive Jupyter notebooks with SymPy derivations, Matplotlib/Plotly visualizations, and Lean proof blocks
- **Multi-provider LLM routing** — uses o3 for math reasoning, Claude for orchestration/writing, Gemini for code generation and multimodal tasks

## Project Status

**Implemented** — all 4 phases complete, 63 unit tests passing.

## Architecture

```
User Question → Orchestrator → Researcher → Formalizer → Verifier → Reporter → Notebook
                                                ↑           │
                                                └───retry────┘
```

Agents are connected via LangGraph with conditional edges (retry on verification failure, up to N attempts).

## Key Files

| File | Description |
|---|---|
| `project.md` | Full project proposal with architecture, tech stack, and decisions |
| `IMPLEMENTATION_PLAN.md` | Detailed phased implementation plan (Phase 0–4) |
| `src/config.py` | Settings, model routing, env key remapping |
| `src/llm.py` | Unified LLM client with fallback chains + cost tracking |
| `src/agents/graph.py` | LangGraph multi-agent pipeline definition |
| `src/agents/single_loop.py` | Simple single-agent proof loop |
| `src/__main__.py` | CLI entry point |

## Quick Start

```bash
# Install uv (no sudo needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --extra dev

# Copy and fill in API keys
cp .env.example .env

# Run single-agent proof loop
uv run python -m src --single "Prove that 1 + 1 = 2"

# Run full multi-agent pipeline
uv run python -m src "Prove that sqrt(2) is irrational"

# Run with source PDFs
uv run python -m src --pdfs paper.pdf "Research question here"

# Run unit tests
uv run pytest tests/ -m "not integration" -v

# (Optional) Install Lean 4 for formal verification
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y
```

## Requirements

- Python 3.12+
- WSL2 / Linux
- API keys in `.env`: `GEMINI_KEY`, `OPENAI_KEY`, `CLAUDE_KEY`
