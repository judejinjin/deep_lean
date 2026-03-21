Project:
build an agentic deep researcher that can do independent research on mathematics and physics.
the agents should use lean to prove the theory and verify the derivations of any formula.

it should load LLM api keys from .env (Gemini, OpenAI, Claude keys provided).
it should use the best available models from Google Gemini, OpenAI, and Anthropic Claude.
it should be developed and tested on WSL linux.
the implementation language is python.
in addition to formal reports, it should generate Jupyter notebooks that illustrate
the derivation process through Python code and visualizations.

---

# DeepLean — Detailed Project Proposal

## 1. Executive Summary

**DeepLean** is an agentic deep-research system that autonomously investigates mathematics and physics problems. It combines LLM-driven reasoning (powered by the best models from **Google Gemini**, **OpenAI**, and **Anthropic Claude**) with the Lean 4 theorem prover to produce formally verified proofs and derivations. The system ingests a research question, decomposes it into sub-problems, searches relevant literature, constructs informal arguments, translates them into Lean 4 code, and iteratively refines until a machine-checked proof is obtained. Beyond a formal Markdown/LaTeX report, the system also **generates interactive Jupyter notebooks** that illustrate each derivation step through Python code, symbolic computation, and visualizations — making the research output both rigorous and pedagogically accessible.

---

## 2. Goals & Success Criteria

| Goal | Measurable Criterion |
|---|---|
| Autonomous research | Given a well-posed math/physics question, the system produces a structured answer with references within a configurable time budget. |
| Formal verification | Every core theorem or derivation is accompanied by a Lean 4 proof that compiles without errors. |
| Iterative self-correction | When Lean rejects a proof, the agent loop re-examines the argument and retries (up to N attempts). |
| Extensibility | New tool plugins (e.g., Mathematica, SageMath, arXiv search) can be added without modifying core orchestration. |
| Interactive notebooks | Every research output includes a generated Jupyter notebook with step-by-step Python code, symbolic math, and plots illustrating the derivation. |
| Reproducibility | All runs are logged with full provenance (prompts, LLM responses, Lean outputs) for audit. |

---

## 3. High-Level Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                        Orchestrator Agent                             │
│  (plan, delegate, evaluate, iterate)                                  │
│  LLMs: Gemini 2.5 Pro · OpenAI o3 / GPT-4o · Claude Opus / Sonnet   │
└───┬──────────┬──────────┬──────────┬──────────┬───────────────────────┘
    │          │          │          │          │
┌───▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼─────┐ ┌─▼────────┐
│Research│ │Formali-│ │Lean    │ │Report   │ │Notebook  │
│ Agent  │ │zation  │ │Verifier│ │Generator│ │Generator │
│        │ │ Agent  │ │ Agent  │ │         │ │          │
└───┬───┘ └───┬────┘ └───┬────┘ └───┬─────┘ └──┬───────┘
    │         │          │          │           │
┌───▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼─────┐ ┌──▼───────┐
│Tools: │ │Tools:  │ │Tools:  │ │Tools:   │ │Tools:    │
│-arXiv │ │-LLM    │ │-lean4  │ │-Markdown│ │-nbformat │
│-Wiki  │ │-Mathlib│ │ CLI    │ │-LaTeX   │ │-SymPy    │
│-Sem.  │ │lookup  │ │-lake   │ │-PDF     │ │-Matplotlib│
│Scholar│ │        │ │ build  │ │         │ │-Manim   │
└───────┘ └────────┘ └────────┘ └─────────┘ └──────────┘
```

### 3.1 Component Descriptions

#### Orchestrator Agent
- Receives the user's research question.
- Decomposes into a DAG of sub-tasks (literature review → informal proof → formalization → verification → report).
- Manages state, retries, and the overall research plan.
- Decides when to escalate, retry, or accept a result.

#### Research Agent
- Performs literature search using arXiv API, Semantic Scholar, Wikipedia, and optionally web search.
- Extracts relevant theorems, definitions, and known results.
- Summarizes findings and passes structured context to downstream agents.

#### Formalization Agent
- Takes an informal mathematical argument or physics derivation and translates it into Lean 4 code.
- Leverages Mathlib4 for existing formalized mathematics.
- Produces incremental Lean files that build on each other.

#### Lean Verifier Agent
- Compiles the generated Lean 4 code using `lake build`.
- Parses compiler output for errors and warnings.
- Returns structured feedback (error location, type mismatch details, missing lemmas) to the Formalization Agent for correction.

#### Report Generator
- Assembles a final human-readable report in Markdown (and optionally LaTeX/PDF).
- Includes the informal argument, formal Lean proofs, references, and verification status.

#### Notebook Generator (NEW)
- Produces an interactive Jupyter notebook (`.ipynb`) that walks through the derivation step by step.
- Each derivation step becomes one or more notebook cells containing:
  - **Markdown cells**: Narrative explanation with LaTeX equations.
  - **Python code cells**: Symbolic computation (SymPy), numerical verification (NumPy/SciPy), and visualizations (Matplotlib/Plotly).
  - **Lean code cells** (as fenced code blocks or via a Lean Jupyter kernel): Showing the formal proof alongside the computational derivation.
- Generates plots and animations where appropriate (e.g., phase portraits, field visualizations, convergence plots).
- Uses `nbformat` to programmatically construct notebooks; optionally uses `Manim` for mathematical animations.
- Output is a self-contained `.ipynb` file that can be opened, run, and shared independently.

---

## 4. Agent Framework Options

### Option A: LangGraph (Recommended)

| Aspect | Detail |
|---|---|
| Library | `langgraph` (part of LangChain ecosystem) |
| Why | First-class support for cyclic agent graphs, state machines, persistence, and human-in-the-loop. Well-suited for the retry loops needed when Lean rejects a proof. |
| Pros | Mature ecosystem, built-in checkpointing, streaming, easy tool integration. |
| Cons | Heavier dependency footprint; tied to LangChain abstractions. |

### Option B: CrewAI

| Aspect | Detail |
|---|---|
| Library | `crewai` |
| Why | Role-based multi-agent framework; easy to define agents with goals, backstories, and tool lists. |
| Pros | Simple declarative API, built-in task delegation, memory, and process modes (sequential/hierarchical). |
| Cons | Less control over complex graph topologies; younger project with faster-changing API. |

### Option C: Custom Lightweight Framework

| Aspect | Detail |
|---|---|
| Library | Plain Python with `asyncio` + a thin agent abstraction |
| Why | Maximum control, minimal dependencies; ideal if the team wants to avoid framework lock-in. |
| Pros | No external framework overhead; full control over retry logic, state, and tool dispatch. |
| Cons | More boilerplate; must implement persistence, logging, and orchestration from scratch. |

### Option D: AutoGen (Microsoft)

| Aspect | Detail |
|---|---|
| Library | `autogen` / `autogen-agentchat` |
| Why | Strong multi-agent conversation patterns, code execution sandboxing. |
| Pros | Good for conversational back-and-forth between agents; built-in Docker execution environments. |
| Cons | Conversation-centric model may not fit the DAG-based workflow as cleanly. |

**Recommendation:** Option A (LangGraph) for its graph-based orchestration which naturally models the iterative proof-refinement loop. Option C is the best fallback if minimal dependencies are preferred.

---

## 5. LLM Provider Strategy

The system uses the **best available models** from the three providers whose API keys are configured in `.env`: **Google Gemini**, **OpenAI**, and **Anthropic Claude**. Each provider is assigned roles based on its strengths.

### Primary Providers (API keys validated ✅)

| Provider | Confirmed Models | Assigned Roles | Strengths |
|---|---|---|---|
| **Google Gemini** | `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` | Multimodal analysis, physics paper parsing, diagram understanding, notebook code generation | 1M token context; native multimodal; strong code generation; cost-effective via flash |
| **OpenAI** | `o3`, `o3-mini`, `o4-mini`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o` | Hard mathematical reasoning, Lean formalization, proof search | o3 excels at competition-level math; best chain-of-thought for formal proofs; gpt-4.1 for reliable coding |
| **Anthropic Claude** | `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-5`, `claude-sonnet-4-5`, `claude-haiku-4-5` | Research synthesis, long-document analysis, report writing, orchestration reasoning | 200K context; excellent at structured output; strong at nuanced reasoning and writing |

