"""
Code Execution Tool

Execute code in Python, Node.js, or shell with timeout and output capture.
"""

import asyncio
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Optional

from src.agent.models.tool import ToolResult
from src.agent.registry.base_tool import AgentContext, BaseTool


@dataclass
class ExecutionResult:
    """Result of code execution."""

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    language: str


# Language configuration for code execution
LANGUAGE_CONFIG = {
    "python": {"cmd": [sys.executable, "-c"], "file_cmd": [sys.executable], "file_ext": ".py"},
    "python3": {"cmd": [sys.executable, "-c"], "file_cmd": [sys.executable], "file_ext": ".py"},
    "node": {"cmd": ["node", "-e"], "file_cmd": ["node"], "file_ext": ".js"},
    "javascript": {"cmd": ["node", "-e"], "file_cmd": ["node"], "file_ext": ".js"},
    "bash": {"cmd": ["bash", "-c"], "file_cmd": ["bash"], "file_ext": ".sh"},
    "shell": {"cmd": ["bash", "-c"], "file_cmd": ["bash"], "file_ext": ".sh"},
    "powershell": {"cmd": ["powershell", "-Command"], "file_cmd": ["powershell", "-File"], "file_ext": ".ps1"},
}


class CodeExecutionTool(BaseTool):
    """Execute code in Python, Node.js, or shell."""

    name = "code_execute"
    description = (
        "Execute code in Python, Node.js, or shell. "
        "Returns stdout, stderr, exit code, and execution time."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Code to execute",
            },
            "language": {
                "type": "string",
                "enum": ["python", "python3", "node", "javascript", "bash", "shell", "powershell"],
                "description": "Programming language (default: python)",
                "default": "python",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 300 = 5 minutes)",
                "default": 300,
            },
            "working_dir": {
                "type": "string",
                "description": "Working directory for execution",
            },
        },
        "required": ["code"],
    }
    is_destructive = True  # Code execution can have side effects

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Execute code and return result."""
        start = time.perf_counter()

        code = params.get("code", "")
        language = params.get("language", "python")
        timeout = params.get("timeout", 300)
        working_dir = params.get("working_dir") or context.working_directory

        if not code.strip():
            return ToolResult.failure_result(
                tool_call_id=context.session_id,
                error="No code provided",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        if language not in LANGUAGE_CONFIG:
            return ToolResult.failure_result(
                tool_call_id=context.session_id,
                error=f"Unsupported language: {language}. Supported: {list(LANGUAGE_CONFIG.keys())}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        result = await self._run_code(code, language, timeout, working_dir)

        return ToolResult.success_result(
            tool_call_id=context.session_id,
            data={
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_seconds": result.duration_seconds,
                "timed_out": result.timed_out,
                "language": result.language,
                "success": result.exit_code == 0 and not result.timed_out,
            },
            duration_ms=(time.perf_counter() - start) * 1000,
        )

    async def _run_code(
        self,
        code: str,
        language: str,
        timeout: int,
        working_dir: Optional[str],
    ) -> ExecutionResult:
        """Execute code asynchronously with timeout."""
        start = time.perf_counter()
        config = LANGUAGE_CONFIG[language]

        # For short code, use inline execution; for longer code, use temp file
        temp_file: Optional[str] = None
        if len(code) < 1000:
            cmd = config["cmd"] + [code]
        else:
            # Create temp file for longer code
            fd, temp_file = tempfile.mkstemp(suffix=config["file_ext"])
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(code)
            except Exception:
                # If writing fails, close fd and clean up
                try:
                    os.close(fd)
                except OSError:
                    pass
                if temp_file and os.path.exists(temp_file):
                    os.unlink(temp_file)
                raise

            # Use file command instead of inline command
            cmd = config["file_cmd"] + [temp_file]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )
                duration = time.perf_counter() - start

                return ExecutionResult(
                    exit_code=proc.returncode or 0,
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    duration_seconds=duration,
                    timed_out=False,
                    language=language,
                )

            except asyncio.TimeoutError:
                # Kill the process on timeout
                proc.kill()
                await proc.wait()
                duration = time.perf_counter() - start

                return ExecutionResult(
                    exit_code=-1,
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds",
                    duration_seconds=duration,
                    timed_out=True,
                    language=language,
                )

        except FileNotFoundError as e:
            # Handle case where interpreter is not found
            duration = time.perf_counter() - start
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Interpreter not found: {e.filename}",
                duration_seconds=duration,
                timed_out=False,
                language=language,
            )

        except Exception as e:
            duration = time.perf_counter() - start
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                duration_seconds=duration,
                timed_out=False,
                language=language,
            )

        finally:
            # Clean up temp file if created
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass  # Best effort cleanup
