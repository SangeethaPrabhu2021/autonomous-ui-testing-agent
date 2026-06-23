# Autonomous UI Testing Agent - Test Plan

## Executive Summary

This document outlines the technical strategy for an **Autonomous UI Testing Agent** that transforms GitHub RFQA (Ready for QA) issues into executable, end-to-end functional test scenarios. Rather than hardcoding test scripts, the agent leverages Large Language Models (LLMs) to intelligently plan, execute, and evaluate tests against dynamically identified UI elements using semantic locators.

The system achieves automation autonomy by:
- **Semantic understanding** via Gemini AI to map issue requirements to test scenarios
- **Semantic locators** to identify UI elements by user-facing properties (role, text, label) rather than brittle selectors
- **Dynamic test orchestration** that executes only the scenarios necessary to verify acceptance criteria
- **Evidence-driven reporting** that provides screenshots, execution logs, and structured verdicts

---

## Objective & Scope

### Objective
Enable automated functional testing of web applications by:
1. Ingesting GitHub issue descriptions as test requirements
2. Autonomously generating a test plan via LLM analysis
3. Executing only the necessary test scenarios in the correct order
4. Collecting evidence (screenshots, logs, traces)
5. Providing a structured pass/fail verdict

### Scope
**In Scope:**
- Multi-page e-commerce flows (SauceDemo)
- Login validation (success and error cases)
- Inventory browsing and product selection
- Shopping cart operations
- Checkout workflows
- Order completion
- Negative scenarios (invalid credentials, locked users, missing fields)
- Dynamic scenario selection based on issue requirements

**Out of Scope:**
- Performance testing
- Load testing
- Security vulnerability scanning
- Mobile-specific testing (desktop browser only)
- Visual regression testing
- API-level testing

---

## Assumptions & Constraints

### Assumptions
1. **Target application is publicly accessible** (or available via test environment URL)
2. **Application exposes stable, semantic accessibility attributes** (ARIA roles, labels, semantic HTML)
3. **Issues are well-formed** with clear acceptance criteria
4. **Test environment state is fresh** for each execution
5. **Gemini API key is configured** and available at runtime

