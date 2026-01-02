"""Interactive SVG to shinymap JSON converter.

Usage:
    uv run python -m shinymap.outline.converter [options]
    python -m shinymap.outline.converter [options]

Options:
    -H, --host TEXT           Bind socket to this host (default: 127.0.0.1)
    -p, --port INTEGER        Bind socket to this port (default: 8000)
    -b, --launch-browser      Launch browser after starting server
    -f, --file PATH           Path to SVG or JSON file to pre-load

Examples:
    # Run on default host/port
    uv run python -m shinymap.outline.converter

    # Run on custom port and open browser
    uv run python -m shinymap.outline.converter -p 9000 -b

    # Pre-load an SVG file
    uv run python -m shinymap.outline.converter -f path/to/file.svg -b

    # Pre-load intermediate JSON
    uv run python -m shinymap.outline.converter -f intermediate.json -b

    # Bind to all interfaces
    uv run python -m shinymap.outline.converter -H 0.0.0.0 -p 8080
"""

import argparse
from pathlib import Path

from ._app import app_run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Interactive SVG to shinymap JSON converter",
        prog="python -m shinymap.outline.converter",
    )
    parser.add_argument(
        "-H",
        "--host",
        default="127.0.0.1",
        help="Bind socket to this host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Bind socket to this port (default: 8000)",
    )
    parser.add_argument(
        "-b",
        "--launch-browser",
        action="store_true",
        help="Launch browser after starting server",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Path to SVG or JSON file to pre-load",
    )

    args = parser.parse_args()

    # CLI-provided file
    cli_file = Path(args.file) if args.file else None
    if isinstance(cli_file, Path) and not cli_file.exists():
        raise FileNotFoundError(f"{cli_file}")

    app_run(
        initial_file=cli_file, host=args.host, port=args.port, launch_browser=args.launch_browser
    )
