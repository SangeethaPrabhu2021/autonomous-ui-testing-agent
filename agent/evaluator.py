import os

from google import genai

from agent.models import RunEvidence, Verdict


EVALUATOR_INSTRUCTIONS = """
You are a QA result evaluator.
Summarize the supplied execution evidence clearly and concisely.
Never mark the run passed when any executed scenario failed.
Do not claim that unexecuted behavior was verified.
"""


def evaluate_run(evidence: RunEvidence, client=None) -> Verdict:
    client = client or genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        contents=(
            f"{EVALUATOR_INSTRUCTIONS}\n\n"
            f"Execution evidence:\n{evidence.model_dump_json(indent=2)}"
        ),
        config={
            "response_mime_type": "application/json",
            "response_json_schema": Verdict.model_json_schema(),
        },
    )
    if not response.text:
        raise RuntimeError("The evaluation model did not return a verdict.")
    verdict = Verdict.model_validate_json(response.text)

    verdict.status = "passed" if evidence.passed else "failed"
    if not evidence.passed:
        verdict.failed_scenarios = [
            result.test_id for result in evidence.results if not result.passed
        ]
    return verdict
