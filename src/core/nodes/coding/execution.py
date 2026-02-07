"""
Code Execution Nodes - Run code in various languages with error handling.
"""

import asyncio
import os
import subprocess
import tempfile
from pathlib import Path

from src.core.nodes.base import BaseNode, FieldType, NodeField


class RunPythonNode(BaseNode):
    """Execute Python code."""

    type = "run-python"
    name = "Run: Python"
    category = "Coding"
    description = "Execute Python code and capture output"
    icon = "code"
    color = "#3776AB"  # Python blue

    inputs = [
        NodeField(
            name="code",
            label="Python Code",
            type=FieldType.TEXT,
            required=True,
            description="Python code to execute.",
        ),
        NodeField(
            name="working_dir",
            label="Working Directory",
            type=FieldType.STRING,
            required=False,
        ),
        NodeField(
            name="timeout",
            label="Timeout (seconds)",
            type=FieldType.NUMBER,
            required=False,
            default=30,
        ),
        NodeField(
            name="python_path",
            label="Python Path",
            type=FieldType.STRING,
            required=False,
            description="Path to Python interpreter (default: system python).",
        ),
        NodeField(
            name="env_vars",
            label="Environment Variables",
            type=FieldType.JSON,
            required=False,
            description="Additional environment variables as JSON object.",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="stdout", label="Standard Output", type=FieldType.TEXT),
        NodeField(name="stderr", label="Standard Error", type=FieldType.TEXT),
        NodeField(name="return_code", label="Return Code", type=FieldType.NUMBER),
        NodeField(name="error_type", label="Error Type", type=FieldType.STRING),
        NodeField(name="error_line", label="Error Line", type=FieldType.NUMBER),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        code = config.get("code", "")
        working_dir = config.get("working_dir") or None
        timeout = int(config.get("timeout", 30))
        python_path = config.get("python_path") or "python"
        env_vars = config.get("env_vars") or {}

        loop = asyncio.get_event_loop()

        def run_code():
            # Create temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_path = f.name

            try:
                env = os.environ.copy()
                env.update(env_vars)

                result = subprocess.run(
                    [python_path, temp_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=working_dir,
                    env=env,
                )

                error_type = ""
                error_line = 0

                if result.returncode != 0:
                    # Parse error from stderr
                    import re

                    error_match = re.search(r"(\w+Error):", result.stderr)
                    if error_match:
                        error_type = error_match.group(1)
                    line_match = re.search(r"line (\d+)", result.stderr)
                    if line_match:
                        error_line = int(line_match.group(1))

                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "error_type": error_type,
                    "error_line": error_line,
                }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds",
                    "return_code": -1,
                    "error_type": "TimeoutError",
                    "error_line": 0,
                }
            finally:
                os.unlink(temp_path)

        try:
            return await loop.run_in_executor(None, run_code)
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "error_type": type(e).__name__,
                "error_line": 0,
            }


class RunNodeJSNode(BaseNode):
    """Execute Node.js/JavaScript code."""

    type = "run-nodejs"
    name = "Run: Node.js"
    category = "Coding"
    description = "Execute JavaScript/Node.js code"
    icon = "code"
    color = "#339933"  # Node.js green

    inputs = [
        NodeField(name="code", label="JavaScript Code", type=FieldType.TEXT, required=True),
        NodeField(
            name="working_dir", label="Working Directory", type=FieldType.STRING, required=False
        ),
        NodeField(
            name="timeout",
            label="Timeout (seconds)",
            type=FieldType.NUMBER,
            required=False,
            default=30,
        ),
        NodeField(name="node_path", label="Node Path", type=FieldType.STRING, required=False),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="stdout", label="Standard Output", type=FieldType.TEXT),
        NodeField(name="stderr", label="Standard Error", type=FieldType.TEXT),
        NodeField(name="return_code", label="Return Code", type=FieldType.NUMBER),
        NodeField(name="error_type", label="Error Type", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        code = config.get("code", "")
        working_dir = config.get("working_dir") or None
        timeout = int(config.get("timeout", 30))
        node_path = config.get("node_path") or "node"

        loop = asyncio.get_event_loop()

        def run_code():
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(code)
                temp_path = f.name

            try:
                result = subprocess.run(
                    [node_path, temp_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=working_dir,
                )

                error_type = ""
                if result.returncode != 0:
                    import re

                    error_match = re.search(r"(\w+Error):", result.stderr)
                    if error_match:
                        error_type = error_match.group(1)

                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "error_type": error_type,
                }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds",
                    "return_code": -1,
                    "error_type": "TimeoutError",
                }
            finally:
                os.unlink(temp_path)

        try:
            return await loop.run_in_executor(None, run_code)
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "error_type": type(e).__name__,
            }


