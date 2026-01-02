"""Tests for geometry conversion utilities (from_svg, from_json, convert)."""

import json
import tempfile
from pathlib import Path

import pytest

from shinymap.outline import convert, from_json, from_svg


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
# from_svg() tests
# ============================================================================


@pytest.mark.unit
def test_from_svg_basic(sample_svg_file):
    """Test basic SVG extraction."""
    result = from_svg(sample_svg_file, output_path=None)

    assert "_metadata" in result
    assert "viewBox" in result["_metadata"]
    assert result["_metadata"]["viewBox"] == "0 0 100 100"

    # Should have auto-generated IDs for paths without IDs
    path_ids = [k for k in result.keys() if k != "_metadata"]
    assert len(path_ids) == 3
    assert "bottom" in path_ids  # Existing ID preserved
    assert "path_1" in path_ids  # Auto-generated ID
    assert "path_2" in path_ids  # Auto-generated ID


@pytest.mark.unit
def test_from_svg_writes_to_file(sample_svg_file):
    """Test that from_svg writes to file when output_path provided."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        result = from_svg(sample_svg_file, output_path=output_path)

        # Should return dict
        assert isinstance(result, dict)

        # Should write to file
        assert Path(output_path).exists()

        # File should contain same data
        with open(output_path) as f:
            file_data = json.load(f)

        assert file_data == result

    finally:
        Path(output_path).unlink(missing_ok=True)


@pytest.mark.unit
def test_from_svg_missing_file():
    """Test from_svg raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError, match="SVG file not found"):
        from_svg("/nonexistent/file.svg")


# ============================================================================
# from_json() tests - relabel parameter (CORE FUNCTIONALITY)
# ============================================================================


@pytest.mark.unit
def test_from_json_relabel_rename_single(sample_intermediate_json):
    """Test relabel parameter with string value (rename single path)."""
    result = from_json(
        sample_intermediate_json,
        output_path=None,
        relabel={
            "top_left": "path_1",  # Rename path_1 -> top_left
            "top_right": "path_2",  # Rename path_2 -> top_right
        },
    )

    # Check renamed IDs
    assert "top_left" in result
    assert "top_right" in result
    assert "bottom" in result  # Unchanged

    # Original IDs should not exist
    assert "path_1" not in result
    assert "path_2" not in result

    # Path data should be preserved (list format)
    assert result["top_left"] == sample_intermediate_json["path_1"]
    assert result["top_right"] == sample_intermediate_json["path_2"]


@pytest.mark.unit
def test_from_json_relabel_merge_multiple(sample_intermediate_json):
    """Test relabel parameter with list value (merge multiple paths)."""
    result = from_json(
        sample_intermediate_json,
        output_path=None,
        relabel={
            "top_merged": ["path_1", "path_2"],  # Merge path_1 + path_2
        },
    )

    # Check merged ID exists
    assert "top_merged" in result
    assert "bottom" in result  # Unchanged

    # Original IDs should not exist
    assert "path_1" not in result
    assert "path_2" not in result

    # Merged path should contain both paths as list
    expected = ["M 10 10 L 40 10 L 40 40 L 10 40 Z", "M 60 10 L 90 10 L 90 40 L 60 40 Z"]
    assert result["top_merged"] == expected


@pytest.mark.unit
def test_from_json_relabel_mixed(sample_intermediate_json):
    """Test relabel with both rename (string) and merge (list) in same call."""
    result = from_json(
        sample_intermediate_json,
        output_path=None,
        relabel={
            "top_merged": ["path_1", "path_2"],  # Merge
            "bottom_renamed": "bottom",  # Rename
        },
    )

    assert "top_merged" in result
    assert "bottom_renamed" in result
    assert "path_1" not in result
    assert "path_2" not in result
    assert "bottom" not in result

    # Check data
    assert result["bottom_renamed"] == sample_intermediate_json["bottom"]


@pytest.mark.unit
def test_from_json_relabel_nonexistent_path(sample_intermediate_json):
    """Test from_json raises ValueError for nonexistent path in relabel."""
    with pytest.raises(ValueError, match="Path 'nonexistent'.*not found"):
        from_json(
            sample_intermediate_json,
            output_path=None,
            relabel={"new_id": "nonexistent"},
        )


