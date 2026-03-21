"""
Sandboxed Jupyter notebook cell execution.

Uses jupyter_client to run cells in an isolated kernel and capture outputs.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import nbformat

from src.utils.logging import log


class NotebookExecutor:
    """Execute notebook cells in an isolated Jupyter kernel."""

    def __init__(self, timeout: int = 30, kernel_name: str = "python3"):
        self.timeout = timeout
        self.kernel_name = kernel_name
        self._km = None
        self._kc = None

    async def start(self) -> None:
        """Start the Jupyter kernel."""
        from jupyter_client import KernelManager

        self._km = KernelManager(kernel_name=self.kernel_name)
        self._km.start_kernel()
        self._kc = self._km.client()
        self._kc.start_channels()

        # Wait for kernel to be ready
        try:
            self._kc.wait_for_ready(timeout=30)
        except Exception as e:
            log.warning("kernel_startup_timeout", error=str(e))
            raise

        log.info("kernel_started", kernel=self.kernel_name)

    async def stop(self) -> None:
        """Shut down the kernel."""
        if self._kc:
            self._kc.stop_channels()
        if self._km:
            self._km.shutdown_kernel(now=True)
        self._km = None
        self._kc = None
        log.info("kernel_stopped")

    async def execute_cell(self, code: str, timeout: int | None = None) -> dict[str, Any]:
        """Execute a single code cell and return outputs.

        Returns:
            dict with keys: success, outputs, error, stdout, stderr
        """
        if not self._kc:
            await self.start()

        timeout = timeout or self.timeout
        result: dict[str, Any] = {
            "success": True,
            "outputs": [],
            "error": None,
            "stdout": "",
            "stderr": "",
        }

        msg_id = self._kc.execute(code)

        # Collect responses
        try:
            while True:
                msg = await asyncio.to_thread(
                    self._kc.get_iopub_msg, timeout=timeout
                )

                msg_type = msg["msg_type"]
                content = msg.get("content", {})

                if msg_type == "status" and content.get("execution_state") == "idle":
                    break
                elif msg_type == "stream":
                    name = content.get("name", "stdout")
                    text = content.get("text", "")
                    if name == "stdout":
                        result["stdout"] += text
                    else:
                        result["stderr"] += text
                elif msg_type in ("display_data", "execute_result"):
                    result["outputs"].append(content.get("data", {}))
                elif msg_type == "error":
                    result["success"] = False
                    result["error"] = {
                        "ename": content.get("ename", ""),
                        "evalue": content.get("evalue", ""),
                        "traceback": content.get("traceback", []),
                    }

        except Exception as e:
            result["success"] = False
            result["error"] = {"ename": "Timeout", "evalue": str(e), "traceback": []}

        return result

    async def execute_notebook(
        self,
        nb_path: str | Path,
        safe_only: bool = True,
    ) -> dict[str, Any]:
        """Execute all (or safe-only) cells in a notebook.

        Args:
            nb_path: Path to the .ipynb file
            safe_only: If True, skip cells marked with # INTERACTIVE or # SKIP

        Returns:
            dict with results per cell index
        """
        path = Path(nb_path)
        nb = nbformat.read(str(path), as_version=4)

        results: dict[str, Any] = {"cells": [], "total": 0, "success": 0, "failed": 0}

        try:
            await self.start()

            for i, cell in enumerate(nb.cells):
                if cell.cell_type != "code":
                    continue

                source = cell.source.strip()
                if not source:
                    continue

                # Skip interactive/manual cells
                if safe_only and any(
                    marker in source for marker in ["# INTERACTIVE", "# SKIP", "# MANUAL"]
                ):
                    log.info("cell_skipped", index=i)
                    continue

                results["total"] += 1
                cell_result = await self.execute_cell(source)
                cell_result["index"] = i
                results["cells"].append(cell_result)

                if cell_result["success"]:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    log.warning(
                        "cell_failed",
                        index=i,
                        error=cell_result.get("error", {}).get("evalue", ""),
                    )

        finally:
            await self.stop()

        log.info(
            "notebook_execution_done",
            total=results["total"],
            success=results["success"],
            failed=results["failed"],
        )

        return results
