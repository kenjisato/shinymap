"""Configuration for repr output formatting.

Provides a context manager to control how much detail is shown in repr output
for Geometry, Regions, and Element objects.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from shinymap._sentinel import MISSING, MissingType


@dataclass
class ReprConfig:
    """Configuration for repr output formatting.

    Controls truncation and verbosity for repr output of shinymap geometry objects.

    Attributes:
        max_regions: Maximum number of regions to show before truncating
        max_elements: Maximum number of elements in a list to show
        max_string_length: Maximum length for string representation
        max_metadata_items: Maximum number of metadata items to show
    """

    max_regions: int = 10
    max_elements: int = 3
    max_string_length: int = 80
    max_metadata_items: int = 10


# Thread-safe context-local state
_repr_config: ContextVar[ReprConfig | None] = ContextVar("_repr_config", default=None)


def get_repr_config() -> ReprConfig:
    """Get current repr configuration.

    Returns:
        Current ReprConfig instance

    Example:
        >>> config = get_repr_config()
        >>> config.max_regions
        10
    """
    config = _repr_config.get()
    if config is None:
        # Initialize with default if not set
        config = ReprConfig()
        _repr_config.set(config)
    return config


@contextmanager
def set_repr_options(
    max_regions: int | MissingType = MISSING,
    max_elements: int | MissingType = MISSING,
    max_string_length: int | MissingType = MISSING,
    max_metadata_items: int | MissingType = MISSING,
) -> Generator[ReprConfig, None, None]:
    """Temporarily set repr configuration options.

    Context manager for controlling how much detail is shown in repr output.
    Only specified parameters are updated; others retain their current values.

    Args:
        max_regions: Maximum number of regions to show before truncating
        max_elements: Maximum number of elements in a list to show
        max_string_length: Maximum length for string representation
        max_metadata_items: Maximum number of metadata items to show

    Yields:
        New ReprConfig with updated settings

    Example:
        >>> from shinymap.geometry import Geometry, Circle, set_repr_options
        >>> geo = Geometry(
        ...     regions={f"r{i}": [Circle(cx=i*10, cy=i*10, r=5)] for i in range(20)},
        ...     metadata={"viewBox": "0 0 500 500"}
        ... )
        >>>
        >>> # Default: shows first 5 of 20 regions
        >>> geo
        Geometry(regions=Regions({
          'r0': [Circle(...)],
          ...
          ... (15 more regions)
        }), metadata=...)
        >>>
        >>> # Show more regions
        >>> with set_repr_options(max_regions=15):
        ...     print(geo)
        Geometry(regions=Regions({
          'r0': [Circle(...)],
          ...
          ... (5 more regions)
        }), metadata=...)
        >>>
        >>> # Show all regions
        >>> with set_repr_options(max_regions=100, max_elements=10):
        ...     print(geo)
        Geometry(regions=Regions({
          'r0': [Circle(...)],
          'r1': [Circle(...)],
          ...
        }), metadata=...)
    """
    current = get_repr_config()

    # Build new config, using current values for missing parameters
    # MISSING is falsy, so we can use `or` for concise defaults
    new_config = ReprConfig(
        max_regions=max_regions or current.max_regions,  # type: ignore[arg-type]
        max_elements=max_elements or current.max_elements,  # type: ignore[arg-type]
        max_string_length=max_string_length or current.max_string_length,  # type: ignore[arg-type]
        max_metadata_items=max_metadata_items or current.max_metadata_items,  # type: ignore[arg-type]
    )

    # Set new config in context
    token = _repr_config.set(new_config)
    try:
        yield new_config
    finally:
        # Restore previous config
        _repr_config.reset(token)


__all__ = ["ReprConfig", "get_repr_config", "set_repr_options"]
