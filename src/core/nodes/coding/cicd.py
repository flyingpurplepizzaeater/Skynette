"""
CI/CD Integration Nodes - Continuous integration and deployment automation.
"""

import asyncio

from src.core.nodes.base import BaseNode, FieldType, NodeField


class GitHubActionsNode(BaseNode):
    """Trigger GitHub Actions workflow."""

    type = "github-actions"
    name = "CI/CD: GitHub Actions"
    category = "Coding"
    description = "Trigger or monitor GitHub Actions workflows"
    icon = "play_circle"
    color = "#2088FF"

    inputs = [
        NodeField(name="token", label="GitHub Token", type=FieldType.SECRET, required=True),
        NodeField(name="owner", label="Repository Owner", type=FieldType.STRING, required=True),
        NodeField(name="repo", label="Repository Name", type=FieldType.STRING, required=True),
        NodeField(
            name="action",
            label="Action",
            type=FieldType.SELECT,
            required=True,
            default="trigger",
            options=[
                {"value": "trigger", "label": "Trigger Workflow"},
                {"value": "status", "label": "Get Workflow Status"},
                {"value": "list", "label": "List Workflows"},
                {"value": "cancel", "label": "Cancel Run"},
            ],
        ),
        NodeField(
            name="workflow_id", label="Workflow ID/Filename", type=FieldType.STRING, required=False
        ),
        NodeField(
            name="ref", label="Branch/Tag", type=FieldType.STRING, required=False, default="main"
        ),
        NodeField(name="inputs", label="Workflow Inputs", type=FieldType.JSON, required=False),
        NodeField(name="run_id", label="Run ID", type=FieldType.STRING, required=False),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="run_id", label="Run ID", type=FieldType.STRING),
        NodeField(name="status", label="Status", type=FieldType.STRING),
        NodeField(name="conclusion", label="Conclusion", type=FieldType.STRING),
        NodeField(name="url", label="Workflow URL", type=FieldType.STRING),
        NodeField(name="workflows", label="Workflows", type=FieldType.JSON),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        import httpx

        token = config.get("token", "")
        owner = config.get("owner", "")
        repo = config.get("repo", "")
        action = config.get("action", "trigger")
        workflow_id = config.get("workflow_id", "")
        ref = config.get("ref", "main")
        inputs = config.get("inputs", {})
        run_id = config.get("run_id", "")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        base_url = f"https://api.github.com/repos/{owner}/{repo}"

        async with httpx.AsyncClient() as client:
            try:
                if action == "trigger":
                    url = f"{base_url}/actions/workflows/{workflow_id}/dispatches"
                    payload = {"ref": ref}
                    if inputs:
                        payload["inputs"] = inputs

                    response = await client.post(url, json=payload, headers=headers)

                    if response.status_code == 204:
                        return {
                            "success": True,
                            "run_id": "",
                            "status": "queued",
                            "conclusion": "",
                            "url": f"https://github.com/{owner}/{repo}/actions",
                            "workflows": [],
                        }

                    return {
                        "success": False,
                        "run_id": "",
                        "status": "failed",
                        "conclusion": "",
                        "url": "",
                        "workflows": [],
                    }

                elif action == "status":
                    if run_id:
                        url = f"{base_url}/actions/runs/{run_id}"
                    else:
                        url = f"{base_url}/actions/runs?per_page=1"

                    response = await client.get(url, headers=headers)
                    data = response.json()

                    if run_id:
                        run_data = data
                    else:
                        runs = data.get("workflow_runs", [])
                        run_data = runs[0] if runs else {}

                    return {
                        "success": True,
                        "run_id": str(run_data.get("id", "")),
                        "status": run_data.get("status", ""),
                        "conclusion": run_data.get("conclusion", ""),
                        "url": run_data.get("html_url", ""),
                        "workflows": [],
                    }

                elif action == "list":
                    url = f"{base_url}/actions/workflows"
                    response = await client.get(url, headers=headers)
                    data = response.json()

                    workflows = [
                        {
                            "id": w.get("id"),
                            "name": w.get("name"),
                            "state": w.get("state"),
                            "path": w.get("path"),
                        }
                        for w in data.get("workflows", [])
                    ]

                    return {
                        "success": True,
                        "run_id": "",
                        "status": "",
                        "conclusion": "",
                        "url": f"https://github.com/{owner}/{repo}/actions",
                        "workflows": workflows,
                    }

                elif action == "cancel":
                    url = f"{base_url}/actions/runs/{run_id}/cancel"
                    response = await client.post(url, headers=headers)

                    return {
                        "success": response.status_code == 202,
                        "run_id": run_id,
                        "status": "cancelled",
                        "conclusion": "",
                        "url": "",
                        "workflows": [],
                    }

            except Exception as e:
                return {
                    "success": False,
                    "run_id": "",
                    "status": "error",
                    "conclusion": str(e),
                    "url": "",
                    "workflows": [],
                }

        return {
            "success": False,
            "run_id": "",
            "status": "",
            "conclusion": "",
            "url": "",
            "workflows": [],
        }


