"""
GitHub Integration Nodes - Interact with GitHub repositories.
"""

from typing import Any, Optional

from src.core.nodes.base import BaseNode, NodeField, FieldType


class GitHubCreateIssueNode(BaseNode):
    """
    Create GitHub issues.
    """

    type = "github-create-issue"
    name = "GitHub: Create Issue"
    category = "Apps"
    description = "Create a new GitHub issue"
    icon = "bug_report"
    color = "#24292E"  # GitHub dark

    inputs = [
        NodeField(
            name="token",
            label="GitHub Token",
            type=FieldType.SECRET,
            required=True,
            description="Personal access token with repo scope.",
        ),
        NodeField(
            name="owner",
            label="Repository Owner",
            type=FieldType.STRING,
            required=True,
            description="Repository owner (user or org).",
        ),
        NodeField(
            name="repo",
            label="Repository Name",
            type=FieldType.STRING,
            required=True,
            description="Repository name.",
        ),
        NodeField(
            name="title",
            label="Issue Title",
            type=FieldType.STRING,
            required=True,
            description="Title of the issue.",
        ),
        NodeField(
            name="body",
            label="Issue Body",
            type=FieldType.TEXT,
            required=False,
            description="Issue description (Markdown supported).",
        ),
        NodeField(
            name="labels",
            label="Labels",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated label names.",
        ),
        NodeField(
            name="assignees",
            label="Assignees",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated usernames to assign.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
        ),
        NodeField(
            name="issue_number",
            label="Issue Number",
            type=FieldType.NUMBER,
        ),
        NodeField(
            name="issue_url",
            label="Issue URL",
            type=FieldType.STRING,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Create GitHub issue."""
        import httpx

        token = config.get("token", "")
        owner = config.get("owner", "")
        repo = config.get("repo", "")
        title = config.get("title", "")
        body = config.get("body", "")
        labels = config.get("labels", "")
        assignees = config.get("assignees", "")

        url = f"https://api.github.com/repos/{owner}/{repo}/issues"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        payload = {"title": title}
        if body:
            payload["body"] = body
        if labels:
            payload["labels"] = [l.strip() for l in labels.split(",")]
        if assignees:
            payload["assignees"] = [a.strip() for a in assignees.split(",")]

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        if response.status_code == 201:
            return {
                "success": True,
                "issue_number": data.get("number", 0),
                "issue_url": data.get("html_url", ""),
            }

        return {
            "success": False,
            "issue_number": 0,
            "issue_url": "",
        }


class GitHubCreatePRNode(BaseNode):
    """
    Create GitHub pull requests.
    """

    type = "github-create-pr"
    name = "GitHub: Create Pull Request"
    category = "Apps"
    description = "Create a new pull request"
    icon = "merge_type"
    color = "#24292E"

    inputs = [
        NodeField(
            name="token",
            label="GitHub Token",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="owner",
            label="Repository Owner",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="repo",
            label="Repository Name",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="title",
            label="PR Title",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="body",
            label="PR Description",
            type=FieldType.TEXT,
            required=False,
        ),
        NodeField(
            name="head",
            label="Head Branch",
            type=FieldType.STRING,
            required=True,
            description="Branch with changes.",
        ),
        NodeField(
            name="base",
            label="Base Branch",
            type=FieldType.STRING,
            required=False,
            default="main",
            description="Branch to merge into.",
        ),
        NodeField(
            name="draft",
            label="Create as Draft",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
        ),
        NodeField(
            name="pr_number",
            label="PR Number",
            type=FieldType.NUMBER,
        ),
        NodeField(
            name="pr_url",
            label="PR URL",
            type=FieldType.STRING,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Create GitHub pull request."""
        import httpx

        token = config.get("token", "")
        owner = config.get("owner", "")
        repo = config.get("repo", "")
        title = config.get("title", "")
        body = config.get("body", "")
        head = config.get("head", "")
        base = config.get("base", "main")
        draft = config.get("draft", False)

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        payload = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft,
        }
        if body:
            payload["body"] = body

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        if response.status_code == 201:
            return {
                "success": True,
                "pr_number": data.get("number", 0),
                "pr_url": data.get("html_url", ""),
            }

        return {
            "success": False,
            "pr_number": 0,
            "pr_url": "",
        }


class GitHubListReposNode(BaseNode):
    """
    List repositories for a user or organization.
    """

    type = "github-list-repos"
    name = "GitHub: List Repositories"
    category = "Apps"
    description = "List repositories"
    icon = "folder"
    color = "#24292E"

    inputs = [
        NodeField(
            name="token",
            label="GitHub Token",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="type",
            label="Repository Type",
            type=FieldType.SELECT,
            required=False,
            default="owner",
            options=[
                {"value": "owner", "label": "My Repositories"},
                {"value": "user", "label": "User's Repositories"},
                {"value": "org", "label": "Organization Repositories"},
            ],
        ),
        NodeField(
            name="username",
            label="Username/Org",
            type=FieldType.STRING,
            required=False,
            description="Required for user/org type.",
        ),
        NodeField(
            name="per_page",
            label="Results Per Page",
            type=FieldType.NUMBER,
            required=False,
            default=30,
        ),
    ]

    outputs = [
        NodeField(
            name="repositories",
            label="Repositories",
            type=FieldType.JSON,
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List GitHub repositories."""
        import httpx

        token = config.get("token", "")
        repo_type = config.get("type", "owner")
        username = config.get("username", "")
        per_page = int(config.get("per_page", 30))

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        if repo_type == "owner":
            url = "https://api.github.com/user/repos"
        elif repo_type == "user":
            url = f"https://api.github.com/users/{username}/repos"
        else:  # org
            url = f"https://api.github.com/orgs/{username}/repos"

        params = {"per_page": per_page}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            repos = response.json()

        if isinstance(repos, list):
            return {
                "repositories": [
                    {
                        "name": r.get("name"),
                        "full_name": r.get("full_name"),
                        "description": r.get("description"),
                        "url": r.get("html_url"),
                        "stars": r.get("stargazers_count"),
                        "forks": r.get("forks_count"),
                        "private": r.get("private"),
                    }
                    for r in repos
                ],
                "count": len(repos),
            }

        return {
            "repositories": [],
            "count": 0,
        }
