"""
Lean 4 executor — write .lean files, run `lake build`, parse output.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from src.config import settings
from src.models import LeanCode, LeanResult
from src.utils.lean_parser import parse_lean_output
from src.utils.logging import log


class LeanExecutor:
    """Bridge between Python and the Lean 4 build system."""

    def __init__(self, project_dir: str | None = None):
        self.project_dir = Path(project_dir or settings.lean_project_dir).resolve()
        self.generated_dir = self.project_dir / "DeepLean" / "Generated"
        self.generated_dir.mkdir(parents=True, exist_ok=True)

    def write_lean_file(self, code: LeanCode) -> Path:
        """Write a .lean file into the generated directory."""
        path = self.generated_dir / code.filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code.source, encoding="utf-8")
        log.info("lean_file_written", path=str(path), size=len(code.source))
        return path

    def clean_generated(self) -> None:
        """Remove all generated .lean files."""
        for f in self.generated_dir.glob("*.lean"):
            f.unlink()

    async def build(self, timeout: int | None = None) -> LeanResult:
        """Run `lake build` and return structured result."""
        timeout = timeout or settings.lean_timeout
        t0 = time.monotonic()

        try:
            proc = await asyncio.create_subprocess_exec(
                "lake",
                "build",
                cwd=str(self.project_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return LeanResult(
                success=False,
                stderr="lake not found. Is Lean 4 / elan installed?",
            )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            elapsed = time.monotonic() - t0
            return LeanResult(
                success=False,
                stderr=f"Build timed out after {timeout}s",
                build_time_seconds=elapsed,
            )

        elapsed = time.monotonic() - t0
        stdout = stdout_bytes.decode(errors="replace")
        stderr = stderr_bytes.decode(errors="replace")

        success = proc.returncode == 0
        errors = [] if success else [e.__dict__ for e in parse_lean_output(stderr)]

        log.info(
            "lean_build",
            success=success,
            return_code=proc.returncode,
            errors=len(errors),
            elapsed_s=round(elapsed, 2),
        )

        return LeanResult(
            success=success,
            stdout=stdout,
            stderr=stderr,
            errors=errors,
            build_time_seconds=round(elapsed, 2),
        )

    async def verify(self, code: LeanCode, timeout: int | None = None) -> LeanResult:
        """Write file + build in one call."""
        self.write_lean_file(code)
        return await self.build(timeout=timeout)

    async def check_available(self) -> bool:
        """Check if lake is available on the system."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "lake", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except FileNotFoundError:
            return False
