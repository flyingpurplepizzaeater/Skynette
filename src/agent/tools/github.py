"""
GitHub Integration Tool

Interact with GitHub: create repos, manage files, create issues/PRs using PyGithub.
"""

import asyncio
import base64
import logging
import os
import time
from typing import Any

from src.agent.models.tool import ToolResult
from src.agent.registry.base_tool import AgentContext, BaseTool

logger = logging.getLogger(__name__)


class GitHubTool(BaseTool):
    """Interact with GitHub repositories, files, issues, and pull requests."""

    name = "github"
    description = (
        "Interact with GitHub: create repos, manage files, create issues/PRs. "
        "Requires GITHUB_TOKEN env var or token parameter. "
        "Actions: create_repo, list_repos, create_file, update_file, get_file, create_issue, create_pr."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "create_repo",
                    "list_repos",
                    "create_file",
                    "update_file",
                    "get_file",
                    "create_issue",
                    "create_pr",
                ],
                "description": "GitHub action to perform",
            },
            "token": {
                "type": "string",
                "description": "GitHub Personal Access Token (or use GITHUB_TOKEN env var)",
            },
            "owner": {
                "type": "string",
                "description": "Repository owner (user or org)",
            },
            "repo": {
                "type": "string",
                "description": "Repository name",
            },
            "name": {
                "type": "string",
                "description": "Name for new repo or file path",
            },
            "content": {
                "type": "string",
                "description": "File content or issue/PR body",
            },
            "message": {
                "type": "string",
                "description": "Commit message",
            },
            "title": {
                "type": "string",
                "description": "Issue or PR title",
            },
            "branch": {
                "type": "string",
                "description": "Branch name (default: main)",
                "default": "main",
            },
            "private": {
                "type": "boolean",
                "description": "Make repo private",
                "default": False,
            },
            "head": {
                "type": "string",
                "description": "Head branch for PR (branch with changes)",
            },
            "base": {
                "type": "string",
                "description": "Base branch for PR (branch to merge into)",
                "default": "main",
            },
            "description": {
                "type": "string",
                "description": "Repository description (for create_repo)",
            },
        },
        "required": ["action"],
    }
    is_destructive = True  # Can modify repositories

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Execute GitHub action."""
        start = time.perf_counter()

        action = params.get("action")
        token = params.get("token") or os.environ.get("GITHUB_TOKEN")

        if not token:
            return ToolResult.failure_result(
                tool_call_id=context.session_id,
                error="GitHub token required: provide 'token' parameter or set GITHUB_TOKEN env var",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        try:
            from github import Auth, Github, GithubException
        except ImportError:
            return ToolResult.failure_result(
                tool_call_id=context.session_id,
                error="PyGithub not installed. Run: pip install PyGithub",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        try:
            if action == "create_repo":
                result = await self._create_repo(token, params)
            elif action == "list_repos":
                result = await self._list_repos(token, params)
            elif action == "create_file":
                result = await self._create_file(token, params)
            elif action == "update_file":
                result = await self._update_file(token, params)
            elif action == "get_file":
                result = await self._get_file(token, params)
            elif action == "create_issue":
                result = await self._create_issue(token, params)
            elif action == "create_pr":
                result = await self._create_pr(token, params)
            else:
                return ToolResult.failure_result(
                    tool_call_id=context.session_id,
                    error=f"Unknown action: {action}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                )

            return ToolResult.success_result(
                tool_call_id=context.session_id,
                data=result,
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        except Exception as e:
            error_msg = str(e)
            # Extract message from GithubException if available
            if hasattr(e, "data") and isinstance(e.data, dict):
                error_msg = e.data.get("message", str(e))
            logger.error(f"GitHub error: {e}", exc_info=True)
            return ToolResult.failure_result(
                tool_call_id=context.session_id,
                error=f"GitHub error: {error_msg}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    async def _create_repo(self, token: str, params: dict) -> dict[str, Any]:
        """Create a new repository."""
        from github import Auth, Github

        name = params.get("name")
        if not name:
            raise ValueError("Repository name required")

        description = params.get("description", params.get("content", ""))
        private = params.get("private", False)

        def _do_create():
            g = Github(auth=Auth.Token(token))
            user = g.get_user()
            repo = user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=True,
            )
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.html_url,
                "clone_url": repo.clone_url,
                "private": repo.private,
            }

        return await asyncio.to_thread(_do_create)

    async def _list_repos(self, token: str, params: dict) -> list[dict[str, Any]]:
        """List repositories for authenticated user."""
        from github import Auth, Github

        def _do_list():
            g = Github(auth=Auth.Token(token))
            user = g.get_user()
            repos = list(user.get_repos())[:30]  # Limit to 30
            return [
                {
                    "name": r.name,
                    "full_name": r.full_name,
                    "url": r.html_url,
                    "description": r.description,
                    "private": r.private,
                    "stars": r.stargazers_count,
                    "forks": r.forks_count,
                }
                for r in repos
            ]

        return await asyncio.to_thread(_do_list)

    async def _create_file(self, token: str, params: dict) -> dict[str, Any]:
        """Create a new file in repository."""
        from github import Auth, Github

        owner = params.get("owner")
        repo_name = params.get("repo")
        file_path = params.get("name")
        content = params.get("content", "")
        message = params.get("message", f"Create {file_path}")
        branch = params.get("branch", "main")

        if not all([owner, repo_name, file_path]):
            raise ValueError("owner, repo, and name (file path) required")

        def _do_create():
            g = Github(auth=Auth.Token(token))
            repo = g.get_repo(f"{owner}/{repo_name}")
            result = repo.create_file(
                path=file_path,
                message=message,
                content=content,
                branch=branch,
            )
            return {
                "path": file_path,
                "sha": result["commit"].sha,
                "url": result["content"].html_url,
            }

        return await asyncio.to_thread(_do_create)

    async def _update_file(self, token: str, params: dict) -> dict[str, Any]:
        """Update an existing file in repository."""
        from github import Auth, Github

        owner = params.get("owner")
        repo_name = params.get("repo")
        file_path = params.get("name")
        content = params.get("content", "")
        message = params.get("message", f"Update {file_path}")
        branch = params.get("branch", "main")

        if not all([owner, repo_name, file_path]):
            raise ValueError("owner, repo, and name (file path) required")

        def _do_update():
            g = Github(auth=Auth.Token(token))
            repo = g.get_repo(f"{owner}/{repo_name}")
            # Get current file to get SHA
            file = repo.get_contents(file_path, ref=branch)
            result = repo.update_file(
                path=file_path,
                message=message,
                content=content,
                sha=file.sha,
                branch=branch,
            )
            return {
                "path": file_path,
                "sha": result["commit"].sha,
                "url": result["content"].html_url,
            }

        return await asyncio.to_thread(_do_update)

    async def _get_file(self, token: str, params: dict) -> dict[str, Any]:
        """Get file content from repository."""
        from github import Auth, Github

        owner = params.get("owner")
        repo_name = params.get("repo")
        file_path = params.get("name")
        branch = params.get("branch", "main")

        if not all([owner, repo_name, file_path]):
            raise ValueError("owner, repo, and name (file path) required")

        def _do_get():
            g = Github(auth=Auth.Token(token))
            repo = g.get_repo(f"{owner}/{repo_name}")
            file = repo.get_contents(file_path, ref=branch)
            # Decode content from base64
            content = base64.b64decode(file.content).decode("utf-8")
            return {
                "path": file.path,
                "content": content,
                "sha": file.sha,
                "url": file.html_url,
                "size": file.size,
            }

        return await asyncio.to_thread(_do_get)

    async def _create_issue(self, token: str, params: dict) -> dict[str, Any]:
        """Create an issue in repository."""
        from github import Auth, Github

        owner = params.get("owner")
        repo_name = params.get("repo")
        title = params.get("title")
        body = params.get("content", "")

        if not all([owner, repo_name, title]):
            raise ValueError("owner, repo, and title required")

        def _do_create():
            g = Github(auth=Auth.Token(token))
            repo = g.get_repo(f"{owner}/{repo_name}")
            issue = repo.create_issue(
                title=title,
                body=body,
            )
            return {
                "number": issue.number,
                "url": issue.html_url,
                "title": issue.title,
            }

        return await asyncio.to_thread(_do_create)

    async def _create_pr(self, token: str, params: dict) -> dict[str, Any]:
        """Create a pull request in repository."""
        from github import Auth, Github

        owner = params.get("owner")
        repo_name = params.get("repo")
        title = params.get("title")
        body = params.get("content", "")
        head = params.get("head")
        base = params.get("base", "main")

        if not all([owner, repo_name, title, head]):
            raise ValueError("owner, repo, title, and head (branch) required")

        def _do_create():
            g = Github(auth=Auth.Token(token))
            repo = g.get_repo(f"{owner}/{repo_name}")
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
            )
            return {
                "number": pr.number,
                "url": pr.html_url,
                "title": pr.title,
                "state": pr.state,
            }

        return await asyncio.to_thread(_do_create)
