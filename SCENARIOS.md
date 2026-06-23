# Autonomous UI Testing Agent - Test Scenarios

## Overview

This document catalogs all executable test scenarios available to the Autonomous UI Testing Agent. Each scenario is a self-contained, allowlisted test that the LLM planner can select based on GitHub issue requirements.

The agent does not execute arbitrary steps; rather, it intelligently chooses from this curated catalog to build a minimal test plan that verifies the issue's acceptance criteria.

---

## Scenario Categories

### Category 1: Authentication (Login/Logout)
- **Purpose:** Validate user authentication flows
- **Target Application:** SauceDemo Login page
- **Use Case:** Issues requesting login validation, credential handling, or access control

### Category 2: Inventory & Product Discovery
- **Purpose:** Validate product browsing and inventory state
- **Target Application:** SauceDemo Inventory page
- **Use Case:** Issues requesting product visibility, product filtering, or browsing workflows

### Category 3: Shopping Cart Operations
- **Purpose:** Validate shopping cart functionality
- **Target Application:** SauceDemo Cart page
- **Use Case:** Issues requesting cart management, item selection, or cart state validation

### Category 4: Checkout & Order Flow
- **Purpose:** Validate end-to-end purchase completion
- **Target Application:** SauceDemo Checkout pages (Step 1, Step 2, Complete)
- **Use Case:** Issues requesting payment flow, order submission, or purchase verification

### Category 5: Full Purchase Workflows
- **Purpose:** Validate complete multi-step scenarios
- **Target Application:** All SauceDemo pages
- **Use Case:** Issues requesting end-to-end testing of complex flows

---

## Detailed Scenario Specifications

---

## Category 1: Authentication

### Scenario ID: `login_success`

**Objective**  
Verify that a standard user can successfully authenticate with valid credentials.

**Preconditions**
- Browser is at the login page (`https://www.saucedemo.com/`)
- Username and password fields are visible and enabled
- Login button is available

**Test Steps**
1. Locate username input field using semantic locator: `get_by_role("textbox", name="Username")`
2. Enter username: `standard_user`
3. Locate password input field using semantic locator: `get_by_role("textbox", name="Password")`
4. Enter password: `secret_sauce`
5. Locate and click login button using semantic locator: `get_by_role("button", name="Login")`
6. Wait for page navigation to complete
7. Assert current URL matches inventory page URL: `https://www.saucedemo.com/inventory.html`
8. Assert "Products" heading is visible

**Expected Results**
- Login form submission succeeds
- User is navigated to the inventory page
- Inventory title "Products" is visible
- Cart badge is displayed but empty (count not shown)

**Evidence Generated**
- Full-page screenshot at inventory page
- Playwright trace showing login flow
- pytest output showing successful assertion chain

**Business Requirement**
- Prerequisite for any issue requiring product browsing or cart operations
- Maps to acceptance criteria: "Login succeeds"

**Notes**
- Uses credentials pre-configured in SauceDemo environment
- Serves as prerequisite for 90% of other scenarios
- ~6 seconds execution time

---

### Scenario ID: `login_invalid_credentials`

**Objective**  
Verify that the system rejects invalid username/password combinations with a clear error message.

**Preconditions**
- Browser is at the login page
- Error message area is hidden (default state)
- Username/password fields are empty

**Test Steps**
1. Locate username input field
2. Enter username: `wrong_user`
3. Locate password input field
4. Enter password: `wrong_pass`
5. Locate and click login button
6. Wait for error message to appear
7. Assert error message contains: "Username and password do not match"
8. Assert user is still on login page (not redirected)

**Expected Results**
- Form submission is rejected
- Error message is displayed prominently
- User remains on login page
- No sensitive information is leaked in error message

**Evidence Generated**
- Screenshot showing error message
- Playwright trace showing attempted login
- pytest output with error message verification

**Business Requirement**
- Security validation: prevent unauthorized access
- Negative test case for authentication flows
- Maps to acceptance criteria: "Login error handling"

**Notes**
- Tests security boundary without risking real credentials
- Validates user-friendly error messaging
- ~4 seconds execution time

---

### Scenario ID: `login_locked_user`