**Bonus Providers** (also validated):
- **OpenRouter** (`OPENROUTER_KEY`) — Unified fallback gateway to all providers; use for redundancy.
- **Grok / xAI** (`GROK_KEY`) — Additional reasoning model; potential alternative for cost savings.

### Model Routing Strategy

| Task | Primary Model | Fallback Model | Rationale |
|---|---|---|---|
| Orchestration & Planning | `claude-sonnet-4-6` | `gemini-2.5-pro` | Claude excels at structured multi-step planning |
| Literature Research & Synthesis | `claude-opus-4-6` | `gemini-2.5-pro` | Long-context analysis, nuanced summarization |
| Mathematical Reasoning | `o3` | `claude-opus-4-6` | o3 is state-of-the-art for hard math |
| Lean 4 Formalization | `o3` | `gpt-4.1` | o3 for theorem proving; gpt-4.1 strong at code |
| Lean Error Analysis & Repair | `claude-sonnet-4-6` | `o4-mini` | Claude is strong at diagnosing and explaining errors |
| Notebook Code Generation | `gemini-2.5-pro` | `gpt-4.1` | Gemini excels at Python code gen & visualization |
| Notebook Narrative (Markdown) | `claude-sonnet-4-6` | `gemini-2.5-flash` | Claude produces excellent pedagogical writing |
| Physics Diagram Interpretation | `gemini-2.5-pro` | `gpt-4o` | Native multimodal, best for images/equations |
| Report Generation | `claude-opus-4-6` | `gemini-2.5-pro` | Best technical writing quality |
| Fast/Cheap Tasks | `gemini-2.5-flash` | `gpt-4.1-mini` | Low-cost for retries, summaries, and simple subtasks |

### Alternative: Local/Open-Source Models (Optional Fallback)

| Model | Use Case |
|---|---|
| `Llama 3.3 70B` (via Ollama) | Privacy-sensitive or offline research |
| `DeepSeek-R1` (local or API) | Cost-free math reasoning fallback |
| `Llemma 34B` | Purpose-built for mathematical reasoning |

### Configuration

```bash
# .env — actual key names in current environment
# NOTE: litellm expects GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
# Our .env uses GEMINI_KEY, OPENAI_KEY, CLAUDE_KEY — remap at load time
GEMINI_KEY=AI...
OPENAI_KEY=sk-...
CLAUDE_KEY=sk-ant-...
OPENROUTER_KEY=sk-or-...
GROK_KEY=xai-...
```

```python
# config.py — remap .env names to litellm-expected env vars
import os
from dotenv import load_dotenv
load_dotenv()
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_KEY", "")
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_KEY", "")
os.environ["ANTHROPIC_API_KEY"] = os.environ.get("CLAUDE_KEY", "")
os.environ["OPENROUTER_API_KEY"] = os.environ.get("OPENROUTER_KEY", "")
```

```python
# Model routing config (litellm model strings)
ORCHESTRATION_MODEL = "anthropic/claude-sonnet-4-6"
REASONING_MODEL = "openai/o3"
FORMALIZATION_MODEL = "openai/o3"
RESEARCH_MODEL = "anthropic/claude-opus-4-6"
NOTEBOOK_CODE_MODEL = "gemini/gemini-2.5-pro"
NOTEBOOK_NARRATIVE_MODEL = "anthropic/claude-sonnet-4-6"
MULTIMODAL_MODEL = "gemini/gemini-2.5-pro"
REPORT_MODEL = "anthropic/claude-opus-4-6"
FAST_MODEL = "gemini/gemini-2.5-flash"          # For lightweight tasks, retries
ERROR_ANALYSIS_MODEL = "anthropic/claude-sonnet-4-6"
FALLBACK_CODING_MODEL = "openai/gpt-4.1"        # Reliable fallback for code tasks
CHEAP_MODEL = "openai/gpt-4.1-mini"             # Budget fallback
```

Use `litellm` as a unified LLM gateway to abstract provider differences behind a single API. All three providers (plus OpenRouter fallback) are called via a consistent interface with automatic fallback on rate limits or errors.

---

## 6. Lean 4 Integration

### 6.1 Setup

- **Lean 4 + Mathlib4**: Installed via `elan` (Lean version manager) and `lake` (build system).
- **Project template**: A pre-configured `lakefile.lean` with Mathlib4 as a dependency.
- Lean toolchain managed within the project to ensure reproducibility.

### 6.2 Interaction Pattern

