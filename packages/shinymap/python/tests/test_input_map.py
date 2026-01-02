"""Tests for input_map functionality.

These tests verify:
1. Raw mode parameter
2. Props generation for JavaScript
"""

import json

import pytest

from shinymap import input_map
from shinymap.geometry import Outline


# Test geometry
GEOMETRY = Outline.from_dict({
    "region1": ["M0 0 L10 0 L10 10 L0 10 Z"],
    "region2": ["M20 0 L30 0 L30 10 L20 10 Z"],
})


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

        import re
        import html as html_lib
        match = re.search(r'data-shinymap-props="([^"]*)"', html_str)
        assert match is not None

        props_json = html_lib.unescape(match.group(1))
        props = json.loads(props_json)

        assert props.get("raw") is True
        assert props["mode"]["type"] == "multiple"


# Mark all tests as unit tests
pytestmark = pytest.mark.unit