class WaitForCINode(BaseNode):
    """Wait for CI/CD pipeline to complete."""

    type = "wait-for-ci"
    name = "CI/CD: Wait for Completion"
    category = "Coding"
    description = "Wait for CI/CD pipeline to complete with polling"
    icon = "hourglass_full"
    color = "#2088FF"

    inputs = [
        NodeField(name="token", label="API Token", type=FieldType.SECRET, required=True),
        NodeField(
            name="provider",
            label="CI Provider",
            type=FieldType.SELECT,
            required=True,
            default="github",
            options=[
                {"value": "github", "label": "GitHub Actions"},
                {"value": "gitlab", "label": "GitLab CI"},
                {"value": "circleci", "label": "CircleCI"},
            ],
        ),
        NodeField(name="owner", label="Owner/Org", type=FieldType.STRING, required=True),
        NodeField(name="repo", label="Repository", type=FieldType.STRING, required=True),
        NodeField(name="run_id", label="Run/Pipeline ID", type=FieldType.STRING, required=False),
        NodeField(
            name="timeout",
            label="Timeout (seconds)",
            type=FieldType.NUMBER,
            required=False,
            default=600,
        ),
        NodeField(
            name="poll_interval",
            label="Poll Interval (seconds)",
            type=FieldType.NUMBER,
            required=False,
            default=30,
        ),
    ]

    outputs = [
        NodeField(name="completed", label="Completed", type=FieldType.BOOLEAN),
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="status", label="Final Status", type=FieldType.STRING),
        NodeField(name="conclusion", label="Conclusion", type=FieldType.STRING),
        NodeField(name="duration", label="Duration (seconds)", type=FieldType.NUMBER),
        NodeField(name="url", label="Pipeline URL", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        import time

        import httpx

        token = config.get("token", "")
        provider = config.get("provider", "github")
        owner = config.get("owner", "")
        repo = config.get("repo", "")
        run_id = config.get("run_id", "")
        timeout = int(config.get("timeout", 600))
        poll_interval = int(config.get("poll_interval", 30))

        start_time = time.time()
        elapsed = 0

        async with httpx.AsyncClient() as client:
            while elapsed < timeout:
                try:
                    if provider == "github":
                        if run_id:
                            url = (
                                f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}"
                            )
                        else:
                            url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=1"

                        headers = {
                            "Authorization": f"Bearer {token}",
                            "Accept": "application/vnd.github+json",
                        }

                        response = await client.get(url, headers=headers)
                        data = response.json()

                        if not run_id:
                            runs = data.get("workflow_runs", [])
                            data = runs[0] if runs else {}

                        status = data.get("status", "")
                        conclusion = data.get("conclusion", "")
                        html_url = data.get("html_url", "")

                        if status == "completed":
                            return {
                                "completed": True,
                                "success": conclusion == "success",
                                "status": status,
                                "conclusion": conclusion,
                                "duration": int(time.time() - start_time),
                                "url": html_url,
                            }

                    elif provider == "gitlab":
                        url = f"https://gitlab.com/api/v4/projects/{owner}%2F{repo}/pipelines/{run_id}"
                        headers = {"PRIVATE-TOKEN": token}

                        response = await client.get(url, headers=headers)
                        data = response.json()

                        status = data.get("status", "")
                        if status in ["success", "failed", "canceled", "skipped"]:
                            return {
                                "completed": True,
                                "success": status == "success",
                                "status": status,
                                "conclusion": status,
                                "duration": int(time.time() - start_time),
                                "url": data.get("web_url", ""),
                            }

                except Exception:
                    pass  # Continue polling

                await asyncio.sleep(poll_interval)
                elapsed = time.time() - start_time

        return {
            "completed": False,
            "success": False,
            "status": "timeout",
            "conclusion": f"Timed out after {timeout} seconds",
            "duration": int(elapsed),
            "url": "",
        }


