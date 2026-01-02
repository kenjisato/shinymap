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
