"""Tests for the Lean executor (mocked subprocess)."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import LeanCode, LeanResult
from src.tools.lean_executor import LeanExecutor


@pytest.fixture
def executor(tmp_path):
    """Create a LeanExecutor with a temp project dir."""
    return LeanExecutor(project_dir=str(tmp_path / "lean_project"))


def test_write_lean_file(executor):
    """Should write a .lean file to the generated directory."""
    code = LeanCode(filename="Test.lean", source="theorem t : True := trivial")
    path = executor.write_lean_file(code)
    assert path.exists()
    assert path.read_text() == "theorem t : True := trivial"


def test_write_lean_file_creates_dirs(executor):
    """Should create subdirectories if needed."""
    code = LeanCode(filename="Sub/Deep.lean", source="-- deep file")
    path = executor.write_lean_file(code)
    assert path.exists()
    assert "Sub" in str(path)


def test_clean_generated(executor):
    """Should remove all .lean files from generated dir."""
    code = LeanCode(filename="Test.lean", source="-- test")
    executor.write_lean_file(code)
    assert any(executor.generated_dir.glob("*.lean"))
    executor.clean_generated()
    assert not any(executor.generated_dir.glob("*.lean"))


@pytest.mark.asyncio
async def test_build_lake_not_found(executor):
    """Should return failure when lake is not found."""
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError("lake not found")):
        result = await executor.build()
    assert not result.success
    assert "lake not found" in result.stderr.lower()


@pytest.mark.asyncio
async def test_check_available_false(executor):
    """Should return False when lake is not installed."""
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
        available = await executor.check_available()
    assert not available


@pytest.mark.asyncio
async def test_verify_writes_and_builds(executor):
    """verify() should write the file then call build."""
    code = LeanCode(filename="Test.lean", source="-- test")

    async def mock_exec(*args, **kwargs):
        proc = MagicMock()
        proc.returncode = 0

        async def mock_communicate():
            return (b"Build OK", b"")

        proc.communicate = mock_communicate
        return proc

    with patch("asyncio.create_subprocess_exec", side_effect=mock_exec):
        result = await executor.verify(code)

    # File should be written
    assert (executor.generated_dir / "Test.lean").exists()
    assert result.success
