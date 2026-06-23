from pathlib import Path

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Ensure pytest's repository-local base temp parent exists."""
    cache_root = Path(config.rootpath) / ".test-cache"
    cache_root.mkdir(exist_ok=True)
