# Autonomous UI Testing Agent

An AI-assisted UI testing agent that reads a QA-ready issue, selects an
approved set of end-to-end scenarios, executes them against
[SauceDemo](https://www.saucedemo.com/), collects evidence, and produces a
structured verdict report.

The implementation deliberately separates AI-assisted decision-making from
browser execution. Gemini may plan and evaluate a run, but it cannot generate
or execute arbitrary code. All executable scenarios are mapped to reviewed
Pytest tests in an explicit allow list.

## Project Overview

The agent implements the following workflow:

1. Read a local Markdown issue or supported GitHub issue URL.
2. Confirm that the issue status is `Ready for QA` or `RFQA`.
3. Ask Gemini to select the smallest useful test plan from an allow-listed
   scenario catalog.
4. Fall back to deterministic planning if Gemini is unavailable or returns an
   invalid plan.
5. Execute the selected Pytest/Playwright scenarios.
6. Capture test output, screenshots, traces, and artifact locations.
7. Ask Gemini to summarize the evidence.
8. Write a final JSON report, using `REVIEW_REQUIRED` if AI evaluation fails.

```text
GitHub issue / Markdown issue
             |
             v
       Issue Reader
             |
             v
          Planner  <------ Gemini
             |              |
             |      deterministic fallback
             v
     Allow-listed TestPlan
             |
             v
          Executor
             |
             +------> Pytest + Playwright
             |          |
             |          +--> screenshots
             |          +--> traces
             |          +--> captured output
             v
        Run Evidence
             |
             v
         Evaluator <------ Gemini
             |               |
             |       REVIEW_REQUIRED fallback
             v
     evidence/report.json
```

## Architecture

### Planner

`agent/planner.py` sends the issue and the approved scenario catalog to Gemini.
The returned JSON is validated with Pydantic and rejected if it contains an
unknown or empty scenario selection.

Gemini failures do not prevent test execution. A deterministic fallback planner
selects relevant scenarios using issue keywords while remaining constrained to
the same allow list.

### Executor

`agent/executor.py` resolves each planned scenario through
`agent/catalog.py`, then launches the corresponding Pytest node ID in a separate
process. Each scenario receives its own artifact directory and a bounded
execution timeout.

The executor records:

- Test ID and result
- Process return code
- Captured stdout and stderr
- Screenshot and trace artifact directory

### Evaluator

`agent/evaluator.py` sends the completed run evidence to Gemini for a concise
verdict. The evaluator never allows the model to override the observed test
status.

If Gemini is unavailable, rate-limited, times out, or returns invalid JSON, the
agent returns:

```json
{
  "verdict": "REVIEW_REQUIRED",
  "summary": "UI tests executed, but AI evaluation service was unavailable.",
  "reason": "<exception details>"
}
```

The evidence and final report are still preserved.

## Key Features

- AI-assisted test planning constrained to reviewed scenarios
- Deterministic fallback planning during Gemini outages
- Pytest and Playwright browser execution
- 22 end-to-end UI tests covering login, inventory, cart, checkout, purchase,
  and logout flows
- Page Object Model for reusable UI behavior
- Semantic locators based on roles, accessible names, and visible text
- Scoped `data-test` fallback locators where the UI lacks suitable semantics
- Screenshots, traces, process output, and structured execution evidence
- Gemini-based evidence summarization
- Graceful handling of model errors, invalid responses, timeouts, and quotas
- Dotenv-based local configuration
- RFQA status gate and optional plan-only mode

## Project Structure

```text
autonomous-ui-testing-agent/
|-- agent/
|   |-- catalog.py          # Allow-listed scenario-to-Pytest mapping
|   |-- config.py           # BASE_URL and HEADLESS configuration helpers
|   |-- evaluator.py        # Gemini evidence evaluation and fallback verdict
|   |-- executor.py         # Controlled Pytest execution and evidence capture
|   |-- issue_reader.py     # Local Markdown and GitHub issue ingestion
|   |-- models.py           # Pydantic request, plan, evidence, and verdict models
|   `-- planner.py          # Gemini planning and deterministic fallback
|-- pages/
|   |-- login.py            # Login page object
|   |-- inventory_page.py   # Inventory page object
|   |-- cart_page.py        # Cart page object
|   |-- checkout_page.py    # Checkout page object
|   `-- locators.py         # Semantic-first locator fallback helper
|-- tests/
|   |-- test_agent_layer.py # Unit tests for configuration and agent behavior
|   `-- test_purchase_flow.py # 22 Playwright UI tests
|-- issues/
|   `-- issue_001.md        # Example Ready-for-QA issue
|-- evidence/
|   |-- runs/               # Per-run screenshots, traces, and test artifacts
|   `-- report.json         # Final structured report
|-- main.py                 # CLI entry point and workflow orchestration
|-- .env.example            # Safe configuration template
|-- pytest.ini              # Pytest configuration and integration marker
|-- requirements.txt        # Pinned Python dependencies
|-- SCENARIOS.md            # Detailed scenario documentation
`-- TEST_PLAN.md            # Design and test strategy
```

## Installation

### Prerequisite

Python 3.10 or newer is required. The codebase uses modern type-hint syntax,
including union types such as `Path | None`, which is supported in Python 3.10+.

### 1. Clone the repository

```powershell
git clone https://github.com/SangeethaPrabhu2021/autonomous-ui-testing-agent.git
cd autonomous-ui-testing-agent
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Install the Playwright browser

```powershell
python -m playwright install chromium
```

## Configuration

Copy the safe template before running the agent:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Example configuration:

```dotenv
GEMINI_API_KEY=replace-with-your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash
BASE_URL=https://www.saucedemo.com/
HEADLESS=true
DEFAULT_ISSUE=issues/issue_001.md
```

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | API key used by the planner and evaluator. Required by the current CLI workflow. |
| `GEMINI_MODEL` | Gemini model used for planning and evaluation. Configured as `gemini-2.0-flash`. |
| `BASE_URL` | Target application URL. Defaults to SauceDemo. |
| `HEADLESS` | Runs Playwright headlessly unless set to `false`, `0`, `no`, or `off`. |
| `DEFAULT_ISSUE` | Issue path or URL used when `--issue` is omitted. |

`.env` is ignored by Git. Do not commit API keys or other credentials.

## Running Tests

Run the full test suite:

```powershell
python -m pytest -vv
```

Run only the 22 Playwright UI tests:

```powershell
python -m pytest tests/test_purchase_flow.py -vv
```

Run the agent-layer unit tests:

```powershell
python -m pytest tests/test_agent_layer.py -q -p no:cacheprovider
```

Run an individual suite:

```powershell
python -m pytest tests/test_purchase_flow.py::TestLogin -vv
python -m pytest tests/test_purchase_flow.py::TestInventory -vv
python -m pytest tests/test_purchase_flow.py::TestCart -vv
python -m pytest tests/test_purchase_flow.py::TestCheckout -vv
python -m pytest tests/test_purchase_flow.py::TestFullPurchaseFlow -vv
```

Run a single test:

```powershell
python -m pytest tests/test_purchase_flow.py::TestFullPurchaseFlow::test_single_item_purchase -vv
```

The current UI suite contains 22 tests and passes when the required Chromium
browser is installed and SauceDemo is reachable.

## Running the Agent

Run the complete workflow:

```powershell
python main.py --issue issues/issue_001.md --status "Ready for QA"
```

If `DEFAULT_ISSUE` is configured, the issue argument may be omitted:

```powershell
python main.py --status "Ready for QA"
```

An explicit `--issue` takes precedence over `DEFAULT_ISSUE`.

Generate and print the plan without running Playwright:

```powershell
python main.py --issue issues/issue_001.md --plan-only
```

Use a public GitHub issue:

```powershell
python main.py --issue https://github.com/OWNER/REPOSITORY/issues/123
```

Private GitHub issue access requires `GITHUB_TOKEN`.

Expected console output includes:

- Gemini planning start, success, or fallback messages
- The generated `TestPlan` JSON
- Per-scenario Pytest output captured in evidence
- Gemini evaluation start, success, or fallback messages
- The final verdict JSON
- The location of `evidence/report.json`

Issues with a status other than `Ready for QA` or `RFQA` are skipped.

## Design Decisions

### Why Playwright

Playwright provides reliable browser automation, built-in waiting, accessible
locator APIs, screenshots, tracing, and strong Pytest integration. These
capabilities reduce custom synchronization code and support useful failure
diagnostics.

### Why Python?
Python was chosen because it supports both LLM orchestration and browser automation cleanly. It has mature SDK support for Gemini, strong Playwright bindings, fast prototyping, and readable syntax for a take-home assignment. The architecture is not Python-specific and could be ported to TypeScript, Java, or another automation stack.

### Why Planner / Executor / Evaluator

The three-stage architecture separates responsibilities:

- The planner decides what should be tested.
- The executor performs controlled, deterministic actions.
- The evaluator summarizes what actually happened.

This separation makes failures easier to diagnose and prevents model output
from being treated as execution evidence.

### Why semantic locators

Role, accessible-name, and visible-text locators describe the interface in
terms close to user behavior. They are generally more maintainable than
absolute XPath or DOM-structure selectors.

Some SauceDemo elements do not expose sufficient accessible semantics. In
those cases, page objects use scoped `data-test` selectors as explicit
fallbacks.

### Why allow-listed execution

Gemini selects scenario IDs, not commands or browser code. The executor only
accepts IDs defined in `agent/catalog.py`, each mapped to a reviewed Pytest
node ID. This limits the execution surface and makes AI-assisted planning safe,
repeatable, and auditable.

## Error Handling

### Gemini API failures

Network failures, service errors, timeouts, unsupported models, and other API
exceptions are caught at the planner and evaluator boundaries.

### Invalid model responses

Model responses are parsed and validated with Pydantic. Unknown scenario IDs,
empty plans, malformed JSON, and missing verdict text are treated as failures
rather than trusted input.

### Quota errors

HTTP `429 RESOURCE_EXHAUSTED` responses trigger the same graceful fallback
path. A project reporting a quota limit of zero still requires an eligible
Google AI project or billing configuration; retry logic cannot create quota.

### Graceful fallback behavior

- Planner failure: build a deterministic plan from allow-listed scenarios.
- Evaluator failure: retain all test evidence and return `REVIEW_REQUIRED`.
- UI test failure: record the return code, output, and artifact directory, then
  continue with the remaining planned scenarios.

This approach keeps infrastructure or LLM failures distinct from product
failures.

## Evidence and Reports

Sample execution evidence is committed under `/evidence` for reviewer
reference. It includes captured execution logs in `report.json`, sequential
screenshots, Playwright traces where available, and the final structured
report.

Each agent run creates a UTC timestamped directory:

```text
evidence/runs/<timestamp>/<sequence>_<test_id>/
```

Depending on the test outcome and Playwright settings, this directory contains:

- Full-page screenshots
- Retained Playwright traces for failures
- Pytest Playwright artifacts

Captured stdout and stderr are stored in the structured run evidence. The final
report is written to:

```text
evidence/report.json
```

The report contains:

```json
{
  "issue": {},
  "plan": {},
  "evidence": {},
  "verdict": {}
}
```

This structure connects the source issue, selected scenarios, observed results,
artifact locations, and final verdict.

## Implementation Coverage

| Requirement | Implementation |
|---|---|
| Read a Ready-for-QA issue | `agent/issue_reader.py` plus the `--status` RFQA gate in `main.py` |
| Generate a test plan | Gemini planner with Pydantic validation in `agent/planner.py` |
| Restrict executable actions | Scenario allow list in `agent/catalog.py` |
| Execute UI tests | Pytest and Playwright execution in `agent/executor.py` |
| Use maintainable automation design | Page Object Model under `pages/` |
| Prefer resilient locators | Semantic Playwright locators with scoped `data-test` fallbacks |
| Collect execution evidence | Screenshots, traces, return codes, output, and artifact paths |
| Generate a verdict | Gemini evaluator in `agent/evaluator.py` |
| Handle LLM outages | Deterministic planning and `REVIEW_REQUIRED` evaluation fallbacks |
| Support local configuration | `python-dotenv`, `.env.example`, and environment-driven settings |
| Produce a final report | Structured `evidence/report.json` |
| Demonstrate functional coverage | 22 UI tests across login, inventory, cart, checkout, purchase, and logout |

## Limitations

- Planning is constrained to predefined scenarios; the agent does not create
  new executable tests at runtime.
- The RFQA status is supplied through the CLI rather than received from a live
  GitHub Projects webhook.
- GitHub issue ingestion does not implement a complete GitHub App
  authentication and event lifecycle.
- The deterministic fallback uses keyword matching and is intentionally less
  nuanced than model-assisted planning.
- The evaluator summarizes functional evidence but does not perform image
  comparison or visual anomaly detection.
- Tests depend on SauceDemo availability and its current UI contract.
- Execution is currently local and sequential rather than distributed.
- The final CLI still requires `GEMINI_API_KEY`, even though runtime planner and
  evaluator fallbacks can handle Gemini request failures.

## Future Improvements

- Add vision-assisted UI exploration and screenshot analysis
- Generate reviewed test candidates dynamically before allow-list promotion
- Integrate GitHub webhooks or a GitHub App for real RFQA events
- Add GitHub Actions or another CI/CD execution workflow
- Run independent scenarios in parallel with isolated browser contexts
- Publish HTML or Allure reports alongside `report.json`
- Add retry policies with explicit transient-error classification
- Add visual regression baselines and accessibility scans
- Expand configuration validation and startup diagnostics
- Support additional applications and scenario catalogs
