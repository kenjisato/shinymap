"""Regions class for clean dictionary representation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._elements import Element


class Regions(dict[str, list["str | Element"]]):
    """Dictionary subclass with clean repr for region data.

    This class wraps the regions dictionary to provide a more readable
    repr output while maintaining full dictionary compatibility.

    Example:
        >>> from shinymap.outline import Circle
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
        Uses global repr configuration from get_repr_config().
        """
        import reprlib

        from ._repr_config import get_repr_config

        if not self:
            return "Regions({})"

        config = get_repr_config()

        # For small dictionaries, show all entries
        if len(self) <= config.max_regions:
            lines = ["Regions({"]
            for key, value in self.items():
                # Use reprlib for value to keep it concise
                r = reprlib.Repr()
                r.maxlist = config.max_elements
                val_repr = r.repr(value)
                lines.append(f"  {key!r}: {val_repr},")
            lines.append("})")
            return "\n".join(lines)
        else:
            # For large dictionaries, show first few + count
            show_count = max(1, config.max_regions // 2)
            lines = ["Regions({"]
            for i, (key, value) in enumerate(self.items()):
                if i >= show_count:
                    break
                r = reprlib.Repr()
                r.maxlist = config.max_elements
                val_repr = r.repr(value)
                lines.append(f"  {key!r}: {val_repr},")
            remaining = len(self) - show_count
            lines.append(f"  ... ({remaining} more regions)")
            lines.append("})")
            return "\n".join(lines)

    def __str__(self) -> str:
        """Return same as __repr__ for consistent display."""
        return self.__repr__()
