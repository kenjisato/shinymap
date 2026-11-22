"""Tests for aes.color scales."""

import math

import pytest

from shinymap.aes.color import SEQUENTIAL_BLUE, scale_continuous, scale_sequential
from shinymap.aes.color.neutral import NEUTRALS


class TestScaleSequentialCounts:
    """scale_sequential colors counts from the unified count model (SPEC)."""

    @pytest.mark.unit
    def test_unclicked_regions_get_palette_start(self):
        # A Count input only reports clicked regions; the rest are zero
        fills = scale_sequential({"b": 10}, ["a", "b"])
        assert fills == {"a": SEQUENTIAL_BLUE[0], "b": SEQUENTIAL_BLUE[-1]}

    @pytest.mark.unit
    def test_max_count_fixes_the_scale(self):
        fills = scale_sequential({"a": 5, "b": 20}, ["a", "b"], max_count=10)
        assert fills["b"] == SEQUENTIAL_BLUE[-1]
        assert fills["a"] not in (SEQUENTIAL_BLUE[0], SEQUENTIAL_BLUE[-1])


class TestScaleContinuous:
    """scale_continuous colors data values; missing data stays neutral."""

    @pytest.mark.unit
    def test_floats_with_default_range(self):
        fills = scale_continuous({"a": 1.5, "b": 3.0, "c": 4.5}, ["a", "b", "c"])
        assert fills["a"] == SEQUENTIAL_BLUE[0]
        assert fills["c"] == SEQUENTIAL_BLUE[-1]
        assert fills["b"] not in (SEQUENTIAL_BLUE[0], SEQUENTIAL_BLUE[-1])

    @pytest.mark.unit
    def test_vmin_vmax_and_clamping(self):
        fills = scale_continuous({"a": -5.0, "b": 50.0}, ["a", "b"], vmin=0, vmax=10)
        assert fills == {"a": SEQUENTIAL_BLUE[0], "b": SEQUENTIAL_BLUE[-1]}

    @pytest.mark.unit
    def test_missing_none_and_nan_get_neutral(self):
        fills = scale_continuous({"a": 1.0, "b": None, "c": math.nan}, ["a", "b", "c", "d"])
        assert fills["b"] == fills["c"] == fills["d"] == NEUTRALS["fill"]

    @pytest.mark.unit
    def test_numpy_values(self):
        np = pytest.importorskip("numpy")
        fills = scale_continuous({"a": np.float64(0.0), "b": np.int64(4)}, ["a", "b"])
        assert fills == {"a": SEQUENTIAL_BLUE[0], "b": SEQUENTIAL_BLUE[-1]}

    @pytest.mark.unit
    def test_all_equal_values(self):
        fills = scale_continuous({"a": 2.0, "b": 2.0}, ["a", "b"])
        assert fills["a"] == fills["b"] == SEQUENTIAL_BLUE[-1]