**Objective**  
Verify that locked-out users receive appropriate error message and cannot access the system.

**Preconditions**
- Locked-out user account exists in SauceDemo
- Browser is at login page
- Error message area is hidden

**Test Steps**
1. Locate username input field
2. Enter username: `locked_out_user`
3. Locate password input field
4. Enter password: `secret_sauce` (correct password for this user)
5. Locate and click login button
6. Wait for error message
7. Assert error message contains: "Sorry, this user has been locked out"
8. Assert user is still on login page

**Expected Results**
- Correct credentials do not allow login for locked users
- System provides specific "locked out" message (not generic auth failure)
- User access control is enforced

**Evidence Generated**
- Screenshot showing locked-out error message
- Playwright trace showing login attempt
- pytest output with locked-out message verification

**Business Requirement**
- Access control validation
- Security scenario: verify lock-out mechanism works
- Maps to acceptance criteria: "Account lock verification"

**Notes**
- Uses SauceDemo's built-in locked-out user account
- Validates that lock-out is enforced at application level
- ~4 seconds execution time

---

## Category 2: Inventory & Product Discovery

### Scenario ID: `inventory_visible`

**Objective**  
Verify that after login, the inventory page displays all expected products.

**Preconditions**
- User is logged in as standard_user
- Inventory page has loaded
- All 6 products are in stock

**Test Steps**
1. Assert current page URL is `https://www.saucedemo.com/inventory.html`
2. Assert "Products" heading is visible
3. Locate all product items using `get_by_test_id("inventory-item")`
4. Count visible product items
5. Assert count equals 6
6. Extract product names using `get_by_test_id("inventory-item-name")`
7. Assert all expected product names are present (exact text match):
   - "Sauce Labs Backpack"
   - "Sauce Labs Bike Light"
   - "Sauce Labs Bolt T-Shirt"
   - "Sauce Labs Fleece Jacket"
   - "Sauce Labs Onesie"
   - "Test.allTheThings() T-Shirt (Red)"

**Expected Results**
- Inventory page loads successfully
- All 6 products are visible
- Product display shows correct names and prices
- Add-to-cart buttons are visible for each product

**Evidence Generated**
- Full-page screenshot of inventory page
- Playwright trace of product discovery
- pytest output with product count and name assertions

**Business Requirement**
- Foundational test for any inventory-related issue
- Maps to acceptance criteria: "The inventory page is displayed" or "Products are visible"

**Notes**
- Second most common prerequisite scenario (after login)
- Validates that inventory state is correct before other operations
- ~2 seconds execution time

---

## Category 3: Shopping Cart

### Scenario ID: `add_backpack_to_cart`

**Objective**  
Verify that adding a product to the cart updates the cart badge and counter correctly.

**Preconditions**
- User is logged in and viewing inventory page
- Sauce Labs Backpack product is visible
- Cart is initially empty (no badge shown or shows 0)

**Test Steps**
1. Locate "Sauce Labs Backpack" product item using `get_by_test_id("inventory-item").filter(has_text="Sauce Labs Backpack")`
2. Within that item, locate the "Add to cart" button using semantic locator with fallback:
   - Semantic: `get_by_role("button", name="Add to cart")`
   - Fallback: `get_by_test_id("add-to-cart-sauce-labs-backpack")`
3. Click the button
4. Wait for cart badge to appear
5. Locate cart badge using `get_by_test_id("shopping-cart-badge")`
6. Assert badge text equals "1"

**Expected Results**
- Button click completes successfully
- Cart badge appears in UI (was not visible before)
- Badge displays correct count "1"
- Badge is visible (not hidden or disabled)

**Evidence Generated**
- Screenshot showing cart badge with count "1"
- Playwright trace showing button click and badge update
- pytest output with cart count assertion

**Business Requirement**
- Core shopping functionality validation
- Maps to acceptance criteria: "The Sauce Labs Backpack can be added" + "The cart badge shows one item"

**Notes**
- Validates both action (button click) and state change (badge update)
- Requires inventory page to be loaded first (depends on login_success + inventory_visible)
- ~2 seconds execution time
- Common prerequisite for cart-related issues

