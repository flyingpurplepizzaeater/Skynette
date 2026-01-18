"""
Code Execution Node

Unified code execution node supporting multiple languages with timeout protection.
"""

import asyncio
import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Any

from src.core.nodes.base import BaseNode, NodeField, NodeOutput, FieldType


class CodeExecutionNode(BaseNode):
    """Execute code snippets in Python, JavaScript, Bash, or PowerShell."""

    type = "code_execution"
    name = "Execute Code"
    category = "Execution"
    description = "Run code snippets (Python, JavaScript, Bash, PowerShell)"
    icon = "code"
    color = "#F97316"  # Orange
    is_trigger = False

    SUPPORTED_LANGUAGES = ["python", "javascript", "bash", "powershell"]
    MAX_TIMEOUT = 300  # Maximum allowed timeout in seconds

    @classmethod
    def get_inputs(cls) -> list[NodeField]:
        return [
            NodeField(
                name="code",
                label="Code",
                type=FieldType.TEXT,
                description="Code to execute",
                required=True,
                placeholder="print('Hello, World!')",
            ),
            NodeField(
                name="language",
                label="Language",
                type=FieldType.SELECT,
                description="Programming language",
                required=True,
                default="python",
                options=[
                    {"label": "Python", "value": "python"},
                    {"label": "JavaScript (Node.js)", "value": "javascript"},
                    {"label": "Bash", "value": "bash"},
                    {"label": "PowerShell", "value": "powershell"},
                ],
            ),
            NodeField(
                name="timeout",
                label="Timeout (seconds)",
                type=FieldType.NUMBER,
                description="Maximum execution time (1-300 seconds)",
                required=False,
                default=30,
                min_value=1,
                max_value=300,
            ),
            NodeField(
                name="working_directory",
                label="Working Directory",
                type=FieldType.STRING,
                description="Directory to run code from",
                required=False,
            ),
        ]

    @classmethod
    def get_outputs(cls) -> list[NodeOutput]:
        return [
            NodeOutput(
                name="stdout",
                type="string",
                description="Standard output from execution",
            ),
            NodeOutput(
                name="stderr",
                type="string",
                description="Standard error from execution",
            ),
            NodeOutput(
                name="return_code",
                type="number",
                description="Process exit code (0 = success)",
            ),
            NodeOutput(
                name="success",
                type="boolean",
                description="True if execution completed with exit code 0",
            ),
        ]

    def _inject_variables(self, code: str, language: str, variables: dict) -> str:
        """Inject workflow variables into code."""
        if not variables:
            return code

        if language == "python":
            # Python: direct assignment with repr for proper escaping
            var_lines = [f'{k} = {repr(v)}' for k, v in variables.items()]
            return "\n".join(var_lines) + "\n\n" + code

        elif language == "javascript":
            # JavaScript: const declarations with JSON for proper escaping
            var_lines = [f'const {k} = {json.dumps(v)};' for k, v in variables.items()]
            return "\n".join(var_lines) + "\n\n" + code

        elif language == "bash":
            # Bash: export variables (escape double quotes)
            var_lines = []
            for k, v in variables.items():
                escaped_value = str(v).replace('"', '\\"')
                var_lines.append(f'export {k}="{escaped_value}"')
            return "\n".join(var_lines) + "\n\n" + code

        elif language == "powershell":
            # PowerShell: Set environment variables (escape double quotes)
            var_lines = []
            for k, v in variables.items():
                escaped_value = str(v).replace('"', '`"')
                var_lines.append(f'$env:{k}="{escaped_value}"')
            return "\n".join(var_lines) + "\n\n" + code

        return code

    def _validate_config(self, config: dict) -> tuple[bool, str]:
        """Validate execution configuration."""
        code = config.get("code", "").strip()
        if not code:
            return False, "Code is required"

        language = config.get("language", "python")
        if language not in self.SUPPORTED_LANGUAGES:
            return False, f"Unsupported language: {language}. Supported: {', '.join(self.SUPPORTED_LANGUAGES)}"

        timeout = config.get("timeout", 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            return False, "Timeout must be a positive number"
        if timeout > self.MAX_TIMEOUT:
            return False, f"Timeout cannot exceed {self.MAX_TIMEOUT} seconds"

        return True, ""

    async def execute(self, config: dict, context: dict) -> dict[str, Any]:
        """Execute code with the given configuration and context."""
        # Validate configuration
        valid, error = self._validate_config(config)
        if not valid:
            return {
                "stdout": "",
                "stderr": error,
                "return_code": -1,
                "success": False,
            }

        code = config.get("code", "")
        language = config.get("language", "python")
        timeout = min(int(config.get("timeout", 30)), self.MAX_TIMEOUT)
        working_dir = config.get("working_directory")

        # Inject workflow variables
        variables = context.get("$vars", {})
        code = self._inject_variables(code, language, variables)

        # File extension mapping
        suffix_map = {
            "python": ".py",
            "javascript": ".js",
            "bash": ".sh",
            "powershell": ".ps1",
        }

        # Get event loop for running blocking code
        loop = asyncio.get_event_loop()

        def run_code():
            # Write code to temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=suffix_map.get(language, ".txt"),
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_path = f.name

            try:
                # Build command based on language
                cmd = {
                    "python": ["python", temp_path],
                    "javascript": ["node", temp_path],
                    "bash": ["bash", temp_path],
                    "powershell": ["powershell", "-ExecutionPolicy", "Bypass", "-File", temp_path],
                }.get(language, ["python", temp_path])

                # Execute the code
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=working_dir,
                    env=os.environ.copy(),
                )

                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "success": result.returncode == 0,
                }

            except subprocess.TimeoutExpired:
                return {
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds",
                    "return_code": -1,
                    "success": False,
                }
            except FileNotFoundError as e:
                interpreter = cmd[0] if cmd else "interpreter"
                return {
                    "stdout": "",
                    "stderr": f"Interpreter '{interpreter}' not found. Please ensure it is installed and in PATH.",
                    "return_code": -1,
                    "success": False,
                }
            finally:
                # Clean up temp file
                Path(temp_path).unlink(missing_ok=True)

        try:
            return await loop.run_in_executor(None, run_code)
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
                "return_code": -1,
                "success": False,
            }
