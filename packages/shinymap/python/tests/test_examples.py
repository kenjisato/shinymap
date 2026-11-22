"""Tests that verify example apps can be imported without errors.

These tests ensure that the example apps are valid Python modules
and that all their imports resolve correctly.
"""

import sys
from pathlib import Path

import pytest

# Add examples directory to path for imports
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


@pytest.fixture(scope="module", autouse=True)
def setup_examples_path():
    """Add examples directory to sys.path for the test module."""
    examples_path = str(EXAMPLES_DIR)
    sys.path.insert(0, examples_path)
    yield
    sys.path.remove(examples_path)


@pytest.mark.unit
def test_import_shared():
    """Test that shared.py can be imported."""
    import shared

    assert shared is not None


@pytest.mark.unit
def test_import_app_basic():
    """Test that app_basic.py can be imported."""
    import app_basic

    assert hasattr(app_basic, "app")


@pytest.mark.unit
def test_import_app_hover():
    """Test that app_hover.py can be imported."""
    import app_hover

    assert hasattr(app_hover, "app")


@pytest.mark.unit
def test_import_app_input_modes():
    """Test that app_input_modes.py can be imported."""
    import app_input_modes

    assert hasattr(app_input_modes, "app")


@pytest.mark.unit
def test_import_app_output():
    """Test that app_output.py can be imported."""
    import app_output

    assert hasattr(app_output, "app")


@pytest.mark.unit
def test_import_app_patterns():
    """Test that app_patterns.py can be imported."""
    import app_patterns

    assert hasattr(app_patterns, "app")


@pytest.mark.unit
def test_import_app_active_vs_selected():
    """Test that app_active_vs_selected.py can be imported."""
    import app_active_vs_selected

    assert hasattr(app_active_vs_selected, "app")


@pytest.mark.unit
def test_import_app_aes_select():
    """Test that app_aes_select.py can be imported."""
    import app_aes_select

    assert hasattr(app_aes_select, "app")


@pytest.mark.unit
def test_import_app_relative():
    """Test that app_relative.py can be imported."""
    import app_relative

    assert hasattr(app_relative, "app")


@pytest.mark.unit
def test_import_app_update_simple():
    """Test that app_update_simple.py can be imported."""
    import app_update_simple

    assert hasattr(app_update_simple, "app")


@pytest.mark.unit
def test_import_app_update_map():
    """Test that app_update_map.py can be imported."""
    import app_update_map

    assert hasattr(app_update_map, "app")


@pytest.mark.unit
def test_import_japan_prefectures():
    """Test that japan_prefectures.py can be imported."""
    import japan_prefectures

    assert japan_prefectures is not None


@pytest.mark.unit
def test_import_app_japan():
    """Test that app_japan.py can be imported."""
    import app_japan

    assert hasattr(app_japan, "app")


@pytest.mark.unit
def test_import_main_app():
    """Test that the main app.py can be imported."""
    import app

    assert hasattr(app, "app")
