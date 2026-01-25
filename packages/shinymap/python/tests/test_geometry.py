"""Tests for Outline class (geometry conversion utilities).

Note: Functional API (from_svg, from_json, convert, infer_relabel) has been
removed from shinymap.outline. Use Outline class methods or shinymap.kit instead.
See test_kit.py for kit.convert tests.
"""

import json
import tempfile
from pathlib import Path

import pytest

from shinymap.outline import Outline


@pytest.fixture
def sample_svg_file():
    """Create a temporary SVG file for testing."""
    svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 10 10 L 40 10 L 40 40 L 10 40 Z" fill="red"/>
  <path d="M 60 10 L 90 10 L 90 40 L 60 40 Z" fill="blue"/>
  <path id="bottom" d="M 10 60 L 90 60 L 90 90 L 10 90 Z" fill="green"/>
</svg>
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
        f.write(svg_content)
        svg_path = f.name

    yield svg_path

    # Cleanup
    Path(svg_path).unlink(missing_ok=True)


@pytest.fixture
def sample_intermediate_json():
    """Sample intermediate JSON for testing (list format)."""
    return {
        "_metadata": {"viewBox": "0 0 100 100"},
        "path_1": ["M 10 10 L 40 10 L 40 40 L 10 40 Z"],
        "path_2": ["M 60 10 L 90 10 L 90 40 L 60 40 Z"],
        "bottom": ["M 10 60 L 90 60 L 90 90 L 10 90 Z"],
    }


# ============================================================================
# Outline OOP API tests
# ============================================================================


@pytest.mark.unit
def test_outline_from_svg_class_method(sample_svg_file):
    """Test Outline.from_svg() class method."""
    geo = Outline.from_svg(sample_svg_file, extract_viewbox=True)

    assert isinstance(geo, Outline)
    assert len(geo.regions) == 3
    assert "viewBox" in geo.metadata
    assert geo.metadata["viewBox"] == "0 0 100 100"
    assert "path_1" in geo.regions
    assert "path_2" in geo.regions
    assert "bottom" in geo.regions


@pytest.mark.unit
def test_outline_from_svg_missing_file():
    """Test Outline.from_svg raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError, match="SVG file not found"):
        Outline.from_svg("/nonexistent/file.svg")


@pytest.mark.unit
def test_outline_from_json_class_method(sample_intermediate_json):
    """Test Outline.from_json() class method."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_intermediate_json, f)
        json_path = f.name

    try:
        geo = Outline.from_json(json_path)

        assert isinstance(geo, Outline)
        assert len(geo.regions) == 3
        assert "viewBox" in geo.metadata
        assert "path_1" in geo.regions
        assert "bottom" in geo.regions

    finally:
        Path(json_path).unlink(missing_ok=True)


@pytest.mark.unit
def test_outline_from_dict_class_method(sample_intermediate_json):
    """Test Outline.from_dict() class method."""
    geo = Outline.from_dict(sample_intermediate_json)

    assert isinstance(geo, Outline)
    assert len(geo.regions) == 3
    assert "viewBox" in geo.metadata
    assert geo.metadata["viewBox"] == "0 0 100 100"


@pytest.mark.unit
def test_outline_relabel_rename_single(sample_intermediate_json):
    """Test Outline.relabel() with single region rename."""
    geo = Outline.from_dict(sample_intermediate_json)
    geo_relabeled = geo.relabel({"top_left": "path_1"})

    # Check original unchanged (immutable)
    assert "path_1" in geo.regions
    assert "top_left" not in geo.regions

    # Check new object has rename
    assert "top_left" in geo_relabeled.regions
    assert "path_1" not in geo_relabeled.regions
    assert "path_2" in geo_relabeled.regions  # Unchanged
    assert "bottom" in geo_relabeled.regions  # Unchanged


@pytest.mark.unit
def test_outline_relabel_merge_multiple(sample_intermediate_json):
    """Test Outline.relabel() with region merge."""
    geo = Outline.from_dict(sample_intermediate_json)
    geo_merged = geo.relabel({"top_merged": ["path_1", "path_2"]})

    # Check original unchanged
    assert "path_1" in geo.regions
    assert "path_2" in geo.regions
    assert "top_merged" not in geo.regions

    # Check new object has merge
    assert "top_merged" in geo_merged.regions
    assert "path_1" not in geo_merged.regions
    assert "path_2" not in geo_merged.regions
    assert "bottom" in geo_merged.regions  # Unchanged

    # Check merged paths
    expected = ["M 10 10 L 40 10 L 40 40 L 10 40 Z", "M 60 10 L 90 10 L 90 40 L 60 40 Z"]
    assert geo_merged.regions["top_merged"] == expected


