import logging
import os

from google import genai

from agent.catalog import TEST_CATALOG, catalog_for_prompt
from agent.models import Issue, PlannedScenario, TestPlan


logger = logging.getLogger(__name__)

PLANNER_INSTRUCTIONS = """
You are a QA planning agent for SauceDemo.
Choose the smallest useful set of scenarios that verifies the issue.
You may only use exact test IDs from the supplied catalog.
Do not invent browser actions, selectors, commands, or test IDs.
Order scenarios from basic prerequisites to the main acceptance flow.
"""


def _fallback_test_plan(issue: Issue) -> TestPlan:
    """Build a safe allowlisted plan when Gemini planning is unavailable."""
    issue_text = f"{issue.title}\n{issue.body}".lower()
    scenario_ids = ["login_success"]

    if any(term in issue_text for term in ("inventory", "product", "backpack", "cart")):
        scenario_ids.append("inventory_visible")
    if any(term in issue_text for term in ("add", "backpack", "cart")):
        scenario_ids.append("add_backpack_to_cart")
    if "cart" in issue_text:
        scenario_ids.append("cart_contains_backpack")
    if any(term in issue_text for term in ("purchase", "checkout", "order")):
        purchase_id = (
            "multi_item_purchase"
            if any(term in issue_text for term in ("multiple", "multi", "two"))
            else "single_item_purchase"
        )
        scenario_ids.append(purchase_id)
    if "logout" in issue_text or "log out" in issue_text:
        scenario_ids.append("logout_after_purchase")
    if "invalid" in issue_text and "credential" in issue_text:
        scenario_ids.append("login_invalid_credentials")
    if "locked" in issue_text:
        scenario_ids.append("login_locked_user")

    # Preserve order while removing duplicates.
    scenario_ids = list(dict.fromkeys(scenario_ids))
    return TestPlan(
        objective=f"Fallback test plan for: {issue.title}",
        scenarios=[
            PlannedScenario(
                test_id=test_id,
                reason=(
                    "Selected by the deterministic fallback planner because "
                    "Gemini planning was unavailable."
                ),
            )
            for test_id in scenario_ids
        ],
    )


def create_test_plan(issue: Issue, client=None) -> TestPlan:
    logger.info("Gemini planning started")

    try:
        client = client or genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=(
                f"{PLANNER_INSTRUCTIONS}\n\n"
                f"Issue title: {issue.title}\n\n"
                f"Issue body:\n{issue.body}\n\n"
                f"Allowed test catalog:\n{catalog_for_prompt()}"
            ),
            config={
                "response_mime_type": "application/json",
                "response_json_schema": TestPlan.model_json_schema(),
            },
        )
        if not response.text:
            raise RuntimeError("The planning model did not return a test plan.")

        plan = TestPlan.model_validate_json(response.text)
        unknown = [
            scenario.test_id
            for scenario in plan.scenarios
            if scenario.test_id not in TEST_CATALOG
        ]
        if unknown:
            raise ValueError(f"Planner selected unknown test IDs: {unknown}")
        if not plan.scenarios:
            raise ValueError("Planner returned an empty test plan.")

        logger.info("Gemini planning succeeded")
        return plan
    except Exception:
        # Planning must not prevent allowlisted UI tests from executing.
        logger.exception("Gemini planning failed")
        logger.warning("Falling back to deterministic allowlisted test plan")
        return _fallback_test_plan(issue)
