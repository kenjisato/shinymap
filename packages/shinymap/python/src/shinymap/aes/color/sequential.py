"""Sequential color palettes for ordered/continuous data.

These palettes progress from light to dark, suitable for count data,
heat maps, or any data with natural ordering.
"""

from __future__ import annotations

# Blue sequential (light to dark)
SEQUENTIAL_BLUE = [
    "#eff6ff",  # blue-50
    "#bfdbfe",  # blue-200
    "#93c5fd",  # blue-300
    "#60a5fa",  # blue-400
    "#3b82f6",  # blue-500
    "#2563eb",  # blue-600
    "#1d4ed8",  # blue-700
]

# Green sequential (light to dark)
SEQUENTIAL_GREEN = [
    "#ecfdf3",  # green-50
    "#bbf7d0",  # green-200
    "#86efac",  # green-300
    "#4ade80",  # green-400
    "#22c55e",  # green-500
    "#16a34a",  # green-600
    "#15803d",  # green-700
]

# Orange sequential (light to dark)
SEQUENTIAL_ORANGE = [
    "#fff7ed",  # orange-50
    "#ffedd5",  # orange-100
    "#fed7aa",  # orange-200
    "#fdba74",  # orange-300
    "#fb923c",  # orange-400
    "#f97316",  # orange-500
    "#c2410c",  # orange-700
]

__all__ = ["SEQUENTIAL_BLUE", "SEQUENTIAL_GREEN", "SEQUENTIAL_ORANGE"]
