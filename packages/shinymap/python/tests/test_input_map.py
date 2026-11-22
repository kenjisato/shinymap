"""Tests for input_map functionality.

These tests verify:
1. Raw mode parameter
2. Props generation for JavaScript
"""

import json

import pytest
from shiny.pytest import create_app_fixture

from shinymap import input_map
from shinymap.outline import Outline

# Test geometry
GEOMETRY = Outline.from_dict(
    {
        "region1": ["M0 0 L10 0 L10 10 L0 10 Z"],
        "region2": ["M20 0 L30 0 L30 10 L20 10 Z"],
    }
)


class TestInputMapRaw:
    """Test input_map raw parameter."""

    def test_raw_false_by_default(self):
        """raw parameter defaults to False and is not in props."""
        result = input_map("test", GEOMETRY, mode="single")

        # Extract props from the HTML output
        html_str = str(result)

        # raw should not be in props when False
        assert '"raw":' not in html_str or '"raw": true' not in html_str

    def test_raw_true_included_in_props(self):
        """raw=True is included in props for JavaScript."""
        result = input_map("test", GEOMETRY, mode="single", raw=True)

        # Extract props from the HTML output
        html_str = str(result)

        # Find the props JSON and parse it
        import re

        match = re.search(r'data-shinymap-props="([^"]*)"', html_str)
        assert match is not None

        # Unescape HTML entities
        import html as html_lib

        props_json = html_lib.unescape(match.group(1))
        props = json.loads(props_json)

        assert props.get("raw") is True

    def test_raw_works_with_multiple_mode(self):
        """raw parameter works with multiple selection mode."""
        result = input_map("test", GEOMETRY, mode="multiple", raw=True)

        html_str = str(result)

        import html as html_lib
        import re

        match = re.search(r'data-shinymap-props="([^"]*)"', html_str)
        assert match is not None

        props_json = html_lib.unescape(match.group(1))
        props = json.loads(props_json)

        assert props.get("raw") is True
        assert props["mode"]["type"] == "multiple"


# Mark all tests as unit tests
pytestmark = pytest.mark.unit


app_allow_deselect = create_app_fixture("apps/app_allow_deselect.py")


class TestAllowDeselect:
    @pytest.mark.integration
    def test_allow_deselect_false_keeps_selection(self, page, app_allow_deselect):
        page.goto(app_allow_deselect.url)
        for map_id in ("keep", "free"):
            page.wait_for_selector(f"#{map_id} svg path", state="attached", timeout=10000)
        page.wait_for_timeout(1500)

        def click(map_id, index):
            page.evaluate(
                f"() => document.querySelectorAll('#{map_id} svg > g')[1]"
                f".querySelectorAll('path')[{index}]"
                ".dispatchEvent(new MouseEvent('click', {bubbles: true}))"
            )
            page.wait_for_timeout(400)

        for map_id in ("keep", "free"):
            click(map_id, 0)  # select a
            click(map_id, 0)  # click a again
        # allow_deselect=False keeps "a"; the default clears it
        assert page.locator("#values").inner_text() == "keep=a free=None"

        click("keep", 1)  # switching to another region still works
        assert page.locator("#values").inner_text() == "keep=b free=None"
