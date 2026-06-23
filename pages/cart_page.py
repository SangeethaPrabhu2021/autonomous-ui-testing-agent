from playwright.sync_api import Page, expect

from agent.config import application_url
from pages.locators import semantic_with_fallback


class CartPage:
    URL = application_url("cart.html")

    def __init__(self, page: Page):
        self.page = page

        # These controls have stable user-facing names in SauceDemo.
        self.title = page.get_by_text("Your Cart", exact=True)
        self.continue_shopping = page.get_by_role(
            "button", name="Go back Continue Shopping", exact=True
        )
        self.checkout_button = page.get_by_role(
            "button", name="Checkout", exact=True
        )

        # Cart rows have no useful landmark/role, so scope via their test ID.
        self.cart_items = page.get_by_test_id("inventory-item")

    def get_item_names(self) -> list[str]:
        return self.page.get_by_test_id("inventory-item-name").all_inner_texts()

    def get_item_count(self) -> int:
        return self.cart_items.count()

    def remove_item_by_name(self, name: str):
        item = self.cart_items.filter(has_text=name)
        semantic_with_fallback(
            item.get_by_role("button", name="Remove", exact=True),
            item.get_by_test_id(f"remove-{name.lower().replace(' ', '-')}"),
            f"Remove button for {name}",
        ).click()

    def get_item_price(self, name: str) -> str:
        item = self.cart_items.filter(has_text=name)
        return item.get_by_test_id("inventory-item-price").inner_text()

    def continue_to_shopping(self):
        semantic_with_fallback(
            self.continue_shopping,
            self.page.get_by_test_id("continue-shopping"),
            "Continue Shopping button",
        ).click()

    def proceed_to_checkout(self):
        semantic_with_fallback(
            self.checkout_button,
            self.page.get_by_test_id("checkout"),
            "Checkout button",
        ).click()

    def assert_on_cart_page(self):
        expect(self.page).to_have_url(self.URL)
        expect(self.title).to_be_visible()

    def assert_item_in_cart(self, name: str):
        expect(
            self.page.get_by_role("link", name=name, exact=True)
        ).to_be_visible()

    def assert_item_not_in_cart(self, name: str):
        expect(
            self.page.get_by_role("link", name=name, exact=True)
        ).to_have_count(0)

    def assert_cart_is_empty(self):
        expect(self.cart_items).to_have_count(0)