```
Formalization Agent
    │
    ├─ Generates .lean file
    │
    ▼
Lean Verifier Agent
    │
    ├─ Runs: lake build
    ├─ Captures stdout/stderr
    ├─ Parses error messages
    │
    ▼
Structured Feedback
    │
    ├─ Success → accept proof
    └─ Failure → return errors to Formalization Agent (retry up to N times)
```

### 6.3 Alternative: Lean REPL / Language Server Protocol

Instead of full `lake build` cycles, consider using:
- **Lean 4 REPL** (`lean --run`): Faster feedback for individual declarations.
- **Lean LSP** (`lean --server`): Real-time diagnostics, go-to-definition for Mathlib exploration.

**Recommendation:** Start with `lake build` for simplicity; migrate to LSP-based interaction for speed once the pipeline is stable.

### 6.4 Mathlib4 Strategy

- Maintain a curated index of relevant Mathlib4 lemmas/theorems by topic (algebra, analysis, topology, etc.).
- Use embedding-based search over Mathlib4 doc-strings to help the Formalization Agent find applicable lemmas.
- Cache frequently used import sets to speed up compilation.

---

## 6.5 Notebook Generation Pipeline

The Notebook Generator is a first-class output alongside the formal report. It translates the research results into a pedagogically rich, executable Jupyter notebook.

### Purpose

| Audience | Value |
|---|---|
| Researchers | Reproduce and extend results interactively |
| Students | Step-by-step walkthrough of proofs and derivations with runnable code |
| Reviewers | Verify numerical computations and inspect visualizations |

### Notebook Cell Types

| Cell Type | Content | Generated By |
|---|---|---|
| **Header** (Markdown) | Title, problem statement, table of contents | Claude Sonnet |
| **Theory** (Markdown) | LaTeX explanation of each derivation step | Claude Sonnet |
| **Symbolic** (Python) | SymPy computation: simplification, equation solving, series expansion | Gemini 2.5 Pro |
| **Numerical** (Python) | NumPy/SciPy verification: numerical integration, root finding, PDE solving | Gemini 2.5 Pro |
| **Visualization** (Python) | Matplotlib/Plotly plots: function graphs, phase portraits, 3D surfaces | Gemini 2.5 Pro |
| **Lean Proof** (Markdown) | Lean 4 code in fenced blocks with syntax highlighting | o3 |
| **Verification Summary** (Markdown) | Badge table of which steps are Lean-verified vs. assumed | Claude Sonnet |

### Visualization Strategy

| Math/Physics Domain | Visualization Type | Library |
|---|---|---|
| Real analysis (limits, continuity) | Function plots, epsilon-delta diagrams | Matplotlib |
| Linear algebra | Vector fields, eigenvalue decomposition | Matplotlib + NumPy |
| Differential equations | Phase portraits, solution families | Matplotlib / Plotly |
| Topology | Surface plots, deformations | Plotly (3D interactive) |
| Classical mechanics | Trajectory plots, energy diagrams | Matplotlib |
| Electromagnetism | Field line plots, potential surfaces | Plotly (3D) |
| General relativity | Spacetime diagrams, geodesics, embedding diagrams | Plotly / Manim |
| Quantum mechanics | Wave function plots, probability densities | Matplotlib |

### Example: Generated Notebook Structure

For the query *"Prove that the harmonic series diverges"*:

```
Cell 1  [Markdown]  # The Harmonic Series: Proof of Divergence
                     Problem statement, historical context

Cell 2  [Markdown]  ## Step 1: Oresme's Grouping Argument
                     Explain the grouping: 1/3+1/4 > 1/2, 1/5+...+1/8 > 1/2, ...

Cell 3  [Python]    # Symbolic verification with SymPy
                     from sympy import *
                     # Show each group sums to > 1/2

Cell 4  [Python]    # Numerical illustration
                     import numpy as np
                     partial_sums = np.cumsum(1/np.arange(1, 10001))
                     # Plot partial sums showing logarithmic growth

Cell 5  [Python]    # Visualization: partial sums vs ln(n)
                     import matplotlib.pyplot as plt
                     plt.plot(partial_sums, label='H_n')
                     plt.plot(np.log(range(1,10001)), label='ln(n)')

Cell 6  [Markdown]  ## Lean 4 Formal Proof
                     ```lean
                     theorem harmonic_diverges : ...
                     ```

Cell 7  [Markdown]  ## Verification Summary
                     ✅ Lean proof compiled successfully
                     ✅ Numerical verification consistent
```

---

## 7. Project Structure

```
deep_lean/
├── project.md                  # This document
├── .env                        # API keys (gitignored)
├── .env.example                # Template for .env
├── pyproject.toml              # Python project config (uv/poetry)
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── config.py               # Settings, env loading (pydantic-settings)
│   ├── models.py               # Data models (research tasks, proof states)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Top-level planning agent
│   │   ├── researcher.py       # Literature search agent
│   │   ├── formalizer.py       # Lean code generation agent
│   │   ├── verifier.py         # Lean compilation & feedback agent
│   │   ├── reporter.py         # Report assembly agent
│   │   └── notebook_agent.py   # Jupyter notebook generation agent
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── arxiv_search.py     # arXiv API wrapper
│   │   ├── semantic_scholar.py # Semantic Scholar API
│   │   ├── lean_executor.py    # Lean build/REPL interface
│   │   ├── mathlib_index.py    # Mathlib4 lemma search
│   │   ├── latex_renderer.py   # LaTeX to PDF
│   │   ├── notebook_builder.py # Jupyter notebook generation (nbformat)
│   │   ├── symbolic_math.py    # SymPy symbolic computation helpers
│   │   ├── plot_generator.py   # Matplotlib/Plotly visualization generation
│   │   └── web_search.py       # General web search (optional)
│   │
│   ├── prompts/
│   │   ├── orchestrator.md
│   │   ├── researcher.md
│   │   ├── formalizer.md
│   │   ├── verifier.md
│   │   └── notebook_agent.md   # Notebook generation prompts
│   │
│   └── utils/
│       ├── __init__.py
│       ├── lean_parser.py      # Parse Lean error messages
│       ├── logging.py          # Structured logging
│       └── provenance.py       # Run audit trail
│
├── lean_project/               # Lean 4 workspace
│   ├── lakefile.lean
│   ├── lean-toolchain
│   ├── DeepLean/
│   │   └── Generated/          # Agent-generated .lean files
│   └── lake-manifest.json
│
├── tests/
│   ├── test_agents/
│   ├── test_tools/
│   └── test_integration/
│
├── notebooks/                  # Jupyter notebooks for demos
│   └── demo_research.ipynb
│
├── output/                     # Generated research outputs
│   ├── reports/                # Markdown/LaTeX/PDF reports
│   └── notebooks/              # Auto-generated derivation notebooks
│
└── docs/
    └── architecture.md
```

