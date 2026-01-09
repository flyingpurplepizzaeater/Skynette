"""
Deployment Platform Nodes - Deploy to cloud platforms.
"""

import asyncio
from typing import Any, Optional

from src.core.nodes.base import BaseNode, NodeField, FieldType


class VercelDeployNode(BaseNode):
    """Deploy to Vercel."""

    type = "vercel-deploy"
    name = "Deploy: Vercel"
    category = "Coding"
    description = "Deploy project to Vercel"
    icon = "rocket_launch"
    color = "#000000"

    inputs = [
        NodeField(name="token", label="Vercel Token", type=FieldType.SECRET, required=True),
        NodeField(name="project_path", label="Project Path", type=FieldType.STRING, required=True),
        NodeField(name="project_name", label="Project Name", type=FieldType.STRING, required=False),
        NodeField(name="production", label="Production Deploy", type=FieldType.BOOLEAN, required=False, default=False),
        NodeField(name="env_vars", label="Environment Variables", type=FieldType.JSON, required=False),
        NodeField(name="team_id", label="Team ID", type=FieldType.STRING, required=False),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="url", label="Deployment URL", type=FieldType.STRING),
        NodeField(name="deployment_id", label="Deployment ID", type=FieldType.STRING),
        NodeField(name="status", label="Status", type=FieldType.STRING),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        import subprocess

        token = config.get("token", "")
        project_path = config.get("project_path", "")
        project_name = config.get("project_name", "")
        production = config.get("production", False)
        env_vars = config.get("env_vars", {})
        team_id = config.get("team_id", "")

        loop = asyncio.get_event_loop()

        def deploy():
            cmd = ["npx", "vercel"]

            if production:
                cmd.append("--prod")
            if project_name:
                cmd.extend(["--name", project_name])
            if team_id:
                cmd.extend(["--scope", team_id])

            # Add env vars
            for key, value in (env_vars or {}).items():
                cmd.extend(["-e", f"{key}={value}"])

            cmd.extend(["--token", token, "--yes"])

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=project_path,
                    timeout=300
                )

                # Parse URL from output
                url = ""
                for line in result.stdout.split("\n"):
                    if "https://" in line:
                        url = line.strip()
                        break

                return {
                    "success": result.returncode == 0,
                    "url": url,
                    "deployment_id": "",
                    "status": "deployed" if result.returncode == 0 else "failed",
                    "error": result.stderr if result.returncode != 0 else "",
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "url": "",
                    "deployment_id": "",
                    "status": "timeout",
                    "error": "Deployment timed out",
                }

        try:
            return await loop.run_in_executor(None, deploy)
        except Exception as e:
            return {
                "success": False,
                "url": "",
                "deployment_id": "",
                "status": "error",
                "error": str(e),
            }


class NetlifyDeployNode(BaseNode):
    """Deploy to Netlify."""

    type = "netlify-deploy"
    name = "Deploy: Netlify"
    category = "Coding"
    description = "Deploy project to Netlify"
    icon = "rocket_launch"
    color = "#00C7B7"

    inputs = [
        NodeField(name="token", label="Netlify Token", type=FieldType.SECRET, required=True),
        NodeField(name="site_id", label="Site ID", type=FieldType.STRING, required=True),
        NodeField(name="build_dir", label="Build Directory", type=FieldType.STRING, required=True,
                  description="Path to the built output directory."),
        NodeField(name="production", label="Production Deploy", type=FieldType.BOOLEAN, required=False, default=False),
        NodeField(name="message", label="Deploy Message", type=FieldType.STRING, required=False),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="url", label="Deployment URL", type=FieldType.STRING),
        NodeField(name="deploy_id", label="Deploy ID", type=FieldType.STRING),
        NodeField(name="status", label="Status", type=FieldType.STRING),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        import subprocess

        token = config.get("token", "")
        site_id = config.get("site_id", "")
        build_dir = config.get("build_dir", "")
        production = config.get("production", False)
        message = config.get("message", "")

        loop = asyncio.get_event_loop()

        def deploy():
            cmd = [
                "npx", "netlify-cli", "deploy",
                "--auth", token,
                "--site", site_id,
                "--dir", build_dir,
            ]

            if production:
                cmd.append("--prod")
            if message:
                cmd.extend(["--message", message])

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                # Parse output for URL
                url = ""
                deploy_id = ""
                for line in result.stdout.split("\n"):
                    if "Website URL:" in line or "Website Draft URL:" in line:
                        url = line.split(":")[-1].strip()
                        if url.startswith("//"):
                            url = "https:" + url
                    if "Deploy ID:" in line:
                        deploy_id = line.split(":")[-1].strip()

                return {
                    "success": result.returncode == 0,
                    "url": url,
                    "deploy_id": deploy_id,
                    "status": "deployed" if result.returncode == 0 else "failed",
                    "error": result.stderr if result.returncode != 0 else "",
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "url": "",
                    "deploy_id": "",
                    "status": "timeout",
                    "error": "Deployment timed out",
                }

        try:
            return await loop.run_in_executor(None, deploy)
        except Exception as e:
            return {
                "success": False,
                "url": "",
                "deploy_id": "",
                "status": "error",
                "error": str(e),
            }


