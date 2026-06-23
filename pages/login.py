from playwright.sync_api import Page, expect

from pages.locators import semantic_with_fallback


class LoginPage:
    URL = "https://www.saucedemo.com/"

    def __init__(self, page: Page):
        self.page = page

        # Accessible names describe the controls as a user experiences them.
        self.username_input = page.get_by_role(
            "textbox", name="Username", exact=True
        )
        self.password_input = page.get_by_role(
            "textbox", name="Password", exact=True
        )
        self.login_button = page.get_by_role("button", name="Login", exact=True)

    def navigate(self):
        self.page.goto(self.URL)

    def login(self, username: str, password: str):
        semantic_with_fallback(
            self.username_input,
            self.page.get_by_test_id("username"),
            "username input",
        ).fill(username)
        semantic_with_fallback(
            self.password_input,
            self.page.get_by_test_id("password"),
            "password input",
        ).fill(password)
        semantic_with_fallback(
            self.login_button,
            self.page.get_by_test_id("login-button"),
            "login button",
        ).click()

    def _error_message(self):
        semantic = self.page.get_by_role("heading").filter(has_text="Error:")
        return semantic_with_fallback(
            semantic,
            self.page.get_by_test_id("error"),
            "login error message",
        )

    def get_error_message(self) -> str:
        return self._error_message().inner_text()

    def assert_on_login_page(self):
        expect(self.page).to_have_url(self.URL)
        expect(self.login_button).to_be_visible()

    def assert_error_visible(self, expected_text: str = ""):
        error_message = self._error_message()
        expect(error_message).to_be_visible()
        if expected_text:
            expect(error_message).to_contain_text(expected_text)
