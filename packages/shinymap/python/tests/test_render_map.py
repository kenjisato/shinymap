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


class TestMapAesForms:
    """Map(aes=...) accepts ByGroup, ByState and single aesthetics (regression in 0.3.0-dev)."""

    OUTLINE_DICT = {"a": "M0 0 L10 0 L10 10 Z", "b": "M20 0 L30 0 L30 10 Z"}

    def _payload(self, map_aes, with_output_map: bool):
        from shinymap import Map
        from shinymap.outline import Outline
        from shinymap.uicore._render_map import _build_payload

        outline = Outline.from_dict(self.OUTLINE_DICT)
        static: dict = {}
        if with_output_map:
            test_id = "_test_map_aes_forms"
            output_map(test_id, outline)
            static = _static_map_params.pop(test_id)
        return _build_payload(Map(outline, aes=map_aes), static)

    @pytest.mark.unit
    @pytest.mark.parametrize("with_output_map", [False, True])
    @pytest.mark.parametrize("form", ["bystate", "shape"])
    def test_non_bygroup_aes_applies_to_all_regions(self, form, with_output_map):
        from shinymap import aes

        shape = aes.Shape(fill_color="#ff0000")
        map_aes = aes.ByState(base=shape) if form == "bystate" else shape

        payload = self._payload(map_aes, with_output_map)

        assert payload["aes"]["__all"]["base"]["fill_color"] == "#ff0000"
        # JS looks up __shape before __all, so the type default must carry it too
        assert payload["aes"]["__shape"]["base"]["fill_color"] == "#ff0000"
        # Wash select/hover defaults are kept
        assert payload["aes"]["__shape"]["select"] is not None

    @pytest.mark.unit
    def test_map_aes_keeps_output_map_region_entries(self):
        from shinymap import Map, aes
        from shinymap.outline import Outline
        from shinymap.uicore._render_map import _build_payload

        outline = Outline.from_dict(self.OUTLINE_DICT)
        test_id = "_test_map_aes_keeps_regions"
        output_map(test_id, outline, aes=aes.ByGroup(a=aes.Shape(fill_color="#123456")))
        static = _static_map_params.pop(test_id)

        payload = _build_payload(Map(aes=aes.Shape(fill_color="#abcdef")), static)

        assert payload["aes"]["a"]["base"]["fill_color"] == "#123456"
        assert payload["aes"]["__shape"]["base"]["fill_color"] == "#abcdef"

    @pytest.mark.unit
    @pytest.mark.parametrize("with_output_map", [False, True])
    def test_bygroup_aes_keys_reach_payload(self, with_output_map):
        from shinymap import aes

        payload = self._payload(aes.ByGroup(a=aes.Shape(fill_color="#ff0000")), with_output_map)

        assert payload["aes"]["a"]["base"]["fill_color"] == "#ff0000"

    @pytest.mark.unit
    def test_dict_aes_is_rejected(self):
        with pytest.raises(TypeError, match="no longer accepts a dict"):
            self._payload({"a": {"fill_color": "#ff0000"}}, with_output_map=False)


class TestWashApplyAllOverridesTypeDefault:
    """aes=ByState/Shape on input_map/output_map must beat the wash's type default."""

    @pytest.mark.unit
    def test_shape_aes_reaches_shape_type_entry(self):
        from shinymap import aes
        from shinymap.outline import Outline
        from shinymap.ui._ui import _default_wash

        outline = Outline.from_dict({"a": "M0 0 L10 0 L10 10 Z"})
        resolved = _default_wash.config.apply(aes.Shape(fill_color="#ff0000"), outline)

        assert resolved["__shape"].base.fill_color == "#ff0000"
        assert resolved["__all"].base.fill_color == "#ff0000"

    @pytest.mark.unit
    def test_line_aes_does_not_touch_shape_entry(self):
        from shinymap import aes
        from shinymap.outline import Outline
        from shinymap.ui._ui import _default_wash

        outline = Outline.from_dict({"a": "M0 0 L10 0 L10 10 Z"})
        default_fill = _default_wash.config.apply(None, outline)["__shape"].base.fill_color
        resolved = _default_wash.config.apply(aes.Line(stroke_color="#ff0000"), outline)

        assert resolved["__shape"].base.fill_color == default_fill
        assert resolved["__line"].base.stroke_color == "#ff0000"