class CloudflareDeployNode(BaseNode):
    """Deploy to Cloudflare Pages/Workers."""

    type = "cloudflare-deploy"
    name = "Deploy: Cloudflare"
    category = "Coding"
    description = "Deploy to Cloudflare Pages or Workers"
    icon = "cloud"
    color = "#F38020"

    inputs = [
        NodeField(name="api_token", label="API Token", type=FieldType.SECRET, required=True),
        NodeField(name="account_id", label="Account ID", type=FieldType.STRING, required=True),
        NodeField(name="project_name", label="Project Name", type=FieldType.STRING, required=True),
        NodeField(name="build_dir", label="Build Directory", type=FieldType.STRING, required=True),
        NodeField(name="branch", label="Branch", type=FieldType.STRING, required=False, default="main"),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="url", label="Deployment URL", type=FieldType.STRING),
        NodeField(name="deployment_id", label="Deployment ID", type=FieldType.STRING),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        import subprocess

        api_token = config.get("api_token", "")
        account_id = config.get("account_id", "")
        project_name = config.get("project_name", "")
        build_dir = config.get("build_dir", "")
        branch = config.get("branch", "main")

        loop = asyncio.get_event_loop()

        def deploy():
            cmd = [
                "npx", "wrangler", "pages", "deploy", build_dir,
                "--project-name", project_name,
                "--branch", branch,
            ]

            env = {
                "CLOUDFLARE_API_TOKEN": api_token,
                "CLOUDFLARE_ACCOUNT_ID": account_id,
            }

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    env={**subprocess.os.environ, **env},
                    timeout=300
                )

                url = ""
                for line in result.stdout.split("\n"):
                    if ".pages.dev" in line or ".workers.dev" in line:
                        import re
                        match = re.search(r'https://[^\s]+', line)
                        if match:
                            url = match.group(0)
                            break

                return {
                    "success": result.returncode == 0,
                    "url": url,
                    "deployment_id": "",
                    "error": result.stderr if result.returncode != 0 else "",
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "url": "",
                    "deployment_id": "",
                    "error": "Deployment timed out",
                }

        try:
            return await loop.run_in_executor(None, deploy)
        except Exception as e:
            return {
                "success": False,
                "url": "",
                "deployment_id": "",
                "error": str(e),
            }


