import os
from urllib.parse import urljoin


DEFAULT_BASE_URL = "https://www.saucedemo.com/"


def application_url(path: str = "") -> str:
    """Build an application URL from the configured base URL."""
    base_url = os.getenv("BASE_URL", DEFAULT_BASE_URL).rstrip("/") + "/"
    return urljoin(base_url, path.lstrip("/"))


def is_headless() -> bool:
    """Return whether Playwright should run without a visible browser window."""
    return os.getenv("HEADLESS", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