---

## 8. Technology Stack (Confirmed for this system)

| Layer | Technology | Status | Alternative |
|---|---|---|---|
| Language | Python 3.12.3 | ✅ Installed | — |
| Package Manager | `uv` | 📦 To install (no-sudo) | pip (venv, already working) |
| Agent Framework | LangGraph | 📦 To install | CrewAI, custom, AutoGen |
| LLM Providers | Gemini + OpenAI + Claude | ✅ All validated | OpenRouter (also validated) |
| LLM Gateway | `litellm` | 📦 To install | Direct provider SDKs |
| Config/Settings | `pydantic-settings` | 📦 To install | `python-dotenv` + dataclasses |
| Theorem Prover | Lean 4 + Mathlib4 | 📦 `elan` (no-sudo) | — |
| Symbolic Math | `sympy` | 📦 To install | SageMath |
| Notebook Gen | `nbformat` + `nbconvert` | 📦 To install | `papermill` |
| Visualization | `matplotlib` + `plotly` | 📦 To install | `altair` |
| Numerical | `numpy`, `scipy` | 📦 To install | — |
| PDF Processing | `pdftotext` + `PyMuPDF` | ✅ pdftotext installed | `pymupdf4llm` |
| Search APIs | arXiv, Semantic Scholar | 🌐 Network confirmed | — |
| Embeddings | OpenAI `text-embedding-3-small` | ✅ API validated | Gemini embeddings |
| Vector Store | ChromaDB | 📦 To install | FAISS |
| Logging | `structlog` | 📦 To install | `loguru` |
| Testing | `pytest` + `pytest-asyncio` | 📦 To install | — |
| Runtime | WSL2 native (no Docker) | ✅ Confirmed | — |

---

## 9. Key Workflows

### 9.1 End-to-End Research Flow

1. **User Input**: "Prove that the square root of 2 is irrational."
2. **Orchestrator**: Decomposes into sub-tasks:
   - Search for known proofs (Research Agent)
   - Construct informal proof sketch (Orchestrator + LLM)
   - Formalize in Lean 4 (Formalization Agent)
   - Verify (Lean Verifier Agent)
   - Generate report (Report Generator)
3. **Research Agent**: Finds classical proof by contradiction in arXiv/textbooks.
4. **Formalization Agent**: Generates Lean 4 proof using `Mathlib.Data.Real.Irrational`.
5. **Lean Verifier**: Runs `lake build` — if errors, feeds them back to step 4 (up to 5 retries).
6. **Report Generator**: Produces Markdown with informal proof, Lean code, and verification status.
7. **Notebook Generator**: Produces a `.ipynb` file with:
   - Cell 1: Problem statement and background (Markdown + LaTeX)
   - Cell 2: SymPy proof that √2 is irrational (symbolic approach)
   - Cell 3: Numerical illustration — approximating √2 with rationals, showing the gap never closes
   - Cell 4: Visualization — plot of |√2 − p/q| for successive rational approximations
   - Cell 5: The Lean 4 proof (displayed as a fenced code block with syntax highlighting)
   - Cell 6: Verification status and references

### 9.2 Physics Derivation Flow

1. **User Input**: "Derive the Schwarzschild metric from Einstein's field equations."
2. **Orchestrator**: Identifies this as a derivation task (not pure proof).
3. **Research Agent**: Retrieves standard derivation steps.
4. **Formalization Agent**: Formalizes key mathematical steps (e.g., solving the ODE for metric components) — full GR formalization may be partial.
5. **Verifier**: Checks what can be checked; flags steps that require axioms not yet in Mathlib.
6. **Report**: Clearly distinguishes verified vs. assumed steps.
7. **Notebook Generator**: Produces a `.ipynb` file with:
   - Markdown cells walking through each derivation step with LaTeX
   - SymPy cells performing the symbolic tensor calculus (Christoffel symbols, Ricci tensor, etc.)
   - Matplotlib/Plotly cells visualizing the metric, geodesics, light cones
   - Numerical cells verifying limits and special cases (e.g., Newtonian limit)
   - Summary cell comparing verified (Lean) vs. assumed steps

### 9.3 Notebook Generation Detail

The Notebook Generator follows a structured pipeline:

```
Research Output + Proof Steps
        │
        ▼
┌─────────────────────┐
│ Narrative Planner   │  ← Claude Sonnet: plans notebook structure,
│ (LLM)               │    section headings, pedagogical flow
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Code Cell Generator │  ← Gemini 2.5 Pro: generates Python code
│ (LLM)               │    (SymPy, NumPy, Matplotlib, Plotly)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Code Validator      │  Executes generated cells in a sandboxed
│                     │  Jupyter kernel to verify they run cleanly
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Notebook Assembler  │  Uses nbformat to build the final .ipynb
│ (nbformat)          │  with outputs pre-rendered
└─────────────────────┘
```

**Key design decisions for notebook generation:**
- Each derivation step maps to a (Markdown + Code) cell pair.
- Visualizations are generated for every non-trivial mathematical object.
- The notebook is self-contained: running all cells from top to bottom reproduces the full derivation.
- A "verification badge" cell at the end summarizes which steps were formally verified in Lean.

---

## 10. Phased Implementation Plan

### Phase 1 — Foundation (Weeks 1–2)
- [ ] Set up Python project with `uv`, linting (`ruff`), and testing (`pytest`).
- [ ] Configure `.env` loading with `pydantic-settings` (Gemini, OpenAI, Claude keys).
- [ ] Install Lean 4 + Mathlib4 via `elan`; create `lean_project/`.
- [ ] Build `lean_executor.py` tool: write `.lean` file → run `lake build` → parse output.
- [ ] Build LLM integration with `litellm` — configure all three providers with model routing.
- [ ] Implement a simple single-agent loop: question → LLM generates Lean → verify → retry.
- [ ] Build `notebook_builder.py` — basic notebook generation with `nbformat`.

### Phase 2 — Multi-Agent System (Weeks 3–4)
- [ ] Implement agent abstractions (base agent class, tool registry).
- [ ] Build Research Agent with arXiv + Semantic Scholar tools.
- [ ] Build Formalization Agent with Mathlib-aware prompting.
- [ ] Build Lean Verifier Agent with structured error parsing.
- [ ] Implement Orchestrator with task DAG management.
- [ ] Build agent communication protocol.