class RunShellNode(BaseNode):
    """Execute shell commands."""

    type = "run-shell"
    name = "Run: Shell"
    category = "Coding"
    description = "Execute shell commands (bash/cmd/powershell)"
    icon = "terminal"
    color = "#4D4D4D"

    inputs = [
        NodeField(name="command", label="Command", type=FieldType.TEXT, required=True),
        NodeField(
            name="working_dir", label="Working Directory", type=FieldType.STRING, required=False
        ),
        NodeField(
            name="timeout",
            label="Timeout (seconds)",
            type=FieldType.NUMBER,
            required=False,
            default=60,
        ),
        NodeField(
            name="shell",
            label="Shell",
            type=FieldType.SELECT,
            required=False,
            default="auto",
            options=[
                {"value": "auto", "label": "Auto-detect"},
                {"value": "bash", "label": "Bash"},
                {"value": "cmd", "label": "CMD (Windows)"},
                {"value": "powershell", "label": "PowerShell"},
            ],
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="stdout", label="Standard Output", type=FieldType.TEXT),
        NodeField(name="stderr", label="Standard Error", type=FieldType.TEXT),
        NodeField(name="return_code", label="Return Code", type=FieldType.NUMBER),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        command = config.get("command", "")
        working_dir = config.get("working_dir") or None
        timeout = int(config.get("timeout", 60))
        shell_type = config.get("shell", "auto")

        loop = asyncio.get_event_loop()

        def run_cmd():

            if shell_type == "auto":
                shell = True
            elif shell_type == "bash":
                shell = ["/bin/bash", "-c", command]
            elif shell_type == "cmd":
                shell = ["cmd", "/c", command]
            elif shell_type == "powershell":
                shell = ["powershell", "-Command", command]
            else:
                shell = True

            try:
                if isinstance(shell, bool):
                    # Security note: shell=True is intentional for this node as it's
                    # designed to execute user-provided shell commands. The node is
                    # meant for workflow automation where users explicitly choose
                    # to run shell commands. Timeout prevents runaway processes.
                    result = subprocess.run(
                        command,
                        shell=True,  # nosec B602 - intentional for shell execution node
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=working_dir,
                    )
                else:
                    result = subprocess.run(
                        shell if shell_type != "auto" else command,
                        shell=shell_type == "auto",  # nosec B602 - intentional
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=working_dir,
                    )

                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "return_code": -1,
                }

        try:
            return await loop.run_in_executor(None, run_cmd)
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
            }


class RunTestsNode(BaseNode):
    """Run test suite and capture results."""

    type = "run-tests"
    name = "Run: Tests"
    category = "Coding"
    description = "Run test suite (pytest, jest, etc.)"
    icon = "science"
    color = "#0A9EDC"

    inputs = [
        NodeField(name="project_path", label="Project Path", type=FieldType.STRING, required=True),
        NodeField(
            name="framework",
            label="Test Framework",
            type=FieldType.SELECT,
            required=True,
            default="pytest",
            options=[
                {"value": "pytest", "label": "Pytest (Python)"},
                {"value": "jest", "label": "Jest (JavaScript)"},
                {"value": "mocha", "label": "Mocha (JavaScript)"},
                {"value": "go", "label": "Go Test"},
                {"value": "cargo", "label": "Cargo Test (Rust)"},
                {"value": "npm", "label": "npm test"},
            ],
        ),
        NodeField(
            name="test_path", label="Test Path/Pattern", type=FieldType.STRING, required=False
        ),
        NodeField(
            name="verbose",
            label="Verbose Output",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
        ),
        NodeField(
            name="timeout",
            label="Timeout (seconds)",
            type=FieldType.NUMBER,
            required=False,
            default=300,
        ),
    ]

    outputs = [
        NodeField(name="success", label="All Tests Passed", type=FieldType.BOOLEAN),
        NodeField(name="total", label="Total Tests", type=FieldType.NUMBER),
        NodeField(name="passed", label="Passed", type=FieldType.NUMBER),
        NodeField(name="failed", label="Failed", type=FieldType.NUMBER),
        NodeField(name="skipped", label="Skipped", type=FieldType.NUMBER),
        NodeField(name="output", label="Test Output", type=FieldType.TEXT),
        NodeField(name="failures", label="Failed Tests", type=FieldType.JSON),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        project_path = config.get("project_path", "")
        framework = config.get("framework", "pytest")
        test_path = config.get("test_path", "")
        verbose = config.get("verbose", True)
        timeout = int(config.get("timeout", 300))

        loop = asyncio.get_event_loop()

        def run_tests():
            if framework == "pytest":
                cmd = ["python", "-m", "pytest"]
                if verbose:
                    cmd.append("-v")
                if test_path:
                    cmd.append(test_path)

            elif framework == "jest":
                cmd = ["npx", "jest"]
                if verbose:
                    cmd.append("--verbose")
                if test_path:
                    cmd.append(test_path)

            elif framework == "mocha":
                cmd = ["npx", "mocha"]
                if test_path:
                    cmd.append(test_path)

            elif framework == "go":
                cmd = ["go", "test"]
                if verbose:
                    cmd.append("-v")
                cmd.append("./...")

            elif framework == "cargo":
                cmd = ["cargo", "test"]
                if verbose:
                    cmd.append("--verbose")

            elif framework == "npm":
                cmd = ["npm", "test"]

            else:
                return {
                    "success": False,
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "output": "Unknown test framework",
                    "failures": [],
                }

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=project_path,
                )

                output = result.stdout + result.stderr
                total = passed = failed = skipped = 0
                failures = []

                # Parse results based on framework
                import re

                if framework == "pytest":
                    match = re.search(r"(\d+) passed", output)
                    if match:
                        passed = int(match.group(1))
                    match = re.search(r"(\d+) failed", output)
                    if match:
                        failed = int(match.group(1))
                    match = re.search(r"(\d+) skipped", output)
                    if match:
                        skipped = int(match.group(1))
                    total = passed + failed + skipped

                    # Extract failure names
                    for match in re.finditer(r"FAILED (.+?) -", output):
                        failures.append(match.group(1))

                elif framework in ["jest", "mocha"]:
                    match = re.search(r"Tests:\s+(\d+) failed", output)
                    if match:
                        failed = int(match.group(1))
                    match = re.search(r"(\d+) passed", output)
                    if match:
                        passed = int(match.group(1))
                    match = re.search(r"(\d+) skipped", output)
                    if match:
                        skipped = int(match.group(1))
                    total = passed + failed + skipped

                return {
                    "success": result.returncode == 0 and failed == 0,
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "skipped": skipped,
                    "output": output,
                    "failures": failures,
                }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "output": f"Tests timed out after {timeout} seconds",
                    "failures": ["TimeoutError"],
                }

        try:
            return await loop.run_in_executor(None, run_tests)
        except Exception as e:
            return {
                "success": False,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "output": str(e),
                "failures": [str(e)],
            }


