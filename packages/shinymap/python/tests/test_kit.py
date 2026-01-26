"""Tests for the shinymap.kit module."""

import tempfile
from pathlib import Path as PathLib

import pytest

from shinymap import Outline
from shinymap.kit import apply_mapping, convert, describe, generate_code, glaze
from shinymap.outline import Regions
from shinymap.svg import Circle, Path, Text


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
    PathLib(svg_path).unlink(missing_ok=True)


@pytest.fixture
def sample_outline():
    """Create a sample Outline for testing."""
    return Outline(
        regions=Regions(
            {
                "region_a": [Path(d="M 0 0 L 50 0 L 50 50 L 0 50 Z")],
                "region_b": [Path(d="M 60 0 L 100 0 L 100 50 L 60 50 Z")],
                "region_c": [Circle(cx=25, cy=75, r=20)],
            }
        ),
        metadata={"viewBox": "0 0 100 100"},
    )


# ============================================================================
# describe() tests
# ============================================================================


class TestDescribe:
    """Tests for describe() function."""

    def test_describe_basic(self, sample_outline):
        """Test basic label generation."""
        labels = describe(sample_outline)

        assert isinstance(labels, Regions)
        assert len(labels) == 3
        assert "_label_region_a" in labels
        assert "_label_region_b" in labels
        assert "_label_region_c" in labels

    def test_describe_generates_text_elements(self, sample_outline):
        """Test that describe generates Text elements."""
        labels = describe(sample_outline)

        for _label_id, elements in labels.items():
            assert len(elements) == 1
            assert isinstance(elements[0], Text)

    def test_describe_text_at_center(self, sample_outline):
        """Test that Text elements are at region centers."""
        labels = describe(sample_outline)

        # region_a: bbox is (0, 0, 50, 50), center is (25, 25)
        text_a = labels["_label_region_a"][0]
        assert text_a.x == 25.0
        assert text_a.y == 25.0

        # region_b: bbox is (60, 0, 100, 50), center is (80, 25)
        text_b = labels["_label_region_b"][0]
        assert text_b.x == 80.0
        assert text_b.y == 25.0

        # region_c: Circle cx=25, cy=75, r=20, bbox is (5, 55, 45, 95), center is (25, 75)
        text_c = labels["_label_region_c"][0]
        assert text_c.x == 25.0
        assert text_c.y == 75.0

    def test_describe_text_content(self, sample_outline):
        """Test that Text elements contain region IDs."""
        labels = describe(sample_outline)

        assert labels["_label_region_a"][0].text == "region_a"
        assert labels["_label_region_b"][0].text == "region_b"
        assert labels["_label_region_c"][0].text == "region_c"

    def test_describe_exclude(self, sample_outline):
        """Test excluding regions from labels."""
        labels = describe(sample_outline, exclude=["region_a", "region_c"])

        assert len(labels) == 1
        assert "_label_region_b" in labels
        assert "_label_region_a" not in labels
        assert "_label_region_c" not in labels

    def test_describe_custom_styling(self, sample_outline):
        """Test custom text styling via kwargs."""
        labels = describe(sample_outline, font_size="10", fill="red")

        text = labels["_label_region_a"][0]
        assert text.font_size == "10"
        assert text.fill == "red"

    def test_describe_default_styling(self, sample_outline):
        """Test default text styling."""
        labels = describe(sample_outline)

        text = labels["_label_region_a"][0]
        # Default is 3% of viewBox (100x100), so 3.0
        assert text.font_size == "3.0"
        assert text.fill == "#333"
        assert text.text_anchor == "middle"
        assert text.dominant_baseline == "central"


# ============================================================================
# glaze() tests
# ============================================================================