---

### Scenario ID: `cart_contains_backpack`

**Objective**  
Verify that the cart page displays the correct product when navigated to after adding an item.

**Preconditions**
- User is logged in and on inventory page
- Sauce Labs Backpack has been added to cart (cart badge shows "1")
- Cart page has not been visited yet

**Test Steps**
1. Locate cart link using `get_by_test_id("shopping-cart-link")`
2. Click cart link
3. Wait for page navigation to complete
4. Assert current URL is `https://www.saucedemo.com/cart.html`
5. Assert "Your Cart" heading is visible
6. Locate all items in cart using `get_by_test_id("inventory-item")`
7. Assert at least 1 item is displayed
8. Locate product names using `get_by_test_id("inventory-item-name")`
9. Assert "Sauce Labs Backpack" is in the product names list
10. Assert "Remove" button is visible next to the Backpack item

**Expected Results**
- Cart page loads successfully
- Backpack item is listed in cart
- Item shows name, description, price
- Remove button is available for the item
- Cart is not empty; shows exactly 1 item

**Evidence Generated**
- Screenshot of cart page with Backpack item visible
- Playwright trace showing navigation and item display
- pytest output with item presence verification

**Business Requirement**
- Validates cart state persistence
- Maps to acceptance criteria: "The cart contains the Sauce Labs Backpack"

**Notes**
- Requires add_backpack_to_cart scenario to run first
- Validates data consistency across page boundaries
- ~2-3 seconds execution time

---

## Category 4: Checkout Flow

### Scenario ID: `single_item_purchase`

**Objective**  
Verify that a user can complete a full purchase workflow with a single item, including checkout steps and order confirmation.

**Preconditions**
- User is logged in as standard_user
- Browser is at inventory page
- No items are currently in cart

**Test Steps**

**Phase 1: Add Item to Cart**
1. Locate Sauce Labs Backpack product
2. Click "Add to cart" button
3. Assert cart badge shows "1"

**Phase 2: Navigate to Cart**
4. Click cart link
5. Assert cart page loads
6. Assert Backpack is in cart

**Phase 3: Proceed to Checkout**
7. Locate "Checkout" button using semantic locator with fallback:
   - Semantic: `get_by_role("button", name="Checkout")`
   - Fallback: `get_by_test_id("checkout")`
8. Click Checkout button
9. Assert page navigates to checkout step 1 (`https://www.saucedemo.com/checkout-step-one.html`)

**Phase 4: Enter Customer Information**
10. Locate "First Name" input using `get_by_role("textbox", name="First Name")`
11. Enter: "Jane"
12. Locate "Last Name" input using `get_by_role("textbox", name="Last Name")`
13. Enter: "Doe"
14. Locate "Zip/Postal Code" input using `get_by_role("textbox", name="Zip/Postal Code")`
15. Enter: "10001"
16. Locate and click "Continue" button
17. Assert page navigates to checkout step 2 (`https://www.saucedemo.com/checkout-step-two.html`)

**Phase 5: Review Order Summary**
18. Assert "Sauce Labs Backpack" is listed in order overview
19. Verify price information is displayed (subtotal, tax, total)

**Phase 6: Complete Purchase**
20. Locate and click "Finish" button using semantic locator with fallback:
    - Semantic: `get_by_role("button", name="Finish")`
    - Fallback: `get_by_test_id("finish")`
21. Assert page navigates to order complete page (`https://www.saucedemo.com/checkout-complete.html`)
22. Assert "Thank you for your order!" heading is visible
23. Assert "Your order has been dispatched" message is visible

**Expected Results**
- All 6 checkout phases complete successfully
- User is guided through multi-step workflow
- Order confirmation is displayed with appropriate messaging
- No errors or unexpected page transitions occur

**Evidence Generated**
- 3 screenshots (add-to-cart, checkout step 2, order complete)
- Playwright trace showing all 6 phases
- pytest output with all navigation and state assertions

**Business Requirement**
- End-to-end happy path for purchase flow
- Maps to acceptance criteria: "User can complete a purchase" or "Checkout flow works"

