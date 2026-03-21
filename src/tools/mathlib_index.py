"""
Mathlib4 lemma index using ChromaDB for semantic search.

Pipeline:
1. Extract declaration names + docstrings from Mathlib4 source files
2. Embed with OpenAI text-embedding-3-small
3. Store in ChromaDB
4. Query: "lemma about continuity of composition" → top-K results
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.config import settings
from src.utils.logging import log


class MathlibIndex:
    """Embedding-based search index over Mathlib4 declarations."""

    def __init__(self, persist_dir: str | None = None):
        import chromadb

        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="mathlib4",
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return self.collection.count()

    async def build_index(self, mathlib_dir: str, batch_size: int = 100) -> int:
        """Scan Mathlib4 .lean files and index declarations.

        Returns number of declarations indexed.
        """
        import asyncio

        lean_dir = Path(mathlib_dir)
        if not lean_dir.exists():
            log.warning("mathlib_dir_not_found", path=mathlib_dir)
            return 0

        declarations = await asyncio.to_thread(self._extract_declarations, lean_dir)
        log.info("mathlib_declarations_found", count=len(declarations))

        if not declarations:
            return 0

        # Index in batches
        for i in range(0, len(declarations), batch_size):
            batch = declarations[i : i + batch_size]
            ids = [d["id"] for d in batch]
            documents = [d["text"] for d in batch]
            metadatas = [{"name": d["name"], "file": d["file"], "kind": d["kind"]} for d in batch]

            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        log.info("mathlib_index_built", total=len(declarations))
        return len(declarations)

    def _extract_declarations(self, lean_dir: Path) -> list[dict[str, str]]:
        """Extract theorem/lemma/def declarations from .lean files."""
        decl_pattern = re.compile(
            r"^(theorem|lemma|def|instance|class|structure|noncomputable def)\s+(\S+)",
            re.MULTILINE,
        )
        doc_pattern = re.compile(r"/--\s*(.*?)\s*-/", re.DOTALL)

        declarations: list[dict[str, str]] = []
        lean_files = list(lean_dir.rglob("*.lean"))

        for lean_file in lean_files[:5000]:  # Cap to prevent very long indexing
            try:
                content = lean_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            rel_path = str(lean_file.relative_to(lean_dir))

            for match in decl_pattern.finditer(content):
                kind = match.group(1)
                name = match.group(2)

                # Try to find preceding docstring
                doc = ""
                pre_text = content[max(0, match.start() - 500) : match.start()]
                doc_match = doc_pattern.search(pre_text)
                if doc_match:
                    doc = doc_match.group(1).strip()[:500]

                # Build the searchable text
                text = f"{kind} {name}"
                if doc:
                    text += f" -- {doc}"

                decl_id = f"{rel_path}::{name}"
                declarations.append(
                    {
                        "id": decl_id,
                        "name": name,
                        "file": rel_path,
                        "kind": kind,
                        "text": text,
                    }
                )

        return declarations

    async def search(self, query: str, n_results: int = 10) -> list[dict[str, Any]]:
        """Semantic search for relevant Mathlib declarations."""
        if self.count == 0:
            log.warning("mathlib_index_empty")
            return []

        results = self.collection.query(query_texts=[query], n_results=n_results)

        hits: list[dict[str, Any]] = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                dist = results["distances"][0][i] if results["distances"] else 0.0
                hits.append(
                    {
                        "text": doc,
                        "name": meta.get("name", ""),
                        "file": meta.get("file", ""),
                        "kind": meta.get("kind", ""),
                        "distance": dist,
                    }
                )

        log.info("mathlib_search", query=query[:60], results=len(hits))
        return hits
