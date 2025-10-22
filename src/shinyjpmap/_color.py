from __future__ import annotations
from typing import Iterable, Mapping


def map_colors(codes: Iterable[str], values: Iterable[str]) -> Mapping[str, str]:
    return {c: v for c, v in zip(codes, values)}


def colorbar_ticks(values: list[float], n: int = 5) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if lo == hi:
        return [lo]
    step = (hi - lo) / (n - 1)
    return [round(lo + i * step, 6) for i in range(n)]
