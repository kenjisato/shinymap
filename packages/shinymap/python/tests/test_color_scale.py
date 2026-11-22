"""Tests for aes.color scales."""

import math

import pytest

from shinymap.aes.color import SEQUENTIAL_BLUE, scale_sequential
from shinymap.aes.color.neutral import NEUTRALS

IDS = ["a", "b", "c", "d"]


class TestScaleSequential:
    @pytest.mark.unit
    def test_counts_keep_zero_baseline(self):
        fills = scale_sequential({"a": 0, "b": 5, "c": 10}, ["a", "b", "c"])
        assert fills["a"] == SEQUENTIAL_BLUE[0]
        assert fills["c"] == SEQUENTIAL_BLUE[-1]

    @pytest.mark.unit
    def test_floats_and_vmin_vmax(self):
        values = {"a": 1_000_000.0, "b": 3_000_000.0, "c": 5_000_000.0}
        fills = scale_sequential(values, ["a", "b", "c"], vmin=1_000_000, vmax=5_000_000)
        assert fills["a"] == SEQUENTIAL_BLUE[0]
        assert fills["c"] == SEQUENTIAL_BLUE[-1]
        assert fills["b"] not in (SEQUENTIAL_BLUE[0], SEQUENTIAL_BLUE[-1])

    @pytest.mark.unit
    def test_values_outside_range_are_clamped(self):
        fills = scale_sequential({"a": -5.0, "b": 50.0}, ["a", "b"], vmin=0, vmax=10)
        assert fills == {"a": SEQUENTIAL_BLUE[0], "b": SEQUENTIAL_BLUE[-1]}

    @pytest.mark.unit
    def test_missing_none_and_nan_get_neutral(self):
        fills = scale_sequential({"a": 1.0, "b": None, "c": math.nan}, IDS)
        assert fills["b"] == fills["c"] == fills["d"] == NEUTRALS["fill"]
        assert fills["a"] == SEQUENTIAL_BLUE[-1]

    @pytest.mark.unit
    def test_numpy_values(self):
        np = pytest.importorskip("numpy")
        fills = scale_sequential({"a": np.float64(0.0), "b": np.int64(4)}, ["a", "b"])
        assert fills == {"a": SEQUENTIAL_BLUE[0], "b": SEQUENTIAL_BLUE[-1]}

    @pytest.mark.unit
    def test_all_equal_values_do_not_divide_by_zero(self):
        fills = scale_sequential({"a": 0, "b": 0}, ["a", "b"])
        assert fills == {"a": NEUTRALS["fill"], "b": NEUTRALS["fill"]}
