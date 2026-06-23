"""
End-to-end purchase-flow tests for https://www.saucedemo.com
Run with:
    pip install playwright pytest pytest-playwright
    playwright install chromium
    pytest test_purchase_flow.py -v
"""

import pytest
from playwright.sync_api import Page, expect

from pages.login import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage


pytestmark = pytest.mark.integration


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
VALID_USER     = "standard_user"
VALID_PASSWORD = "secret_sauce"
LOCKED_USER    = "locked_out_user"

ITEM_1 = "Sauce Labs Backpack"
ITEM_2 = "Sauce Labs Bike Light"

CUSTOMER = {"first": "Jane", "last": "Doe", "zip": "10001"}


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture()
def login_page(page: Page) -> LoginPage:
    lp = LoginPage(page)
    lp.navigate()
    return lp


@pytest.fixture()
def logged_in(page: Page) -> InventoryPage:
    """Return an InventoryPage for a freshly logged-in standard_user."""
    lp = LoginPage(page)
    lp.navigate()
    lp.login(VALID_USER, VALID_PASSWORD)
    inv = InventoryPage(page)
    inv.assert_on_inventory_page()
    return inv


# ──────────────────────────────────────────────────────────────────────────────
# Login tests
# ──────────────────────────────────────────────────────────────────────────────
class TestLogin:

    def test_successful_login(self, login_page: LoginPage, page: Page):
        login_page.login(VALID_USER, VALID_PASSWORD)
        inv = InventoryPage(page)
        inv.assert_on_inventory_page()

    def test_invalid_credentials(self, login_page: LoginPage):
        login_page.login("wrong_user", "wrong_pass")
        login_page.assert_error_visible("Username and password do not match")

    def test_locked_out_user(self, login_page: LoginPage):
        login_page.login(LOCKED_USER, VALID_PASSWORD)
        login_page.assert_error_visible("Sorry, this user has been locked out")

    def test_empty_username(self, login_page: LoginPage):
        login_page.login("", VALID_PASSWORD)
        login_page.assert_error_visible("Username is required")

    def test_empty_password(self, login_page: LoginPage):
        login_page.login(VALID_USER, "")
        login_page.assert_error_visible("Password is required")


# ──────────────────────────────────────────────────────────────────────────────
# Inventory tests
# ──────────────────────────────────────────────────────────────────────────────
class TestInventory:

    def test_inventory_page_shows_products(self, logged_in: InventoryPage):
        names = logged_in.get_all_item_names()
        assert len(names) == 6, f"Expected 6 products, got {len(names)}"

    def test_add_single_item_updates_cart_badge(self, logged_in: InventoryPage):
        logged_in.add_item_to_cart_by_name(ITEM_1)
        logged_in.assert_cart_count(1)

    def test_add_multiple_items_updates_cart_badge(self, logged_in: InventoryPage):
        logged_in.add_item_to_cart_by_name(ITEM_1)
        logged_in.add_item_to_cart_by_name(ITEM_2)
        logged_in.assert_cart_count(2)

    def test_remove_item_decrements_cart_badge(self, logged_in: InventoryPage):
        logged_in.add_item_to_cart_by_name(ITEM_1)
        logged_in.remove_item_from_cart_by_name(ITEM_1)
        logged_in.assert_cart_count(0)


# ──────────────────────────────────────────────────────────────────────────────
# Cart tests
# ──────────────────────────────────────────────────────────────────────────────
class TestCart:

    def test_cart_shows_added_item(self, logged_in: InventoryPage, page: Page):
        logged_in.add_item_to_cart_by_name(ITEM_1)
        logged_in.go_to_cart()

        cart = CartPage(page)
        cart.assert_on_cart_page()
        cart.assert_item_in_cart(ITEM_1)

    def test_cart_shows_multiple_items(self, logged_in: InventoryPage, page: Page):
        logged_in.add_item_to_cart_by_name(ITEM_1)
        logged_in.add_item_to_cart_by_name(ITEM_2)
        logged_in.go_to_cart()

        cart = CartPage(page)
        cart.assert_item_in_cart(ITEM_1)
        cart.assert_item_in_cart(ITEM_2)
        assert cart.get_item_count() == 2

    def test_remove_item_from_cart(self, logged_in: InventoryPage, page: Page):
        logged_in.add_item_to_cart_by_name(ITEM_1)
        logged_in.go_to_cart()

        cart = CartPage(page)
        cart.remove_item_by_name(ITEM_1)
        cart.assert_item_not_in_cart(ITEM_1)
        cart.assert_cart_is_empty()

    def test_continue_shopping_returns_to_inventory(
        self, logged_in: InventoryPage, page: Page
    ):
        logged_in.go_to_cart()
        cart = CartPage(page)
        cart.continue_to_shopping()
        InventoryPage(page).assert_on_inventory_page()


