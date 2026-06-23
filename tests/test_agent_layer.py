from pathlib import Path

import pytest

from agent.catalog import TEST_CATALOG
from agent.issue_reader import read_issue
from agent.models import PlannedScenario, TestPlan as AgentTestPlan
from agent.planner import create_test_plan


def test_reads_local_issue(tmp_path: Path):
    issue_path = tmp_path / "issue.md"
    issue_path.write_text("# Add item\n\nAdd the Backpack.", encoding="utf-8")

    issue = read_issue(str(issue_path))

    assert issue.title == "Add item"
    assert issue.body == "Add the Backpack."


def test_planner_rejects_unknown_test_id():
    class FakeResponse:
        text = AgentTestPlan(
            objective="Test something",
            scenarios=[PlannedScenario(
                test_id="arbitrary_shell_command",
                reason="No",
            )],
        ).model_dump_json()

    class FakeModels:
        @staticmethod
        def generate_content(**_kwargs):
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    issue = read_issue("issues/issue_001.md")
    with pytest.raises(ValueError, match="unknown test IDs"):
        create_test_plan(issue, client=FakeClient())


def test_catalog_maps_only_to_pytest_node_ids():
    assert TEST_CATALOG
    assert all(
        entry["node_id"].startswith("tests/test_purchase_flow.py::")
        for entry in TEST_CATALOG.values()
    )