class TestGlaze:
    """Tests for glaze() function."""

    def test_glaze_adds_regions(self, sample_outline):
        """Test that glaze adds new regions."""
        labels = Regions({"_note": [Text(x=50, y=50, text="Note")]})
        result = glaze(sample_outline, labels)

        assert "_note" in result.regions
        assert "region_a" in result.regions

    def test_glaze_as_overlay_default(self, sample_outline):
        """Test that glaze adds as overlay by default."""
        labels = Regions({"_note": [Text(x=50, y=50, text="Note")]})
        result = glaze(sample_outline, labels)

        assert "_note" in result.metadata.get("overlay", [])
        assert "_note" not in result.metadata.get("underlay", [])

    def test_glaze_as_underlay(self, sample_outline):
        """Test that glaze can add as underlay."""
        labels = Regions({"_bg": [Path(d="M 0 0 L 100 0 L 100 100 L 0 100 Z")]})
        result = glaze(sample_outline, labels, as_underlay=True)

        assert "_bg" in result.metadata.get("underlay", [])
        assert "_bg" not in result.metadata.get("overlay", [])

    def test_glaze_accepts_outline(self, sample_outline):
        """Test that glaze accepts Outline as input."""
        other = Outline(
            regions=Regions({"_extra": [Circle(cx=50, cy=50, r=10)]}),
            metadata={},
        )
        result = glaze(sample_outline, other)

        assert "_extra" in result.regions
        assert "_extra" in result.metadata.get("overlay", [])

    def test_glaze_preserves_original_metadata(self, sample_outline):
        """Test that glaze preserves original metadata."""
        labels = Regions({"_note": [Text(x=50, y=50, text="Note")]})
        result = glaze(sample_outline, labels)

        assert result.metadata.get("viewBox") == "0 0 100 100"

    def test_glaze_immutable(self, sample_outline):
        """Test that glaze doesn't modify original outline."""
        original_regions = set(sample_outline.regions.keys())
        labels = Regions({"_note": [Text(x=50, y=50, text="Note")]})
        glaze(sample_outline, labels)

        assert set(sample_outline.regions.keys()) == original_regions


# ============================================================================
# convert() tests
# ============================================================================


class TestConvert:
    """Tests for convert() function."""

    def test_convert_basic(self, sample_svg_file):
        """Test basic SVG conversion."""
        result = convert(sample_svg_file)

        assert isinstance(result, dict)
        assert "_metadata" in result

    def test_convert_with_relabel(self, sample_svg_file):
        """Test conversion with relabeling."""
        result = convert(sample_svg_file, relabel={"top_left": "path_1"})

        assert "top_left" in result
        assert "path_1" not in result

    def test_convert_with_overlay(self, sample_svg_file):
        """Test conversion with overlay assignment."""
        result = convert(sample_svg_file, overlay_ids=["bottom"])

        assert "bottom" in result["_metadata"].get("overlay", [])

    def test_convert_with_underlay(self, sample_svg_file):
        """Test conversion with underlay assignment."""
        result = convert(sample_svg_file, underlay_ids=["bottom"])

        assert "bottom" in result["_metadata"].get("underlay", [])

    def test_convert_with_hidden(self, sample_svg_file):
        """Test conversion with hidden assignment."""
        result = convert(sample_svg_file, hidden_ids=["bottom"])

        assert "bottom" in result["_metadata"].get("hidden", [])

    def test_convert_with_annotation(self, sample_svg_file):
        """Test conversion with annotation assignment."""
        result = convert(sample_svg_file, annotation_ids=["bottom"])

        assert "bottom" in result["_metadata"].get("annotation", [])

    def test_convert_with_all_layers(self, sample_svg_file):
        """Test conversion with all layer types."""
        result = convert(
            sample_svg_file,
            overlay_ids=["path_1"],
            underlay_ids=["path_2"],
            hidden_ids=["bottom"],
        )

        assert "path_1" in result["_metadata"].get("overlay", [])
        assert "path_2" in result["_metadata"].get("underlay", [])
        assert "bottom" in result["_metadata"].get("hidden", [])

    def test_convert_with_metadata(self, sample_svg_file):
        """Test conversion with metadata."""
        result = convert(sample_svg_file, metadata={"source": "test"})

        assert result["_metadata"].get("source") == "test"

    def test_convert_writes_output(self, sample_svg_file):
        """Test conversion writes to output file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            convert(sample_svg_file, output_path)
            assert PathLib(output_path).exists()
        finally:
            PathLib(output_path).unlink(missing_ok=True)


# ============================================================================
# apply_mapping() tests
# ============================================================================


class TestApplyMapping:
    """Tests for apply_mapping() function."""

    def test_apply_mapping_groups(self, sample_outline):
        """Test applying groups mapping."""
        mapping = {"groups": {"combined": ["region_a", "region_b"]}}
        result = apply_mapping(sample_outline, mapping)

        assert "combined" in result.regions
        assert "region_a" not in result.regions
        assert "region_b" not in result.regions

    def test_apply_mapping_layers(self, sample_outline):
        """Test applying layers mapping."""
        mapping = {"layers": {"overlay": ["region_a"], "hidden": ["region_c"]}}
        result = apply_mapping(sample_outline, mapping)

        assert "region_a" in result.metadata.get("overlay", [])
        assert "region_c" in result.metadata.get("hidden", [])

    def test_apply_mapping_lines_as_path(self, sample_outline):
        """Test applying lines_as_path mapping."""
        mapping = {"lines_as_path": ["region_a"]}
        result = apply_mapping(sample_outline, mapping)

        assert "region_a" in result.metadata.get("lines_as_path", [])

    def test_apply_mapping_metadata(self, sample_outline):
        """Test applying metadata mapping."""
        mapping = {"metadata": {"source": "test", "license": "MIT"}}
        result = apply_mapping(sample_outline, mapping)

        assert result.metadata.get("source") == "test"
        assert result.metadata.get("license") == "MIT"

    def test_apply_mapping_combined(self, sample_outline):
        """Test applying all mappings together."""
        mapping = {
            "groups": {"ab": ["region_a", "region_b"]},
            "layers": {"overlay": ["region_c"]},
            "metadata": {"source": "combined"},
        }
        result = apply_mapping(sample_outline, mapping)

        assert "ab" in result.regions
        assert "region_c" in result.metadata.get("overlay", [])
        assert result.metadata.get("source") == "combined"

    def test_apply_mapping_immutable(self, sample_outline):
        """Test that apply_mapping doesn't modify original."""
        original_regions = set(sample_outline.regions.keys())
        mapping = {"groups": {"new": ["region_a"]}}
        apply_mapping(sample_outline, mapping)

        assert set(sample_outline.regions.keys()) == original_regions


