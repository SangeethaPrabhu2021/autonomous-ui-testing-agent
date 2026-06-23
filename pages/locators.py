import logging

from playwright.sync_api import Locator


LOGGER = logging.getLogger("ui.locators")


def semantic_with_fallback(
    semantic: Locator,
    fallback: Locator,
    description: str,
) -> Locator:
    """Prefer a user-facing locator and use a stable test ID only if needed."""
    if semantic.count() == 1 and semantic.is_visible():
        LOGGER.info("Using semantic locator for %s", description)
        return semantic

    LOGGER.warning("Using data-test fallback for %s", description)
    return fallback