# ──────────────────────────────────────────────────────────────────────────────
# Checkout tests
# ──────────────────────────────────────────────────────────────────────────────
class TestCheckout:

    @pytest.fixture(autouse=True)
    def add_item_and_go_to_checkout(self, logged_in: InventoryPage, page: Page):
        """Add one item, navigate to checkout step 1 before each test."""
        logged_in.add_item_to_cart_by_name(ITEM_1)
        logged_in.go_to_cart()
        cart = CartPage(page)
        cart.proceed_to_checkout()
        self.checkout = CheckoutPage(page)
        self.checkout.assert_on_step_one()

    def test_step_one_empty_first_name(self):
        self.checkout.fill_and_submit_customer_info("", "Doe", "10001")
        self.checkout.assert_error_visible("First Name is required")

    def test_step_one_empty_last_name(self):
        self.checkout.fill_and_submit_customer_info("Jane", "", "10001")
        self.checkout.assert_error_visible("Last Name is required")

    def test_step_one_empty_zip(self):
        self.checkout.fill_and_submit_customer_info("Jane", "Doe", "")
        self.checkout.assert_error_visible("Postal Code is required")

    def test_step_one_proceeds_to_step_two(self):
        self.checkout.fill_and_submit_customer_info(
            CUSTOMER["first"], CUSTOMER["last"], CUSTOMER["zip"]
        )
        self.checkout.assert_on_step_two()

    def test_step_two_shows_correct_item(self):
        self.checkout.fill_and_submit_customer_info(
            CUSTOMER["first"], CUSTOMER["last"], CUSTOMER["zip"]
        )
        self.checkout.assert_item_in_overview(ITEM_1)

    def test_step_two_shows_price_summary(self):
        self.checkout.fill_and_submit_customer_info(
            CUSTOMER["first"], CUSTOMER["last"], CUSTOMER["zip"]
        )
        subtotal = self.checkout.get_subtotal()
        tax      = self.checkout.get_tax()
        total    = self.checkout.get_total()
        assert "Item total" in subtotal
        assert "Tax"        in tax
        assert "Total"      in total


# ──────────────────────────────────────────────────────────────────────────────
# Full purchase flow (happy path)
# ──────────────────────────────────────────────────────────────────────────────
class TestFullPurchaseFlow:

    def test_single_item_purchase(self, page: Page):
        # 1. Login
        login = LoginPage(page)
        login.navigate()
        login.login(VALID_USER, VALID_PASSWORD)

        # 2. Add item to cart
        inv = InventoryPage(page)
        inv.assert_on_inventory_page()
        inv.add_item_to_cart_by_name(ITEM_1)
        inv.assert_cart_count(1)
        inv.go_to_cart()

        # 3. Verify cart
        cart = CartPage(page)
        cart.assert_on_cart_page()
        cart.assert_item_in_cart(ITEM_1)
        cart.proceed_to_checkout()

        # 4. Fill customer info
        checkout = CheckoutPage(page)
        checkout.assert_on_step_one()
        checkout.fill_and_submit_customer_info(
            CUSTOMER["first"], CUSTOMER["last"], CUSTOMER["zip"]
        )

        # 5. Review order
        checkout.assert_on_step_two()
        checkout.assert_item_in_overview(ITEM_1)
        checkout.finish_order()

        # 6. Confirm completion
        checkout.assert_order_complete()

    def test_multi_item_purchase(self, page: Page):
        # 1. Login
        login = LoginPage(page)
        login.navigate()
        login.login(VALID_USER, VALID_PASSWORD)

        # 2. Add two items
        inv = InventoryPage(page)
        inv.add_item_to_cart_by_name(ITEM_1)
        inv.add_item_to_cart_by_name(ITEM_2)
        inv.assert_cart_count(2)
        inv.go_to_cart()

        # 3. Verify both items in cart
        cart = CartPage(page)
        cart.assert_item_in_cart(ITEM_1)
        cart.assert_item_in_cart(ITEM_2)
        cart.proceed_to_checkout()

        # 4. Checkout
        checkout = CheckoutPage(page)
        checkout.fill_and_submit_customer_info(
            CUSTOMER["first"], CUSTOMER["last"], CUSTOMER["zip"]
        )
        checkout.assert_item_in_overview(ITEM_1)
        checkout.assert_item_in_overview(ITEM_2)
        checkout.finish_order()

        # 5. Confirm
        checkout.assert_order_complete()

    def test_logout_after_purchase(self, page: Page):
        # Full purchase then logout
        login = LoginPage(page)
        login.navigate()
        login.login(VALID_USER, VALID_PASSWORD)

        inv = InventoryPage(page)
        inv.add_item_to_cart_by_name(ITEM_1)
        inv.go_to_cart()

        cart = CartPage(page)
        cart.proceed_to_checkout()

        checkout = CheckoutPage(page)
        checkout.fill_and_submit_customer_info(
            CUSTOMER["first"], CUSTOMER["last"], CUSTOMER["zip"]
        )
        checkout.finish_order()
        checkout.assert_order_complete()
        checkout.go_back_to_products()

        inv2 = InventoryPage(page)
        inv2.assert_on_inventory_page()
        inv2.logout()

        login2 = LoginPage(page)
        login2.assert_on_login_page()