### Constraints
1. **Scenario catalog is allowlisted** – the LLM planner can only select from pre-defined test IDs
2. **Single-threaded execution** – scenarios execute sequentially to avoid race conditions
3. **120-second timeout per scenario** – prevents hanging on unresponsive UI
4. **English-only issue parsing** – currently processes English language issues only
5. **No AI-driven self-healing** – failures are recorded as evidence and execution continues with the remaining planned scenarios

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                       Issue Input (GitHub/File)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Issue Reader (agent/issue_reader.py)                          │
│  - Parse markdown/GitHub API                                    │
│  - Extract title and acceptance criteria                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Planner (agent/planner.py)                                     │
│  - Send to Gemini: issue + allowed catalog                      │
│  - Receive: ordered test scenario list                          │
│  - Validate against TEST_CATALOG                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Executor (agent/executor.py)                                   │
│  - For each scenario in plan:                                   │
│    1. Resolve test_id to pytest node_id                         │
│    2. Launch pytest with Playwright                             │
│    3. Capture screenshots, traces, output                       │
│    4. Parse exit code (0=pass, non-zero=fail)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Evaluator (agent/evaluator.py)                                 │
│  - Analyze execution evidence                                   │
│  - Send to Gemini for verdict summarization                     │
│  - Generate pass/fail status + recommendations                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Report (evidence/report.json)                   │
│  - Issue metadata                                               │
│  - Generated plan                                               │
│  - Execution results (per scenario)                             │
│  - Final verdict + recommendations                              │
└─────────────────────────────────────────────────────────────────┘
```

### Key Modules

| Module | Responsibility |
|--------|---|
| `agent/issue_reader.py` | Parse GitHub/file issues; extract title and body |
| `agent/planner.py` | Invoke Gemini to map requirements to scenarios |
| `agent/executor.py` | Execute pytest scenarios; manage artifacts |
| `agent/evaluator.py` | Summarize results; generate verdict via Gemini |
| `agent/catalog.py` | Define allowed test scenarios |
| `agent/models.py` | Pydantic models for issue, plan, evidence, verdict |
| `tests/test_purchase_flow.py` | End-to-end Playwright test implementations |
| `pages/*.py` | Page Object Model for each application page |
| `main.py` | Orchestration entry point |

---

## Detailed Workflow

### 1. Issue Ingestion

**Input:** GitHub issue markdown or URL

**Process:**
```
Issue input (URL or file path)
    ↓
Match against GitHub URL pattern
    ↓
If GitHub URL: fetch via GitHub API (with GITHUB_TOKEN if available)
    If local file: read markdown
    ↓
Extract title (first line)
Extract body (remaining lines)
    ↓
Create Issue object: {title, body, source}
```

**Implementation:** `agent/issue_reader.py`
- Supports both `https://github.com/OWNER/REPO/issues/123` and local markdown paths
- Falls back to unauthenticated API calls; respects `GITHUB_TOKEN` env var for private repos
- Validates that issue is not empty before proceeding

**Example Input:**
```markdown
# Verify a standard user can add the Backpack to the cart

As a SauceDemo customer, I want to log in with the standard user and add the
Sauce Labs Backpack to my cart.

Acceptance criteria:
- Login succeeds.
- The inventory page is displayed.
- The Sauce Labs Backpack can be added.
- The cart badge shows one item.
- The cart contains the Sauce Labs Backpack.
```

---

### 2. LLM-Driven Planning

**Input:** Issue object + TEST_CATALOG

**Process:**

The planner sends a structured prompt to Gemini (or other LLM) with:
1. System instructions (PLANNER_INSTRUCTIONS)
2. Issue title and body
3. Allowlisted test catalog with descriptions

**Planner Instructions:**
```
You are a QA planning agent for SauceDemo.
Choose the smallest useful set of scenarios that verifies the issue.
You may only use exact test IDs from the supplied catalog.
Do not invent browser actions, selectors, commands, or test IDs.
Order scenarios from basic prerequisites to the main acceptance flow.
```

**LLM Response:** Structured JSON matching `TestPlan` schema:
```json
{
  "objective": "Verify that a standard user can successfully log in, view the inventory, add the Sauce Labs Backpack to the cart, and confirm it appears in the cart with the correct badge count.",
  "scenarios": [
    {
      "test_id": "login_success",
      "reason": "Verifies that the standard user can successfully log in as a prerequisite."
    },
    {
      "test_id": "inventory_visible",
      "reason": "Verifies that the inventory page is displayed with the expected products after logging in."
    },
    {
      "test_id": "add_backpack_to_cart",
      "reason": "Verifies that the Sauce Labs Backpack can be added and the cart badge updates to show one item."
    },
    {
      "test_id": "cart_contains_backpack",
      "reason": "Verifies that the cart actually contains the Sauce Labs Backpack once added."
    }
  ]
}
```

**Validation:**
- All returned `test_id` values must exist in `TEST_CATALOG`
- At least one scenario must be selected
- Response must be valid JSON matching the `TestPlan` schema

**Why This Approach:**
- **Prevents hallucination:** LLM cannot invent test IDs; constrained to catalog
- **Respects test order:** Planner orders scenarios logically (prerequisites first)
- **Aligns with requirements:** Explicit `reason` field traces each scenario to issue acceptance criteria
- **Cost-effective:** Uses Gemini (lightweight, fast LLM suitable for this task)

---

### 3. Scenario Execution

**Input:** TestPlan with ordered scenarios

**Process:**

For each scenario in the plan:

1. **Resolve test mapping**
   ```python
   test_id = "add_backpack_to_cart"
   node_id = TEST_CATALOG[test_id]["node_id"]
   # Result: "tests/test_purchase_flow.py::TestInventory::test_add_single_item_updates_cart_badge"
   ```

2. **Create artifact directory**
   ```
   evidence/runs/{timestamp}/{index:02d}_{test_id}/
   ```

3. **Execute pytest**
   ```powershell
   pytest {node_id} \
     -q \
     --screenshot=on \
     --full-page-screenshot \
     --tracing=retain-on-failure \
     --output={artifact_dir}
   ```

4. **Capture results**
   - Exit code (0 = pass, non-zero = fail)
   - stdout/stderr output
   - Artifact directory path (screenshots, traces)

5. **Record execution result**
   ```python
   ExecutionResult(
       test_id="add_backpack_to_cart",
       passed=True,
       return_code=0,
       output="... pytest output ...",
       artifact_directory="evidence/runs/.../03_add_backpack_to_cart"
   )
   ```

6. **Continue after failure**
   - Execute every planned allow-listed scenario
   - Record each scenario's exit code, logs, and artifact path
   - Preserve all failures for the final report

**Artifact Output:**
- `screenshot_*.png` – Full-page screenshots at test completion
- `trace.zip` – Playwright trace for debugging
- pytest output logs

---

### 4. Evidence Collection

**Collected During Execution:**

| Artifact | Purpose | Location |
|----------|---------|----------|
| Full-page screenshot | Visual proof of state | `{artifact_dir}/screenshot_*.png` |
| Playwright trace | Step-by-step browser interaction | `{artifact_dir}/trace.zip` |
| pytest output | Test execution logs | Captured in `ExecutionResult.output` |

**Structured Evidence Object:**
```python
RunEvidence(
    objective="...",
    passed=True/False,  # True iff ALL results.passed == True
    results=[ExecutionResult, ...]
)
```

---

### 5. Evaluation & Verdict

**Input:** RunEvidence

**Process:**

Evaluator sends evidence to Gemini with instructions:
```
You are a QA result evaluator.
Summarize the supplied execution evidence clearly and concisely.
Never mark the run passed when any executed scenario failed.
Do not claim that unexecuted behavior was verified.
```

**LLM Response:** Structured JSON matching `Verdict` schema:
```json
{
  "status": "passed",
  "summary": "All test scenarios passed successfully. Verified standard user login, inventory page visibility, adding the Sauce Labs Backpack to the cart, and verifying its presence in the cart.",
  "failed_scenarios": [],
  "recommendations": [
    "Proceed with testing checkout and payment flows next."
  ]
}
```

**Guardrails:**
- Evaluator explicitly sets `status` based on `evidence.passed` (not LLM choice)
- If any scenario failed, populate `failed_scenarios` with test IDs
- Prevents LLM from claiming unexecuted behavior was verified

---

## Locator Strategy: Semantic-First Approach

### Rationale
Traditional CSS/XPath selectors are brittle – they break when the DOM changes. Semantic locators are resilient because they query UI elements by **user-facing properties** rather than implementation details.

### Semantic Locator Hierarchy

**Priority 1: Accessibility-First (get_by_role)**
```python
# Instead of: page.locator("button[class*='login']")
button = page.get_by_role("button", name="Login", exact=True)
```
Advantages:
- Requires element to have a semantic role
- Aligns with accessibility best practices
- Reflects how users perceive the UI

**Priority 2: User-Visible Text (get_by_text)**
```python
# Instead of: page.locator(".product-card:has-text('Sauce Labs Backpack')")
product = page.get_by_text("Sauce Labs Backpack", exact=True)
```
Advantages:
- Matches visible product names
- Resilient to CSS/class changes
- Fails fast if text changes (alerts to breaking changes)

**Priority 3: Labeled Inputs (get_by_label)**
```python
# Instead of: page.locator("input[id='firstName']")
first_name = page.get_by_label("First Name", exact=True)
```
Advantages:
- Respects HTML `<label>` associations
- Semantic and accessible

**Priority 4: Placeholder (get_by_placeholder)**
```python
# Instead of: page.locator("input[placeholder='MM/DD/YYYY']")
date_input = page.get_by_placeholder("MM/DD/YYYY", exact=True)
```

**Priority 5: Data-Test-ID (Fallback Only)**
```python
# Use ONLY when semantic locators fail
locator = semantic_with_fallback(
    semantic=page.get_by_role("button", name="Add to cart"),
    fallback=page.get_by_test_id("add-to-cart-backpack"),
    description="Add to cart button for Backpack"
)
```

### Implementation: Semantic-with-Fallback Pattern

**File:** `pages/locators.py`

```python
def semantic_with_fallback(
    semantic: Locator,
    fallback: Locator,
    description: str,
) -> Locator:
    """Prefer a user-facing locator and use a stable test ID only if needed."""
    if semantic.count() == 1 and semantic.is_visible():
        LOGGER.info("Using semantic locator for %s", description)
        return semantic
    
    LOGGER.warning("Using data-test fallback for %s", description)
    return fallback
```

**Example from LoginPage:**
```python
def login(self, username: str, password: str):
    # Prefer semantic role-based locators
    semantic_with_fallback(
        self.username_input,  # page.get_by_role("textbox", name="Username")
        self.page.get_by_test_id("username"),  # Fallback to data-testid
        "username input"
    ).fill(username)
    
    # Log which approach was used
    # Result: "Using semantic locator for username input" (in normal case)
    # Result: "Using data-test fallback for username input" (if UI changed)
```

**Benefits:**
- Graceful degradation – falls back to test IDs if semantic approach fails
- Logging visibility – know when fallbacks are being used (signals UI changes)
- Reduced brittleness – tests self-adapt to minor DOM changes
- Accessibility compliance – validates app is accessible

---

## Error Handling & Recovery

### Error Categories

#### 1. Scenario Execution Failures

**When:** A Playwright test assertion fails or times out

**Handling:**
```python
# executor.py
completed = subprocess.run(
    [python, "-m", "pytest", node_id, ...],
    timeout=120,  # Kill after 120 seconds
)
return ExecutionResult(
    test_id=scenario.test_id,
    passed=completed.returncode == 0,  # 0 = pass, non-zero = fail
    return_code=completed.returncode,
    output=completed.stdout + completed.stderr,  # Full logs captured
    artifact_directory=str(artifact_dir)
)
```

**Current behavior:** Log the failure and continue to next scenario

**Detection in Evidence:** `passed=False` flag in ExecutionResult

---

#### 2. Locator Not Found

**When:** `get_by_role()` and fallback `get_by_test_id()` both fail to locate element

**Handling:**
```python
# pages/login.py
semantic_with_fallback(
    page.get_by_role("button", name="Login"),  # Fails if no such role exists
    page.get_by_test_id("login-button"),        # Fails if test ID removed
    "login button"
)
```

**Result:** Playwright throws `TimeoutError` → test fails → captured in logs → alerted to UI change

**Evidence:** Screenshot in artifact directory shows the unexpected UI state

---

#### 3. Unexpected Page State

**When:** Test navigates to wrong page or page fails to load

**Handling:**
```python
# pages/inventory_page.py
def assert_on_inventory_page(self):
    expect(self.page).to_have_url(self.URL)
    expect(self.title).to_be_visible()
    # Both assertions must pass; any failure stops test
```

**Result:** Assertion error with clear failure message

**Evidence:** Screenshot shows actual state; test output explains what was expected

---

#### 4. API Errors (Issue Reader)

**When:** GitHub API is unreachable or issue URL is malformed

**Handling:**
```python
# agent/issue_reader.py
try:
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        payload = json.load(response)
except URLError:
    raise RuntimeError(f"Failed to fetch GitHub issue from {source}")
```

**Result:** Graceful error message; prevents hanging on network issues

---

#### 5. Planner/Evaluator Hallucination

**When:** LLM returns invalid test_id or empty scenario list

**Handling:**
```python
# agent/planner.py
unknown = [
    scenario.test_id
    for scenario in plan.scenarios
    if scenario.test_id not in TEST_CATALOG
]
if unknown:
    raise ValueError(f"Planner selected unknown test IDs: {unknown}")
if not plan.scenarios:
    raise ValueError("Planner returned an empty test plan.")
```

**Result:** Fail fast with clear error message instead of attempting invalid tests

---

### Recovery Strategy

**Current behavior: Continue on failure**

1. Execute each planned allow-listed scenario in order.
2. If a scenario fails, capture its exit code, logs, screenshot, trace, and
   artifact path where available.
3. Mark that scenario as failed and continue to the next planned scenario.
4. Include every failed scenario in the final evidence and verdict.
5. Derive the final status from observed execution results so a failed scenario
   cannot produce a false PASS.

Automated locator repair or AI-driven self-healing is not implemented. It is a
possible future improvement, not current recovery behavior.

### Concrete Failure Walkthrough

Example: an expected element cannot be located or a Playwright assertion fails.

1. Playwright waits until the locator or assertion timeout is reached.
2. Pytest returns a non-zero exit code for the scenario.
3. The executor records the failure reason from stdout/stderr and the scenario's
   artifact directory.
4. Pytest Playwright captures a screenshot and retains a trace when available.
5. The executor continues with the next scenario in the finite test plan.
6. The final report lists the failed scenario, failure output, and evidence
   path; the evaluator is not permitted to convert the run to PASS.

### Loop Prevention Strategy

- Gemini cannot execute browser actions, shell commands, or arbitrary code.
- Gemini can only select scenario IDs from the allow-listed catalog.
- Unknown, invalid, empty, or unsupported scenario selections are rejected or
  handled through the deterministic allow-listed fallback plan.
- Each selected scenario maps to a finite Pytest/Playwright implementation.
- Every scenario process has a fixed 120-second timeout.
- Scenarios execute sequentially once; there is no recursive planning,
  re-planning, or retry loop.
- The executor completes after the finite scenario list is exhausted.

These constraints guarantee termination even when LLM output is incomplete or
imperfect.

---

## Browser & Test Execution Environment

### Playwright Configuration

**Browser:** Chromium (via Playwright)

**Headless Mode:** Yes (no visual display during execution)

**Timeout:** 120 seconds per scenario

**Screenshot:** Full page at test completion

**Tracing:** Retained on failure (allows debugging)

```bash
pytest tests/test_purchase_flow.py::TestLogin::test_successful_login \
  -q \
  --screenshot=on \
  --full-page-screenshot \
  --tracing=retain-on-failure \
  --output=evidence/runs/20260621T201656Z/01_login_success
```

### Test Environment (SauceDemo)

**URL:** `https://www.saucedemo.com/`

**Credentials:** 
- Standard user: `standard_user` / `secret_sauce`
- Locked user: `locked_out_user` / `secret_sauce`

**State:** Fresh state per test (isolated runs; no cross-test pollution)

---

## Reporting & Verdict Generation

### Report Structure (`evidence/report.json`)

```json
{
  "issue": {
    "title": "Verify a standard user can add the Backpack to the cart",
    "body": "As a SauceDemo customer, ...",
    "source": "issues/issue_001.md"
  },
  "plan": {
    "objective": "Verify that a standard user...",
    "scenarios": [
      {"test_id": "login_success", "reason": "..."},
      {"test_id": "inventory_visible", "reason": "..."}
    ]
  },
  "evidence": {
    "objective": "...",
    "passed": true,
    "results": [
      {
        "test_id": "login_success",
        "passed": true,
        "return_code": 0,
        "output": "1 passed in 6.35s",
        "artifact_directory": "evidence/runs/.../01_login_success"
      }
    ]
  },
  "verdict": {
    "status": "passed",
    "summary": "All test scenarios passed successfully. Verified...",
    "failed_scenarios": [],
    "recommendations": ["Proceed with testing checkout and payment flows next."]
  }
}
```

### Report Interpretation

**Status = "passed":**
- All scenarios executed successfully
- All acceptance criteria verified
- Safe to proceed with feature deployment

**Status = "failed":**
- One or more scenarios failed
- `failed_scenarios` lists which ones
- Issue recommendations for fixes
- May require UI changes or issue clarification

---

## Handling Unexpected UI States

### Scenario: UI Element Not Found
**Symptom:** Semantic locator returns 0 elements

**Agent Response:**
1. Fallback locator is attempted
2. If both fail, test assertion raises `PlaywrightException`
3. Test marked as failed
4. Screenshot captures unexpected UI state
5. Error message logged: "Could not locate [element description]"

**Evidence:** Screenshot, trace, and error logs clearly show what went wrong

---

### Scenario: Wrong Page Navigation
**Symptom:** Expected URL doesn't match actual URL

**Agent Response:**
```python
expect(self.page).to_have_url(self.URL)  # Assertion fails
# Playwright stops test, captures screenshot of actual page
```

**Evidence:** Screenshot shows actual page; message indicates expected vs. actual URL

---

### Scenario: Timing Issue (Element Not Ready)
**Symptom:** Element exists but is not visible/enabled

**Agent Response:**
```python
expect(button).to_be_visible()  # Waits up to timeout (default 30s)
# If not visible after timeout, test fails
```

**Evidence:** Screenshot captures state at timeout; trace shows when element appeared/disappeared

---

## Future Improvements

### Future: Self-Healing Mechanism
- **Goal:** Automatically recover from minor UI changes
- **Approach:** After locator failure, attempt alternative locators; log recovery
- **Benefit:** Reduce false negatives from cosmetic UI changes

### Future: Webhook Integration
- **Goal:** Trigger agent automatically when issue moves to "RFQA" column
- **Approach:** GitHub Project webhook → local Flask server → agent invocation
- **Benefit:** True CI/CD integration; zero-latency test triggering

### v3: Multi-LLM Support
- **Current:** Gemini only
- **Proposed:** Support Claude, GPT-4o, Llama for cost/latency optimization
- **Benefit:** No vendor lock-in; choose best model per use case

### v3: Parallel Scenario Execution
- **Current:** Sequential execution only
- **Proposed:** Execute independent scenarios concurrently (e.g., login tests don't interfere with cart tests in different sessions)
- **Benefit:** Faster execution for large test plans

### v3: Intelligent Scenario Caching
- **Goal:** Reuse execution results from prior runs if issue requirements haven't changed
- **Approach:** Hash issue + compute coverage fingerprint; cache verdicts
- **Benefit:** Instant feedback for re-runs without UI interaction

### v3: Visual Change Detection
- **Goal:** Flag visual regressions automatically
- **Approach:** Compare screenshots against baseline using image diffing
- **Benefit:** Catch unintended CSS/layout breaks

### v4: Autonomous Debugging
- **Goal:** When a scenario fails, agent generates targeted mini-tests to isolate root cause
- **Approach:** LLM generates alternative test paths to narrow down failure
- **Benefit:** Reduce manual debugging time

---

## Conclusion

This test plan describes an **autonomous, LLM-guided functional testing agent** that:

1. **Understands requirements** via semantic analysis of GitHub issues
2. **Plans intelligently** by mapping requirements to a curated scenario catalog
3. **Executes reliably** using semantic locators with intelligent fallbacks
4. **Handles errors gracefully** with comprehensive logging and evidence capture
5. **Reports clearly** via structured JSON verdicts and actionable recommendations

The system prioritizes **autonomy** (minimal human intervention), **resilience** (semantic locators, error recovery), and **traceability** (comprehensive evidence and logs) to create a production-ready QA automation platform.

---

## Appendix: Configuration

### Environment Variables
```powershell
$env:GEMINI_API_KEY = "your-api-key"        # Required
$env:GEMINI_MODEL = "gemini-2.0-flash"      # Optional, configured model
$env:GITHUB_TOKEN = "your-github-token"     # Optional (private repos)
```

### Dependencies
```
google-genai        # Gemini API
playwright          # Browser automation
pytest              # Test framework
pytest-playwright   # Pytest + Playwright integration
pydantic            # Data validation
```

### Running the Agent
```powershell
python main.py --issue issues/issue_001.md
python main.py --issue https://github.com/owner/repo/issues/123
python main.py --issue issues/issue_001.md --plan-only  # See plan without executing
```

---

**Document Version:** 1.0  
**Date:** 2026-06-23  
**Status:** Complete