### Phase 3 — Intelligence & Retrieval (Weeks 5–6)
- [ ] Build Mathlib4 lemma index with embeddings + ChromaDB.
- [ ] Implement RAG pipeline for Mathlib search during formalization.
- [ ] Add few-shot example retrieval for common proof patterns.
- [ ] Implement proof decomposition strategies (break complex proofs into lemmas).
- [ ] Add support for `sorry`-guided incremental verification.

### Phase 4 — Notebook Generation & Polish (Weeks 7–8)
- [ ] Build full Notebook Generator agent with narrative planning + code generation.
- [ ] Integrate SymPy symbolic computation cells for algebraic derivations.
- [ ] Implement visualization generation (Matplotlib, Plotly) for derivation steps.
- [ ] Build sandboxed notebook execution & validation (run cells, capture outputs).
- [ ] Build Report Generator (Markdown + optional LaTeX).
- [ ] Create evaluation benchmark (miniF2F, selected problems).
- [ ] Implement logging and provenance tracking.
- [ ] Add human-in-the-loop mode (pause for user guidance at key decision points).
- [ ] Write documentation and demo notebooks.
- [ ] End-to-end integration tests.

---

## 11. Risk Analysis & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM generates invalid Lean syntax | High | Iterative retry loop; few-shot examples; fine-tuned prompts with Lean grammar guidance |
| Mathlib4 compilation is slow (~minutes) | Medium | Cache builds; use incremental compilation; pre-compile Mathlib; consider Lean REPL for faster checks |
| Physics formalizations are incomplete in Mathlib | High | Clearly distinguish verified vs. unverified steps; use `sorry` for gaps; build custom axiom sets |
| LLM hallucinated theorems | High | Every claim must pass Lean verification; Research Agent cross-references with known sources |
| API rate limits / costs | Medium | Model routing across Gemini/OpenAI/Claude (use Gemini Flash for lightweight tasks); caching of LLM responses |
| Generated notebook code fails to execute | Medium | Sandboxed pre-execution of all code cells before including in final notebook; auto-repair loop with LLM |
| Lean 4 / Mathlib breaking changes | Low | Pin toolchain version in `lean-toolchain`; use `lake-manifest.json` lockfile |

---

## 12. Alternative Architectural Approaches

### Alt-A: Lean-First Approach
Instead of LLM-first reasoning, start from Lean's type system:
- Use Lean's `#check` and `#search` to explore the type-theoretic landscape.
- The LLM acts as a "tactic suggester" rather than a full proof writer.
- **Pro:** Higher verification success rate. **Con:** Slower; less natural for physics.

### Alt-B: Hybrid Symbolic + Neural
- Integrate a Computer Algebra System (SageMath/SymPy) for symbolic computation.
- Use CAS for derivations, then verify critical steps in Lean.
- **Pro:** Better for physics (differential equations, tensor algebra). **Con:** More complex pipeline.

### Alt-C: Fine-Tuned Model Approach
- Fine-tune an open-source model (e.g., Llama 3) on Lean 4 + Mathlib data.
- Use the fine-tuned model as the primary formalization engine.
- **Pro:** Better Lean code generation out of the box. **Con:** Expensive training; model may become outdated as Mathlib evolves.

### Alt-D: Tree-of-Proofs Search
- Instead of linear retry, explore multiple proof strategies in parallel (breadth-first).
- Use Monte Carlo Tree Search (MCTS) to prioritize promising proof paths.
- **Pro:** Handles hard proofs better. **Con:** Higher compute cost; complex implementation.

---

## 13. Resolved Decisions (from System Investigation)

System investigation performed on the WSL2 development environment. All decisions below are based on confirmed capabilities.

### 13.1 System Profile

| Resource | Value |
|---|---|
| OS | Ubuntu 24.04.3 LTS on WSL2 (kernel 6.6.87.2) |
| CPU | Intel i7-7700HQ, 4 cores / 8 threads @ 2.80 GHz |
| RAM | 16 GB total (~8 GB available) |
| GPU | NVIDIA Quadro M2200, 4 GB VRAM (CUDA libs present, no toolkit) |
| Disk | 1 TB (~896 GB free) |
| Python | 3.12.3 (system); venv at `.venv/` with pip 26.0.1 |
| Node.js | v24.10.0, npm 11.6.1 |
| Build tools | gcc 13.3.0, make 4.3, git 2.43.0, curl, wget, pdftotext |
| **Not installed** | Lean4/elan, Docker, jupyter, LaTeX, pandoc, ollama |
| **Sudo** | Not available (password required) — all installs must be user-local |

### 13.2 API Keys (all validated HTTP 200)

| Key | Provider | Status |
|---|---|---|
| `GEMINI_KEY` | Google Gemini | ✅ Active |
| `OPENAI_KEY` | OpenAI | ✅ Active |
| `CLAUDE_KEY` | Anthropic Claude | ✅ Active |
| `OPENROUTER_KEY` | OpenRouter | ✅ Active |
| `GROK_KEY` | xAI / Grok | ✅ Active |

### 13.3 Confirmed Available Models

**Gemini**: `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.0-flash`
**OpenAI**: `o3`, `o3-mini`, `o4-mini`, `o4-mini-deep-research`, `o1`, `o1-pro`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o`
**Claude**: `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-5`, `claude-sonnet-4-5`, `claude-haiku-4-5`, `claude-3-haiku`

### 13.4 Decision Log

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Agent framework | **LangGraph** | Best state machine / graph model for multi-agent orchestration; good tool integration; langgraph-checkpoint for state persistence |
| 2 | LLM providers | **All three + OpenRouter fallback** | 5 validated API keys; task-based routing maximizes each provider's strengths |
| 3 | Lean interaction mode | **`lake build` initially, REPL later** | `lake build` is simplest to implement; add REPL in Phase 3 for faster iteration |
| 4 | Physics formalization scope | **Partial — `sorry` for physics axioms** | Mathlib has limited physics coverage; verify the math, axiomatize the physics |
| 5 | Local model support | **Deferred (Phase 4+)** | 4 GB VRAM is insufficient for useful math models; API models are superior and available |
| 6 | Package manager | **`uv`** | Installable without sudo (`curl -LsSf https://astral.sh/uv/install.sh \| sh`); fastest Python package manager; replaces pip, venv, and poetry |
| 7 | Notebook visualization | **Matplotlib + Plotly hybrid** | Matplotlib for static publication plots; Plotly for interactive exploration; skip Manim (too heavy for this system) |
| 8 | Notebook execution | **Pre-execute safe cells, leave interactive for user** | Auto-run pure computation cells (SymPy, plots); leave Lean and exploratory cells for user |
| 9 | Lean installation | **`elan` user-local** | `curl https://elan-init.trycloudflare.com/elan-init.sh -sSf \| sh` — no sudo needed |
| 10 | Docker | **Skip** | Not installed, no sudo to install; run everything natively in venv |
| 11 | PDF processing | **`pdftotext` + `PyMuPDF`** | `pdftotext` already installed; PyMuPDF for scanned PDFs with OCR |
| 12 | Embeddings & vector store | **OpenAI `text-embedding-3-small` + ChromaDB** | Good quality, low cost; ChromaDB is lightweight, no Docker needed |

