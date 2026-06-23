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
$env:GEMINI_API_KEY="your-api-key"
```

Optionally select a different model:

```powershell
$env:GEMINI_MODEL="gemini-3.5-flash"
```

## Run

```powershell
python main.py --issue issues/issue_001.md
```

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
