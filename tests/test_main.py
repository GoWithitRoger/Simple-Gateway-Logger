# tests/test_main.py

import pytest


def test_dependencies_importable():
    """Checks that the main dependencies can be imported."""
    try:
        pass
    except ImportError as e:
        pytest.fail(f"Failed to import a required dependency: {e}")
