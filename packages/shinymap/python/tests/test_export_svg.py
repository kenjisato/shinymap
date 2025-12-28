"""Integration tests for export_svg() function."""

from shinymap.geometry import Circle, Geometry, Path, Rect, Text, export_svg


class TestExportSvgBasic:
    """Test basic export_svg() functionality."""

    def test_export_basic(self, tmp_path):
        """Export geometry with basic elements."""
        geom = Geometry(
            regions={
                "circle_region": [Circle(cx=50, cy=50, r=30, fill="#ff0000")],
                "rect_region": [Rect(x=100, y=100, width=50, height=30, fill="#00ff00")],
            },
            metadata={"viewBox": "0 0 200 200"},
        )

        output_path = tmp_path / "basic.svg"
        export_svg(geom, output_path)

        assert output_path.exists()
        content = output_path.read_text()

        # Verify SVG root element
        assert "<svg" in content
        assert 'viewBox="0 0 200 200"' in content

        # Verify elements with id attributes
        assert 'id="circle_region"' in content
        assert 'id="rect_region"' in content

        # Verify element types
        assert "<circle" in content
        assert "<rect" in content

    def test_export_with_path_elements(self, tmp_path):
        """Export geometry with path elements."""
        geom = Geometry(
            regions={
                "path1": [Path(d="M 0 0 L 100 0 L 100 100 Z", fill="#0000ff")],
            },
            metadata={"viewBox": "0 0 200 200"},
        )

        output_path = tmp_path / "paths.svg"
        export_svg(geom, output_path)

        content = output_path.read_text()
        assert "<path" in content
        assert "M 0 0 L 100 0 L 100 100 Z" in content

    def test_export_with_text_elements(self, tmp_path):
        """Export geometry with text elements."""
        geom = Geometry(
            regions={
                "label": [Text(x=100, y=100, text="Test Label", font_size=14)],
            },
            metadata={"viewBox": "0 0 200 200"},
        )

        output_path = tmp_path / "text.svg"
        export_svg(geom, output_path)

        content = output_path.read_text()
        assert "<text" in content
        assert "Test Label" in content


class TestExportSvgViewBox:
    """Test viewBox handling in export_svg()."""

    def test_export_uses_metadata_viewbox(self, tmp_path):
        """export_svg uses viewBox from geometry.metadata."""
        geom = Geometry(
            regions={"region": [Circle(cx=50, cy=50, r=30)]},
            metadata={"viewBox": "10 20 300 400"},
        )

        output_path = tmp_path / "metadata_viewbox.svg"
        export_svg(geom, output_path)

        content = output_path.read_text()
        assert 'viewBox="10 20 300 400"' in content

    def test_export_custom_viewbox(self, tmp_path):
        """export_svg accepts custom viewBox parameter."""
        geom = Geometry(
            regions={"region": [Circle(cx=50, cy=50, r=30)]},
            metadata={"viewBox": "0 0 100 100"},
        )

        output_path = tmp_path / "custom_viewbox.svg"
        export_svg(geom, output_path, viewbox="0 0 500 500")

        content = output_path.read_text()
        assert 'viewBox="0 0 500 500"' in content

    def test_export_auto_calculate_viewbox(self, tmp_path):
        """export_svg auto-calculates viewBox if not in metadata."""
        geom = Geometry(
            regions={"region": [Circle(cx=50, cy=50, r=30)]},
            metadata={},  # No viewBox
        )

        output_path = tmp_path / "auto_viewbox.svg"
        export_svg(geom, output_path)

        content = output_path.read_text()
        # viewBox should be auto-calculated from circle bounds (20, 20, 80, 80)
        # with 2% padding
        assert "viewBox=" in content


class TestExportSvgWidthHeight:
    """Test width/height attribute handling."""

    def test_export_width_height_from_viewbox(self, tmp_path):
        """export_svg extracts width/height from viewBox."""
        geom = Geometry(
            regions={"region": [Circle(cx=50, cy=50, r=30)]},
            metadata={"viewBox": "0 0 800 600"},
        )

        output_path = tmp_path / "width_height.svg"
        export_svg(geom, output_path)

        content = output_path.read_text()
        assert 'width="800"' in content
        assert 'height="600"' in content

    def test_export_custom_width_height(self, tmp_path):
        """export_svg accepts custom width/height parameters."""
        geom = Geometry(
            regions={"region": [Circle(cx=50, cy=50, r=30)]},
            metadata={"viewBox": "0 0 100 100"},
        )

        output_path = tmp_path / "custom_width_height.svg"
        export_svg(geom, output_path, width=1000, height=800)

        content = output_path.read_text()
        assert 'width="1000"' in content
        assert 'height="800"' in content