# ============================================================================
# generate_code() tests
# ============================================================================


class TestGenerateCode:
    """Tests for generate_code() function."""

    def test_generate_code_basic(self):
        """Test basic code generation."""
        code = generate_code("input.svg", "output.json")

        assert "from shinymap.kit import convert" in code
        assert '"input.svg"' in code
        assert '"output.json"' in code

    def test_generate_code_with_relabel(self):
        """Test code generation with relabeling."""
        code = generate_code("input.svg", "output.json", relabel={"tokyo": "path_1"})

        assert "relabel={" in code
        assert '"tokyo"' in code
        assert "path_1" in code

    def test_generate_code_with_overlay(self):
        """Test code generation with overlay_ids."""
        code = generate_code("input.svg", "output.json", overlay_ids=["_border"])

        assert "overlay_ids=" in code
        assert "_border" in code

    def test_generate_code_with_underlay(self):
        """Test code generation with underlay_ids."""
        code = generate_code("input.svg", "output.json", underlay_ids=["_background"])

        assert "underlay_ids=" in code
        assert "_background" in code

    def test_generate_code_with_hidden(self):
        """Test code generation with hidden_ids."""
        code = generate_code("input.svg", "output.json", hidden_ids=["_guides"])

        assert "hidden_ids=" in code
        assert "_guides" in code

    def test_generate_code_with_annotation(self):
        """Test code generation with annotation_ids."""
        code = generate_code("input.svg", "output.json", annotation_ids=["_labels"])

        assert "annotation_ids=" in code
        assert "_labels" in code

    def test_generate_code_with_all_layers(self):
        """Test code generation with all layer types."""
        code = generate_code(
            "input.svg",
            "output.json",
            overlay_ids=["_border"],
            underlay_ids=["_background"],
            hidden_ids=["_guides"],
            annotation_ids=["_labels"],
        )

        assert "overlay_ids=" in code
        assert "underlay_ids=" in code
        assert "hidden_ids=" in code
        assert "annotation_ids=" in code

    def test_generate_code_with_metadata(self):
        """Test code generation with metadata."""
        code = generate_code(
            "input.svg", "output.json", metadata={"source": "test", "license": "MIT"}
        )

        assert "metadata={" in code
        assert '"source"' in code
        assert '"license"' in code


# ============================================================================
# Module import tests
# ============================================================================


class TestModuleImports:
    """Tests for module imports and exports."""

    def test_import_from_kit(self):
        """Test importing from shinymap.kit."""
        from shinymap.kit import apply_mapping, convert, describe, generate_code, glaze

        assert callable(describe)
        assert callable(glaze)
        assert callable(convert)
        assert callable(apply_mapping)
        assert callable(generate_code)

    def test_import_sketch_app(self):
        """Test importing sketch app."""
        from shinymap.kit.sketch.app import app_run

        assert callable(app_run)

    def test_import_caption_module(self):
        """Test importing caption module."""
        from shinymap.kit.caption.__main__ import main

        assert callable(main)
