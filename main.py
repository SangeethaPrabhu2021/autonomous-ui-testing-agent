import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent.evaluator import evaluate_run
from agent.executor import execute_plan
from agent.issue_reader import read_issue
from agent.planner import create_test_plan


ROOT = Path(__file__).resolve().parent


def is_ready_for_qa(status: str) -> bool:
    """Check if a GitHub issue status indicates it's ready for QA testing."""
    return status.lower() in ("ready for qa", "rfqa")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan and execute SauceDemo tests from an issue."
    )
    parser.add_argument(
        "--issue",
        help=(
            "Path to an issue Markdown file or a public GitHub issue URL. "
            "Defaults to DEFAULT_ISSUE from the environment."
        ),
    )
    parser.add_argument(
        "--status",
        default="Ready for QA",
        help=(
            "GitHub issue status/column (e.g., 'Ready for QA' or 'RFQA'). "
            "Agent only executes if status is RFQA."
        ),
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Generate the plan without launching Playwright.",
    )
    return parser.parse_args(argv)


def resolve_issue_source(cli_issue: str | None) -> str | None:
    """Prefer the CLI issue while allowing a dotenv-backed default."""
    return cli_issue or os.getenv("DEFAULT_ISSUE")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv()
    args = parse_args()

    issue_source = resolve_issue_source(args.issue)
    if not issue_source:
        print(
            "No issue was provided. Use --issue or set DEFAULT_ISSUE in .env.",
            file=sys.stderr,
        )
        return 2

    # Check if issue is ready for QA before proceeding
    if not is_ready_for_qa(args.status):
        print(
            f"⏭️  Issue status '{args.status}' is not 'Ready for QA'.",
            file=sys.stderr,
        )
        print(
            "Agent will begin testing only when the issue is moved to the 'Ready for QA' column.",
            file=sys.stderr,
        )
        return 0
    
    if not os.getenv("GEMINI_API_KEY"):
        print(
            "GEMINI_API_KEY is not set. Set it before running the agent.",
            file=sys.stderr,
        )
        return 2

    issue = read_issue(issue_source)
    plan = create_test_plan(issue)
    print("Generated plan:")
    print(plan.model_dump_json(indent=2))

    if args.plan_only:
        return 0

    evidence = execute_plan(
        plan,
        project_root=ROOT,
        python_executable=sys.executable,
    )
    verdict = evaluate_run(evidence)
    verdict_data = (
        verdict.model_dump() if hasattr(verdict, "model_dump") else verdict
    )

    report = {
        "issue": issue.model_dump(),
        "plan": plan.model_dump(),
        "evidence": evidence.model_dump(),
        "verdict": verdict_data,
    }
    report_path = ROOT / "evidence" / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\nFinal verdict:")
    print(json.dumps(verdict_data, indent=2))
    print(f"\nReport: {report_path}")
    return 0 if verdict_data.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