class TestMapAesLayering:
    """Map(aes=...) is layered over output_map(aes=...) and resolved through one wash."""

    OUTLINE_DICT = {"a": "M0 0 L10 0 L10 10 Z", "b": "M20 0 L30 0 L30 10 Z"}

    def _payload(self, output_map_fn, map_aes, outline_in_output_map: bool = True):
        from shinymap import Map
        from shinymap.outline import Outline
        from shinymap.uicore._render_map import _build_payload

        outline = Outline.from_dict(self.OUTLINE_DICT)
        test_id = "_test_map_aes_layering"
        if outline_in_output_map:
            output_map_fn(test_id, outline)
            builder = Map(aes=map_aes)
        else:
            output_map_fn(test_id)
            builder = Map(outline, aes=map_aes)
        static = _static_map_params.pop(test_id, {})
        return _build_payload(builder, static)["aes"]

    @pytest.mark.unit
    def test_bygroup_all_reaches_type_entry(self):
        from shinymap import aes

        payload = self._payload(output_map, aes.ByGroup(__all=aes.Shape(fill_color="#ff0000")))

        assert payload["__shape"]["base"]["fill_color"] == "#ff0000"

    @pytest.mark.unit
    def test_output_map_fields_survive_map_aes(self):
        from functools import partial

        from shinymap import aes

        om = partial(output_map, aes=aes.Shape(stroke_width=3))
        payload = self._payload(om, aes.Shape(fill_color="#ff0000"))

        assert payload["__shape"]["base"]["fill_color"] == "#ff0000"
        assert payload["__shape"]["base"]["stroke_width"] == 3

    @pytest.mark.unit
    def test_output_map_hover_none_survives_map_aes(self):
        from functools import partial

        from shinymap import aes

        om = partial(output_map, aes=aes.ByState(hover=None))
        payload = self._payload(om, aes.Shape(fill_color="#ff0000"))

        assert payload["__shape"]["hover"] is None

    @pytest.mark.unit
    @pytest.mark.parametrize("outline_in_output_map", [True, False])
    def test_custom_wash_is_used(self, outline_in_output_map):
        from shinymap import Wash, aes

        wc = Wash(shape=aes.Shape(fill_color="#111111"))
        payload = self._payload(
            wc.output_map, aes.Shape(stroke_width=2), outline_in_output_map=outline_in_output_map
        )

        assert payload["__shape"]["base"]["fill_color"] == "#111111"
        assert payload["__shape"]["base"]["stroke_width"] == 2

    @pytest.mark.unit
    def test_select_only_bystate_keeps_base_default(self):
        from shinymap import aes
        from shinymap.ui._ui import _default_wash

        payload = self._payload(output_map, aes.ByState(select=aes.Shape(fill_color="#ff0000")))
        default_fill = _default_wash.config.shape.base.fill_color

        assert payload["__shape"]["select"]["fill_color"] == "#ff0000"
        assert payload["__shape"]["base"]["fill_color"] == default_fill


class TestElementKind:
    @pytest.mark.unit
    def test_kinds(self):
        from shinymap import aes
        from shinymap.uicore._wash import element_kind

        assert element_kind(aes.Shape()) == "shape"
        assert element_kind(aes.Line()) == "line"
        assert element_kind(aes.Text()) == "text"
        assert element_kind(aes.Path()) == "shape"
        assert element_kind(aes.Path(kind="line")) == "line"
        assert element_kind(aes.ByState(hover=aes.Line())) == "line"

    @pytest.mark.unit
    def test_text_aes_reaches_text_entry(self):
        from shinymap import aes
        from shinymap.outline import Outline
        from shinymap.ui._ui import _default_wash

        outline = Outline.from_dict({"a": "M0 0 L10 0 L10 10 Z"})
        resolved = _default_wash.config.apply(aes.Text(fill_color="#ff0000"), outline)

        assert resolved["__text"].base.fill_color == "#ff0000"


app_click_with_render_ui = create_app_fixture("apps/app_click_with_render_ui.py")


class TestInitialValueRace:
    @pytest.mark.integration
    def test_click_right_after_load_is_kept(self, page, app_click_with_render_ui):
        """A pending initial-value retry must not overwrite the user's first click.

        The bridge retries setInputValue(id, initial) every 50 ms until Shiny is
        ready. To open that window deterministically, hide Shiny.setInputValue
        from the bridge until the test says so, then click right away.
        """
        page.add_init_script(
            """
            let real;
            Object.defineProperty(window, "Shiny", {
              configurable: true,
              get() { return real; },
              set(v) {
                real = new Proxy(v, {
                  get(t, k) {
                    if (k === "setInputValue" && !window.__shinyReady) return undefined;
                    return Reflect.get(t, k);
                  },
                });
              },
            });
            """
        )
        page.goto(app_click_with_render_ui.url)
        page.wait_for_selector("#pick svg path", state="attached", timeout=10000)
        page.evaluate(
            "() => { window.__shinyReady = true;"
            " document.querySelectorAll('#pick svg > g')[1].querySelectorAll('path')[1]"
            ".dispatchEvent(new MouseEvent('click', {bubbles: true})); }"
        )
        page.wait_for_timeout(1500)
        assert page.locator("#picked").inner_text() == "picked: b"