@pytest.mark.unit
def test_from_json_relabel_merge_nonexistent(sample_intermediate_json):
    """Test from_json raises ValueError when merging nonexistent path."""
    with pytest.raises(ValueError, match="Path 'missing'.*not found"):
        from_json(
            sample_intermediate_json,
            output_path=None,
            relabel={"merged": ["path_1", "missing"]},
        )


@pytest.mark.unit
def test_from_json_relabel_partial(sample_intermediate_json):
    """Test that relabel only affects specified paths, others unchanged."""
    result = from_json(
        sample_intermediate_json,
        output_path=None,
        relabel={"top": "path_1"},  # Only relabel path_1
    )

    assert "top" in result
    assert "path_2" in result  # Unchanged
    assert "bottom" in result  # Unchanged
    assert "path_1" not in result


@pytest.mark.unit
def test_from_json_no_relabel(sample_intermediate_json):
    """Test from_json without relabel preserves all IDs."""
    result = from_json(sample_intermediate_json, output_path=None)

    assert "path_1" in result
    assert "path_2" in result
    assert "bottom" in result


# ============================================================================
# from_json() tests - overlay_ids and metadata
# ============================================================================


@pytest.mark.unit
def test_from_json_overlay_ids(sample_intermediate_json):
    """Test overlay_ids parameter adds to metadata."""
    result = from_json(
        sample_intermediate_json,
        output_path=None,
        overlay_ids=["bottom"],
    )

    assert "_metadata" in result
    assert "overlays" in result["_metadata"]
    assert result["_metadata"]["overlays"] == ["bottom"]


@pytest.mark.unit
def test_from_json_metadata_merge(sample_intermediate_json):
    """Test metadata parameter merges with existing metadata."""
    result = from_json(
        sample_intermediate_json,
        output_path=None,
        metadata={"source": "Test", "license": "MIT"},
    )

    assert "_metadata" in result
    assert result["_metadata"]["viewBox"] == "0 0 100 100"  # Existing preserved
    assert result["_metadata"]["source"] == "Test"  # New added
    assert result["_metadata"]["license"] == "MIT"  # New added


@pytest.mark.unit
def test_from_json_metadata_overwrites(sample_intermediate_json):
    """Test that metadata parameter overwrites existing keys."""
    result = from_json(
        sample_intermediate_json,
        output_path=None,
        metadata={"viewBox": "0 0 200 200"},  # Override existing
    )

    assert result["_metadata"]["viewBox"] == "0 0 200 200"


# ============================================================================
# from_json() tests - file I/O
# ============================================================================


@pytest.mark.unit
def test_from_json_loads_from_file_path(sample_intermediate_json):
    """Test from_json can load from JSON file path (string)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_intermediate_json, f)
        json_path = f.name

    try:
        result = from_json(json_path, output_path=None, relabel={"top": "path_1"})

        assert "top" in result
        assert "path_2" in result

    finally:
        Path(json_path).unlink(missing_ok=True)


@pytest.mark.unit
def test_from_json_loads_from_path_object(sample_intermediate_json):
    """Test from_json can load from Path object."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_intermediate_json, f)
        json_path = Path(f.name)

    try:
        result = from_json(json_path, output_path=None, relabel={"top": "path_1"})

        assert "top" in result

    finally:
        json_path.unlink(missing_ok=True)


@pytest.mark.unit
def test_from_json_writes_to_file(sample_intermediate_json):
    """Test from_json writes to file when output_path provided."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        result = from_json(
            sample_intermediate_json,
            output_path=output_path,
            relabel={"top": "path_1"},
        )

        # Should write to file
        assert Path(output_path).exists()

        # File should contain same data
        with open(output_path) as f:
            file_data = json.load(f)

        assert file_data == result

    finally:
        Path(output_path).unlink(missing_ok=True)


@pytest.mark.unit
def test_from_json_missing_file():
    """Test from_json raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError, match="JSON file not found"):
        from_json("/nonexistent/file.json")


