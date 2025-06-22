"""Pytest configuration and fixtures."""

import asyncio
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from agenttools import AgentTools


@pytest.fixture
def tools():
    """Create AgentTools instance."""
    return AgentTools()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def tmp_path(temp_dir):
    """Alias for temp_dir for compatibility."""
    return temp_dir