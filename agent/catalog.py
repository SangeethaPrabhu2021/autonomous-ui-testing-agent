TEST_CATALOG = {
    "login_success": {
        "node_id": "tests/test_purchase_flow.py::TestLogin::test_successful_login",
        "description": "Log in with the standard SauceDemo user.",
    },
    "login_invalid_credentials": {
        "node_id": "tests/test_purchase_flow.py::TestLogin::test_invalid_credentials",
        "description": "Verify invalid credentials show an error.",
    },
    "login_locked_user": {
        "node_id": "tests/test_purchase_flow.py::TestLogin::test_locked_out_user",
        "description": "Verify a locked-out user cannot log in.",
    },
    "inventory_visible": {
        "node_id": "tests/test_purchase_flow.py::TestInventory::test_inventory_page_shows_products",
        "description": "Verify the inventory contains the expected products.",
    },
    "add_backpack_to_cart": {
        "node_id": "tests/test_purchase_flow.py::TestInventory::test_add_single_item_updates_cart_badge",
        "description": "Add the Sauce Labs Backpack and verify the cart badge.",
    },
    "cart_contains_backpack": {
        "node_id": "tests/test_purchase_flow.py::TestCart::test_cart_shows_added_item",
        "description": "Add the Backpack and verify it appears in the cart.",
    },
    "single_item_purchase": {
        "node_id": "tests/test_purchase_flow.py::TestFullPurchaseFlow::test_single_item_purchase",
        "description": "Complete a purchase of one Backpack.",
    },
    "multi_item_purchase": {
        "node_id": "tests/test_purchase_flow.py::TestFullPurchaseFlow::test_multi_item_purchase",
        "description": "Complete a purchase of two products.",
    },
    "logout_after_purchase": {
        "node_id": "tests/test_purchase_flow.py::TestFullPurchaseFlow::test_logout_after_purchase",
        "description": "Complete a purchase and then log out.",
    },
}


def catalog_for_prompt() -> str:
    return "\n".join(
        f"- {test_id}: {entry['description']}"
        for test_id, entry in TEST_CATALOG.items()
    )
