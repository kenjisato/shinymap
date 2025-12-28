"""Cycle mode color palettes for multi-state selection.

These palettes are designed for Cycle mode where clicks cycle through
a fixed number of states with wrapping (state → state+1 → ... → 0).
"""

from __future__ import annotations

# Traffic light: neutral → red → yellow → green (4 states)
# Use case: survey ratings, satisfaction levels
HUE_CYCLE_4 = [
    "#e2e8f0",  # slate-200 (neutral/unrated)
    "#ef4444",  # red-500 (negative/bad)
    "#eab308",  # yellow-500 (neutral/okay)
    "#22c55e",  # green-500 (positive/good)
]

# Sentiment (3 states): negative → neutral → positive
SENTIMENT_3 = [
    "#fecaca",  # red-200 (negative)
    "#e2e8f0",  # slate-200 (neutral)
    "#bbf7d0",  # green-200 (positive)
]

# Priority levels (5 states): none → low → medium → high → critical
PRIORITY_5 = [
    "#e2e8f0",  # slate-200 (none)
    "#dbeafe",  # blue-100 (low)
    "#fef3c7",  # amber-100 (medium)
    "#fed7aa",  # orange-200 (high)
    "#fecaca",  # red-200 (critical)
]

# Agreement scale (5 states): strongly disagree → disagree → neutral → agree → strongly agree
LIKERT_5 = [
    "#fecaca",  # red-200 (strongly disagree)
    "#fed7aa",  # orange-200 (disagree)
    "#e2e8f0",  # slate-200 (neutral)
    "#bbf7d0",  # green-200 (agree)
    "#86efac",  # green-300 (strongly agree)
]

__all__ = ["HUE_CYCLE_4", "SENTIMENT_3", "PRIORITY_5", "LIKERT_5"]
