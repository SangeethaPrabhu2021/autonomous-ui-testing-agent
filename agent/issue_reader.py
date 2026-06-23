import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

from agent.models import Issue


GITHUB_ISSUE_PATTERN = re.compile(
    r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)/?$"
)


def read_issue(source: str) -> Issue:
    match = GITHUB_ISSUE_PATTERN.fullmatch(source)
    if match:
        owner, repository, number = match.groups()
        return _read_github_issue(owner, repository, number, source)

    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"Issue file not found: {path}")

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Issue file is empty: {path}")

    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip()
    body = "\n".join(lines[1:]).strip() or title
    return Issue(title=title, body=body, source=str(path.resolve()))


def _read_github_issue(
    owner: str, repository: str, number: str, source: str
) -> Issue:
    url = f"https://api.github.com/repos/{owner}/{repository}/issues/{number}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "autonomous-ui-testing-agent",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with urlopen(Request(url, headers=headers), timeout=20) as response:
        payload = json.load(response)

    return Issue(
        title=payload["title"],
        body=payload.get("body") or "",
        source=source,
    )