@pytest.mark.unit
def test_outline_relabel_nonexistent_raises(sample_intermediate_json):
    """Test Outline.relabel() raises ValueError for nonexistent region."""
    geo = Outline.from_dict(sample_intermediate_json)

    with pytest.raises(ValueError, match="Path 'nonexistent' not found"):
        geo.relabel({"new": "nonexistent"})


@pytest.mark.unit
def test_outline_set_overlays(sample_intermediate_json):
    """Test Outline.set_overlays() method."""
    geo = Outline.from_dict(sample_intermediate_json)
    geo_overlays = geo.set_overlays(["bottom", "_border"])

    # Check original unchanged
    assert "overlay" not in geo.metadata

    # Check new object has overlay
    assert "overlay" in geo_overlays.metadata
    assert geo_overlays.metadata["overlay"] == ["bottom", "_border"]
    assert "viewBox" in geo_overlays.metadata  # Other metadata preserved


@pytest.mark.unit
def test_outline_update_metadata(sample_intermediate_json):
    """Test Outline.update_metadata() method."""
    geo = Outline.from_dict(sample_intermediate_json)
    geo_updated = geo.update_metadata({"source": "Test", "license": "MIT"})

    # Check original unchanged
    assert "source" not in geo.metadata
    assert "license" not in geo.metadata

    # Check new object has updated metadata
    assert geo_updated.metadata["source"] == "Test"
    assert geo_updated.metadata["license"] == "MIT"
    assert geo_updated.metadata["viewBox"] == "0 0 100 100"  # Original preserved


@pytest.mark.unit
def test_outline_update_metadata_overwrites(sample_intermediate_json):
    """Test Outline.update_metadata() overwrites existing keys."""
    geo = Outline.from_dict(sample_intermediate_json)
    geo_updated = geo.update_metadata({"viewBox": "0 0 200 200"})

    # Check original unchanged
    assert geo.metadata["viewBox"] == "0 0 100 100"

    # Check new object has overwritten value
    assert geo_updated.metadata["viewBox"] == "0 0 200 200"


@pytest.mark.unit
def test_outline_to_dict(sample_intermediate_json):
    """Test Outline.to_dict() method."""
    geo = Outline.from_dict(sample_intermediate_json)
    output = geo.to_dict()

    assert "_metadata" in output
    assert output["_metadata"] == geo.metadata
    assert "path_1" in output
    assert "path_2" in output
    assert "bottom" in output