**Notes**
- Longest-running scenario (~8-10 seconds)
- Covers multiple pages and workflows
- Most comprehensive scenario for e-commerce functionality
- Common requirement for any feature affecting purchase flow

---

### Scenario ID: `multi_item_purchase`

**Objective**  
Verify that a user can purchase multiple items, with correct cart count and order summary.

**Preconditions**
- User is logged in as standard_user
- Browser is at inventory page
- No items are currently in cart

**Test Steps**

**Phase 1: Add Two Items**
1. Locate "Sauce Labs Backpack" and click "Add to cart"
2. Assert cart badge shows "1"
3. Locate "Sauce Labs Bike Light" and click "Add to cart"
4. Assert cart badge shows "2"

**Phase 2: Review Cart**
5. Click cart link
6. Assert cart page shows 2 items
7. Assert both "Sauce Labs Backpack" and "Sauce Labs Bike Light" are listed

**Phase 3: Checkout Steps 1 & 2**
8. Click "Checkout" button
9. Fill customer info: "Jane" / "Doe" / "10001"
10. Click "Continue"
11. Assert checkout step 2 page loads
12. Assert both items are in order overview
13. Verify subtotal reflects 2 items (prices added correctly)

**Phase 4: Complete Purchase**
14. Click "Finish" button
15. Assert order complete page displays

**Expected Results**
- Cart correctly shows 2 items throughout workflow
- Both items persist through checkout
- Order summary displays both items with correct pricing
- Order completion succeeds with multiple items

**Evidence Generated**
- Screenshots showing 2-item cart state at multiple checkpoints
- Playwright trace showing multi-item workflow
- pytest output with cart count and item assertions

**Business Requirement**
- Validates cart capacity and multi-item checkout
- Maps to acceptance criteria: "Multiple items can be purchased" or "Cart handles multiple products"

**Notes**
- Verifies cart accumulation logic
- Tests pricing calculation with multiple items
- ~9-11 seconds execution time
- Important for realistic user scenarios

---

### Scenario ID: `logout_after_purchase`

**Objective**  
Verify that a user can complete a purchase and then log out successfully, with session properly terminated.

**Preconditions**
- User is logged in as standard_user
- Browser is at inventory page

**Test Steps**

**Phase 1-3: Complete Purchase (same as single_item_purchase)**
1. Add Backpack to cart
2. Navigate to cart and proceed to checkout
3. Complete all checkout steps and finish order
4. Assert order complete page is displayed

**Phase 4: Return to Inventory**
5. Locate "Back Home" button using semantic locator with fallback:
   - Semantic: `get_by_role("button", name="Back Home")`
   - Fallback: `get_by_test_id("back-to-products")`
6. Click "Back Home" button
7. Assert page navigates back to inventory
8. Assert "Products" heading is visible again

**Phase 5: Logout**
9. Locate hamburger menu button using `get_by_role("button", name="Open Menu")`
10. Click menu button
11. Locate "Logout" link using `get_by_role("link", name="Logout")`
12. Wait for logout link to be visible (menu animation)
13. Click "Logout" link
14. Assert page navigates back to login page (`https://www.saucedemo.com/`)
15. Assert login button is visible and ready for new login

**Expected Results**
- User can return to inventory after purchase completion
- Hamburger menu opens and displays logout option
- Logout link is clickable
- Session is terminated (redirected to login)
- Login page is ready for next user

**Evidence Generated**
- Screenshot showing order complete confirmation
- Screenshot showing inventory page after "Back Home"
- Screenshot showing login page after logout
- Playwright trace showing full workflow including logout sequence

**Business Requirement**
- Session management validation
- Maps to acceptance criteria: "User can logout after purchase" or "Session termination works"

**Notes**
- Tests post-purchase navigation and session cleanup
- Validates menu interaction (hamburger menu is not always default)
- ~12-15 seconds execution time (longest scenario)
- Important for security and session isolation

---

## Category 5: Full Purchase Workflows

### Scenario ID: `single_item_purchase` (Alias for multi-step workflow)

*See detailed specification under "Category 4: Checkout Flow" above.*

---

### Scenario ID: `multi_item_purchase` (Alias for multi-step workflow)

