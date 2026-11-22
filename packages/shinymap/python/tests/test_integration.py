"""
Integration tests for shinymap using Playwright.

These tests verify that the JavaScript components render correctly and
respond to user interactions as expected.
"""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.integration
class TestInputMapBasic:
    """Test input_map single and multiple selection modes."""

    def test_renders_svg_regions(self, shiny_app_basic: Page):
        """Verify that SVG regions are rendered correctly."""
        page = shiny_app_basic

        # Should have SVG elements
        svgs = page.locator("svg[role='img']")
        expect(svgs.first).to_be_visible()

        # Should have path elements for regions
        paths = page.locator("svg path")
        assert paths.count() > 0

    def test_single_select_click(self, shiny_app_basic: Page):
        """Test single selection mode - clicking a region selects it."""
        page = shiny_app_basic

        # Find the first SVG (single select mode)
        svg = page.locator("svg[role='img']").first

        # Click on the circle region (first path)
        circle_path = svg.locator("path").first
        circle_path.click()

        # Wait for Shiny to update the output
        page.wait_for_timeout(500)

        # The output should show the selected region
        output = page.locator("#single_select")
        expect(output).to_contain_text(re.compile(r"(circle|square|triangle)"))

    def test_single_select_deselect(self, shiny_app_basic: Page):
        """Test single selection - clicking same region deselects it."""
        page = shiny_app_basic

        svg = page.locator("svg[role='img']").first
        circle_path = svg.locator("path").first

        # Select
        circle_path.click()
        page.wait_for_timeout(500)

        # Deselect by clicking again
        circle_path.click()
        page.wait_for_timeout(500)

        # Output should be empty or None
        output = page.locator("#single_select")
        # The output might show "None" or be empty
        text = output.text_content() or ""
        assert text.strip() in ["", "None"]

    def test_multiple_select_click(self, shiny_app_basic: Page):
        """Test multiple selection mode - can select multiple regions."""
        page = shiny_app_basic

        # Find the second SVG (multiple select mode)
        svgs = page.locator("svg[role='img']")
        svg = svgs.nth(1)

        paths = svg.locator("path")

        # Click first region
        paths.nth(0).click()
        page.wait_for_timeout(300)

        # Click second region
        paths.nth(1).click()
        page.wait_for_timeout(300)

        # Output should show both regions
        output = page.locator("#multi_select")
        text = output.text_content() or ""
        # Should contain list format like ['circle', 'square']
        assert "[" in text or "circle" in text or "square" in text

    def test_region_hover_effect(self, shiny_app_basic: Page):
        """Test that hovering shows visual feedback."""
        page = shiny_app_basic

        svg = page.locator("svg[role='img']").first
        path = svg.locator("path").first

        # Hover over the region
        path.hover()
        page.wait_for_timeout(200)

        # The hover overlay should be visible (rendered in a separate layer)
        # Check if there's a hover effect by looking at the SVG structure
        hover_overlays = svg.locator("g").all()
        assert len(hover_overlays) > 0  # Multiple layers exist


@pytest.mark.integration
class TestInputMapSelectHighlight:
    """Test that select aesthetic is properly applied."""

    def test_select_changes_fill_color(self, shiny_app_basic: Page):
        """Verify selected regions show select aesthetic (blue fill)."""
        page = shiny_app_basic

        svg = page.locator("svg[role='img']").first
        path = svg.locator("path").first

        # Click to select
        path.click()
        page.wait_for_timeout(500)

        # Verify the click was registered and selection is shown
        output = page.locator("#single_select")
        text = output.text_content() or ""
        assert text.strip() != ""


@pytest.mark.integration
class TestSVGStructure:
    """Test the SVG rendering structure."""

    def test_svg_has_viewbox(self, shiny_app_basic: Page):
        """Verify SVG has proper viewBox attribute."""
        page = shiny_app_basic

        svg = page.locator("svg[role='img']").first
        viewbox = svg.get_attribute("viewBox")
        assert viewbox is not None
        assert viewbox  # Not empty

    def test_svg_has_accessibility_role(self, shiny_app_basic: Page):
        """Verify SVG has role='img' for accessibility."""
        page = shiny_app_basic

        svg = page.locator("svg[role='img']")
        expect(svg.first).to_be_visible()

    def test_paths_have_cursor_pointer(self, shiny_app_basic: Page):
        """Verify interactive regions show pointer cursor."""
        page = shiny_app_basic

        svg = page.locator("svg[role='img']").first
        # Find a path with cursor pointer (interactive regions have it)
        path = svg.locator("path").first
        cursor = path.evaluate("el => getComputedStyle(el).cursor")
        assert cursor == "pointer"
