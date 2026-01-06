"""Tests for render_map decorator edge cases."""

import pytest
from shiny.pytest import create_app_fixture

from shinymap import output_map
from shinymap.uicore._registry import _static_map_params

# Create fixture for the bug reproduction app
app_render_map_bug = create_app_fixture("apps/app_render_map_bug.py")


class TestRenderMapModeDefault:
    """Tests for render_map mode defaulting behavior."""

    @pytest.mark.integration
    def test_render_map_handles_missing_mode(self, page, app_render_map_bug):
        """Test that render_map handles missing mode in static_params.

        This tests the actual code path in _render_map.py that fails when
        mode is not in static_params.

        The bug: when output_map() is called without outline, mode is not
        stored in static_params. Then render_map tries to call mode.to_dict()
        on None, causing AttributeError.
        """
        # Navigate to the app (app_render_map_bug is a ShinyAppProc with .url property)
        page.goto(app_render_map_bug.url)

        # If the bug exists, the app would have crashed during render
        # Wait for the SVG to be visible (proves rendering succeeded)
        page.wait_for_selector("svg[role='img']", timeout=5000)

        # Verify the map rendered
        svg = page.locator("svg[role='img']")
        assert svg.is_visible()

    def test_output_map_without_outline_does_not_raise(self):
        """Test that output_map can be called without outline parameter."""
        result = output_map("test_map")
        assert result is not None

    def test_output_map_without_outline_does_not_register_mode(self):
        """Test that output_map without outline doesn't register mode.

        This verifies the precondition that causes the bug:
        when output_map() is called without outline, mode is not in static_params.
        """
        test_id = "_test_no_outline_no_mode"

        # Call output_map without outline
        output_map(test_id)

        # Check what was registered
        params = _static_map_params.get(test_id, {})

        # mode should NOT be in params (this is the root cause of the bug)
        assert "mode" not in params

        # Cleanup
        if test_id in _static_map_params:
            del _static_map_params[test_id]