*See detailed specification under "Category 4: Checkout Flow" above.*

---

### Scenario ID: `logout_after_purchase` (Alias for complete session workflow)

*See detailed specification under "Category 4: Checkout Flow" above.*

---

## Scenario Dependency Graph

The following diagram shows logical dependencies between scenarios (solid line = must run first):

```
login_success ──────────────────┐
                                │
                       ┌────────▼────────┐
                       │                 │
                inventory_visible  add_backpack_to_cart ─┐
                       │                 │              │
                       └────────┬────────┘              │
                                │                      │
                       cart_contains_backpack ◀────────┘
                                │
                       ┌────────┴────────┐
                       │                 │
              single_item_purchase  multi_item_purchase
                       │                 │
                       └────────┬────────┘
                                │
                       logout_after_purchase
```

**Legend:**
- **login_success** → All other scenarios (hard requirement)
- **add_backpack_to_cart** → **cart_contains_backpack** (state dependency)
- **inventory_visible** → **add_backpack_to_cart** (page prerequisite)
- **add_backpack_to_cart** + **cart_contains_backpack** → **single_item_purchase** (conceptually similar)

---

## Scenario Selection Strategy (LLM Planner)

### How the Planner Chooses Scenarios

When the LLM planner receives a GitHub issue, it performs the following analysis:

#### Step 1: Parse Acceptance Criteria
Extract keywords from the issue body to identify requirements:

| Keyword / Pattern | Suggested Scenarios |
|---|---|
| "log in" OR "login" OR "authenticate" | `login_success` |
| "invalid credentials" OR "wrong password" OR "error message" | `login_invalid_credentials` |
| "locked" OR "locked out" OR "access denied" | `login_locked_user` |
| "inventory" OR "products" OR "browse" OR "product list" | `inventory_visible` |
| "add to cart" OR "cart" OR "shopping cart" | `add_backpack_to_cart`, `cart_contains_backpack` |
| "checkout" OR "order" OR "purchase" | `single_item_purchase` |
| "multiple items" OR "two products" OR "multiple purchases" | `multi_item_purchase` |
| "logout" OR "session" OR "end session" | `logout_after_purchase` |

#### Step 2: Resolve Dependencies
Automatically prepend prerequisite scenarios:

```python
if "add_backpack_to_cart" in selected:
    # Dependency chain: login → inventory → add item
    scenarios = ["login_success", "inventory_visible", "add_backpack_to_cart", ...]

if "checkout" in selected:
    # Must have added item to cart first
    scenarios = [..., "add_backpack_to_cart", "single_item_purchase"]
```

#### Step 3: Optimize for Minimal Testing
Use the **smallest sufficient set** of scenarios:

```
GOOD (Minimal):
Issue: "User can add backpack to cart"
Plan: [login_success, inventory_visible, add_backpack_to_cart]

REDUNDANT (Over-testing):
Issue: "User can add backpack to cart"
Plan: [login_success, inventory_visible, add_backpack_to_cart, 
       cart_contains_backpack, single_item_purchase]
       # ↑ Unnecessary; already verified by first 3
```

#### Step 4: Order Scenarios Logically
Arrange from basic prerequisites to complex workflows:

```
✓ 1. login_success              (prerequisite)
✓ 2. inventory_visible          (prerequisite after login)
✓ 3. add_backpack_to_cart       (core requirement)
✓ 4. cart_contains_backpack     (verification of step 3)
✗ single_item_purchase          (redundant if steps 1-4 pass)
```

### Example: LLM Plan Generation

**Input Issue:**
```markdown
# Feature: Users should be able to add items to cart

As a SauceDemo customer, I want to add products to my cart.

Acceptance criteria:
- I can log in with standard_user
- I can see the inventory page
- I can add the Backpack to my cart
- The cart badge shows "1"
- The cart page shows my item
```