class HerokuDeployNode(BaseNode):
    """Deploy to Heroku."""

    type = "heroku-deploy"
    name = "Deploy: Heroku"
    category = "Coding"
    description = "Deploy to Heroku via Git or Container"
    icon = "cloud_upload"
    color = "#430098"

    inputs = [
        NodeField(name="api_key", label="Heroku API Key", type=FieldType.SECRET, required=True),
        NodeField(name="app_name", label="App Name", type=FieldType.STRING, required=True),
        NodeField(name="project_path", label="Project Path", type=FieldType.STRING, required=True),
        NodeField(
            name="deploy_method",
            label="Deploy Method",
            type=FieldType.SELECT,
            required=False,
            default="git",
            options=[
                {"value": "git", "label": "Git Push"},
                {"value": "container", "label": "Container"},
            ],
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="url", label="App URL", type=FieldType.STRING),
        NodeField(name="output", label="Output", type=FieldType.TEXT),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        import subprocess

        api_key = config.get("api_key", "")
        app_name = config.get("app_name", "")
        project_path = config.get("project_path", "")
        deploy_method = config.get("deploy_method", "git")

        loop = asyncio.get_event_loop()

        def deploy():
            env = {
                "HEROKU_API_KEY": api_key,
            }

            if deploy_method == "git":
                # Add Heroku remote and push
                subprocess.run(
                    ["git", "remote", "add", "heroku", f"https://git.heroku.com/{app_name}.git"],
                    capture_output=True,
                    cwd=project_path,
                )

                result = subprocess.run(
                    ["git", "push", "heroku", "main", "--force"],
                    capture_output=True,
                    text=True,
                    cwd=project_path,
                    env={**subprocess.os.environ, **env},
                    timeout=300
                )
            else:
                # Container deploy
                subprocess.run(
                    ["heroku", "container:login"],
                    env={**subprocess.os.environ, **env},
                    capture_output=True,
                )

                subprocess.run(
                    ["heroku", "container:push", "web", "-a", app_name],
                    cwd=project_path,
                    env={**subprocess.os.environ, **env},
                    capture_output=True,
                )

                result = subprocess.run(
                    ["heroku", "container:release", "web", "-a", app_name],
                    capture_output=True,
                    text=True,
                    env={**subprocess.os.environ, **env},
                    timeout=300
                )

            return {
                "success": result.returncode == 0,
                "url": f"https://{app_name}.herokuapp.com",
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else "",
            }

        try:
            return await loop.run_in_executor(None, deploy)
        except Exception as e:
            return {
                "success": False,
                "url": "",
                "output": "",
                "error": str(e),
            }


class RailwayDeployNode(BaseNode):
    """Deploy to Railway."""

    type = "railway-deploy"
    name = "Deploy: Railway"
    category = "Coding"
    description = "Deploy to Railway.app"
    icon = "train"
    color = "#0B0D0E"

    inputs = [
        NodeField(name="token", label="Railway Token", type=FieldType.SECRET, required=True),
        NodeField(name="project_path", label="Project Path", type=FieldType.STRING, required=True),
        NodeField(name="service", label="Service Name", type=FieldType.STRING, required=False),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="url", label="Deployment URL", type=FieldType.STRING),
        NodeField(name="output", label="Output", type=FieldType.TEXT),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        import subprocess

        token = config.get("token", "")
        project_path = config.get("project_path", "")
        service = config.get("service", "")

        loop = asyncio.get_event_loop()

        def deploy():
            cmd = ["npx", "@railway/cli", "up"]
            if service:
                cmd.extend(["--service", service])

            env = {"RAILWAY_TOKEN": token}

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=project_path,
                    env={**subprocess.os.environ, **env},
                    timeout=300
                )

                url = ""
                for line in result.stdout.split("\n"):
                    if "railway.app" in line:
                        import re
                        match = re.search(r'https://[^\s]+railway\.app[^\s]*', line)
                        if match:
                            url = match.group(0)
                            break

                return {
                    "success": result.returncode == 0,
                    "url": url,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else "",
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "url": "",
                    "output": "",
                    "error": "Deployment timed out",
                }

        try:
            return await loop.run_in_executor(None, deploy)
        except Exception as e:
            return {
                "success": False,
                "url": "",
                "output": "",
                "error": str(e),
            }


class SupabaseDeployNode(BaseNode):
    """Deploy Supabase Edge Functions."""

    type = "supabase-deploy"
    name = "Deploy: Supabase Functions"
    category = "Coding"
    description = "Deploy Supabase Edge Functions"
    icon = "functions"
    color = "#3ECF8E"

    inputs = [
        NodeField(name="access_token", label="Access Token", type=FieldType.SECRET, required=True),
        NodeField(name="project_ref", label="Project Reference", type=FieldType.STRING, required=True),
        NodeField(name="function_name", label="Function Name", type=FieldType.STRING, required=True),
        NodeField(name="project_path", label="Project Path", type=FieldType.STRING, required=True),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="url", label="Function URL", type=FieldType.STRING),
        NodeField(name="output", label="Output", type=FieldType.TEXT),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        import subprocess

        access_token = config.get("access_token", "")
        project_ref = config.get("project_ref", "")
        function_name = config.get("function_name", "")
        project_path = config.get("project_path", "")

        loop = asyncio.get_event_loop()

        def deploy():
            cmd = [
                "npx", "supabase", "functions", "deploy", function_name,
                "--project-ref", project_ref,
            ]

            env = {"SUPABASE_ACCESS_TOKEN": access_token}

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=project_path,
                    env={**subprocess.os.environ, **env},
                    timeout=120
                )

                url = f"https://{project_ref}.supabase.co/functions/v1/{function_name}"

                return {
                    "success": result.returncode == 0,
                    "url": url if result.returncode == 0 else "",
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else "",
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "url": "",
                    "output": "",
                    "error": "Deployment timed out",
                }

        try:
            return await loop.run_in_executor(None, deploy)
        except Exception as e:
            return {
                "success": False,
                "url": "",
                "output": "",
                "error": str(e),
            }
