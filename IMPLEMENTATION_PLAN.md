# DeepLean — Detailed Implementation Plan

> Based on architecture decisions confirmed in `project.md` §13.
> Target system: WSL2 Ubuntu 24.04 · Python 3.12 · No sudo · No Docker.

---

## Table of Contents

1. [Phase 0 — Environment Bootstrap](#phase-0--environment-bootstrap)
2. [Phase 1 — Core Infrastructure](#phase-1--core-infrastructure-weeks-12)
3. [Phase 2 — Multi-Agent System](#phase-2--multi-agent-system-weeks-34)
4. [Phase 3 — Intelligence & Retrieval](#phase-3--intelligence--retrieval-weeks-56)
5. [Phase 4 — Notebook Generation & Polish](#phase-4--notebook-generation--polish-weeks-78)
6. [File-by-File Implementation Guide](#file-by-file-implementation-guide)
7. [Dependency Graph](#dependency-graph)
8. [Testing Strategy](#testing-strategy)
9. [Acceptance Criteria](#acceptance-criteria)

---

## Phase 0 — Environment Bootstrap

**Goal:** Stand up a fully working development environment from the current bare WSL2 system.  
**Duration:** ~2 hours (one-time setup).  
**Constraint:** No sudo — everything is user-local.

### 0.1 Install `uv` (Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc   # or ~/.profile — adds ~/.local/bin to PATH
uv --version
```

### 0.2 Initialize Python Project

```bash
cd /home/jude/deep_lean
uv init --python 3.12
```

This creates `pyproject.toml`. Then configure it:

```toml
[project]
name = "deep-lean"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    # --- Core ---
    "litellm>=1.55",
    "langgraph>=0.4",
    "langchain-core>=0.3",
    "pydantic>=2.10",
    "pydantic-settings>=2.7",
    "python-dotenv>=1.0",
    # --- Search & Retrieval ---
    "arxiv>=2.1",
    "semanticscholar>=0.8",
    "chromadb>=0.6",
    "openai>=1.60",          # for embeddings
    # --- Symbolic & Numerical ---
    "sympy>=1.13",
    "numpy>=2.1",
    "scipy>=1.14",
    # --- Notebook ---
    "nbformat>=5.10",
    "nbconvert>=7.16",
    "jupyter-client>=8.6",
    "ipykernel>=6.29",
    # --- Visualization ---
    "matplotlib>=3.9",
    "plotly>=5.24",
    # --- PDF ---
    "PyMuPDF>=1.25",
    # --- Logging & Observability ---
    "structlog>=24.4",
    # --- Dev ---
    "ruff>=0.8",
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "TCH"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

```bash
uv sync   # creates .venv, installs all deps
```

### 0.3 Install Lean 4 + Mathlib4

```bash
# Install elan (Lean version manager) — user-local, no sudo
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y
source ~/.bashrc
elan --version
lean --version
```

```bash
# Create the Lean project inside deep_lean/
mkdir -p lean_project && cd lean_project
lake +leanprover/lean4:stable init DeepLean math
# This creates lakefile.lean with Mathlib dependency

# First build — downloads Mathlib cache (~10–20 min first time)
lake exe cache get   # download pre-built Mathlib oleans
lake build           # compile project scaffolding
cd ..
```

### 0.4 Verify `.env`

The `.env` already exists with validated keys. Create `.env.example` for reference:

```bash
cat > .env.example << 'EOF'
# API Keys — rename to .env and fill in values
GEMINI_KEY=
OPENAI_KEY=
CLAUDE_KEY=
OPENROUTER_KEY=
GROK_KEY=
EOF
```

### 0.5 Git Setup

```bash
cat > .gitignore << 'EOF'
.env
.venv/
__pycache__/
*.pyc
.ruff_cache/
.pytest_cache/
lean_project/build/
lean_project/.lake/
output/
*.egg-info/
dist/
.coverage
htmlcov/
EOF

git init
git add -A
git commit -m "chore: initial project scaffold"
```

### Phase 0 Deliverables

| Deliverable | Verification |
|---|---|
| `uv` installed, `uv --version` works | ✅ |
| `pyproject.toml` with all deps | `uv sync` succeeds |
| `.venv/` with Python 3.12 + all packages | `uv run python -c "import litellm, langgraph"` |
| Lean 4 toolchain | `lean --version` prints `leanprover/lean4:v4.x.0` |
| `lean_project/` with Mathlib | `cd lean_project && lake build` succeeds |
| `.env` present, `.env.example` committed | `test -f .env` |
| `.gitignore` covers all build artifacts | `git status` is clean |

---

## Phase 1 — Core Infrastructure (Weeks 1–2)

**Goal:** Build the foundation layer — config, LLM integration, Lean executor, and a working single-agent proof loop.

### Step 1.1 — Configuration Module

**File:** `src/config.py`

```python
"""
Load .env, remap key names for litellm, expose typed settings.
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()
# Remap our key names → litellm expected names
os.environ["GEMINI_API_KEY"]    = os.environ.get("GEMINI_KEY", "")
os.environ["OPENAI_API_KEY"]    = os.environ.get("OPENAI_KEY", "")
os.environ["ANTHROPIC_API_KEY"] = os.environ.get("CLAUDE_KEY", "")
os.environ["OPENROUTER_API_KEY"]= os.environ.get("OPENROUTER_KEY", "")

class Settings(BaseSettings):
    # Model routing
    orchestration_model:       str = "anthropic/claude-sonnet-4-6"
    reasoning_model:           str = "openai/o3"
    formalization_model:       str = "openai/o3"
    research_model:            str = "anthropic/claude-opus-4-6"
    notebook_code_model:       str = "gemini/gemini-2.5-pro"
    notebook_narrative_model:  str = "anthropic/claude-sonnet-4-6"
    multimodal_model:          str = "gemini/gemini-2.5-pro"
    report_model:              str = "anthropic/claude-opus-4-6"
    fast_model:                str = "gemini/gemini-2.5-flash"
    error_analysis_model:      str = "anthropic/claude-sonnet-4-6"
    fallback_coding_model:     str = "openai/gpt-4.1"
    cheap_model:               str = "openai/gpt-4.1-mini"
    
    # Lean
    lean_project_dir:   str = "lean_project"
    lean_max_retries:   int = 5
    lean_timeout:       int = 120  # seconds per build
    
    # Paths
    output_dir:         str = "output"
    reports_dir:        str = "output/reports"
    notebooks_dir:      str = "output/notebooks"
    prompts_dir:        str = "src/prompts"
    
    # Embeddings
    embedding_model:    str = "text-embedding-3-small"
    chroma_persist_dir: str = ".chromadb"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Tasks:**
- [ ] Create `src/__init__.py`, `src/config.py`
- [ ] Write `tests/test_config.py` — verify settings load, keys are present, models are valid strings
- [ ] Test: `uv run pytest tests/test_config.py`

### Step 1.2 — Data Models

**File:** `src/models.py`

Define Pydantic models for all data flowing through the system:

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class TaskStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    SUCCESS   = "success"
    FAILED    = "failed"
    RETRYING  = "retrying"

class ResearchQuestion(BaseModel):
    """The user's input query."""
    question: str
    context: str = ""               # optional background
    source_pdfs: list[str] = []     # paths to reference PDFs

class LiteratureResult(BaseModel):
    """Output from the Research Agent."""
    query: str
    papers: list[dict]              # {title, authors, abstract, url, year}
    key_theorems: list[str]
    summary: str

class InformalProof(BaseModel):
    """A natural-language mathematical argument."""
    steps: list[str]
    assumptions: list[str]
    conclusion: str

class LeanCode(BaseModel):
    """Generated Lean 4 source code."""
    filename: str
    source: str
    imports: list[str] = []
    depends_on: list[str] = []      # other .lean files

class LeanResult(BaseModel):
    """Output from running lake build."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    errors: list[dict] = []         # {line, column, message, severity}
    build_time_seconds: float = 0.0

class ProofAttempt(BaseModel):
    """One cycle of formalize → verify."""
    attempt_number: int
    lean_code: LeanCode
    result: LeanResult
    timestamp: datetime = Field(default_factory=datetime.now)

class NotebookPlan(BaseModel):
    """Structure plan for a generated notebook."""
    title: str
    sections: list[dict]            # {heading, type, description}
    visualization_specs: list[dict] # {step, chart_type, data_source}

class ResearchOutput(BaseModel):
    """The complete output of a research session."""
    question: ResearchQuestion
    literature: LiteratureResult | None = None
    informal_proof: InformalProof | None = None
    proof_attempts: list[ProofAttempt] = []
    final_lean_code: LeanCode | None = None
    verified: bool = False
    report_path: str | None = None
    notebook_path: str | None = None
    total_llm_calls: int = 0
    total_cost_usd: float = 0.0
```

**Tasks:**
- [ ] Create `src/models.py` with all models above
- [ ] Write `tests/test_models.py` — test serialization, defaults, validation
- [ ] Ensure all downstream code uses these models (no raw dicts)

### Step 1.3 — LLM Client Wrapper

**File:** `src/llm.py`

Wrap `litellm` with model routing, retries, cost tracking, and structured output:

```python
"""
Unified LLM interface via litellm with:
- Model routing (pick model by task role)
- Automatic fallback on failure / rate-limit
- Response caching (optional)
- Cost tracking
- Structured output via Pydantic
"""
import litellm
from litellm import completion, acompletion
from src.config import settings

FALLBACK_CHAINS = {
    settings.orchestration_model: [settings.fast_model],
    settings.reasoning_model:     [settings.research_model],
    settings.formalization_model:  [settings.fallback_coding_model],
    settings.research_model:       [settings.multimodal_model],
    settings.notebook_code_model:  [settings.fallback_coding_model],
    settings.report_model:         [settings.multimodal_model],
}

async def call_llm(
    model: str,
    messages: list[dict],
    temperature: float = 0.0,
    max_tokens: int = 4096,
    response_format: type | None = None,  # Pydantic model for structured output
    **kwargs,
) -> str | dict:
    """Call an LLM with automatic fallback."""
    ...
```

**Key behaviors:**
- `call_llm(settings.reasoning_model, messages)` → tries `o3`, falls back to `claude-opus-4-6`
- Structured output: pass a Pydantic model as `response_format` → get a validated dict back
- Cost tracking: accumulate `litellm.completion_cost()` per session
- Async-first: all calls are `async`, with a sync wrapper for simple scripts

**Tasks:**
- [ ] Create `src/llm.py` with `call_llm()`, `call_llm_sync()`, fallback chains
- [ ] Implement cost tracking (session-level accumulator)
- [ ] Implement optional response caching (hash messages → cache response on disk)
- [ ] Write `tests/test_llm.py` — mock litellm calls, test fallback logic, test cost tracking
- [ ] Manual smoke test: call each of the 3 providers with a trivial prompt

### Step 1.4 — Lean Executor Tool

**File:** `src/tools/lean_executor.py`

The bridge between Python and Lean 4:

```python
"""
Write Lean files, run `lake build`, parse output.
"""
import asyncio
import subprocess
from pathlib import Path
from src.config import settings
from src.models import LeanCode, LeanResult

class LeanExecutor:
    def __init__(self, project_dir: str = settings.lean_project_dir):
        self.project_dir = Path(project_dir).resolve()
        self.generated_dir = self.project_dir / "DeepLean" / "Generated"
        self.generated_dir.mkdir(parents=True, exist_ok=True)
    
    def write_lean_file(self, code: LeanCode) -> Path:
        """Write a .lean file into the project."""
        path = self.generated_dir / code.filename
        path.write_text(code.source)
        return path
    
    async def build(self, timeout: int = settings.lean_timeout) -> LeanResult:
        """Run `lake build` and parse the output."""
        proc = await asyncio.create_subprocess_exec(
            "lake", "build",
            cwd=str(self.project_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            return LeanResult(success=False, stderr="Build timed out")
        
        return LeanResult(
            success=proc.returncode == 0,
            stdout=stdout.decode(),
            stderr=stderr.decode(),
            errors=self._parse_errors(stderr.decode()),
        )
    
    def _parse_errors(self, stderr: str) -> list[dict]:
        """Parse Lean compiler error messages into structured dicts."""
        ...
    
    async def verify(self, code: LeanCode) -> LeanResult:
        """Write file + build in one call."""
        self.write_lean_file(code)
        return await self.build()
```

**Tasks:**
- [ ] Create `src/tools/__init__.py`, `src/tools/lean_executor.py`
- [ ] Implement `_parse_errors()` — regex parsing of Lean error format: `file:line:col: error: message`
- [ ] Write `tests/test_tools/test_lean_executor.py` — test file writing, error parsing (mock subprocess)
- [ ] Integration test: write a trivial Lean theorem, build, confirm success
- [ ] Integration test: write an invalid theorem, build, confirm errors are parsed

### Step 1.5 — Lean Error Parser

**File:** `src/utils/lean_parser.py`

Detailed parsing of Lean 4 compiler output into actionable feedback:

```python
"""
Parse Lean compiler errors into structured, LLM-friendly feedback.
"""
import re

class LeanError:
    file: str
    line: int
    column: int
    severity: str       # "error" | "warning" | "info"
    message: str
    category: str       # "type_mismatch" | "unknown_identifier" | "tactic_failed" | ...
    suggestion: str     # auto-generated repair hint

ERROR_PATTERNS = {
    "type_mismatch": re.compile(r"type mismatch"),
    "unknown_identifier": re.compile(r"unknown identifier '(.+?)'"),
    "tactic_failed": re.compile(r"tactic '(.+?)' failed"),
    "declaration_uses_sorry": re.compile(r"declaration uses 'sorry'"),
    "missing_import": re.compile(r"unknown namespace '(.+?)'"),
}

def parse_lean_output(stderr: str) -> list[LeanError]:
    """Parse raw stderr into structured errors."""
    ...

def format_for_llm(errors: list[LeanError]) -> str:
    """Format errors as a clear prompt section for the Formalization Agent."""
    ...
```

**Tasks:**
- [ ] Create `src/utils/__init__.py`, `src/utils/lean_parser.py`
- [ ] Implement all error category patterns
- [ ] Write `format_for_llm()` — produces clean text for LLM repair prompts
- [ ] Write `tests/test_utils/test_lean_parser.py` with sample error outputs

### Step 1.6 — Single-Agent Proof Loop

**File:** `src/agents/single_loop.py`

The simplest end-to-end pipeline — no multi-agent orchestration yet:

```
User question
    → LLM generates informal proof sketch
    → LLM translates to Lean 4
    → Lean executor builds
    → If error: feed errors back to LLM, retry (up to N times)
    → Return result
```

```python
async def single_agent_prove(question: str) -> ResearchOutput:
    """
    The simplest proof pipeline: one LLM, iterative Lean verification.
    This validates the full stack before building multi-agent.
    """
    output = ResearchOutput(question=ResearchQuestion(question=question))
    executor = LeanExecutor()
    
    # Step 1: Generate informal proof
    informal = await call_llm(
        settings.reasoning_model,
        messages=[{"role": "user", "content": f"Prove: {question}\n\nGive a step-by-step proof."}]
    )
    
    # Step 2: Translate to Lean 4
    lean_source = await call_llm(
        settings.formalization_model,
        messages=[{
            "role": "user",
            "content": f"Translate this proof to Lean 4 using Mathlib:\n\n{informal}"
        }]
    )
    
    # Step 3: Verify with retries
    for attempt in range(settings.lean_max_retries):
        code = LeanCode(filename="Proof.lean", source=lean_source)
        result = await executor.verify(code)
        output.proof_attempts.append(
            ProofAttempt(attempt_number=attempt + 1, lean_code=code, result=result)
        )
        if result.success:
            output.verified = True
            output.final_lean_code = code
            break
        # Feed errors back
        error_feedback = format_for_llm(parse_lean_output(result.stderr))
        lean_source = await call_llm(
            settings.formalization_model,
            messages=[{
                "role": "user",
                "content": f"This Lean code failed:\n```lean\n{lean_source}\n```\n\nErrors:\n{error_feedback}\n\nFix the code."
            }]
        )
    
    return output
```

**Tasks:**
- [ ] Create `src/agents/__init__.py`, `src/agents/single_loop.py`
- [ ] Implement the loop above
- [ ] Write a CLI entry point: `uv run python -m src.agents.single_loop "sqrt 2 is irrational"`
- [ ] Test with 3 problems of increasing difficulty:
  1. `theorem : 1 + 1 = 2` (trivial)
  2. `theorem : ∀ n : ℕ, 0 ≤ n` (uses Nat)
  3. `theorem : Irrational (Real.sqrt 2)` (uses Mathlib)
- [ ] Record success rate, average retries, cost per problem

### Step 1.7 — Basic Notebook Builder

**File:** `src/tools/notebook_builder.py`

Programmatic Jupyter notebook construction:

```python
"""
Build .ipynb files programmatically using nbformat.
"""
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
from pathlib import Path

class NotebookBuilder:
    def __init__(self, title: str):
        self.nb = new_notebook()
        self.nb.metadata.kernelspec = {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        }
        self.add_markdown(f"# {title}")
    
    def add_markdown(self, content: str) -> "NotebookBuilder":
        self.nb.cells.append(new_markdown_cell(content))
        return self
    
    def add_code(self, source: str, outputs: list | None = None) -> "NotebookBuilder":
        cell = new_code_cell(source)
        if outputs:
            cell.outputs = outputs
        self.nb.cells.append(cell)
        return self
    
    def add_lean_block(self, lean_source: str, verified: bool = False) -> "NotebookBuilder":
        badge = "✅ Verified" if verified else "⚠️ Unverified"
        md = f"### Lean 4 Proof {badge}\n\n```lean\n{lean_source}\n```"
        self.nb.cells.append(new_markdown_cell(md))
        return self
    
    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            nbformat.write(self.nb, f)
        return path
```

**Tasks:**
- [ ] Create `src/tools/notebook_builder.py`
- [ ] Write `tests/test_tools/test_notebook_builder.py` — create a notebook, verify it's valid JSON, verify cell types
- [ ] Integration test: build a simple notebook and open it in `jupyter` (manual verification)

### Step 1.8 — Structured Logging

**File:** `src/utils/logging.py`

```python
import structlog

def setup_logging(log_level: str = "INFO"):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
    )

log = structlog.get_logger()
```

**Tasks:**
- [ ] Create `src/utils/logging.py`
- [ ] Integrate into `llm.py` (log every LLM call: model, tokens, cost, latency)
- [ ] Integrate into `lean_executor.py` (log build commands, results)

### Step 1.9 — Provenance Tracker

**File:** `src/utils/provenance.py`

Record every action for auditability:

```python
"""
Append-only JSON log of all LLM calls, tool invocations, and decisions.
"""
import json
from pathlib import Path
from datetime import datetime

class ProvenanceTracker:
    def __init__(self, session_id: str):
        self.log_path = Path(f"output/provenance/{session_id}.jsonl")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def record(self, event_type: str, data: dict):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **data,
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

**Tasks:**
- [ ] Create `src/utils/provenance.py`
- [ ] Wire into `llm.py` and `lean_executor.py`
- [ ] Test: run single_loop, confirm `.jsonl` log is written with all events

### Phase 1 Exit Criteria

| Criterion | Test |
|---|---|
| Config loads all 5 API keys | `pytest tests/test_config.py` |
| LLM calls work across 3 providers | Manual smoke test with trivial prompts |
| Lean executor can write, build, and parse | `pytest tests/test_tools/test_lean_executor.py` |
| Single-agent loop solves `1+1=2` in Lean | `python -m src.agents.single_loop "1 + 1 = 2"` |
| Notebook builder creates valid `.ipynb` | `pytest tests/test_tools/test_notebook_builder.py` |
| Provenance log is written | `.jsonl` file exists after a run |

---

## Phase 2 — Multi-Agent System (Weeks 3–4)

**Goal:** Replace the single-agent loop with a LangGraph-based multi-agent graph with specialized agents.

### Step 2.1 — Agent Base Class

**File:** `src/agents/base.py`

```python
from abc import ABC, abstractmethod
from src.llm import call_llm
from src.utils.logging import log

class BaseAgent(ABC):
    """Base class for all DeepLean agents."""
    
    name: str
    model: str            # default LLM model for this agent
    system_prompt: str    # loaded from src/prompts/{name}.md
    
    @abstractmethod
    async def run(self, state: dict) -> dict:
        """Execute the agent's core logic, reading/writing to shared state."""
        ...
    
    async def llm(self, messages: list[dict], **kwargs) -> str:
        """Convenience: call this agent's assigned model."""
        return await call_llm(self.model, messages, **kwargs)
```

**Tasks:**
- [ ] Create `src/agents/base.py`
- [ ] Define `AgentState` TypedDict for LangGraph state (shared across all nodes)

### Step 2.2 — LangGraph State & Graph Definition

**File:** `src/agents/graph.py`

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Shared state flowing through the LangGraph."""
    question: str
    research_context: str
    informal_proof: str
    lean_code: str
    lean_errors: str
    lean_verified: bool
    attempt_count: int
    report_md: str
    notebook_path: str
    messages: Annotated[list, add_messages]

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("formalizer", formalizer_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("reporter", reporter_node)
    graph.add_node("notebook_gen", notebook_gen_node)
    
    # Define edges
    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "researcher")
    graph.add_edge("researcher", "formalizer")
    graph.add_edge("formalizer", "verifier")
    graph.add_conditional_edges(
        "verifier",
        route_after_verification,     # success → reporter, failure → formalizer (retry)
        {"retry": "formalizer", "accept": "reporter", "give_up": "reporter"},
    )
    graph.add_edge("reporter", "notebook_gen")
    graph.add_edge("notebook_gen", END)
    
    return graph.compile()
```

**Tasks:**
- [ ] Create `src/agents/graph.py`
- [ ] Define `AgentState` with all necessary fields
- [ ] Implement `route_after_verification()` — check `lean_verified` and `attempt_count < max`
- [ ] Write `tests/test_agents/test_graph.py` — test graph topology, routing logic

### Step 2.3 — Research Agent

**File:** `src/agents/researcher.py`

**Tools:** `src/tools/arxiv_search.py`, `src/tools/semantic_scholar.py`, `src/tools/pdf_reader.py`

| Sub-step | Implementation |
|---|---|
| arXiv search | Use `arxiv` Python package; query by topic; extract title, abstract, PDF URL |
| Semantic Scholar | Use `semanticscholar` package; find related papers by keyword |
| PDF extraction | `pdftotext` for text PDFs; `PyMuPDF` for scanned PDFs |
| Synthesis | Send collected abstracts + question to `research_model`; get `LiteratureResult` |

```python
class ResearcherAgent(BaseAgent):
    name = "researcher"
    model = settings.research_model     # claude-opus-4-6
    
    async def run(self, state: AgentState) -> dict:
        # 1. Search arXiv + Semantic Scholar
        papers = await self.search(state["question"])
        # 2. Extract key results from PDFs if provided
        pdf_content = await self.extract_pdfs(state.get("source_pdfs", []))
        # 3. Synthesize into structured context
        context = await self.synthesize(state["question"], papers, pdf_content)
        return {"research_context": context}
```

**Tasks:**
- [ ] Create `src/tools/arxiv_search.py` — `search(query, max_results=10) -> list[dict]`
- [ ] Create `src/tools/semantic_scholar.py` — `search(query, max_results=10) -> list[dict]`
- [ ] Create `src/tools/pdf_reader.py` — `extract_text(path) -> str` (pdftotext + PyMuPDF fallback)
- [ ] Create `src/agents/researcher.py`
- [ ] Write prompts: `src/prompts/researcher.md`
- [ ] Tests: mock API responses, verify structured output

### Step 2.4 — Formalization Agent

**File:** `src/agents/formalizer.py`

**Model:** `o3` (primary), `gpt-4.1` (fallback)

The most critical agent — translates informal math into Lean 4 code:

```python
class FormalizerAgent(BaseAgent):
    name = "formalizer"
    model = settings.formalization_model    # openai/o3
    
    async def run(self, state: AgentState) -> dict:
        if state.get("lean_errors"):
            # Repair mode: fix based on errors
            lean_code = await self.repair(
                state["lean_code"], state["lean_errors"]
            )
        else:
            # Initial formalization
            lean_code = await self.formalize(
                state["question"],
                state["research_context"],
                state.get("informal_proof", ""),
            )
        return {"lean_code": lean_code}
```

**The prompt is critical.** It must include:
- Lean 4 syntax reference (not Lean 3!)
- Commonly needed Mathlib imports
- Examples of correct Lean 4 proofs
- If errors are provided: the exact error text + original code

**Tasks:**
- [ ] Create `src/agents/formalizer.py`
- [ ] Write `src/prompts/formalizer.md` — extensive prompt with Lean 4 syntax guide + few-shot examples
- [ ] Implement repair logic (takes errors + previous code, produces fixed code)
- [ ] Implement Lean code extraction (strip markdown fences from LLM output)
- [ ] Tests: mock LLM responses, verify output is valid `LeanCode`

### Step 2.5 — Verifier Agent

**File:** `src/agents/verifier.py`

Thin wrapper around `LeanExecutor` with structured error feedback:

```python
class VerifierAgent(BaseAgent):
    name = "verifier"
    model = settings.error_analysis_model   # claude-sonnet-4-6
    
    async def run(self, state: AgentState) -> dict:
        code = LeanCode(filename="Proof.lean", source=state["lean_code"])
        result = await self.executor.verify(code)
        
        if result.success:
            return {"lean_verified": True, "lean_errors": ""}
        
        # Use LLM to analyze errors and produce actionable feedback
        analysis = await self.analyze_errors(result, state["lean_code"])
        return {
            "lean_verified": False,
            "lean_errors": analysis,
            "attempt_count": state.get("attempt_count", 0) + 1,
        }
```

**Tasks:**
- [ ] Create `src/agents/verifier.py`
- [ ] Write `src/prompts/verifier.md` — instruct Claude to analyze Lean errors and suggest fixes
- [ ] Integrate `lean_parser.py` for structured error extraction
- [ ] Tests: mock lean build outcomes (success, type mismatch, unknown identifier, sorry)

### Step 2.6 — Orchestrator Agent

**File:** `src/agents/orchestrator.py`

**Model:** `claude-sonnet-4-6`

Plans the research strategy and decomposes the question:

```python
class OrchestratorAgent(BaseAgent):
    name = "orchestrator"
    model = settings.orchestration_model    # claude-sonnet-4-6
    
    async def run(self, state: AgentState) -> dict:
        plan = await self.llm([{
            "role": "user",
            "content": f"Decompose this research question into sub-tasks:\n\n{state['question']}"
        }])
        return {
            "informal_proof": "",           # populated later
            "research_context": "",         # populated by researcher
            "lean_code": "",
            "lean_verified": False,
            "attempt_count": 0,
        }
```

**Tasks:**
- [ ] Create `src/agents/orchestrator.py`
- [ ] Write `src/prompts/orchestrator.md`
- [ ] Implement task decomposition (output a list of sub-tasks)
- [ ] Implement decision logic: which agents to invoke and in what order

### Step 2.7 — Report Generator

**File:** `src/agents/reporter.py`

**Model:** `claude-opus-4-6`

Assembles the final Markdown report:

```python
class ReporterAgent(BaseAgent):
    name = "reporter"
    model = settings.report_model   # claude-opus-4-6
    
    async def run(self, state: AgentState) -> dict:
        report = await self.llm([{
            "role": "system",
            "content": self.system_prompt,
        }, {
            "role": "user",
            "content": self._build_report_prompt(state),
        }])
        
        # Save to file
        path = Path(settings.reports_dir) / f"report_{session_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report)
        
        return {"report_md": report}
```

**Report structure:**
1. Title & Problem Statement
2. Literature Review (from Research Agent)
3. Informal Proof / Derivation
4. Formal Lean 4 Proof (with syntax highlighting)
5. Verification Status (✅/❌ per theorem)
6. Discussion & Limitations
7. References

**Tasks:**
- [ ] Create `src/agents/reporter.py`
- [ ] Write `src/prompts/reporter.md`
- [ ] Template the report structure (ensure consistent format)
- [ ] Tests: verify output is valid Markdown with expected sections

### Step 2.8 — CLI Entry Point

**File:** `src/__main__.py`

```python
"""
Usage: uv run python -m src "Prove that sqrt(2) is irrational"
"""
import asyncio
import sys
from src.agents.graph import build_graph

async def main():
    question = " ".join(sys.argv[1:])
    graph = build_graph()
    result = await graph.ainvoke({"question": question})
    print(f"\n{'='*60}")
    print(f"Verified: {result['lean_verified']}")
    print(f"Report: {result.get('report_md', 'N/A')[:200]}...")
    print(f"Notebook: {result.get('notebook_path', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Tasks:**
- [ ] Create `src/__main__.py`
- [ ] Test: `uv run python -m src "Prove 1+1=2"` runs full pipeline

### Phase 2 Exit Criteria

| Criterion | Test |
|---|---|
| LangGraph compiles and runs | `pytest tests/test_agents/test_graph.py` |
| Research Agent returns papers | Test with "irrational numbers" query |
| Formalization Agent produces Lean code | Test with pre-written informal proof |
| Verifier detects errors and triggers retry | Test with intentionally broken Lean |
| Full pipeline: question → verified proof | `python -m src "Prove 1+1=2"` |
| Report is generated | `.md` file in `output/reports/` |
| Retries work (up to N) | Confirm `attempt_count` > 1 for hard problems |

---

## Phase 3 — Intelligence & Retrieval (Weeks 5–6)

**Goal:** Make the agents smarter with RAG (Mathlib search), few-shot examples, proof decomposition, and sorry-driven development.

### Step 3.1 — Mathlib4 Lemma Index

**File:** `src/tools/mathlib_index.py`

Build an embedding-based search index over Mathlib4 declarations:

```python
"""
Index Mathlib4 lemmas/theorems for semantic search during formalization.

Pipeline:
1. Extract declaration names + docstrings from Mathlib4 source
2. Embed with OpenAI text-embedding-3-small
3. Store in ChromaDB
4. Query: "lemma about continuity of composition" → top-K results
"""
import chromadb
from src.config import settings

class MathlibIndex:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="mathlib4",
            metadata={"hnsw:space": "cosine"},
        )
    
    async def build_index(self, mathlib_dir: str):
        """Scan Mathlib4 .lean files, extract declarations, embed, store."""
        ...
    
    async def search(self, query: str, n_results: int = 10) -> list[dict]:
        """Semantic search for relevant Mathlib lemmas."""
        ...
```

**Tasks:**
- [ ] Create `src/tools/mathlib_index.py`
- [ ] Write the Mathlib extraction script (parse `.lean` files for `theorem`, `lemma`, `def` with docstrings)
- [ ] Build the index (one-time, ~30 min for full Mathlib)
- [ ] Write `search()` with embedding-based retrieval
- [ ] Tests: index a small subset, verify search returns relevant results
- [ ] Integrate into `formalizer.py` — include top-K Mathlib results in the prompt

### Step 3.2 — Few-Shot Example Bank

**File:** `src/tools/example_bank.py`

Curated examples of correct `(informal proof → Lean 4 code)` pairs:

```python
EXAMPLES = [
    {
        "category": "number_theory",
        "informal": "Prove that the square root of 2 is irrational.",
        "lean": """
import Mathlib.Data.Real.Irrational
theorem sqrt2_irrational : Irrational (Real.sqrt 2) := by
  exact irrational_sqrt_two
""",
    },
    # ... 20-30 curated examples across categories
]

def get_relevant_examples(query: str, n: int = 3) -> list[dict]:
    """Return the most relevant few-shot examples for a query."""
    ...
```

**Tasks:**
- [ ] Create `src/tools/example_bank.py`
- [ ] Curate 20+ examples covering: algebra, analysis, number theory, topology, set theory
- [ ] Implement retrieval (keyword + embedding match)
- [ ] Integrate into formalization prompt (prepend examples)

### Step 3.3 — Proof Decomposition

**File:** `src/agents/decomposer.py`

Break a complex proof into independently verifiable lemmas:

```python
async def decompose_proof(question: str, context: str) -> list[str]:
    """
    Use the reasoning model to break a proof into lemmas.
    Each lemma is verified independently, then composed.
    """
    response = await call_llm(
        settings.reasoning_model,
        messages=[{
            "role": "user",
            "content": f"""Break this proof into independent lemmas, 
            each provable on its own:
            
            {question}
            
            Context: {context}"""
        }]
    )
    return parse_lemmas(response)
```

**Tasks:**
- [ ] Create `src/agents/decomposer.py`
- [ ] Integrate into the LangGraph — add a decomposition step before formalization
- [ ] Handle lemma dependencies (order them topologically)
- [ ] Tests: decompose "√2 is irrational" into sub-lemmas

### Step 3.4 — Sorry-Guided Incremental Verification

Allow partial proofs with `sorry` placeholders, then fill them in iteratively:

```python
async def sorry_driven_verify(lean_code: str) -> tuple[bool, list[str]]:
    """
    1. Replace all tactic blocks with sorry
    2. Verify structure compiles
    3. Iteratively replace sorry with actual proofs
    4. Return list of remaining sorry positions
    """
    ...
```

**Tasks:**
- [ ] Implement sorry insertion (replace `by ...` with `by sorry`)
- [ ] Implement incremental sorry removal (one at a time)
- [ ] Integrate into the retry loop — if full proof fails, try sorry-driven approach
- [ ] Tests: verify sorry detection and replacement

### Step 3.5 — Lean REPL Integration (Optional Speedup)

**File:** `src/tools/lean_repl.py`

For faster feedback than full `lake build`:

```python
"""
Interactive Lean 4 REPL for fast type-checking of individual declarations.
"""
import asyncio

class LeanRepl:
    async def start(self):
        """Start a persistent Lean process."""
        self.proc = await asyncio.create_subprocess_exec(
            "lean", "--stdin",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    
    async def check(self, declaration: str) -> dict:
        """Send a declaration and get immediate feedback."""
        ...
```

**Tasks:**
- [ ] Create `src/tools/lean_repl.py` (optional, nice-to-have)
- [ ] Benchmark: REPL check time vs. `lake build` time
- [ ] Integrate as alternative backend in `LeanExecutor`

### Phase 3 Exit Criteria

| Criterion | Test |
|---|---|
| Mathlib index built + searchable | `index.search("continuous function composition")` returns results |
| Few-shot examples improve proof rate | Compare success rate with/without examples on 10 test problems |
| Decomposition produces valid lemmas | Decompose 3 problems, verify each sub-lemma can be stated in Lean |
| Sorry-guided verification works | A proof with sorry compiles; removing sorry and adding proof also compiles |

---

## Phase 4 — Notebook Generation & Polish (Weeks 7–8)

**Goal:** Build the full Notebook Generator agent, report generator, evaluation, and polish for the test research topic.

### Step 4.1 — Notebook Generator Agent

**File:** `src/agents/notebook_agent.py`

Full implementation with the two-LLM pipeline (narrative planner + code generator):

```python
class NotebookAgent(BaseAgent):
    name = "notebook_gen"
    
    async def run(self, state: AgentState) -> dict:
        # Phase 1: Plan notebook structure (Claude)
        plan = await call_llm(
            settings.notebook_narrative_model,
            messages=[...],          # question, proof steps, research context
            response_format=NotebookPlan,
        )
        
        # Phase 2: Generate narrative cells (Claude)
        markdown_cells = await self.generate_narrative(plan)
        
        # Phase 3: Generate code cells (Gemini)
        code_cells = await self.generate_code(plan)
        
        # Phase 4: Validate code cells (execute in sandbox)
        validated_cells = await self.validate_code(code_cells)
        
        # Phase 5: Assemble notebook
        nb = NotebookBuilder(title=plan.title)
        for section in plan.sections:
            nb.add_markdown(markdown_cells[section["heading"]])
            if section["type"] in ("symbolic", "numerical", "visualization"):
                nb.add_code(validated_cells[section["heading"]])
            if section["type"] == "lean":
                nb.add_lean_block(state["lean_code"], state["lean_verified"])
        
        path = nb.save(f"{settings.notebooks_dir}/{session_id}.ipynb")
        return {"notebook_path": str(path)}
```

**Tasks:**
- [ ] Create `src/agents/notebook_agent.py`
- [ ] Write `src/prompts/notebook_agent.md` — detailed notebook planning prompt
- [ ] Implement `generate_narrative()` — one LLM call per section
- [ ] Implement `generate_code()` — SymPy, NumPy, Matplotlib/Plotly code generation
- [ ] Implement `validate_code()` — execute cells in a sandboxed kernel
- [ ] Tests: generate notebook for "1+1=2", verify structure

### Step 4.2 — Symbolic Math Helpers

**File:** `src/tools/symbolic_math.py`

```python
"""
SymPy helpers for common operations in generated notebooks.
"""
from sympy import *

def verify_equation(lhs: str, rhs: str) -> bool:
    """Symbolically verify that lhs equals rhs."""
    ...

def compute_derivative(expr_str: str, var: str) -> str:
    """Return the derivative as a LaTeX string."""
    ...

def solve_ode(ode_str: str, func: str, var: str) -> str:
    """Solve an ODE and return the general solution."""
    ...
```

**Tasks:**
- [ ] Create `src/tools/symbolic_math.py`
- [ ] Implement common operations (differentiation, integration, ODE solving, series expansion)
- [ ] Write helpers the LLM can reference in generated code cells
- [ ] Tests: verify each helper produces correct SymPy output

### Step 4.3 — Visualization Generator

**File:** `src/tools/plot_generator.py`

```python
"""
Generate Matplotlib / Plotly visualizations from specifications.
"""
def generate_plot_code(spec: dict) -> str:
    """
    Given a spec like:
    {"type": "vector_field", "expressions": ["x", "-y"], "domain": [-5, 5]}
    Return Python code that produces the plot.
    """
    ...
```

**Tasks:**
- [ ] Create `src/tools/plot_generator.py`
- [ ] Implement templates for: line plot, vector field, 3D surface, contour, phase portrait
- [ ] Write Plotly variants for interactive versions
- [ ] Tests: generate code for each template, execute, verify no errors

### Step 4.4 — Sandboxed Notebook Execution

**File:** `src/tools/notebook_executor.py`

```python
"""
Execute notebook cells in a sandboxed Jupyter kernel.
"""
from jupyter_client import KernelManager

class NotebookExecutor:
    async def execute_cell(self, code: str, timeout: int = 30) -> dict:
        """Run a code cell, return outputs or errors."""
        ...
    
    async def execute_notebook(self, nb_path: str, safe_only: bool = True):
        """Execute all (or safe-only) cells in a notebook."""
        ...
```

**Tasks:**
- [ ] Create `src/tools/notebook_executor.py`
- [ ] Implement cell execution with timeout + error capture
- [ ] Implement the "safe cells only" filter (skip cells marked as interactive)
- [ ] Write auto-repair: if a cell fails, send error to LLM for fix, retry
- [ ] Tests: execute a notebook with known-good and known-bad cells

### Step 4.5 — End-to-End Test: Sciama Research Topic

Run the complete system on the test research topic from Appendix A:

```bash
uv run python -m src "Sciama's gravitational vector potential and electromagnetic 
origin of gravity — derive G = c²/Φ from Machian first principles, verify 
formalization in Lean 4, and analyze Gallucci's dipole mechanism"
```

**Expected outputs:**
1. `output/reports/sciama_gravity.md` — full research report
2. `output/notebooks/sciama_gravity.ipynb` — interactive notebook with:
   - Derivation of Sciama's potential integral
   - SymPy computation of $G = c^2/\Phi$
   - Gallucci's 3-atom force calculation (reproduced numerically)
   - Vector field plots (gravitoelectric + gravitomagnetic)
   - Electron orbit distortion visualization
   - Lean proof blocks for mathematically verifiable steps
3. `lean_project/DeepLean/Generated/SciamaPotential.lean` — Lean proofs

**Tasks:**
- [ ] Run the full pipeline on the Sciama topic
- [ ] Verify report quality — all sections present, references correct
- [ ] Verify notebook executes cleanly (all cells run without error)
- [ ] Verify Lean proofs compile (or clearly mark sorry gaps)
- [ ] Measure: total API cost, total time, number of retries

### Step 4.6 — Evaluation Benchmark

**File:** `tests/test_integration/test_benchmark.py`

Test on a standard set of problems:

| # | Problem | Difficulty | Expected |
|---|---|---|---|
| 1 | $1 + 1 = 2$ | Trivial | Lean proof, 0 retries |
| 2 | $\forall n : \mathbb{N}, 0 \le n$ | Easy | Lean proof, ≤1 retry |
| 3 | $\sqrt{2}$ is irrational | Medium | Lean proof, ≤3 retries |
| 4 | Infinitude of primes | Medium | Lean proof, ≤5 retries |
| 5 | Fundamental Theorem of Calculus | Hard | Partial Lean (sorry for analysis axioms) |
| 6 | Cantor's diagonal argument | Medium | Lean proof |
| 7 | Derive Euler-Lagrange equation | Hard/Physics | Partial, notebook-heavy |
| 8 | Sciama gravity topic (Appendix A) | Advanced | Report + notebook + partial Lean |

**Tasks:**
- [ ] Create benchmark script that runs each problem and records results
- [ ] Record: success rate, average retries, cost, time
- [ ] Create a summary table comparing across problems

### Step 4.7 — Human-in-the-Loop Mode

Add optional pause points where the system asks for user guidance:

```python
async def human_checkpoint(state: AgentState, question: str) -> str:
    """Pause and ask the user for input. Used at key decision points."""
    print(f"\n🤔 {question}")
    print(f"Current state: verified={state['lean_verified']}, attempts={state['attempt_count']}")
    return input("Your guidance (or press Enter to continue): ")
```

**Tasks:**
- [ ] Add HITL checkpoints at: after research, after first verification failure, before report
- [ ] Make HITL configurable (on/off via settings)
- [ ] Test: run a problem with HITL enabled, verify prompts appear

### Step 4.8 — Documentation

- [ ] Write `README.md` — project overview, setup instructions, usage examples
- [ ] Write `docs/architecture.md` — detailed architecture documentation (reference project.md)
- [ ] Add docstrings to all public functions and classes
- [ ] Create `notebooks/demo_research.ipynb` — a hand-crafted demo notebook showing the system

### Phase 4 Exit Criteria

| Criterion | Test |
|---|---|
| Notebook Generator produces valid `.ipynb` | Open in Jupyter, all cells run |
| Sciama topic produces report + notebook | Full end-to-end run |
| Benchmark: ≥50% success rate on medium problems | Run benchmark suite |
| HITL mode works | Manual test |
| README is complete | Read it, follow setup instructions from scratch |

---

## File-by-File Implementation Guide

Complete list of every file to create, in implementation order:

### Round 1 (Phase 0 + 1): Foundation

| # | File | Purpose | Deps |
|---|---|---|---|
| 1 | `pyproject.toml` | Project config + all dependencies | — |
| 2 | `.env.example` | Template for API keys | — |
| 3 | `.gitignore` | Ignore build artifacts | — |
| 4 | `src/__init__.py` | Package marker | — |
| 5 | `src/config.py` | Settings + env remapping | pydantic-settings, dotenv |
| 6 | `src/models.py` | All Pydantic data models | pydantic |
| 7 | `src/llm.py` | LLM client with routing + fallback | litellm, config |
| 8 | `src/utils/__init__.py` | Package marker | — |
| 9 | `src/utils/logging.py` | Structured logging setup | structlog |
| 10 | `src/utils/provenance.py` | Append-only event log | — |
| 11 | `src/utils/lean_parser.py` | Parse Lean compiler errors | — |
| 12 | `src/tools/__init__.py` | Package marker | — |
| 13 | `src/tools/lean_executor.py` | Write .lean + run lake build | lean_parser, models |
| 14 | `src/tools/notebook_builder.py` | Build .ipynb with nbformat | nbformat |
| 15 | `src/agents/__init__.py` | Package marker | — |
| 16 | `src/agents/single_loop.py` | Minimal proof loop (proof-of-concept) | llm, lean_executor, models |

### Round 2 (Phase 2): Multi-Agent

| # | File | Purpose | Deps |
|---|---|---|---|
| 17 | `src/agents/base.py` | Agent base class | llm, logging |
| 18 | `src/agents/graph.py` | LangGraph state + graph definition | langgraph, all agents |
| 19 | `src/tools/arxiv_search.py` | arXiv API wrapper | arxiv |
| 20 | `src/tools/semantic_scholar.py` | Semantic Scholar API | semanticscholar |
| 21 | `src/tools/pdf_reader.py` | PDF text extraction | PyMuPDF, subprocess |
| 22 | `src/agents/orchestrator.py` | Task planning agent | base, llm |
| 23 | `src/agents/researcher.py` | Literature search agent | base, arxiv, semantic_scholar, pdf_reader |
| 24 | `src/agents/formalizer.py` | Lean code generation agent | base, llm |
| 25 | `src/agents/verifier.py` | Lean verify + error analysis | base, lean_executor, lean_parser |
| 26 | `src/agents/reporter.py` | Report generation agent | base, llm |
| 27 | `src/prompts/orchestrator.md` | Orchestrator system prompt | — |
| 28 | `src/prompts/researcher.md` | Researcher system prompt | — |
| 29 | `src/prompts/formalizer.md` | Formalizer system prompt (with Lean 4 guide) | — |
| 30 | `src/prompts/verifier.md` | Verifier system prompt | — |
| 31 | `src/prompts/reporter.md` | Reporter system prompt | — |
| 32 | `src/__main__.py` | CLI entry point | graph |

### Round 3 (Phase 3): Intelligence

| # | File | Purpose | Deps |
|---|---|---|---|
| 33 | `src/tools/mathlib_index.py` | ChromaDB index of Mathlib4 | chromadb, openai |
| 34 | `src/tools/example_bank.py` | Curated few-shot proof examples | — |
| 35 | `src/agents/decomposer.py` | Proof decomposition | base, llm |
| 36 | `src/tools/lean_repl.py` | Fast Lean REPL (optional) | asyncio |

### Round 4 (Phase 4): Notebooks & Polish

| # | File | Purpose | Deps |
|---|---|---|---|
| 37 | `src/agents/notebook_agent.py` | Full notebook generation agent | base, notebook_builder, llm |
| 38 | `src/tools/symbolic_math.py` | SymPy helper library | sympy |
| 39 | `src/tools/plot_generator.py` | Matplotlib/Plotly code templates | matplotlib, plotly |
| 40 | `src/tools/notebook_executor.py` | Sandboxed cell execution | jupyter-client |
| 41 | `src/prompts/notebook_agent.md` | Notebook agent prompts | — |
| 42 | `README.md` | Project documentation | — |
| 43 | `docs/architecture.md` | Architecture docs | — |

### Tests (parallel with implementation)

| # | File | Tests |
|---|---|---|
| T1 | `tests/test_config.py` | Settings load, keys present |
| T2 | `tests/test_models.py` | Pydantic models serialize/validate |
| T3 | `tests/test_llm.py` | LLM calls, fallback, cost tracking |
| T4 | `tests/test_utils/test_lean_parser.py` | Error parsing patterns |
| T5 | `tests/test_tools/test_lean_executor.py` | File writing, build, parse |
| T6 | `tests/test_tools/test_notebook_builder.py` | Notebook creation, validation |
| T7 | `tests/test_tools/test_arxiv_search.py` | arXiv API mock |
| T8 | `tests/test_tools/test_mathlib_index.py` | Index build, search |
| T9 | `tests/test_agents/test_graph.py` | Graph topology, routing |
| T10 | `tests/test_agents/test_formalizer.py` | Lean code generation |
| T11 | `tests/test_agents/test_verifier.py` | Error handling, retry logic |
| T12 | `tests/test_integration/test_e2e.py` | Full pipeline test |
| T13 | `tests/test_integration/test_benchmark.py` | Benchmark suite |

---

## Dependency Graph

Implementation order respecting dependencies:

```
Phase 0: uv → pyproject.toml → uv sync → elan → lean_project
              │
Phase 1:      ├── config.py ──┬── models.py
              │               │
              │               ├── llm.py ────────────────┐
              │               │                          │
              │               ├── logging.py             │
              │               │                          │
              │               ├── provenance.py          │
              │               │                          │
              │               ├── lean_parser.py         │
              │               │       │                  │
              │               ├── lean_executor.py ◄─────┤
              │               │                          │
              │               ├── notebook_builder.py    │
              │               │                          │
              │               └── single_loop.py ◄───────┘
              │
Phase 2:      ├── base.py ◄── llm.py
              │     │
              │     ├── orchestrator.py
              │     ├── researcher.py ◄── arxiv_search, semantic_scholar, pdf_reader
              │     ├── formalizer.py
              │     ├── verifier.py ◄── lean_executor
              │     ├── reporter.py
              │     └── graph.py ◄── all agents
              │           │
              │           └── __main__.py
              │
Phase 3:      ├── mathlib_index.py ◄── chromadb, openai embeddings
              ├── example_bank.py
              ├── decomposer.py
              └── lean_repl.py (optional)
              │
Phase 4:      ├── notebook_agent.py ◄── notebook_builder, symbolic_math, plot_generator
              ├── symbolic_math.py
              ├── plot_generator.py
              ├── notebook_executor.py
              └── benchmark + docs
```

---

## Testing Strategy

### Unit Tests
- Every module has a corresponding test file.
- Mock all external calls (LLM APIs, Lean subprocess, network).
- Target: 80%+ code coverage on `src/`.

### Integration Tests
- `test_e2e.py`: Run the full pipeline on a trivial problem (`1+1=2`).
- `test_benchmark.py`: Run on 8 graded problems, record metrics.
- Require: live API keys (skip in CI if not present).

### Manual Validation
- After each phase: run the system on a real problem, inspect outputs.
- Check notebooks open and execute in Jupyter.
- Check Lean proofs compile with `lake build`.

### Running Tests

```bash
# Unit tests (fast, no API calls)
uv run pytest tests/ -m "not integration" -v

# Integration tests (requires API keys + Lean)
uv run pytest tests/ -m integration -v --timeout=300

# Coverage report
uv run pytest tests/ --cov=src --cov-report=html
```

---

## Acceptance Criteria

The project is considered **v0.1 complete** when:

| # | Criterion | How to Verify |
|---|---|---|
| 1 | Pipeline runs end-to-end without crashing | `python -m src "Prove 1+1=2"` exits cleanly |
| 2 | ≥3 out of 8 benchmark problems produce verified Lean proofs | Benchmark suite results |
| 3 | Reports are well-structured and readable | Human review of 3 reports |
| 4 | Notebooks execute without errors (for safe cells) | Open in Jupyter, Run All |
| 5 | API costs are tracked per session | Check provenance log for cost entries |
| 6 | System handles all 3 LLM providers | Force each provider individually, verify it works |
| 7 | Lean errors trigger retry (not crash) | Run a problem that requires ≥2 attempts |
| 8 | Sciama test topic produces meaningful output | Report + notebook for Appendix A topic |
| 9 | All unit tests pass | `pytest tests/ -m "not integration"` passes |
| 10 | README allows a new developer to set up and run | Follow README from scratch on a clean system |

---

## Timeline Summary

| Week | Phase | Key Milestone |
|---|---|---|
| 0 | Bootstrap | `uv sync` works, Lean compiles, all APIs validated |
| 1 | Phase 1a | Config + LLM + Lean executor working |
| 2 | Phase 1b | Single-agent loop proves trivial theorems |
| 3 | Phase 2a | LangGraph graph defined, Research + Formalization agents working |
| 4 | Phase 2b | Full multi-agent pipeline runs end-to-end |
| 5 | Phase 3a | Mathlib index built, RAG integrated into formalization |
| 6 | Phase 3b | Few-shot, decomposition, sorry-driven verification |
| 7 | Phase 4a | Notebook generator produces full derivation notebooks |
| 8 | Phase 4b | Sciama test topic, benchmark, documentation |