@pytest.mark.unit
def test_from_json_invalid_json():
    """Test from_json raises ValueError for invalid JSON."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{ invalid json }")
        json_path = f.name

    try:
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            from_json(json_path)

    finally:
        Path(json_path).unlink(missing_ok=True)


# ============================================================================
# convert() tests (one-shot conversion)
# ============================================================================


@pytest.mark.unit
def test_convert_basic(sample_svg_file):
    """Test convert() performs one-shot SVG -> JSON conversion."""
    result = convert(sample_svg_file, output_path=None)

    # Should have metadata
    assert "_metadata" in result
    assert result["_metadata"]["viewBox"] == "0 0 100 100"

    # Should have paths
    path_ids = [k for k in result.keys() if k != "_metadata"]
    assert len(path_ids) == 3


@pytest.mark.unit
def test_convert_with_relabel(sample_svg_file):
    """Test convert() with relabel parameter."""
    result = convert(
        sample_svg_file,
        output_path=None,
        relabel={
            "top_left": "path_1",
            "top_right": "path_2",
            "bottom_rect": "bottom",
        },
    )

    assert "top_left" in result
    assert "top_right" in result
    assert "bottom_rect" in result
    assert "path_1" not in result
    assert "path_2" not in result
    assert "bottom" not in result


@pytest.mark.unit
def test_convert_with_merge(sample_svg_file):
    """Test convert() with path merging."""
    result = convert(
        sample_svg_file,
        output_path=None,
        relabel={
            "all_regions": ["path_1", "path_2", "bottom"],
        },
    )

    assert "all_regions" in result
    assert "path_1" not in result
    assert "path_2" not in result
    assert "bottom" not in result

    # Should have merged all three paths (list format)
    # v1.x format: Elements are dicts with type and attributes
    all_regions = result["all_regions"]
    assert len(all_regions) == 3
    # Check that all elements are path dicts
    assert all(isinstance(elem, dict) and elem.get("type") == "path" for elem in all_regions)
    # Check that the merged paths contain the expected path data
    path_strings = [elem.get("d", "") for elem in all_regions]
    assert any("M 10 10" in path for path in path_strings)
    assert any("M 60 10" in path for path in path_strings)
    assert any("M 10 60" in path for path in path_strings)


@pytest.mark.unit
def test_convert_with_overlay_and_metadata(sample_svg_file):
    """Test convert() with overlay_ids and metadata."""
    result = convert(
        sample_svg_file,
        output_path=None,
        relabel={"border": "bottom"},
        overlay_ids=["border"],
        metadata={"source": "Test SVG", "license": "MIT"},
    )

    assert result["_metadata"]["overlays"] == ["border"]
    assert result["_metadata"]["source"] == "Test SVG"
    assert result["_metadata"]["license"] == "MIT"
    assert result["_metadata"]["viewBox"] == "0 0 100 100"  # Preserved


@pytest.mark.unit
def test_convert_writes_to_file(sample_svg_file):
    """Test convert() writes to file when output_path provided."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        result = convert(sample_svg_file, output_path=output_path)

        # Should write to file
        assert Path(output_path).exists()

        # File should contain same data
        with open(output_path) as f:
            file_data = json.load(f)

        assert file_data == result

    finally:
        Path(output_path).unlink(missing_ok=True)


# ============================================================================
# Integration tests - complete workflows
# ============================================================================


@pytest.mark.integration
def test_interactive_workflow(sample_svg_file):
    """Test complete interactive workflow: SVG -> intermediate -> final."""
    # Step 1: Extract intermediate JSON
    intermediate = from_svg(sample_svg_file, output_path=None)

    # Inspect intermediate (simulated)
    path_ids = [k for k in intermediate.keys() if k != "_metadata"]
    assert len(path_ids) == 3

    # Step 2: Apply transformations
    final = from_json(
        intermediate,
        output_path=None,
        relabel={
            "region_north": ["path_1", "path_2"],
            "_border": "bottom",
        },
        overlay_ids=["_border"],
        metadata={"source": "Custom", "license": "MIT"},
    )

    # Verify final output
    assert "region_north" in final
    assert "_border" in final
    assert final["_metadata"]["overlays"] == ["_border"]
    assert final["_metadata"]["source"] == "Custom"


