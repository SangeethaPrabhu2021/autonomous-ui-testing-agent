# Autonomous UI Testing Agent

This project turns an issue into an evidence-backed SauceDemo test run:

```text
Issue -> Gemini test plan -> allowlisted pytest/Playwright tests
      -> screenshots and traces -> Gemini verdict -> JSON report
```

The model plans and evaluates. It cannot execute arbitrary commands or freely
navigate the site; execution is restricted to the scenarios in
`agent/catalog.py`.

## Setup

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder `GEMINI_API_KEY` with your real key.
The file also configures the Gemini model, target URL, browser visibility, and
default issue:

```dotenv
GEMINI_API_KEY=replace-with-your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
BASE_URL=https://www.saucedemo.com/
HEADLESS=true
DEFAULT_ISSUE=issues/issue_001.md
```

`.env` is ignored by Git. Never commit real API keys.

If Gemini planning is unavailable because of a model outage, quota limit, or
invalid response, the agent uses a deterministic allowlisted test plan and
continues the UI run. A quota response with a limit of `0` still requires an
eligible Google AI project or billing configuration.

## Run

```powershell
python main.py --issue issues/issue_001.md
```

When `DEFAULT_ISSUE` is configured in `.env`, `--issue` may be omitted:

```powershell
python main.py
```

An explicit `--issue` always overrides `DEFAULT_ISSUE`, preserving existing
CLI usage.

Generate only the Gemini plan:

```powershell
python main.py --issue issues/issue_001.md --plan-only
```

Or provide a public GitHub issue URL:

```powershell
python main.py --issue https://github.com/OWNER/REPO/issues/123
```

For private repositories, set `GITHUB_TOKEN`. The final report is written to
`evidence/report.json`; screenshots and traces are stored under
`evidence/runs/`.

### RFQA (Ready for QA) Trigger

The agent respects a `--status` argument that simulates a GitHub Project card being moved to the "Ready for QA" column. Only when an issue has this status will the agent proceed with test execution.

**Example: Run tests only if issue is RFQA**
```powershell
python main.py --issue issues/issue_001.md --status "Ready for QA"
```

**Example: Issue not ready for QA (agent skips execution)**
```powershell
python main.py --issue issues/issue_001.md --status "In Progress"
# Output: ⏭️  Issue status 'In Progress' is not 'Ready for QA'.
#         Agent will begin testing only when the issue is moved to the 'Ready for QA' column.
```

**Accepted status values:**
- `"Ready for QA"` (default)
- `"RFQA"`

**Use Case - GitHub Project Automation:**

In a production environment, this entry point would be triggered by:
- **GitHub Webhook** – Listen for project card movement events
- **GitHub Actions** – Use `repository_dispatch` event when card moves to "Ready for QA"
- **GitHub App** – Custom app monitoring project board changes

Example workflow that could trigger this agent:
```yaml
name: Run QA Tests on RFQA
on:
  repository_dispatch:
    types: [issue-ready-for-qa]
    
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run autonomous QA agent
        run: |
          python main.py \
            --issue "https://github.com/${{ github.repository }}/issues/${{ github.event.client_payload.issue_number }}" \
            --status "Ready for QA"
```

For now, the `--status` argument allows local simulation and testing of the RFQA workflow.