---

## 14. References & Prior Art

- **LeanDojo** — Extracting data from Lean and training models for theorem proving.
- **ReProver** — LLM-based premise selection for Lean proofs.
- **Draft, Sketch, Prove** — Informal-to-formal proof pipeline using language models.
- **LEGO-Prover** — Growing a library of lemmas for LLM-based theorem proving.
- **AlphaProof (DeepMind)** — Reinforcement learning for mathematical proof search.
- **Mathlib4** — The comprehensive Lean 4 mathematics library.
- **miniF2F** — Benchmark for neural theorem proving.

---

*This proposal is a living document. Update it as architectural decisions are made and implementation progresses.*

---

# Appendix A: Test Research Topic

## Sciama's Gravitational Vector Potential, Electromagnetic Dipole Gravity, and the Unification of Gravity with Electromagnetism

### 1. Background & Motivation

The hypothesis that gravity has electromagnetic origins has been explored from multiple independent starting points. This research topic synthesizes **three complementary lines of evidence**:

**A. Sciama's Machian Derivation (1953).** Dennis Sciama published "On the Origin of Inertia" (MNRAS 113, 34–42), deriving Newtonian gravity as a **necessary consequence** of Mach's Principle — the hypothesis that inertia is entirely determined by the mass distribution of the universe. His construction is strikingly electromagnetic in character.

**B. Gallucci's Dipole Mechanism (Electric Universe Theory).** Raymond Gallucci, in "Electromagnetic Gravity? Examination of the Electric Universe Theory," analyzed how neighboring atoms can **distort hydrogen atoms into electric dipoles** through asymmetric Coulomb forces. The resulting dipole-dipole interactions, scaling as $r^{-4}$ between co-linear pairs but aggregating to $r^{-2}$ over extended bodies, may recover the inverse-square law of gravity. The extreme weakness of gravity ($\sim 10^{-39}$ times the electrostatic force) is interpreted as a measure of the minute distortion of subatomic particles.

**C. Classical Gravitoelectromagnetism (GEM).** The weak-field limit of General Relativity produces Maxwell-like "gravitoelectric" and "gravitomagnetic" field equations (Heaviside 1893, Mashhoon 2007). Combined with Kaluza-Klein theory (1921/1926), which embeds the EM vector potential within a 5D metric, there are strong mathematical reasons to suspect a deep structural connection.

Sciama's key construction is strikingly electromagnetic in character:

1. **Inertial forces as EM-like fields.** The centrifugal and Coriolis forces in rotating frames map exactly onto "gravelectric" and "gravomagnetic" fields derived from scalar and vector potentials:

$$\Phi = -\frac{1}{2}(\vec{\omega} \times \vec{r})^2, \qquad \vec{A} = \vec{\omega} \times \vec{r}$$

$$\vec{E}_{\text{grav}} = -\nabla \Phi - \frac{\partial \vec{A}}{\partial t}, \qquad \vec{B}_{\text{grav}} = \nabla \times \vec{A}$$

These are formally **identical** to the electric and magnetic fields derived from electromagnetic potentials.

2. **Matter as the source of the potential.** Sciama then takes the decisive Machian step: instead of treating these potentials as properties of an absolute inertial field, he defines them as integrals over all matter in the observable universe, in direct analogy with electromagnetic retarded potentials:

