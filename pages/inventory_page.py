from playwright.sync_api import Page, expect

from agent.config import application_url
from pages.locators import semantic_with_fallback


class InventoryPage:
    URL = application_url("inventory.html")

    def __init__(self, page: Page):
        self.page = page

        # Prefer visible language and accessible roles over DOM structure.
        self.title = page.get_by_text("Products", exact=True)
        self.sort_dropdown = page.get_by_role("combobox")
        self.burger_menu = page.get_by_role(
            "button", name="Open Menu", exact=True
        )
        self.logout_link = page.get_by_role("link", name="Logout", exact=True)

        # SauceDemo does not expose an accessible name for the cart link/badge.
        self.cart_link = page.get_by_test_id("shopping-cart-link")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")

        # Repeated product cards need a stable container before semantic scoping.
        self.inventory_items = page.get_by_test_id("inventory-item")

    def get_item_by_name(self, name: str):
        return self.inventory_items.filter(has_text=name)

    def _item_action(self, name: str, action: str):
        item = self.get_item_by_name(name)
        semantic = item.get_by_role("button", name=action, exact=True)
        slug = name.lower().replace(" ", "-")
        test_id = (
            f"add-to-cart-{slug}" if action == "Add to cart" else f"remove-{slug}"
        )
        return semantic_with_fallback(
            semantic,
            item.get_by_test_id(test_id),
            f"{action} button for {name}",
        )

    def add_item_to_cart_by_name(self, name: str):
        self._item_action(name, "Add to cart").click()

    def remove_item_from_cart_by_name(self, name: str):
        self._item_action(name, "Remove").click()

    def get_add_button_for_item(self, name: str):
        return self._item_action(name, "Add to cart")

    def get_item_price(self, name: str) -> str:
        item = self.get_item_by_name(name)
        # Price has no useful role/name, so keep the scoped stable test ID.
        return item.get_by_test_id("inventory-item-price").inner_text()

    def get_all_item_names(self) -> list[str]:
        # Product links are duplicated by image/title; this test ID is unambiguous.
        return self.page.get_by_test_id("inventory-item-name").all_inner_texts()

    def get_cart_count(self) -> int:
        if self.cart_badge.count() == 0:
            return 0
        return int(self.cart_badge.inner_text())

    def go_to_cart(self):
        self.cart_link.click()

    def sort_by(self, option: str):
        """Option values: az, za, lohi, hilo."""
        self.sort_dropdown.select_option(option)

    def logout(self):
        self.burger_menu.click()
        expect(self.logout_link).to_be_visible()
        self.logout_link.click()

    def assert_on_inventory_page(self):
        expect(self.page).to_have_url(self.URL)
        expect(self.title).to_be_visible()

    def assert_cart_count(self, count: int):
        if count == 0:
            expect(self.cart_badge).to_have_count(0)
        else:
            expect(self.cart_badge).to_have_text(str(count))
