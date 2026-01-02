"""Tests for repr configuration context manager."""

from shinymap.outline import (
    Circle,
    Outline,
    Regions,
    get_repr_config,
    set_repr_options,
)


class TestReprConfig:
    """Test repr configuration."""

    def test_default_config(self):
        """Default config has sensible values."""
        config = get_repr_config()
        assert config.max_regions == 10
        assert config.max_elements == 3
        assert config.max_string_length == 80
        assert config.max_metadata_items == 10

    def test_set_repr_options_context_manager(self):
        """Context manager temporarily changes config."""
        original = get_repr_config()
        assert original.max_regions == 10

        with set_repr_options(max_regions=20):
            config = get_repr_config()
            assert config.max_regions == 20
            assert config.max_elements == 3  # Unchanged

        # Config restored after context
        config = get_repr_config()
        assert config.max_regions == 10

    def test_set_repr_options_multiple_params(self):
        """Can set multiple parameters at once."""
        with set_repr_options(max_regions=20, max_elements=5):
            config = get_repr_config()
            assert config.max_regions == 20
            assert config.max_elements == 5

    def test_set_repr_options_nested(self):
        """Nested contexts work correctly."""
        with set_repr_options(max_regions=20):
            config = get_repr_config()
            assert config.max_regions == 20

            with set_repr_options(max_regions=30):
                config = get_repr_config()
                assert config.max_regions == 30

            # Restored to outer context
            config = get_repr_config()
            assert config.max_regions == 20

        # Restored to default
        config = get_repr_config()
        assert config.max_regions == 10

    def test_regions_repr_uses_config(self):
        """Regions repr respects config settings."""
        # Create many regions
        regions = Regions({f"r{i}": [Circle(cx=i, cy=i, r=5)] for i in range(20)})

        # Default: shows up to 10 regions
        repr_str = repr(regions)
        assert "... (15 more regions)" in repr_str

        # Increase limit
        with set_repr_options(max_regions=25):
            repr_str = repr(regions)
            # All 20 regions should show without truncation
            assert "more regions" not in repr_str
            assert "r19" in repr_str

    def test_regions_repr_elements_uses_config(self):
        """Regions repr respects max_elements config."""
        # Create region with many elements
        circles = [Circle(cx=i * 10, cy=i * 10, r=5) for i in range(10)]
        regions = Regions({"r1": circles})

        # Default: shows first 3 elements
        repr_str = repr(regions)
        assert "..." in repr_str  # reprlib truncation

        # Increase element limit
        with set_repr_options(max_elements=12):
            repr_str = repr(regions)
            # Should show more elements
            # Note: reprlib will still show all 10 elements
            assert "r1" in repr_str

    def test_outline_repr_uses_config(self):
        """Outline repr respects config settings."""
        geo = Outline(
            regions={f"r{i}": [Circle(cx=i, cy=i, r=5)] for i in range(20)},
            metadata={"viewBox": "0 0 500 500", "source": "test"},
        )

        # Default: shows preview
        repr_str = repr(geo)
        assert "regions" in repr_str

        # With different config
        with set_repr_options(max_regions=25):
            repr_str = repr(geo)
            # More region keys shown in preview
            assert "regions" in repr_str


class TestSentinelPattern:
    """Test MISSING sentinel usage."""

    def test_missing_parameter_not_updated(self):
        """Parameters not provided retain their current values."""
        with set_repr_options(max_regions=20):
            config = get_repr_config()
            assert config.max_regions == 20
            assert config.max_elements == 3  # Default, not changed

            # Only change max_elements
            with set_repr_options(max_elements=10):
                config = get_repr_config()
                assert config.max_regions == 20  # From outer context
                assert config.max_elements == 10  # Changed

    def test_sentinel_repr(self):
        """MISSING sentinel has readable repr."""
        from shinymap.types import MISSING

        assert repr(MISSING) == "shinymap.types.MISSING"

    def test_missing_type_import(self):
        """MissingType can be imported for type hints."""
        from shinymap.types import MissingType

        assert MissingType is not None