class TestExportSvgIds:
    """Test id attribute handling."""

    def test_export_with_ids(self, tmp_path):
        """export_svg adds id attributes by default."""
        geom = Geometry(
            regions={
                "region_01": [Circle(cx=50, cy=50, r=30)],
                "region_02": [Rect(x=100, y=100, width=50, height=30)],
            },
            metadata={"viewBox": "0 0 200 200"},
        )

        output_path = tmp_path / "with_ids.svg"
        export_svg(geom, output_path)

        content = output_path.read_text()
        assert 'id="region_01"' in content
        assert 'id="region_02"' in content

    def test_export_without_ids(self, tmp_path):
        """export_svg can omit id attributes."""
        geom = Geometry(
            regions={
                "region_01": [Circle(cx=50, cy=50, r=30)],
                "region_02": [Rect(x=100, y=100, width=50, height=30)],
            },
            metadata={"viewBox": "0 0 200 200"},
        )

        output_path = tmp_path / "without_ids.svg"
        export_svg(geom, output_path, include_ids=False)

        content = output_path.read_text()
        assert 'id="region_01"' not in content
        assert 'id="region_02"' not in content


class TestExportSvgAesthetics:
    """Test that aesthetic attributes are preserved."""

    def test_export_preserves_fill(self, tmp_path):
        """export_svg preserves fill attributes."""
        geom = Geometry(
            regions={"region": [Circle(cx=50, cy=50, r=30, fill="#ff0000")]},
            metadata={"viewBox": "0 0 100 100"},
        )

        output_path = tmp_path / "preserve_fill.svg"
        export_svg(geom, output_path)

        content = output_path.read_text()
        assert 'fill="#ff0000"' in content

    def test_export_preserves_stroke(self, tmp_path):
        """export_svg preserves stroke attributes."""
        geom = Geometry(
            regions={
                "region": [
                    Circle(
                        cx=50,
                        cy=50,
                        r=30,
                        stroke="#000000",
                        stroke_width=2,
                    )
                ]
            },
            metadata={"viewBox": "0 0 100 100"},
        )

        output_path = tmp_path / "preserve_stroke.svg"
        export_svg(geom, output_path)

        content = output_path.read_text()
        assert 'stroke="#000000"' in content
        assert 'stroke-width="2"' in content


class TestExportSvgRoundTrip:
    """Test SVG round-tripping: SVG → Geometry → SVG."""

    def test_roundtrip_preserves_structure(self, tmp_path):
        """Round-trip preserves basic structure."""
        # Create original SVG
        original_svg = tmp_path / "original.svg"
        original_svg.write_text(
            """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <circle id="circle1" cx="50" cy="50" r="30" fill="#ff0000"/>
            <rect id="rect1" x="100" y="100" width="50" height="30" fill="#00ff00"/>
        </svg>"""
        )

        # Convert to Geometry
        geom = Geometry.from_svg(original_svg)

        # Export back to SVG
        exported_svg = tmp_path / "exported.svg"
        export_svg(geom, exported_svg)

        content = exported_svg.read_text()

        # Verify structure preserved
        assert "<circle" in content
        assert "<rect" in content
        assert 'viewBox="0 0 200 200"' in content

    def test_roundtrip_preserves_aesthetics(self, tmp_path):
        """Round-trip preserves aesthetic attributes."""
        # Create original SVG with aesthetics
        original_svg = tmp_path / "original.svg"
        original_svg.write_text(
            """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <circle id="styled" cx="50" cy="50" r="30"
                    fill="#ff0000" stroke="#000000" stroke-width="2"/>
        </svg>"""
        )

        # Round-trip
        geom = Geometry.from_svg(original_svg)
        exported_svg = tmp_path / "exported.svg"
        export_svg(geom, exported_svg)

        content = exported_svg.read_text()

        # Verify aesthetics preserved
        assert 'fill="#ff0000"' in content
        assert 'stroke="#000000"' in content
        assert 'stroke-width="2"' in content


class TestExportSvgMergedRegions:
    """Test exporting regions with multiple elements."""

    def test_export_merged_region(self, tmp_path):
        """Export region with multiple elements."""
        geom = Geometry(
            regions={
                "merged": [
                    Circle(cx=50, cy=50, r=30),
                    Circle(cx=150, cy=150, r=30),
                ]
            },
            metadata={"viewBox": "0 0 200 200"},
        )

        output_path = tmp_path / "merged.svg"
        export_svg(geom, output_path)

        content = output_path.read_text()

        # Both circles should have same id (merged region)
        assert content.count('id="merged"') == 2
        assert content.count("<circle") == 2
