import argparse
import json
import os
import sys
from pathlib import Path

from agent.evaluator import evaluate_run
from agent.executor import execute_plan
from agent.issue_reader import read_issue
from agent.planner import create_test_plan


ROOT = Path(__file__).resolve().parent


def is_ready_for_qa(status: str) -> bool:
    """Check if a GitHub issue status indicates it's ready for QA testing."""
    return status.lower() in ("ready for qa", "rfqa")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan and execute SauceDemo tests from an issue."
    )
    parser.add_argument(
        "--issue",
        required=True,
        help="Path to an issue Markdown file or a public GitHub issue URL.",
    )
    parser.add_argument(
        "--status",
        default="Ready for QA",
        help="GitHub issue status/column (e.g., 'Ready for QA' or 'RFQA'). Agent only executes if status is RFQA.",
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Generate the plan without launching Playwright.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    
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

    issue = read_issue(args.issue)
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

    report = {
        "issue": issue.model_dump(),
        "plan": plan.model_dump(),
        "evidence": evidence.model_dump(),
        "verdict": verdict.model_dump(),
    }
    report_path = ROOT / "evidence" / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\nFinal verdict:")
    print(verdict.model_dump_json(indent=2))
    print(f"\nReport: {report_path}")
    return 0 if verdict.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
