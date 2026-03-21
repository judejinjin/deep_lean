# DeepLean Architecture

## Overview

DeepLean is an agentic deep-research system built on LangGraph that:
1. Takes a mathematical/physics research question
2. Searches literature (arXiv, Semantic Scholar, PDFs)
3. Generates formal Lean 4 proofs with Mathlib
4. Iteratively repairs proofs using compiler feedback
5. Produces a Markdown report and interactive Jupyter notebook

## Agent Pipeline

```
User Question
    │
    ▼
┌─────────────┐
│ Orchestrator │ — Plans research strategy, decomposes question
└──────┬──────┘
       │
       ▼
┌────────────┐
│ Researcher │ — Searches arXiv, Semantic Scholar, extracts PDFs
└──────┬─────┘
       │
       ▼
┌─────────────┐
│ Formalizer  │ ←──── retry with error feedback ────┐
└──────┬──────┘                                      │
       │                                             │
       ▼                                             │
┌──────────┐    success → Reporter                   │
│ Verifier │────────────────────────────┐            │
└──────────┘    failure + retries left ──┘            │
       │                  │                           │
       │              give_up → Reporter              │
       │                                              │
       ▼                                              │
┌──────────┐                                          │
│ Reporter │ — Generates Markdown report              │
└──────┬───┘                                          │
       │                                              │
       ▼                                              │
┌──────────────┐                                      │
│ Notebook Gen │ — Builds .ipynb with SymPy + plots   │
└──────────────┘                                      │
```

## Module Structure

```
src/
├── __init__.py
├── __main__.py          # CLI entry point
├── config.py            # Settings, model routing, env keys
├── llm.py               # Unified LLM client (litellm)
├── models.py            # Pydantic data models
├── agents/
│   ├── base.py          # Abstract base agent
│   ├── graph.py         # LangGraph state + flow
│   ├── orchestrator.py  # Task planning
│   ├── researcher.py    # Literature search
│   ├── formalizer.py    # Lean 4 code generation
│   ├── verifier.py      # Lean compilation + error analysis
│   ├── reporter.py      # Report generation
│   ├── notebook_agent.py# Notebook generation
│   ├── decomposer.py   # Proof decomposition
│   └── single_loop.py  # Simple single-agent loop
├── tools/
│   ├── arxiv_search.py      # arXiv API
│   ├── semantic_scholar.py  # Semantic Scholar API
│   ├── pdf_reader.py        # PDF text extraction
│   ├── lean_executor.py     # Lean 4 build system
│   ├── notebook_builder.py  # nbformat wrapper
│   ├── notebook_executor.py # Sandboxed cell execution
│   ├── mathlib_index.py     # ChromaDB vector index
│   ├── example_bank.py      # Few-shot proof examples
│   ├── symbolic_math.py     # SymPy helpers
│   └── plot_generator.py    # Matplotlib/Plotly templates
├── utils/
│   ├── logging.py       # structlog setup
│   ├── provenance.py    # Audit trail (JSONL)
│   └── lean_parser.py   # Lean error parser
└── prompts/
    ├── orchestrator.md
    ├── researcher.md
    ├── formalizer.md    # Lean 4 syntax guide + examples
    ├── verifier.md
    ├── reporter.md
    └── notebook_agent.md
```

## LLM Strategy

All models route through `litellm` for unified API. During testing, all roles use `anthropic/claude-sonnet-4-6`. Production routing table:

| Role | Primary | Fallback |
|------|---------|----------|
| Orchestration | claude-sonnet-4-6 | gemini-2.5-flash |
| Reasoning | o3 | claude-opus-4-6 |
| Formalization | o3 | gpt-4.1 |
| Research | claude-opus-4-6 | gemini-2.5-pro |
| Notebook Code | gemini-2.5-pro | gpt-4.1 |
| Error Analysis | claude-sonnet-4-6 | gemini-2.5-flash |
| Reports | claude-opus-4-6 | gemini-2.5-pro |

## Key Design Decisions

1. **LangGraph over CrewAI/AutoGen** — cleaner state management, explicit graph topology
2. **litellm** — unified interface across 3+ providers with cost tracking
3. **ChromaDB** — local embedding store for Mathlib search (no server needed)
4. **nbformat** — programmatic notebook construction (no Jupyter server dependency)
5. **asyncio-first** — all I/O is async, enabling concurrent API calls
6. **Sorry-guided verification** — allow partial proofs, fill gaps iteratively
