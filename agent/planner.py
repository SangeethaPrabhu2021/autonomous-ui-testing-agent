import os

from google import genai

from agent.catalog import TEST_CATALOG, catalog_for_prompt
from agent.models import Issue, TestPlan


PLANNER_INSTRUCTIONS = """
You are a QA planning agent for SauceDemo.
Choose the smallest useful set of scenarios that verifies the issue.
You may only use exact test IDs from the supplied catalog.
Do not invent browser actions, selectors, commands, or test IDs.
Order scenarios from basic prerequisites to the main acceptance flow.
"""


def create_test_plan(issue: Issue, client=None) -> TestPlan:
    client = client or genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
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
    return plan
