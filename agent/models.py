from typing import Literal

from pydantic import BaseModel, Field


class Issue(BaseModel):
    title: str
    body: str
    source: str


class PlannedScenario(BaseModel):
    test_id: str = Field(description="An exact test id from the supplied catalog")
    reason: str


class TestPlan(BaseModel):
    objective: str
    scenarios: list[PlannedScenario]


class ExecutionResult(BaseModel):
    test_id: str
    passed: bool
    return_code: int
    output: str
    artifact_directory: str


class RunEvidence(BaseModel):
    objective: str
    passed: bool
    results: list[ExecutionResult]


class Verdict(BaseModel):
    status: Literal["passed", "failed"]
    summary: str
    failed_scenarios: list[str] = []
    recommendations: list[str] = []
