from playwright.sync_api import Page, expect

from agent.config import application_url
from pages.locators import semantic_with_fallback


class CheckoutPage:
    URL_STEP_ONE = application_url("checkout-step-one.html")
    URL_STEP_TWO = application_url("checkout-step-two.html")
    URL_COMPLETE = application_url("checkout-complete.html")

    def __init__(self, page: Page):
        self.page = page

        # Customer fields and workflow controls expose accessible names.
        self.first_name_input = page.get_by_role(
            "textbox", name="First Name", exact=True
        )
        self.last_name_input = page.get_by_role(
            "textbox", name="Last Name", exact=True
        )
        self.zip_code_input = page.get_by_role(
            "textbox", name="Zip/Postal Code", exact=True
        )
        self.continue_button = page.get_by_role(
            "button", name="Continue", exact=True
        )
        self.cancel_button_s1 = page.get_by_role(
            "button", name="Go back Cancel", exact=True
        )
        self.finish_button = page.get_by_role(
            "button", name="Finish", exact=True
        )
        self.cancel_button_s2 = self.cancel_button_s1
        self.back_home_button = page.get_by_role(
            "button", name="Back Home", exact=True
        )

        # Overview rows have no semantic container role.
        self.overview_items = page.locator(
            '[data-test="inventory-item"]'
        )
        self.subtotal_label = page.locator(
            '[data-test="subtotal-label"]'
        )
        self.tax_label = page.locator(
            '[data-test="tax-label"]'
        )
        self.total_label = page.locator(
            '[data-test="total-label"]'
        )
        self.complete_header = page.get_by_role(
            "heading", name="Thank you for your order!", exact=True
        )
        self.complete_text = page.get_by_text(
            "Your order has been dispatched", exact=False
        )

    def _field(self, semantic, test_id: str, description: str):
        return semantic_with_fallback(
            semantic,
            self.page.get_by_test_id(test_id),
            description,
        )

    def fill_customer_info(self, first_name: str, last_name: str, zip_code: str):
        self._field(
            self.first_name_input, "firstName", "first-name input"
        ).fill(first_name)
        self._field(
            self.last_name_input, "lastName", "last-name input"
        ).fill(last_name)
        self._field(
            self.zip_code_input, "postalCode", "postal-code input"
        ).fill(zip_code)

    def submit_customer_info(self):
        self._field(
            self.continue_button, "continue", "Continue button"
        ).click()

    def fill_and_submit_customer_info(
        self, first_name: str, last_name: str, zip_code: str
    ):
        self.fill_customer_info(first_name, last_name, zip_code)
        self.submit_customer_info()

    def _error_message(self):
        semantic = self.page.get_by_role("heading").filter(has_text="Error:")
        return semantic_with_fallback(
            semantic,
            self.page.get_by_test_id("error"),
            "checkout error message",
        )

    def get_error_message(self) -> str:
        return self._error_message().inner_text()

    def get_subtotal(self) -> str:
        return self.subtotal_label.inner_text()

    def get_tax(self) -> str:
        return self.tax_label.inner_text()

    def get_total(self) -> str:
        return self.total_label.inner_text()

    def get_overview_item_names(self) -> list[str]:
        return self.page.locator(
            '[data-test="inventory-item-name"]'
        ).all_inner_texts()

    def finish_order(self):
        self._field(self.finish_button, "finish", "Finish button").click()

    def cancel_checkout(self):
        self._field(
            self.cancel_button_s2, "cancel", "Cancel button"
        ).click()

    def go_back_to_products(self):
        self._field(
            self.back_home_button, "back-to-products", "Back Home button"
        ).click()

    def assert_on_step_one(self):
        expect(self.page).to_have_url(self.URL_STEP_ONE)

    def assert_on_step_two(self):
        expect(self.page).to_have_url(self.URL_STEP_TWO)

    def assert_on_complete_page(self):
        expect(self.page).to_have_url(self.URL_COMPLETE)

    def assert_order_complete(self):
        self.assert_on_complete_page()
        expect(self.complete_header).to_be_visible()

    def assert_error_visible(self, expected_text: str = ""):
        error_message = self._error_message()
        expect(error_message).to_be_visible()
        if expected_text:
            expect(error_message).to_contain_text(expected_text)

    def assert_item_in_overview(self, name: str):
        expect(
            self.page.get_by_role("link", name=name, exact=True)
        ).to_be_visible()
