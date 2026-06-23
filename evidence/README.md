# Test Execution Evidence

This directory contains generated evidence from Autonomous UI Testing Agent
runs against SauceDemo.

## Contents

- `report.json` — final structured report containing the source issue, generated
  plan, captured Pytest output, scenario results, artifact paths, and verdict.
- `runs/<timestamp>/` — timestamped execution records grouped by scenario.
- `*.png` — full-page screenshots captured by Pytest Playwright after each
  executed scenario.
- `*.zip` — Playwright traces retained for failed or diagnostic runs. Open a
  trace with:

  ```powershell
  python -m playwright show-trace path\to\trace.zip
  ```

## Latest successful run

`20260623T132227Z` contains passing evidence for:

1. Successful standard-user login
2. Inventory page visibility
3. Adding the Sauce Labs Backpack and verifying the cart badge
4. Verifying the Backpack is present in the cart

The matching final result is stored in `report.json`.

## Notes

- Console execution output is embedded in each result within `report.json`.
- The current implementation captures sequential screenshots and Playwright
  traces; it does not record video.
- Evidence is intentionally committed for review. Future automated or
  high-volume runs should normally publish artifacts through CI storage rather
  than continuously adding binary files to Git history.
