"""
Git Operations Nodes - Version control workflow automation.
"""

import asyncio
import subprocess

from src.core.nodes.base import BaseNode, FieldType, NodeField


class GitCloneNode(BaseNode):
    """Clone a Git repository."""

    type = "git-clone"
    name = "Git: Clone"
    category = "Coding"
    description = "Clone a Git repository"
    icon = "download"
    color = "#F05032"  # Git orange

    inputs = [
        NodeField(
            name="repo_url",
            label="Repository URL",
            type=FieldType.STRING,
            required=True,
            description="Git repository URL (HTTPS or SSH).",
        ),
        NodeField(
            name="destination",
            label="Destination Path",
            type=FieldType.STRING,
            required=True,
            description="Local path to clone into.",
        ),
        NodeField(
            name="branch",
            label="Branch",
            type=FieldType.STRING,
            required=False,
            description="Branch to clone (default: main/master).",
        ),
        NodeField(
            name="depth",
            label="Depth",
            type=FieldType.NUMBER,
            required=False,
            description="Shallow clone depth (0 for full clone).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="path", label="Clone Path", type=FieldType.STRING),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        repo_url = config.get("repo_url", "")
        destination = config.get("destination", "")
        branch = config.get("branch")
        depth = config.get("depth", 0)

        cmd = ["git", "clone"]
        if branch:
            cmd.extend(["-b", branch])
        if depth and int(depth) > 0:
            cmd.extend(["--depth", str(int(depth))])
        cmd.extend([repo_url, destination])

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: subprocess.run(cmd, capture_output=True, text=True)
            )
            if result.returncode == 0:
                return {"success": True, "path": destination, "error": ""}
            return {"success": False, "path": "", "error": result.stderr}
        except Exception as e:
            return {"success": False, "path": "", "error": str(e)}


class GitCommitNode(BaseNode):
    """Create a Git commit."""

    type = "git-commit"
    name = "Git: Commit"
    category = "Coding"
    description = "Stage and commit changes"
    icon = "check_circle"
    color = "#F05032"

    inputs = [
        NodeField(
            name="repo_path",
            label="Repository Path",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="message",
            label="Commit Message",
            type=FieldType.TEXT,
            required=True,
        ),
        NodeField(
            name="files",
            label="Files to Stage",
            type=FieldType.STRING,
            required=False,
            default=".",
            description="Files to stage (space-separated, or '.' for all).",
        ),
        NodeField(
            name="author",
            label="Author",
            type=FieldType.STRING,
            required=False,
            description="Author (format: Name <email>).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="commit_hash", label="Commit Hash", type=FieldType.STRING),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        repo_path = config.get("repo_path", "")
        message = config.get("message", "")
        files = config.get("files", ".")
        author = config.get("author")

        loop = asyncio.get_event_loop()

        try:
            # Stage files
            add_cmd = ["git", "-C", repo_path, "add"] + files.split()
            await loop.run_in_executor(None, lambda: subprocess.run(add_cmd, capture_output=True))

            # Commit
            commit_cmd = ["git", "-C", repo_path, "commit", "-m", message]
            if author:
                commit_cmd.extend(["--author", author])

            result = await loop.run_in_executor(
                None, lambda: subprocess.run(commit_cmd, capture_output=True, text=True)
            )

            if result.returncode == 0:
                # Get commit hash
                hash_cmd = ["git", "-C", repo_path, "rev-parse", "HEAD"]
                hash_result = await loop.run_in_executor(
                    None, lambda: subprocess.run(hash_cmd, capture_output=True, text=True)
                )
                commit_hash = hash_result.stdout.strip()[:8]
                return {"success": True, "commit_hash": commit_hash, "error": ""}

            return {"success": False, "commit_hash": "", "error": result.stderr}

        except Exception as e:
            return {"success": False, "commit_hash": "", "error": str(e)}


class GitPushNode(BaseNode):
    """Push commits to remote."""

    type = "git-push"
    name = "Git: Push"
    category = "Coding"
    description = "Push commits to remote repository"
    icon = "cloud_upload"
    color = "#F05032"

    inputs = [
        NodeField(name="repo_path", label="Repository Path", type=FieldType.STRING, required=True),
        NodeField(
            name="remote", label="Remote", type=FieldType.STRING, required=False, default="origin"
        ),
        NodeField(name="branch", label="Branch", type=FieldType.STRING, required=False),
        NodeField(
            name="force", label="Force Push", type=FieldType.BOOLEAN, required=False, default=False
        ),
        NodeField(
            name="set_upstream",
            label="Set Upstream",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        repo_path = config.get("repo_path", "")
        remote = config.get("remote", "origin")
        branch = config.get("branch")
        force = config.get("force", False)
        set_upstream = config.get("set_upstream", False)

        cmd = ["git", "-C", repo_path, "push"]
        if force:
            cmd.append("--force")
        if set_upstream:
            cmd.append("-u")
        cmd.append(remote)
        if branch:
            cmd.append(branch)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: subprocess.run(cmd, capture_output=True, text=True)
            )
            if result.returncode == 0:
                return {"success": True, "error": ""}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}


class GitPullNode(BaseNode):
    """Pull changes from remote."""

    type = "git-pull"
    name = "Git: Pull"
    category = "Coding"
    description = "Pull changes from remote repository"
    icon = "cloud_download"
    color = "#F05032"

    inputs = [
        NodeField(name="repo_path", label="Repository Path", type=FieldType.STRING, required=True),
        NodeField(
            name="remote", label="Remote", type=FieldType.STRING, required=False, default="origin"
        ),
        NodeField(name="branch", label="Branch", type=FieldType.STRING, required=False),
        NodeField(
            name="rebase", label="Rebase", type=FieldType.BOOLEAN, required=False, default=False
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="updated", label="Files Updated", type=FieldType.BOOLEAN),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        repo_path = config.get("repo_path", "")
        remote = config.get("remote", "origin")
        branch = config.get("branch")
        rebase = config.get("rebase", False)

        cmd = ["git", "-C", repo_path, "pull"]
        if rebase:
            cmd.append("--rebase")
        cmd.append(remote)
        if branch:
            cmd.append(branch)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: subprocess.run(cmd, capture_output=True, text=True)
            )
            if result.returncode == 0:
                updated = "Already up to date" not in result.stdout
                return {"success": True, "updated": updated, "error": ""}
            return {"success": False, "updated": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "updated": False, "error": str(e)}


class GitBranchNode(BaseNode):
    """Create or switch Git branches."""

    type = "git-branch"
    name = "Git: Branch"
    category = "Coding"
    description = "Create, switch, or list branches"
    icon = "account_tree"
    color = "#F05032"

    inputs = [
        NodeField(name="repo_path", label="Repository Path", type=FieldType.STRING, required=True),
        NodeField(
            name="action",
            label="Action",
            type=FieldType.SELECT,
            required=True,
            default="list",
            options=[
                {"value": "list", "label": "List Branches"},
                {"value": "create", "label": "Create Branch"},
                {"value": "switch", "label": "Switch Branch"},
                {"value": "delete", "label": "Delete Branch"},
            ],
        ),
        NodeField(name="branch_name", label="Branch Name", type=FieldType.STRING, required=False),
        NodeField(name="from_branch", label="From Branch", type=FieldType.STRING, required=False),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="branches", label="Branches", type=FieldType.JSON),
        NodeField(name="current", label="Current Branch", type=FieldType.STRING),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        repo_path = config.get("repo_path", "")
        action = config.get("action", "list")
        branch_name = config.get("branch_name", "")
        from_branch = config.get("from_branch")

        loop = asyncio.get_event_loop()

        try:
            if action == "list":
                cmd = ["git", "-C", repo_path, "branch", "-a"]
                result = await loop.run_in_executor(
                    None, lambda: subprocess.run(cmd, capture_output=True, text=True)
                )
                branches = [b.strip().lstrip("* ") for b in result.stdout.split("\n") if b.strip()]
                current_cmd = ["git", "-C", repo_path, "branch", "--show-current"]
                current_result = await loop.run_in_executor(
                    None, lambda: subprocess.run(current_cmd, capture_output=True, text=True)
                )
                return {
                    "success": True,
                    "branches": branches,
                    "current": current_result.stdout.strip(),
                    "error": "",
                }

            elif action == "create":
                cmd = ["git", "-C", repo_path, "checkout", "-b", branch_name]
                if from_branch:
                    cmd.append(from_branch)
                result = await loop.run_in_executor(
                    None, lambda: subprocess.run(cmd, capture_output=True, text=True)
                )
                return {
                    "success": result.returncode == 0,
                    "branches": [],
                    "current": branch_name if result.returncode == 0 else "",
                    "error": result.stderr,
                }

            elif action == "switch":
                cmd = ["git", "-C", repo_path, "checkout", branch_name]
                result = await loop.run_in_executor(
                    None, lambda: subprocess.run(cmd, capture_output=True, text=True)
                )
                return {
                    "success": result.returncode == 0,
                    "branches": [],
                    "current": branch_name if result.returncode == 0 else "",
                    "error": result.stderr,
                }

            elif action == "delete":
                cmd = ["git", "-C", repo_path, "branch", "-d", branch_name]
                result = await loop.run_in_executor(
                    None, lambda: subprocess.run(cmd, capture_output=True, text=True)
                )
                return {
                    "success": result.returncode == 0,
                    "branches": [],
                    "current": "",
                    "error": result.stderr,
                }

        except Exception as e:
            return {"success": False, "branches": [], "current": "", "error": str(e)}

        return {"success": False, "branches": [], "current": "", "error": "Unknown action"}


class GitStatusNode(BaseNode):
    """Get Git repository status."""

    type = "git-status"
    name = "Git: Status"
    category = "Coding"
    description = "Get repository status and changes"
    icon = "info"
    color = "#F05032"

    inputs = [
        NodeField(name="repo_path", label="Repository Path", type=FieldType.STRING, required=True),
    ]

    outputs = [
        NodeField(name="clean", label="Is Clean", type=FieldType.BOOLEAN),
        NodeField(name="branch", label="Current Branch", type=FieldType.STRING),
        NodeField(name="modified", label="Modified Files", type=FieldType.JSON),
        NodeField(name="untracked", label="Untracked Files", type=FieldType.JSON),
        NodeField(name="staged", label="Staged Files", type=FieldType.JSON),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        repo_path = config.get("repo_path", "")
        loop = asyncio.get_event_loop()

        try:
            # Get status
            status_cmd = ["git", "-C", repo_path, "status", "--porcelain"]
            result = await loop.run_in_executor(
                None, lambda: subprocess.run(status_cmd, capture_output=True, text=True)
            )

            # Get branch
            branch_cmd = ["git", "-C", repo_path, "branch", "--show-current"]
            branch_result = await loop.run_in_executor(
                None, lambda: subprocess.run(branch_cmd, capture_output=True, text=True)
            )

            modified = []
            untracked = []
            staged = []

            for line in result.stdout.split("\n"):
                if not line:
                    continue
                status = line[:2]
                filename = line[3:]

                if status[0] in "MADRC":
                    staged.append(filename)
                if status[1] == "M":
                    modified.append(filename)
                if status == "??":
                    untracked.append(filename)

            return {
                "clean": len(result.stdout.strip()) == 0,
                "branch": branch_result.stdout.strip(),
                "modified": modified,
                "untracked": untracked,
                "staged": staged,
            }

        except Exception:
            return {
                "clean": False,
                "branch": "",
                "modified": [],
                "untracked": [],
                "staged": [],
            }


class GitDiffNode(BaseNode):
    """Get Git diff of changes."""

    type = "git-diff"
    name = "Git: Diff"
    category = "Coding"
    description = "Get diff of file changes"
    icon = "difference"
    color = "#F05032"

    inputs = [
        NodeField(name="repo_path", label="Repository Path", type=FieldType.STRING, required=True),
        NodeField(name="file", label="File Path", type=FieldType.STRING, required=False),
        NodeField(
            name="staged",
            label="Staged Changes Only",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
        ),
        NodeField(name="commit", label="Compare to Commit", type=FieldType.STRING, required=False),
    ]

    outputs = [
        NodeField(name="diff", label="Diff Output", type=FieldType.TEXT),
        NodeField(name="files_changed", label="Files Changed", type=FieldType.NUMBER),
        NodeField(name="insertions", label="Insertions", type=FieldType.NUMBER),
        NodeField(name="deletions", label="Deletions", type=FieldType.NUMBER),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        repo_path = config.get("repo_path", "")
        file_path = config.get("file")
        staged = config.get("staged", False)
        commit = config.get("commit")

        cmd = ["git", "-C", repo_path, "diff"]
        if staged:
            cmd.append("--cached")
        if commit:
            cmd.append(commit)
        if file_path:
            cmd.extend(["--", file_path])

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: subprocess.run(cmd, capture_output=True, text=True)
            )

            # Get stats
            stat_cmd = cmd + ["--stat"]
            stat_result = await loop.run_in_executor(
                None, lambda: subprocess.run(stat_cmd, capture_output=True, text=True)
            )

            # Parse stats
            files_changed = 0
            insertions = 0
            deletions = 0

            if stat_result.stdout:
                lines = stat_result.stdout.strip().split("\n")
                if lines:
                    last_line = lines[-1]
                    import re

                    match = re.search(r"(\d+) files? changed", last_line)
                    if match:
                        files_changed = int(match.group(1))
                    match = re.search(r"(\d+) insertions?", last_line)
                    if match:
                        insertions = int(match.group(1))
                    match = re.search(r"(\d+) deletions?", last_line)
                    if match:
                        deletions = int(match.group(1))

            return {
                "diff": result.stdout,
                "files_changed": files_changed,
                "insertions": insertions,
                "deletions": deletions,
            }

        except Exception:
            return {"diff": "", "files_changed": 0, "insertions": 0, "deletions": 0}
