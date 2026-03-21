"""Pytest configuration — custom markers and fixtures."""

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: marks tests requiring live APIs")
    config.addinivalue_line("markers", "benchmark: marks benchmark suite tests")
