from __future__ import annotations
from typing import Any, Iterable, List

PREF_CODE_COL = "pref_code"


def is_dataframe(x: Any) -> bool:
    return hasattr(x, "__dataframe__") or hasattr(x, "to_dict")


def iter_codes(df: Any) -> Iterable[str]:
    values = column_values(df, PREF_CODE_COL)
    return (str(v).zfill(2) for v in values)


def strings_from_column(df: Any, column: str) -> List[str]:
    values = column_values(df, column)
    return ["" if v is None else str(v) for v in values]


def column_values(df: Any, column: str) -> List[Any]:
    if hasattr(df, "to_dict"):
        if column not in getattr(df, "columns", []):
            raise KeyError(column)
        series = df[column]
        if hasattr(series, "tolist"):
            return series.tolist()
        return list(series)
    if hasattr(df, "get_column"):
        try:
            series = df.get_column(column)
        except Exception as exc:  # pragma: no cover - polars specific
            raise KeyError(column) from exc
        if hasattr(series, "to_list"):
            return series.to_list()
        return list(series)
    raise TypeError("Unsupported DataFrame-like object")