@pytest.mark.unit
def test_outline_to_json(sample_intermediate_json):
    """Test Outline.to_json() method."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        geo = Outline.from_dict(sample_intermediate_json)
        geo.to_json(output_path)

        # Verify file created
        assert Path(output_path).exists()

        # Verify file contents
        with open(output_path) as f:
            file_data = json.load(f)

        assert file_data == geo.to_dict()

    finally:
        Path(output_path).unlink(missing_ok=True)


@pytest.mark.unit
def test_outline_method_chaining(sample_intermediate_json):
    """Test Outline fluent API with method chaining."""
    geo = (
        Outline.from_dict(sample_intermediate_json)
        .relabel({"top_merged": ["path_1", "path_2"]})
        .set_overlays(["bottom"])
        .update_metadata({"source": "Test", "processed": "true"})
    )

    # Verify all transformations applied
    assert "top_merged" in geo.regions
    assert "path_1" not in geo.regions
    assert "path_2" not in geo.regions
    assert geo.metadata["overlay"] == ["bottom"]
    assert geo.metadata["source"] == "Test"
    assert geo.metadata["processed"] == "true"
    assert geo.metadata["viewBox"] == "0 0 100 100"  # Original preserved


@pytest.mark.unit
def test_outline_immutability(sample_intermediate_json):
    """Test that Outline transformations are immutable."""
    original = Outline.from_dict(sample_intermediate_json)
    original_region_count = len(original.regions)
    original_metadata_keys = set(original.metadata.keys())

    # Apply multiple transformations
    modified = original.relabel({"new": "path_1"})
    modified = modified.set_overlays(["bottom"])
    modified = modified.update_metadata({"custom": "value"})

    # Verify original unchanged
    assert len(original.regions) == original_region_count
    assert set(original.metadata.keys()) == original_metadata_keys
    assert "path_1" in original.regions
    assert "new" not in original.regions
    assert "overlay" not in original.metadata
    assert "custom" not in original.metadata

    # Verify modified has changes
    assert "new" in modified.regions
    assert "path_1" not in modified.regions
    assert "overlay" in modified.metadata
    assert "custom" in modified.metadata


@pytest.mark.integration
def test_outline_oop_workflow(sample_svg_file):
    """Test complete OOP workflow: load -> transform -> export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.json"

        # Complete workflow using OOP API
        geo = (
            Outline.from_svg(sample_svg_file, extract_viewbox=True)
            .relabel(
                {
                    "top_merged": ["path_1", "path_2"],
                    "_border": "bottom",
                }
            )
            .set_overlays(["_border"])
            .update_metadata({"source": "Test SVG", "license": "MIT"})
        )

        # Export to file
        geo.to_json(output_path)

        # Verify file created
        assert output_path.exists()

        # Load back and verify
        geo_reloaded = Outline.from_json(output_path)
        assert "top_merged" in geo_reloaded.regions
        assert "_border" in geo_reloaded.regions
        assert geo_reloaded.metadata["overlay"] == ["_border"]
        assert geo_reloaded.metadata["source"] == "Test SVG"


# ============================================================================
# move_layer() tests
# ============================================================================


@pytest.mark.unit
def test_move_layer_overlay():
    """Test move_layer() moves regions to overlay."""
    geo = Outline.from_dict(
        {
            "region": ["M 0 0"],
            "_border": ["M 0 0 L 100 0"],
        }
    )
    geo2 = geo.move_layer("overlay", "_border")

    assert geo2.overlay_ids() == ["_border"]
    # Original unchanged
    assert geo.overlay_ids() == []


@pytest.mark.unit
def test_move_layer_underlay():
    """Test move_layer() moves regions to underlay."""
    geo = Outline.from_dict(
        {
            "region": ["M 0 0"],
            "_grid": ["M 0 50 L 100 50"],
        }
    )
    geo2 = geo.move_layer("underlay", "_grid")

    assert geo2.underlay_ids() == ["_grid"]


@pytest.mark.unit
def test_move_layer_hidden():
    """Test move_layer() moves regions to hidden."""
    geo = Outline.from_dict(
        {
            "region": ["M 0 0"],
            "_guides": ["M 0 0 L 50 50"],
        }
    )
    geo2 = geo.move_layer("hidden", "_guides")

    assert geo2.hidden_ids() == ["_guides"]


@pytest.mark.unit
def test_move_layer_main():
    """Test move_layer('main') removes from all layers."""
    geo = Outline.from_dict(
        {
            "region": ["M 0 0"],
            "_border": ["M 0 0 L 100 0"],
            "_metadata": {"overlay": ["_border"]},
        }
    )
    assert geo.overlay_ids() == ["_border"]

    geo2 = geo.move_layer("main", "_border")
    assert geo2.overlay_ids() == []


@pytest.mark.unit
def test_move_layer_multiple_varargs():
    """Test move_layer() with multiple varargs."""
    geo = Outline.from_dict(
        {
            "region": ["M 0 0"],
            "_a": ["M 0 0"],
            "_b": ["M 0 0"],
        }
    )
    geo2 = geo.move_layer("overlay", "_a", "_b")

    assert sorted(geo2.overlay_ids()) == ["_a", "_b"]


@pytest.mark.unit
def test_move_layer_list_arg():
    """Test move_layer() with single list argument."""
    geo = Outline.from_dict(
        {
            "region": ["M 0 0"],
            "_a": ["M 0 0"],
            "_b": ["M 0 0"],
        }
    )
    geo2 = geo.move_layer("overlay", ["_a", "_b"])

    assert sorted(geo2.overlay_ids()) == ["_a", "_b"]


