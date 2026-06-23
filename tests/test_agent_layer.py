from pathlib import Path

import pytest

from agent.catalog import TEST_CATALOG
from agent.config import application_url, is_headless
from agent.evaluator import evaluate_run
from agent.executor import execute_plan
from agent.issue_reader import read_issue
from agent.models import (
    ExecutionResult,
    PlannedScenario,
    RunEvidence,
    TestPlan as AgentTestPlan,
    Verdict,
)
from agent.planner import create_test_plan
from main import parse_args, resolve_issue_source


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_reads_local_issue(tmp_path: Path):
    issue_path = tmp_path / "issue.md"
    issue_path.write_text("# Add item\n\nAdd the Backpack.", encoding="utf-8")

    issue = read_issue(str(issue_path))

    assert issue.title == "Add item"
    assert issue.body == "Add the Backpack."


def test_planner_falls_back_when_model_returns_unknown_test_id(caplog):
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

    issue = read_issue(str(PROJECT_ROOT / "issues" / "issue_001.md"))
    with caplog.at_level("INFO"):
        plan = create_test_plan(issue, client=FakeClient())

    assert [scenario.test_id for scenario in plan.scenarios] == [
        "login_success",
        "inventory_visible",
        "add_backpack_to_cart",
        "cart_contains_backpack",
    ]
    assert "Gemini planning failed" in caplog.text
    assert "Falling back to deterministic allowlisted test plan" in caplog.text


def test_planner_falls_back_when_gemini_quota_is_exhausted(caplog):
    class FakeModels:
        @staticmethod
        def generate_content(**_kwargs):
            raise RuntimeError("429 RESOURCE_EXHAUSTED")

    class FakeClient:
        models = FakeModels()

    issue = read_issue(str(PROJECT_ROOT / "issues" / "issue_001.md"))
    with caplog.at_level("INFO"):
        plan = create_test_plan(issue, client=FakeClient())

    assert plan.scenarios
    assert all(
        scenario.test_id in TEST_CATALOG for scenario in plan.scenarios
    )
    assert "Gemini planning failed" in caplog.text


def test_planner_uses_current_default_model(monkeypatch):
    class FakeResponse:
        text = AgentTestPlan(
            objective="Test login",
            scenarios=[
                PlannedScenario(test_id="login_success", reason="Required")
            ],
        ).model_dump_json()

    class FakeModels:
        @staticmethod
        def generate_content(**kwargs):
            assert kwargs["model"] == "gemini-2.5-flash"
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    issue = read_issue(str(PROJECT_ROOT / "issues" / "issue_001.md"))

    plan = create_test_plan(issue, client=FakeClient())

    assert plan.scenarios[0].test_id == "login_success"


def test_catalog_maps_only_to_pytest_node_ids():
    assert TEST_CATALOG
    assert all(
        entry["node_id"].startswith("tests/test_purchase_flow.py::")
        for entry in TEST_CATALOG.values()
    )


def test_environment_configures_base_url_and_headless(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://example.test/app")
    monkeypatch.setenv("HEADLESS", "false")

    assert application_url("inventory.html") == (
        "https://example.test/app/inventory.html"
    )
    assert is_headless() is False


def test_environment_defaults_to_headless(monkeypatch):
    monkeypatch.delenv("HEADLESS", raising=False)

    assert is_headless() is True


def test_cli_issue_overrides_default_issue(monkeypatch):
    monkeypatch.setenv("DEFAULT_ISSUE", "issues/default.md")

    args = parse_args(["--issue", "issues/explicit.md"])

    assert resolve_issue_source(args.issue) == "issues/explicit.md"


def test_default_issue_is_used_when_cli_issue_is_omitted(monkeypatch):
    monkeypatch.setenv("DEFAULT_ISSUE", "issues/default.md")

    args = parse_args([])

    assert resolve_issue_source(args.issue) == "issues/default.md"


def test_headless_false_launches_playwright_in_headed_mode(
    monkeypatch, tmp_path: Path
):
    captured_command = []

    class Completed:
        returncode = 0
        stdout = "passed"
        stderr = ""

    def fake_run(command, **_kwargs):
        captured_command.extend(command)
        return Completed()

    test_id = next(iter(TEST_CATALOG))
    plan = AgentTestPlan(
        objective="Verify headed configuration",
        scenarios=[PlannedScenario(test_id=test_id, reason="Configuration test")],
    )
    monkeypatch.setenv("HEADLESS", "false")
    monkeypatch.setattr("agent.executor.subprocess.run", fake_run)

    execute_plan(plan, project_root=tmp_path, python_executable="python")

    assert "--headed" in captured_command


def _evidence(passed: bool = True) -> RunEvidence:
    return RunEvidence(
        objective="Verify the purchase flow",
        passed=passed,
        results=[
            ExecutionResult(
                test_id="purchase_flow",
                passed=passed,
                return_code=0 if passed else 1,
                output="test output",
                artifact_directory="evidence/runs/test/purchase_flow",
            )
        ],
    )


def test_evaluator_returns_ai_verdict_on_success(monkeypatch, caplog):
    class FakeResponse:
        text = Verdict(
            status="passed",
            summary="The test passed.",
        ).model_dump_json()

    class FakeModels:
        @staticmethod
        def generate_content(**kwargs):
            assert kwargs["model"] == "gemini-2.5-flash"
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    with caplog.at_level("INFO"):
        verdict = evaluate_run(_evidence(), client=FakeClient())

    assert isinstance(verdict, Verdict)
    assert verdict.status == "passed"
    assert "Gemini evaluation started" in caplog.text
    assert "Gemini evaluation succeeded" in caplog.text


def test_evaluator_uses_configured_model(monkeypatch):
    class FakeResponse:
        text = Verdict(status="passed", summary="Passed.").model_dump_json()

    class FakeModels:
        @staticmethod
        def generate_content(**kwargs):
            assert kwargs["model"] == "custom-gemini-model"
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    monkeypatch.setenv("GEMINI_MODEL", "custom-gemini-model")

    verdict = evaluate_run(_evidence(), client=FakeClient())

    assert isinstance(verdict, Verdict)


def test_evaluator_falls_back_when_gemini_fails(caplog):
    class FakeModels:
        @staticmethod
        def generate_content(**_kwargs):
            raise TimeoutError("Gemini request timed out")

    class FakeClient:
        models = FakeModels()

    with caplog.at_level("INFO"):
        verdict = evaluate_run(_evidence(), client=FakeClient())

    assert verdict == {
        "verdict": "REVIEW_REQUIRED",
        "summary": "UI tests executed, but AI evaluation service was unavailable.",
        "reason": "Gemini request timed out",
    }
    assert "Gemini evaluation failed" in caplog.text
    assert "Falling back to REVIEW_REQUIRED verdict" in caplog.text


def test_evaluator_falls_back_on_invalid_response():
    class FakeResponse:
        text = "not valid JSON"

    class FakeModels:
        @staticmethod
        def generate_content(**_kwargs):
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    verdict = evaluate_run(_evidence(), client=FakeClient())

    assert verdict["verdict"] == "REVIEW_REQUIRED"
    assert verdict["reason"]