@pytest.mark.integration
def test_workflow_with_json_persistence(sample_svg_file):
    """Test workflow with intermediate JSON saved to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        intermediate_path = Path(tmpdir) / "intermediate.json"
        final_path = Path(tmpdir) / "final.json"

        # Step 1: SVG -> intermediate JSON (save to file)
        from_svg(sample_svg_file, output_path=intermediate_path)

        assert intermediate_path.exists()

        # Step 2: Load intermediate, apply transformations, save final
        from_json(
            intermediate_path,  # Load from file
            output_path=final_path,  # Save to file
            relabel={"merged": ["path_1", "path_2"]},
        )

        assert final_path.exists()

        # Verify final JSON
        with open(final_path) as f:
            final = json.load(f)

        assert "merged" in final
        assert "bottom" in final


@pytest.mark.integration
def test_one_shot_vs_two_step_equivalence(sample_svg_file):
    """Test that convert() produces same result as from_svg() + from_json()."""
    relabel = {"top": ["path_1", "path_2"], "bottom_rect": "bottom"}
    metadata = {"source": "Test", "license": "MIT"}
    overlay_ids = ["bottom_rect"]

    # One-shot conversion
    result_one_shot = convert(
        sample_svg_file,
        output_path=None,
        relabel=relabel,
        overlay_ids=overlay_ids,
        metadata=metadata,
    )

    # Two-step conversion
    intermediate = from_svg(sample_svg_file, output_path=None)
    result_two_step = from_json(
        intermediate,
        output_path=None,
        relabel=relabel,
        overlay_ids=overlay_ids,
        metadata=metadata,
    )

    # Should be identical
    assert result_one_shot == result_two_step


@pytest.mark.integration
def test_convert_accepts_json_input(sample_svg_file):
    """Test that convert() can accept intermediate JSON file as input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        intermediate_path = Path(tmpdir) / "intermediate.json"

        # Step 1: Create intermediate JSON from SVG
        from_svg(sample_svg_file, output_path=intermediate_path)

        # Step 2: Use convert() with JSON input
        result = convert(
            intermediate_path,
            output_path=None,
            relabel={
                "top_left": "path_1",
                "top_right": "path_2",
            },
        )

        # Verify transformation applied
        assert "top_left" in result
        assert "top_right" in result
        assert "bottom" in result
        assert "path_1" not in result
        assert "path_2" not in result


