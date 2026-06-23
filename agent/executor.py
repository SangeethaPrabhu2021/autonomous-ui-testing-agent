import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from agent.catalog import TEST_CATALOG
from agent.config import is_headless
from agent.models import ExecutionResult, RunEvidence, TestPlan


def execute_plan(
    plan: TestPlan,
    project_root: Path | None = None,
    python_executable: str | None = None,
) -> RunEvidence:
    root = project_root or Path(__file__).resolve().parents[1]
    python = python_executable or sys.executable
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = root / "evidence" / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    results = []
    for index, scenario in enumerate(plan.scenarios, start=1):
        entry = TEST_CATALOG[scenario.test_id]
        artifact_dir = run_root / f"{index:02d}_{scenario.test_id}"
        command = [
            python,
            "-m",
            "pytest",
            entry["node_id"],
            "-q",
            "--screenshot=on",
            "--full-page-screenshot",
            "--tracing=retain-on-failure",
            f"--output={artifact_dir}",
        ]
        if not is_headless():
            command.append("--headed")
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = (completed.stdout + "\n" + completed.stderr).strip()
        results.append(
            ExecutionResult(
                test_id=scenario.test_id,
                passed=completed.returncode == 0,
                return_code=completed.returncode,
                output=output[-6000:],
                artifact_directory=str(artifact_dir),
            )
        )

    return RunEvidence(
        objective=plan.objective,
        passed=all(result.passed for result in results),
        results=results,
    )
