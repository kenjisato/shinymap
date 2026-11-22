"""Tests for Outline layer metadata."""

import pytest

from shinymap.outline import Outline


class TestPluralLayerKeysRejected:
    """Layer keys became singular in 0.3.0; plural keys must not be silently ignored."""

    @pytest.mark.unit
    @pytest.mark.parametrize("key", ["overlays", "underlays", "annotations"])
    def test_metadata_plural_key_raises(self, key):
        with pytest.raises(ValueError, match=f"'{key}'.*'{key[:-1]}'"):
            Outline.from_dict({"a": "M0 0 L1 1", "_metadata": {key: ["a"]}})

    @pytest.mark.unit
    def test_merge_layers_plural_key_raises(self):
        outline = Outline.from_dict({"a": "M0 0 L1 1"})
        with pytest.raises(ValueError, match="'overlays'.*'overlay'"):
            outline.merge_layers({"overlays": ["a"]})

    @pytest.mark.unit
    def test_map_layers_plural_key_raises(self):
        from shinymap import Map

        with pytest.raises(ValueError, match="'underlays'.*'underlay'"):
            Map(layers={"underlays": ["a"]})

    @pytest.mark.unit
    def test_singular_keys_still_work(self):
        outline = Outline.from_dict({"a": "M0 0 L1 1", "_metadata": {"overlay": ["a"]}})
        assert outline.overlay_ids() == ["a"]
