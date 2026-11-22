"""
Pytest fixtures for integration testing with Playwright.

Provides fixtures to run Shiny apps in a subprocess and test them with Playwright.
"""

import socket
import subprocess
import sys
import time
from collections.abc import Generator
from pathlib import Path

import pytest
from playwright.sync_api import Page

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def find_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="function")
def shiny_app_basic(page: Page) -> Generator[Page, None, None]:
    """Start app_basic.py and navigate to it with Playwright."""
    port = find_free_port()
    app_path = EXAMPLES_DIR / "app_basic.py"

    # Start the Shiny app
    process = subprocess.Popen(
        [sys.executable, "-m", "shiny", "run", str(app_path), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(EXAMPLES_DIR),
    )

    try:
        # Wait for app to start
        url = f"http://localhost:{port}"
        for _ in range(30):  # Wait up to 30 seconds
            try:
                page.goto(url, timeout=1000)
                # Wait for the Shiny app to fully load
                page.wait_for_selector("svg[role='img']", timeout=5000)
                break
            except Exception:
                time.sleep(1)
        else:
            raise TimeoutError(f"Shiny app at {url} did not start in time")

        yield page
    finally:
        process.terminate()
        process.wait(timeout=5)


@pytest.fixture(scope="function")
def shiny_app_output(page: Page) -> Generator[Page, None, None]:
    """Start app_output.py and navigate to it with Playwright."""
    port = find_free_port()
    app_path = EXAMPLES_DIR / "app_output.py"

    # Start the Shiny app
    process = subprocess.Popen(
        [sys.executable, "-m", "shiny", "run", str(app_path), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(EXAMPLES_DIR),
    )

    try:
        # Wait for app to start
        url = f"http://localhost:{port}"
        for _ in range(30):
            try:
                page.goto(url, timeout=1000)
                page.wait_for_selector("svg[role='img']", timeout=5000)
                break
            except Exception:
                time.sleep(1)
        else:
            raise TimeoutError(f"Shiny app at {url} did not start in time")

        yield page
    finally:
        process.terminate()
        process.wait(timeout=5)


@pytest.fixture(scope="function")
def shiny_app(request: pytest.FixtureRequest, page: Page) -> Generator[Page, None, None]:
    """Generic fixture to start any app. Use with pytest.mark.parametrize.

    Example:
        @pytest.mark.parametrize("shiny_app", ["app_basic.py"], indirect=True)
        def test_something(shiny_app):
            ...
    """
    app_name = request.param
    port = find_free_port()
    app_path = EXAMPLES_DIR / app_name

    if not app_path.exists():
        pytest.skip(f"App {app_name} not found")

    process = subprocess.Popen(
        [sys.executable, "-m", "shiny", "run", str(app_path), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(EXAMPLES_DIR),
    )

    try:
        url = f"http://localhost:{port}"
        for _ in range(30):
            try:
                page.goto(url, timeout=1000)
                page.wait_for_selector("svg[role='img']", timeout=5000)
                break
            except Exception:
                time.sleep(1)
        else:
            raise TimeoutError(f"Shiny app at {url} did not start in time")

        yield page
    finally:
        process.terminate()
        process.wait(timeout=5)
