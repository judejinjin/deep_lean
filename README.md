# DeepLean

An agentic deep-research system that autonomously investigates mathematics and physics problems. It combines LLM-driven reasoning (Google Gemini, OpenAI, Anthropic Claude) with the **Lean 4** theorem prover to produce formally verified proofs and derivations.

## What It Does

- **Autonomous research** — takes a math/physics question, searches literature, constructs proofs, and verifies them
- **Formal verification** — translates reasoning into Lean 4 code and iteratively refines until it compiles against Mathlib4
- **Multi-agent architecture** — Orchestrator, Research, Formalization, Verification, Report, and Notebook agents coordinated via LangGraph
- **Notebook generation** — produces interactive Jupyter notebooks with SymPy derivations, Matplotlib/Plotly visualizations, and Lean proof blocks
- **Multi-provider LLM routing** — uses o3 for math reasoning, Claude for orchestration/writing, Gemini for code generation and multimodal tasks

## Project Status

**Pre-implementation** — architecture decisions finalized, implementation plan ready.

## Key Files

| File | Description |
|---|---|
| `project.md` | Full project proposal with architecture, tech stack, and decisions |
| `IMPLEMENTATION_PLAN.md` | Detailed phased implementation plan (Phase 0–4) |
| `sciama_1953.pdf` | Sciama's "On the Origin of Inertia" (1953) — test research topic source |
| `on_sciama_1953.pdf` | Fay's commentary on Sciama 1953 |
| `dipole_gravity.pdf` | Gallucci's electromagnetic dipole gravity analysis |

## Quick Start

```bash
# Install uv (no sudo needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install Lean 4
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y

# Run (once implemented)
uv run python -m src "Prove that sqrt(2) is irrational"
```

## Requirements

- Python 3.12+
- WSL2 / Linux
- API keys in `.env`: `GEMINI_KEY`, `OPENAI_KEY`, `CLAUDE_KEY`