**Planner Output:**
```json
{
  "objective": "Verify that standard users can add items to their cart, with correct cart state reflected.",
  "scenarios": [
    {
      "test_id": "login_success",
      "reason": "Prerequisite: Validate standard_user authentication before testing cart operations."
    },
    {
      "test_id": "inventory_visible",
      "reason": "Prerequisite: Verify inventory page loads with all products available for selection."
    },
    {
      "test_id": "add_backpack_to_cart",
      "reason": "Core requirement: Add Backpack to cart and verify cart badge updates to '1'."
    },
    {
      "test_id": "cart_contains_backpack",
      "reason": "Verification: Confirm cart page displays the added Backpack item correctly."
    }
  ]
}
```

**Why This Order?**
1. **login_success** – User must be authenticated
2. **inventory_visible** – Products must be discoverable
3. **add_backpack_to_cart** – Direct requirement
4. **cart_contains_backpack** – Validates state after requirement 3

---

## Scenario Catalog Reference

Quick lookup table for all scenarios:

| Scenario ID | Category | Prerequisite | Duration | Status |
|---|---|---|---|---|
| `login_success` | Auth | None | ~6s | Active |
| `login_invalid_credentials` | Auth | None | ~4s | Active |
| `login_locked_user` | Auth | None | ~4s | Active |
| `inventory_visible` | Inventory | login_success | ~2s | Active |
| `add_backpack_to_cart` | Cart | inventory_visible | ~2s | Active |
| `cart_contains_backpack` | Cart | add_backpack_to_cart | ~3s | Active |
| `single_item_purchase` | Checkout | login_success | ~10s | Active |
| `multi_item_purchase` | Checkout | login_success | ~11s | Active |
| `logout_after_purchase` | Session | single_item_purchase | ~15s | Active |

---

## Scenario Maintenance & Updates

### Adding a New Scenario

To extend the agent with a new scenario:

1. **Implement test in `tests/test_purchase_flow.py`**
   ```python
   def test_new_workflow(self, page: Page):
       # Implementation using Page Object Model
       pass
   ```

2. **Register in `agent/catalog.py`**
   ```python
   TEST_CATALOG = {
       ...
       "new_workflow_id": {
           "node_id": "tests/test_purchase_flow.py::TestClass::test_new_workflow",
           "description": "Brief description of scenario",
       },
   }
   ```

3. **Update this document** with new scenario details

4. **Test the planner** with an issue that requires the new scenario
   ```powershell
   python main.py --issue new_test_issue.md --plan-only
   ```

### Deprecating a Scenario

If a scenario becomes obsolete:

1. Remove from `TEST_CATALOG` in `agent/catalog.py`
2. Archive test method in `tests/test_purchase_flow.py` (don't delete)
3. Note in `SCENARIOS.md` under "Deprecated Scenarios" section
4. LLM will no longer select it; existing plans remain valid

---

## Appendix: Business Requirement Mappings

### User Story: "As a customer, I want to purchase items online"

**Required Scenarios (in order):**
1. `login_success` – Authentication
2. `inventory_visible` – Product discovery
3. `add_backpack_to_cart` – Item selection
4. `cart_contains_backpack` – Cart verification
5. `single_item_purchase` – Purchase completion

**Optional Extensions:**
- `multi_item_purchase` – Multiple items
- `logout_after_purchase` – Session cleanup

---

### User Story: "As an admin, I want to verify authentication security"

**Required Scenarios:**
1. `login_success` – Valid auth works
2. `login_invalid_credentials` – Invalid auth fails
3. `login_locked_user` – Lock-out mechanism works

---

### User Story: "As a QA engineer, I want to ensure cart state persists across pages"

**Required Scenarios:**
1. `login_success` – Setup
2. `inventory_visible` – Setup
3. `add_backpack_to_cart` – Add item
4. `cart_contains_backpack` – Verify state persistence

---

## Conclusion

The scenario catalog provides a **flexible, composable set of building blocks** that the LLM planner uses to construct minimal, targeted test plans. Each scenario is:

- **Well-defined** – Clear preconditions, steps, and expected results
- **Traceable** – Maps to business requirements and GitHub issues
- **Executable** – Runs in < 15 seconds with full evidence collection
- **Maintainable** – Uses Page Object Model and semantic locators

This design enables the agent to scale from simple login tests to complex multi-step purchase workflows without hardcoding specific test flows.

---

**Document Version:** 1.0  
**Date:** 2026-06-23  
**Status:** Complete