$$A_\mu(x) = -\int_V \frac{p_\mu(x')}{c\,r} \, dV$$

where $p_\mu = (\rho\sqrt{c^2 + v^2},\; \rho v_1,\; \rho v_2,\; \rho v_3)$ is the four-momentum density of cosmic matter.

3. **Gravity emerges from inhomogeneity.** In a perfectly homogeneous universe, the gravelectric field vanishes and bodies follow inertial paths. But when a local mass $M$ is present, the potential becomes $A_0 = \Phi + \phi$ where $\phi = -M/r$, and Newton's law of gravitation is recovered:

$$\frac{\partial \vec{v}}{\partial t} = -G \frac{M}{r^2} \hat{r}, \qquad \text{where } G = \frac{c^2}{\Phi}$$

The gravitational constant $G$ is **not** a fundamental constant but is inversely proportional to the total gravitational potential $\Phi = 2\pi\rho c^2 \tau^2$ of the observable universe. Its smallness reflects the universe's vastness.

4. **Gravity is predicted, not postulated.** Unlike General Relativity, which takes the Einstein field equations as axiomatic, Sciama's approach **derives** the existence of gravity as an inevitable consequence of defining inertia relationally. This is arguably the deepest explanation of why gravity exists at all.

### 2. The Central Question

**If gravity can be expressed entirely in terms of a four-vector potential with the same mathematical structure as electromagnetism, is this formal analogy a hint of a deeper physical identity? Specifically: can Sciama's Machian framework and Gallucci's dipole mechanism be shown to be complementary descriptions of a single underlying phenomenon — gravity as an emergent electromagnetic effect?**

In other words: Sciama shows gravity emerges from a cosmological EM-like potential (top-down, from the universe to local physics). Gallucci shows gravity could emerge from atomic-scale dipole distortions (bottom-up, from atomic physics to macroscopic force laws). **Can these two directions be reconciled into a unified electromagnetic theory of gravity?**

### 3. Specific Research Sub-Questions

#### 3.1 Mathematical Structure Comparison
- Sciama's gravitational four-potential $A_\mu^{(\text{grav})}$ and the electromagnetic four-potential $A_\mu^{(\text{EM})}$ obey formally identical equations. **What are the precise conditions under which these two potentials can be treated as components of a single unified potential?**
- Can the gravitational and electromagnetic potentials be combined into a higher-rank object (e.g., a 5D vector potential à la Kaluza-Klein) while preserving the Machian origin of $G$?

#### 3.2 The Charge–Mass Asymmetry Problem
- In electromagnetism, positive and negative charges exist, causing distant matter to be electrically neutral and EM effects to be local. For gravity, there is only positive mass, so the inertial potential is dominated by the most distant matter.
- **Can this asymmetry be reinterpreted?** For instance, if antimatter carries "negative gravitational charge" (speculative but testable), would Sciama's framework naturally accommodate electromagnetic-like cancellation for gravity at some scale?

#### 3.3 The Spin-2 vs. Spin-1 Obstacle
- Standard gravitoelectromagnetism (GEM) in the weak-field limit of GR produces Maxwell-like equations, but the GEM equations are **not Lorentz-invariant** because gravity's source is the rank-2 stress-energy tensor rather than the rank-1 four-current. This traces to gravity being a spin-2 field vs. EM being spin-1.
- Sciama's model, however, works with a **spin-1 (vector)** gravitational potential. **Is this a deficiency of Sciama's model, or evidence that the spin-2 description is an effective theory of a deeper spin-1 reality?**
- Can Sciama's vector potential be shown to reproduce linearized GR (including gravitational waves) under appropriate conditions?

#### 3.4 Derivation of G from Electromagnetic Constants
- Sciama derives $G = c^2 / \Phi$ where $\Phi$ depends on the cosmic mass density $\rho$ and the Hubble time $\tau$. If gravity has electromagnetic origins, **can $G$ be expressed purely in terms of electromagnetic constants** ($\epsilon_0$, $\mu_0$, $e$, $m_e$) and cosmological parameters?
- Dirac's Large Number Hypothesis noted $G m_p m_e / \hbar c \sim (e^2/m_e c^2) / (c/H_0)$. **Does Sciama's framework provide a physical mechanism for this numerological coincidence?**

#### 3.5 Kaluza-Klein Connection
- Kaluza (1921) showed that 5D general relativity naturally produces both Einstein's equations and Maxwell's equations, with the electromagnetic vector potential embedded in the 5D metric. The "Kaluza miracle" is that EM stress-energy emerges from the 5D vacuum.
- **Can Sciama's Machian construction be embedded within Kaluza-Klein theory?** Specifically, can the 5D Kaluza-Klein metric be re-derived starting from a Machian integral over matter, generalizing Sciama's 4D approach?
- If so, does the resulting theory resolve Sciama's known limitations (non-relativistic, no metrical effects)?

#### 3.6 The Atomic Dipole Mechanism (Gallucci)
- Gallucci models three aligned hydrogen atoms (radius $R$, spacing $3R$ center-to-center). Each atom's electron and proton experience six Coulomb forces from the two neighbors. The net effect is:
  - The reference electron orbit is **repelled** (pushed away from neighbors) with a scaled net force difference of $\Delta F_{\text{scaled}} = 0.08744$ at $\theta = 0$.
  - The reference proton is **attracted** (pulled toward neighbors) with a scaled net force of $0.01717$.
  - The atom becomes an **electric dipole**, with electron displacement $\sim 4.86 \times 10^{-15}$ m ($\sim 0.01\%$ of Bohr radius) and proton displacement $\sim 5.20 \times 10^{-19}$ m ($\sim 10^{-6}\%$), a ratio of $\sim 10{,}000$ reflecting the $\sim 1{,}836$-fold mass ratio.
- **Key question**: Can the dipole-dipole force ($\propto r^{-4}$) between co-linear atomic dipoles be rigorously shown to aggregate to an inverse-square law over extended 3D bodies? This requires integrating the dipole interaction over a solid body's volume — a calculation Gallucci acknowledges but does not complete.
- **Can the $10^{39}$ ratio be derived?** The dipole moment $p = q \cdot d$ where $d \sim 10^{-15}$ m. The dipole-dipole force is $F \propto p^2/r^4$. After integration over a macroscopic body, **does the resulting effective $G$ match $6.674 \times 10^{-11}$** N m² kg⁻²?
- **Sensitivity analysis**: Gallucci notes the result depends critically on the assumed electron orbital speed (speed of light vs. $c/22$ vs. $c/137$). The displacement scales as $v^{-2}$. **Which orbital speed produces physically consistent results?**

#### 3.7 Reconciling Top-Down (Sciama) and Bottom-Up (Gallucci)
- Sciama derives $G = c^2/\Phi$ from the cosmological mass integral. Gallucci's dipole model would derive $G$ from atomic-scale electromagnetic distortions. **Are these the same $G$?**
- If Sciama's $\Phi = 2\pi\rho c^2 \tau^2$ (cosmic potential) determines $G$, and Gallucci's dipole moment $p = qd$ is determined by atomic physics, then consistency requires $d \propto \Phi^{-1}$. **Is there a physical mechanism by which the cosmic mass distribution determines the degree of atomic dipole distortion?**
- Gallucci's model uses classical electron orbits (Bohr model). **Can it be reformulated quantum-mechanically?** The electron "cloud" reinterpretation is noted but not developed.

#### 3.8 Predictions & Experimental Tests
- If gravity is electromagnetic in origin, there should be measurable consequences:
  - **Modified gravitomagnetic effects** near rapidly rotating masses (frame-dragging deviations from GR predictions). Compare with Gravity Probe B data.
  - **Variation of $G$** on cosmological timescales (since $G = c^2/\Phi$ and $\Phi$ changes as the universe expands).
  - **Coupling between EM and gravitational fields** beyond what GR predicts (e.g., photon mass in gravitational fields, EM-gravity cross-terms).
  - **Atomic dipole effects**: If gravity arises from dipole distortion, extremely isolated atoms (in deep vacuum, far from neighbors) should exhibit **reduced gravitational mass** — a testable prediction distinct from GR.
  - **Material-dependent $G$?** Different atomic structures (polarizability, electron orbital radii) could produce slightly different effective gravitational coupling — measurable as composition-dependent violations of the Weak Equivalence Principle.

### 4. Formalization Strategy (for Lean 4)

The following components are candidates for formal verification:

| Component | Lean Formalization Target |
|---|---|
| Sciama's potential integral | Define $A_\mu$ as an integral over a matter distribution; prove it reduces to Newtonian form for point mass |
| Derivation of $G = c^2/\Phi$ | Formal proof from the homogeneous + inhomogeneous universe construction |
| Centrifugal/Coriolis recovery | Prove the rotating universe produces the correct inertial forces from the four-potential |
| Equivalence to Newton's law | Prove $\partial_t \vec{v} = -G M r^{-2} \hat{r}$ from the inhomogeneous Machian potential |
| GEM equations from Sciama | Derive the gravitoelectric and gravitomagnetic field equations from the four-potential |
| Kaluza-Klein decomposition | Prove that the 5D metric decomposes into 4D gravity + EM vector potential (purely mathematical) |
| Dipole force law | Prove the force between two co-linear electric dipoles scales as $r^{-4}$; then prove integration over a 3D body yields $r^{-2}$ |
| Gallucci displacement calc | Formalize the 6-force Coulomb calculation for three aligned H atoms; verify the displacement ratio $\sim m_p/m_e$ |
| Dipole moment → $G$ derivation | Formally derive effective gravitational constant from dipole-dipole interaction integrated over macroscopic body |

### 5. Notebook Visualization Plan

| Derivation Step | Visualization |
|---|---|
| Cosmic matter integral for $\Phi$ | 3D plot of mass distribution in expanding universe; $\Phi$ as function of Hubble radius |
| Rotating universe → inertial forces | Vector field plot of centrifugal + Coriolis fields; animated Foucault pendulum |
| Inhomogeneous potential → gravity | Contour plot of $A_0 = \Phi + \phi$ near a point mass; gravity as gradient |
| $G = c^2/\Phi$ scaling | Plot of $G$ vs. cosmological parameters; comparison with Dirac's Large Numbers |
| EM vs. gravity field comparison | Side-by-side vector field plots of Coulomb vs. Newton, magnetic dipole vs. gravitomagnetic (Lense-Thirring) |
| Kaluza-Klein 5D metric structure | Visualization of the 5D metric decomposition; projection from 5D to 4D+EM |
| Gravitomagnetic precession | Animated gyroscope precession (Gravity Probe B) under Sciama's prediction vs. GR |
| Gallucci 3-atom geometry | Reproduce Fig. 2 from Gallucci: three aligned H atoms with force vectors on reference electron/proton |
| Electron orbit distortion | Plot the distorted electron orbit (Fig. 4 from Gallucci): near-side vs. far-side asymmetry |
| Net force on reference electron | Plot scaled net force vs. $\theta$ for near/far hemispheres (reproducing Fig. 3 from Gallucci) |
| Dipole-to-gravity aggregation | 3D visualization of how $r^{-4}$ dipole forces integrate to $r^{-2}$ over a macroscopic sphere |
| Displacement vs. orbital speed | Sensitivity plot: electron/proton displacement as function of assumed orbital speed ($c$, $c/22$, $c/137$) |

### 6. Key References

- Sciama, D. W. (1953). "On the Origin of Inertia." *Monthly Notices of the Royal Astronomical Society*, 113(1), 34–42.
- Sciama, D. W. (1953). "On the Origin of Inertia." PhD thesis, University of Cambridge.
- Fay, J. (2024). "On Sciama 1953." Preprint / commentary.
- Kaluza, T. (1921). "Zum Unitätsproblem der Physik." *Sitzungsber. Preuss. Akad. Wiss.*, 966–972.
- Klein, O. (1926). "Quantentheorie und fünfdimensionale Relativitätstheorie." *Zeitschrift für Physik*, 37(12), 895–906.
- Heaviside, O. (1893). "A Gravitational and Electromagnetic Analogy." *Electromagnetic Theory*, Vol. 1, 455–464.
- Reissner, H. (1915). "Über eine Möglichkeit die Gravitation als unmittelbare Folge der Relativität der Trägheit abzuleiten." *Physik. Zeitschr.*, 16, 179–185.
- Schrödinger, E. (1925/1995). "The Possibility of Fulfillment of the Relativity Requirement in Classical Mechanics." In *Mach's Principle*, 147–158.
- Mashhoon, B. (2007). "Gravitoelectromagnetism: A Brief Review." In *The Measurement of Gravitomagnetism*, Nova Science.
- Jefimenko, O. D. (2006). *Gravitation and Cogravitation*. Electret Scientific.
- Brans, C. H. & Dicke, R. H. (1961). "Mach's Principle and a Relativistic Theory of Gravitation." *Physical Review*, 124(3), 925–935.
- Overduin, J. M. & Wesson, P. S. (1997). "Kaluza-Klein Gravity." *Physics Reports*, 283(5), 303–378.
- Gallucci, R. H. V. "Electromagnetic Gravity? Examination of the Electric Universe Theory." (`dipole_gravity.pdf`)
- Wal Thornhill / Electric Universe. "Electric Gravity in an Electric Universe." http://www.holoscience.com/wp/electric-gravity-in-an-electric-universe/
- Hughes, K. (2014). *The Binary Universe: A Theory of Time*. Hughes Publishing.

### 7. Why This Topic Tests the Agentic Researcher

This research topic is an ideal stress test for the DeepLean system because it requires:

| Capability | Challenge |
|---|---|
| **Literature search** | Spanning 1893 (Heaviside) to 2024 (Fay), across classical mechanics, GR, Kaluza-Klein, and modern GEM |
| **Mathematical formalization** | Translating vector potential integrals, coordinate transformations, and field equations into Lean 4 |
| **Multi-step derivation** | The chain Mach's Principle → inertial field → EM analogy → matter integral → gravity is a 5+ step logical argument |
| **Symbolic computation** | SymPy for tensor calculus (Christoffel symbols, Ricci tensor in Kaluza-Klein), integral evaluation, series expansions |
| **Visualization** | Vector fields, potential surfaces, animated rotating frames, 5D-to-4D projections |
| **Critical analysis** | Must identify known obstacles (spin-2 vs spin-1, Lorentz invariance, metrical effects) rather than blindly confirming the hypothesis |
| **Lean verification** | Some steps are formally provable (mathematical derivations); others require stating explicit physical axioms |
| **Intellectual honesty** | The hypothesis that "gravity is electromagnetic" is speculative; the system must clearly flag what is proven vs. conjectured |
| **Cross-source synthesis** | Must reconcile Sciama's top-down cosmological approach with Gallucci's bottom-up atomic approach — two very different frameworks targeting the same question |
| **Numerical reproduction** | Must reproduce Gallucci's force calculations, displacement estimates, and sensitivity analysis from first principles using SymPy |
| **PDF extraction** | Must handle scanned PDFs (Sciama 1953) and text-extractable PDFs (Fay commentary, Gallucci) with different processing strategies |