class NPMPublishNode(BaseNode):
    """Publish package to NPM."""

    type = "npm-publish"
    name = "CI/CD: NPM Publish"
    category = "Coding"
    description = "Publish package to NPM registry"
    icon = "publish"
    color = "#CB3837"

    inputs = [
        NodeField(name="project_path", label="Project Path", type=FieldType.STRING, required=True),
        NodeField(name="npm_token", label="NPM Token", type=FieldType.SECRET, required=True),
        NodeField(name="tag", label="Tag", type=FieldType.STRING, required=False, default="latest"),
        NodeField(
            name="access",
            label="Access",
            type=FieldType.SELECT,
            required=False,
            default="public",
            options=[
                {"value": "public", "label": "Public"},
                {"value": "restricted", "label": "Restricted"},
            ],
        ),
        NodeField(
            name="dry_run", label="Dry Run", type=FieldType.BOOLEAN, required=False, default=False
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="package", label="Package Name", type=FieldType.STRING),
        NodeField(name="version", label="Version", type=FieldType.STRING),
        NodeField(name="output", label="Output", type=FieldType.TEXT),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        import json
        import subprocess
        from pathlib import Path

        project_path = config.get("project_path", "")
        npm_token = config.get("npm_token", "")
        tag = config.get("tag", "latest")
        access = config.get("access", "public")
        dry_run = config.get("dry_run", False)

        loop = asyncio.get_event_loop()

        def publish():
            # Read package.json
            pkg_path = Path(project_path) / "package.json"
            if pkg_path.exists():
                with open(pkg_path) as f:
                    pkg = json.load(f)
                    package_name = pkg.get("name", "")
                    version = pkg.get("version", "")
            else:
                return {
                    "success": False,
                    "package": "",
                    "version": "",
                    "output": "",
                    "error": "package.json not found",
                }

            # Set up npm auth
            npmrc_path = Path(project_path) / ".npmrc"
            npmrc_path.write_text(f"//registry.npmjs.org/:_authToken={npm_token}\n")

            try:
                cmd = ["npm", "publish", f"--tag={tag}", f"--access={access}"]
                if dry_run:
                    cmd.append("--dry-run")

                result = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=project_path, timeout=120
                )

                return {
                    "success": result.returncode == 0,
                    "package": package_name,
                    "version": version,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else "",
                }
            finally:
                # Clean up npmrc
                if npmrc_path.exists():
                    npmrc_path.unlink()

        try:
            return await loop.run_in_executor(None, publish)
        except Exception as e:
            return {
                "success": False,
                "package": "",
                "version": "",
                "output": "",
                "error": str(e),
            }


class PyPIPublishNode(BaseNode):
    """Publish package to PyPI."""

    type = "pypi-publish"
    name = "CI/CD: PyPI Publish"
    category = "Coding"
    description = "Publish package to PyPI"
    icon = "publish"
    color = "#3776AB"

    inputs = [
        NodeField(name="project_path", label="Project Path", type=FieldType.STRING, required=True),
        NodeField(name="pypi_token", label="PyPI Token", type=FieldType.SECRET, required=True),
        NodeField(
            name="repository",
            label="Repository",
            type=FieldType.SELECT,
            required=False,
            default="pypi",
            options=[
                {"value": "pypi", "label": "PyPI"},
                {"value": "testpypi", "label": "TestPyPI"},
            ],
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="package", label="Package Name", type=FieldType.STRING),
        NodeField(name="version", label="Version", type=FieldType.STRING),
        NodeField(name="output", label="Output", type=FieldType.TEXT),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        import subprocess

        project_path = config.get("project_path", "")
        pypi_token = config.get("pypi_token", "")
        repository = config.get("repository", "pypi")

        loop = asyncio.get_event_loop()

        def publish():
            # Build
            build_result = subprocess.run(
                ["python", "-m", "build"],
                capture_output=True,
                text=True,
                cwd=project_path,
                timeout=120,
            )

            if build_result.returncode != 0:
                return {
                    "success": False,
                    "package": "",
                    "version": "",
                    "output": build_result.stdout,
                    "error": build_result.stderr,
                }

            # Upload
            cmd = ["python", "-m", "twine", "upload", "dist/*"]
            if repository == "testpypi":
                cmd.extend(["--repository", "testpypi"])

            env = {
                "TWINE_USERNAME": "__token__",
                "TWINE_PASSWORD": pypi_token,
            }

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_path,
                env={**subprocess.os.environ, **env},
                timeout=120,
            )

            return {
                "success": result.returncode == 0,
                "package": "",  # Would parse from pyproject.toml
                "version": "",
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else "",
            }

        try:
            return await loop.run_in_executor(None, publish)
        except Exception as e:
            return {
                "success": False,
                "package": "",
                "version": "",
                "output": "",
                "error": str(e),
            }
