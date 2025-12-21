"""Regions class for clean dictionary representation."""

from __future__ import annotations

from collections.abc import Iterator, KeysView, ValuesView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._elements import Element


class Regions(dict):
    """Dictionary subclass with clean repr for region data.

    This class wraps the regions dictionary to provide a more readable
    repr output while maintaining full dictionary compatibility.

    Example:
        >>> from shinymap.geometry import Circle
        >>> regions = Regions({"r1": [Circle(cx=100, cy=100, r=50)]})
        >>> regions
        Regions({
          'r1': [Circle(cx=100, cy=100, r=50)]
        })
    """

    def __repr__(self) -> str:
        """Return clean repr with indented entries.

        Shows region IDs and their elements in a readable format.
        Truncates long lists and shows counts for large dictionaries.
        """
        import reprlib

        if not self:
            return "Regions({})"

        # For small dictionaries, show all entries
        if len(self) <= 10:
            lines = ["Regions({"]
            for key, value in self.items():
                # Use reprlib for value to keep it concise
                r = reprlib.Repr()
                r.maxlist = 3  # Show first 3 elements max
                val_repr = r.repr(value)
                lines.append(f"  {key!r}: {val_repr},")
            lines.append("})")
            return "\n".join(lines)
        else:
            # For large dictionaries, show first few + count
            lines = ["Regions({"]
            for i, (key, value) in enumerate(self.items()):
                if i >= 5:  # Show first 5 entries
                    break
                r = reprlib.Repr()
                r.maxlist = 3
                val_repr = r.repr(value)
                lines.append(f"  {key!r}: {val_repr},")
            remaining = len(self) - 5
            lines.append(f"  ... ({remaining} more regions)")
            lines.append("})")
            return "\n".join(lines)

    def __str__(self) -> str:
        """Return same as __repr__ for consistent display."""
        return self.__repr__()