@pytest.mark.integration
def test_convert_svg_vs_json_equivalence(sample_svg_file):
    """Test that convert() produces same result whether input is SVG or JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        intermediate_path = Path(tmpdir) / "intermediate.json"

        # Create intermediate JSON
        from_svg(sample_svg_file, output_path=intermediate_path)

        relabel = {"merged": ["path_1", "path_2"]}
        metadata = {"source": "Test"}

        # Convert from SVG
        result_from_svg = convert(
            sample_svg_file,
            output_path=None,
            relabel=relabel,
            metadata=metadata,
        )

        # Convert from JSON
        result_from_json = convert(
            intermediate_path,
            output_path=None,
            relabel=relabel,
            metadata=metadata,
        )

        # Should be identical
        assert result_from_svg == result_from_json


# ============================================================================
# infer_relabel() tests
# ============================================================================


@pytest.mark.unit
def test_infer_relabel_from_svg(sample_svg_file):
    """Test inferring relabel from SVG to final JSON."""
    from shinymap.outline import infer_relabel

    # Create final JSON with renames (v1.x format with Element dicts)
    # Must match what from_svg() produces, including fill attributes
    final = {
        "_metadata": {"viewBox": "0 0 100 100"},
        "top_left": [{"type": "path", "d": "M 10 10 L 40 10 L 40 40 L 10 40 Z", "fill": "red"}],
        "top_right": [{"type": "path", "d": "M 60 10 L 90 10 L 90 40 L 60 40 Z", "fill": "blue"}],
        "bottom": [{"type": "path", "d": "M 10 60 L 90 60 L 90 90 L 10 90 Z", "fill": "green"}],
    }

    inferred = infer_relabel(sample_svg_file, final)

    assert inferred is not None
    assert inferred["top_left"] == "path_1"
    assert inferred["top_right"] == "path_2"
    # "bottom" has same ID in both, so not in relabel mapping
    assert "bottom" not in inferred


@pytest.mark.unit
def test_infer_relabel_merge(sample_svg_file):
    """Test inferring merge transformations."""
    from shinymap.outline import infer_relabel

    # Create final JSON with merge (v1.x format with Element dicts)
    # Must match what from_svg() produces, including fill attributes
    final = {
        "_metadata": {"viewBox": "0 0 100 100"},
        "all_top": [
            {"type": "path", "d": "M 10 10 L 40 10 L 40 40 L 10 40 Z", "fill": "red"},
            {"type": "path", "d": "M 60 10 L 90 10 L 90 40 L 60 40 Z", "fill": "blue"},
        ],
        "bottom": [{"type": "path", "d": "M 10 60 L 90 60 L 90 90 L 10 90 Z", "fill": "green"}],
    }

    inferred = infer_relabel(sample_svg_file, final)

    assert inferred is not None
    assert inferred["all_top"] == ["path_1", "path_2"]
    assert "bottom" not in inferred


@pytest.mark.unit
def test_infer_relabel_from_intermediate_json(sample_svg_file):
    """Test inferring relabel from intermediate JSON."""
    from shinymap.outline import infer_relabel

    with tempfile.TemporaryDirectory() as tmpdir:
        intermediate_path = Path(tmpdir) / "intermediate.json"
        from_svg(sample_svg_file, output_path=intermediate_path)

        # Create final JSON (v1.x format with Element dicts)
        # Must match what from_svg() produces, including fill attributes
        final = {
            "_metadata": {"viewBox": "0 0 100 100"},
            "region_a": [{"type": "path", "d": "M 10 10 L 40 10 L 40 40 L 10 40 Z", "fill": "red"}],
            "region_b": [
                {"type": "path", "d": "M 60 10 L 90 10 L 90 40 L 60 40 Z", "fill": "blue"}
            ],
            "bottom": [{"type": "path", "d": "M 10 60 L 90 60 L 90 90 L 10 90 Z", "fill": "green"}],
        }

        inferred = infer_relabel(intermediate_path, final)

        assert inferred is not None
        assert inferred["region_a"] == "path_1"
        assert inferred["region_b"] == "path_2"


@pytest.mark.unit
def test_infer_relabel_no_changes(sample_intermediate_json):
    """Test that infer_relabel returns None when no transformations."""
    from shinymap.outline import infer_relabel

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write intermediate to file
        intermediate_path = Path(tmpdir) / "intermediate.json"
        with open(intermediate_path, "w") as f:
            json.dump(sample_intermediate_json, f)

        # Final is identical to intermediate
        final = sample_intermediate_json.copy()

        inferred = infer_relabel(intermediate_path, final)

        assert inferred is None  # No transformations needed


# ============================================================================
# Outline OOP API tests
# ============================================================================


@pytest.mark.unit
def test_geometry_from_svg_class_method(sample_svg_file):
    """Test Outline.from_svg() class method."""
    from shinymap.outline import Outline

    geo = Outline.from_svg(sample_svg_file, extract_viewbox=True)

    assert isinstance(geo, Outline)
    assert len(geo.regions) == 3
    assert "viewBox" in geo.metadata
    assert geo.metadata["viewBox"] == "0 0 100 100"
    assert "path_1" in geo.regions
    assert "path_2" in geo.regions
    assert "bottom" in geo.regions


@pytest.mark.unit
def test_geometry_from_json_class_method(sample_intermediate_json):
    """Test Outline.from_json() class method."""
    from shinymap.outline import Outline

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
def test_geometry_from_dict_class_method(sample_intermediate_json):
    """Test Outline.from_dict() class method."""
    from shinymap.outline import Outline

    geo = Outline.from_dict(sample_intermediate_json)

    assert isinstance(geo, Outline)
    assert len(geo.regions) == 3
    assert "viewBox" in geo.metadata
    assert geo.metadata["viewBox"] == "0 0 100 100"


@pytest.mark.unit
def test_geometry_relabel_rename_single(sample_intermediate_json):
    """Test Outline.relabel() with single region rename."""
    from shinymap.outline import Outline

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
def test_geometry_relabel_merge_multiple(sample_intermediate_json):
    """Test Outline.relabel() with region merge."""
    from shinymap.outline import Outline

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
def test_geometry_relabel_nonexistent_raises(sample_intermediate_json):
    """Test Outline.relabel() raises ValueError for nonexistent region."""
    from shinymap.outline import Outline

    geo = Outline.from_dict(sample_intermediate_json)

    with pytest.raises(ValueError, match="Path 'nonexistent' not found"):
        geo.relabel({"new": "nonexistent"})


@pytest.mark.unit
def test_geometry_set_overlays(sample_intermediate_json):
    """Test Outline.set_overlays() method."""
    from shinymap.outline import Outline

    geo = Outline.from_dict(sample_intermediate_json)
    geo_overlays = geo.set_overlays(["bottom", "_border"])

    # Check original unchanged
    assert "overlays" not in geo.metadata

    # Check new object has overlays
    assert "overlays" in geo_overlays.metadata
    assert geo_overlays.metadata["overlays"] == ["bottom", "_border"]
    assert "viewBox" in geo_overlays.metadata  # Other metadata preserved


@pytest.mark.unit
def test_geometry_update_metadata(sample_intermediate_json):
    """Test Outline.update_metadata() method."""
    from shinymap.outline import Outline

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
def test_geometry_update_metadata_overwrites(sample_intermediate_json):
    """Test Outline.update_metadata() overwrites existing keys."""
    from shinymap.outline import Outline

    geo = Outline.from_dict(sample_intermediate_json)
    geo_updated = geo.update_metadata({"viewBox": "0 0 200 200"})

    # Check original unchanged
    assert geo.metadata["viewBox"] == "0 0 100 100"

    # Check new object has overwritten value
    assert geo_updated.metadata["viewBox"] == "0 0 200 200"


@pytest.mark.unit
def test_geometry_to_dict(sample_intermediate_json):
    """Test Outline.to_dict() method."""
    from shinymap.outline import Outline

    geo = Outline.from_dict(sample_intermediate_json)
    output = geo.to_dict()

    assert "_metadata" in output
    assert output["_metadata"] == geo.metadata
    assert "path_1" in output
    assert "path_2" in output
    assert "bottom" in output


@pytest.mark.unit
def test_geometry_to_json(sample_intermediate_json):
    """Test Outline.to_json() method."""
    from shinymap.outline import Outline

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
    from shinymap.outline import Outline

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
    assert geo.metadata["overlays"] == ["bottom"]
    assert geo.metadata["source"] == "Test"
    assert geo.metadata["processed"] == "true"
    assert geo.metadata["viewBox"] == "0 0 100 100"  # Original preserved


@pytest.mark.unit
def test_outline_immutability(sample_intermediate_json):
    """Test that Outline transformations are immutable."""
    from shinymap.outline import Outline

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
    assert "overlays" not in original.metadata
    assert "custom" not in original.metadata

    # Verify modified has changes
    assert "new" in modified.regions
    assert "path_1" not in modified.regions
    assert "overlays" in modified.metadata
    assert "custom" in modified.metadata


@pytest.mark.integration
def test_geometry_oop_workflow(sample_svg_file):
    """Test complete OOP workflow: load -> transform -> export."""
    from shinymap.outline import Outline

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
        assert geo_reloaded.metadata["overlays"] == ["_border"]
        assert geo_reloaded.metadata["source"] == "Test SVG"


@pytest.mark.integration
def test_functional_api_uses_outline_internally(sample_svg_file):
    """Test that functional API delegates to Outline class."""
    from shinymap.outline import Outline

    # Functional API
    result_functional = from_svg(sample_svg_file, output_path=None)

    # OOP API
    geo = Outline.from_svg(sample_svg_file, extract_viewbox=True)
    result_oop = geo.to_dict()

    # Should produce identical results
    assert result_functional == result_oop


@pytest.mark.integration
def test_geometry_oop_equivalence_with_functional(sample_svg_file):
    """Test that OOP and functional APIs produce identical results."""
    relabel = {"merged": ["path_1", "path_2"], "border": "bottom"}
    overlay_ids = ["border"]
    metadata = {"source": "Test", "license": "MIT"}

    # Functional API
    result_functional = convert(
        sample_svg_file,
        output_path=None,
        relabel=relabel,
        overlay_ids=overlay_ids,
        metadata=metadata,
    )

    # OOP API
    from shinymap.outline import Outline

    geo = (
        Outline.from_svg(sample_svg_file, extract_viewbox=True)
        .relabel(relabel)
        .set_overlays(overlay_ids)
        .update_metadata(metadata)
    )
    result_oop = geo.to_dict()

    # Should be identical
    assert result_functional == result_oop