@pytest.mark.unit
def test_move_layer_removes_from_previous():
    """Test move_layer() removes region from previous layer."""
    geo = Outline.from_dict(
        {
            "region": ["M 0 0"],
            "_border": ["M 0 0 L 100 0"],
            "_metadata": {"overlay": ["_border"]},
        }
    )
    # Move from overlay to underlay
    geo2 = geo.move_layer("underlay", "_border")

    assert geo2.overlay_ids() == []
    assert geo2.underlay_ids() == ["_border"]


@pytest.mark.unit
def test_move_layer_chaining():
    """Test move_layer() can be chained."""
    geo = Outline.from_dict(
        {
            "region": ["M 0 0"],
            "_border": ["M 0 0 L 100 0"],
            "_grid": ["M 0 50 L 100 50"],
        }
    )
    geo2 = geo.move_layer("overlay", "_border").move_layer("underlay", "_grid")

    assert geo2.overlay_ids() == ["_border"]
    assert geo2.underlay_ids() == ["_grid"]


# ============================================================================
# move_group() tests
# ============================================================================


@pytest.mark.unit
def test_move_group_rename():
    """Test move_group() renames single region."""
    geo = Outline.from_dict(
        {
            "path_1": ["M 0 0 L 10 0"],
            "path_2": ["M 20 0 L 30 0"],
        }
    )
    geo2 = geo.move_group("renamed", "path_1")

    assert "renamed" in geo2.regions
    assert "path_1" not in geo2.regions
    assert "path_2" in geo2.regions


@pytest.mark.unit
def test_move_group_merge_varargs():
    """Test move_group() merges multiple regions with varargs."""
    geo = Outline.from_dict(
        {
            "path_1": ["M 0 0 L 10 0"],
            "path_2": ["M 20 0 L 30 0"],
            "path_3": ["M 40 0 L 50 0"],
        }
    )
    geo2 = geo.move_group("combined", "path_1", "path_2")

    assert sorted(geo2.regions.keys()) == ["combined", "path_3"]
    # Combined has both paths
    assert len(geo2.regions["combined"]) == 2


@pytest.mark.unit
def test_move_group_merge_list():
    """Test move_group() merges regions with list argument."""
    geo = Outline.from_dict(
        {
            "path_1": ["M 0 0 L 10 0"],
            "path_2": ["M 20 0 L 30 0"],
            "path_3": ["M 40 0 L 50 0"],
        }
    )
    geo2 = geo.move_group("all", ["path_1", "path_2", "path_3"])

    assert list(geo2.regions.keys()) == ["all"]
    assert len(geo2.regions["all"]) == 3


@pytest.mark.unit
def test_move_group_nonexistent_raises():
    """Test move_group() raises ValueError for nonexistent region."""
    geo = Outline.from_dict(
        {
            "path_1": ["M 0 0 L 10 0"],
        }
    )

    with pytest.raises(ValueError, match="Path 'nonexistent' not found"):
        geo.move_group("new", "nonexistent")


@pytest.mark.unit
def test_move_group_chaining():
    """Test move_group() can be chained."""
    geo = Outline.from_dict(
        {
            "path_1": ["M 0 0"],
            "path_2": ["M 10 0"],
            "path_3": ["M 20 0"],
            "path_4": ["M 30 0"],
        }
    )
    geo2 = geo.move_group("group_a", "path_1", "path_2").move_group("group_b", "path_3", "path_4")

    assert sorted(geo2.regions.keys()) == ["group_a", "group_b"]


# ============================================================================
# EOL stub tests
# ============================================================================


@pytest.mark.unit
def test_deprecated_from_svg_raises():
    """Test that importing from_svg from outline raises ImportError."""
    with pytest.raises(ImportError, match="has been removed"):
        from shinymap.outline import from_svg  # noqa: F401


@pytest.mark.unit
def test_deprecated_from_json_raises():
    """Test that importing from_json from outline raises ImportError."""
    with pytest.raises(ImportError, match="has been removed"):
        from shinymap.outline import from_json  # noqa: F401


@pytest.mark.unit
def test_deprecated_convert_raises():
    """Test that importing convert from outline raises ImportError."""
    with pytest.raises(ImportError, match="has been removed"):
        from shinymap.outline import convert  # noqa: F401


@pytest.mark.unit
def test_deprecated_infer_relabel_raises():
    """Test that importing infer_relabel from outline raises ImportError."""
    with pytest.raises(ImportError, match="has been removed"):
        from shinymap.outline import infer_relabel  # noqa: F401