class LintCodeNode(BaseNode):
    """Run linter on code."""

    type = "lint-code"
    name = "Lint: Code"
    category = "Coding"
    description = "Run linter to check code quality"
    icon = "rule"
    color = "#CB2029"

    inputs = [
        NodeField(name="project_path", label="Project Path", type=FieldType.STRING, required=True),
        NodeField(
            name="linter",
            label="Linter",
            type=FieldType.SELECT,
            required=True,
            default="auto",
            options=[
                {"value": "auto", "label": "Auto-detect"},
                {"value": "ruff", "label": "Ruff (Python)"},
                {"value": "pylint", "label": "Pylint (Python)"},
                {"value": "flake8", "label": "Flake8 (Python)"},
                {"value": "eslint", "label": "ESLint (JavaScript)"},
                {"value": "tsc", "label": "TypeScript Compiler"},
            ],
        ),
        NodeField(
            name="fix",
            label="Auto-fix Issues",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
        ),
    ]

    outputs = [
        NodeField(name="success", label="No Issues", type=FieldType.BOOLEAN),
        NodeField(name="issues_count", label="Issues Count", type=FieldType.NUMBER),
        NodeField(name="issues", label="Issues", type=FieldType.JSON),
        NodeField(name="output", label="Linter Output", type=FieldType.TEXT),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        project_path = config.get("project_path", "")
        linter = config.get("linter", "auto")
        fix = config.get("fix", False)

        loop = asyncio.get_event_loop()

        def run_linter():
            # Auto-detect linter based on project files
            if linter == "auto":
                project = Path(project_path)
                if (project / "pyproject.toml").exists() or list(project.glob("*.py")):
                    actual_linter = "ruff"
                elif (project / "package.json").exists():
                    actual_linter = "eslint"
                elif (project / "tsconfig.json").exists():
                    actual_linter = "tsc"
                else:
                    actual_linter = "ruff"
            else:
                actual_linter = linter

            if actual_linter == "ruff":
                cmd = ["ruff", "check", "."]
                if fix:
                    cmd.append("--fix")
            elif actual_linter == "pylint":
                cmd = ["pylint", "."]
            elif actual_linter == "flake8":
                cmd = ["flake8", "."]
            elif actual_linter == "eslint":
                cmd = ["npx", "eslint", "."]
                if fix:
                    cmd.append("--fix")
            elif actual_linter == "tsc":
                cmd = ["npx", "tsc", "--noEmit"]
            else:
                cmd = ["ruff", "check", "."]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=project_path,
                )

                output = result.stdout + result.stderr
                issues = []

                # Parse issues (simplified)
                import re

                for line in output.split("\n"):
                    if re.match(r".+:\d+:\d+:", line) or re.match(r".+\(\d+,\d+\):", line):
                        issues.append(line)

                return {
                    "success": result.returncode == 0,
                    "issues_count": len(issues),
                    "issues": issues[:50],  # Limit to 50
                    "output": output,
                }

            except FileNotFoundError:
                return {
                    "success": False,
                    "issues_count": 0,
                    "issues": [],
                    "output": f"Linter '{actual_linter}' not found. Install it first.",
                }

        try:
            return await loop.run_in_executor(None, run_linter)
        except Exception as e:
            return {
                "success": False,
                "issues_count": 0,
                "issues": [],
                "output": str(e),
            }
