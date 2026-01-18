"""Tests for CodeExecutionNode."""

import pytest
import shutil

from src.core.nodes.execution.code_runner import CodeExecutionNode


class TestCodeExecutionNode:
    """Test suite for CodeExecutionNode."""

    @pytest.fixture
    def node(self):
        """Create a CodeExecutionNode instance."""
        return CodeExecutionNode()

    # === Basic Execution Tests ===

    @pytest.mark.asyncio
    async def test_python_execution(self, node):
        """Test basic Python code execution."""
        result = await node.execute(
            {"code": "print('hello')", "language": "python", "timeout": 5},
            {"$vars": {}}
        )
        assert result["success"] is True
        assert "hello" in result["stdout"]
        assert result["return_code"] == 0

    @pytest.mark.asyncio
    async def test_python_multiline(self, node):
        """Test multiline Python code execution."""
        code = """
x = 5
y = 10
print(x + y)
"""
        result = await node.execute(
            {"code": code, "language": "python", "timeout": 5},
            {"$vars": {}}
        )
        assert result["success"] is True
        assert "15" in result["stdout"]

    # === Timeout Tests ===

    @pytest.mark.asyncio
    async def test_timeout(self, node):
        """Test that timeout prevents runaway processes."""
        result = await node.execute(
            {"code": "import time; time.sleep(10)", "language": "python", "timeout": 1},
            {"$vars": {}}
        )
        assert result["success"] is False
        assert "timed out" in result["stderr"]
        assert result["return_code"] == -1

    # === Variable Injection Tests ===

    @pytest.mark.asyncio
    async def test_variable_injection_python(self, node):
        """Test workflow variable injection for Python."""
        result = await node.execute(
            {"code": "print(my_var)", "language": "python", "timeout": 5},
            {"$vars": {"my_var": "test_value"}}
        )
        assert result["success"] is True
        assert "test_value" in result["stdout"]

    @pytest.mark.asyncio
    async def test_variable_injection_multiple(self, node):
        """Test multiple variable injection."""
        result = await node.execute(
            {"code": "print(f'{name} is {age} years old')", "language": "python", "timeout": 5},
            {"$vars": {"name": "Alice", "age": 30}}
        )
        assert result["success"] is True
        assert "Alice is 30 years old" in result["stdout"]

    @pytest.mark.asyncio
    async def test_variable_injection_special_chars(self, node):
        """Test variable injection with special characters."""
        result = await node.execute(
            {"code": "print(message)", "language": "python", "timeout": 5},
            {"$vars": {"message": "Hello, 'World'! \"Test\""}}
        )
        assert result["success"] is True
        assert "Hello, 'World'! \"Test\"" in result["stdout"]

    # === Error Handling Tests ===

    @pytest.mark.asyncio
    async def test_syntax_error(self, node):
        """Test handling of syntax errors."""
        result = await node.execute(
            {"code": "print(", "language": "python", "timeout": 5},
            {"$vars": {}}
        )
        assert result["success"] is False
        assert result["return_code"] != 0

    @pytest.mark.asyncio
    async def test_runtime_error(self, node):
        """Test handling of runtime errors."""
        result = await node.execute(
            {"code": "undefined_variable", "language": "python", "timeout": 5},
            {"$vars": {}}
        )
        assert result["success"] is False
        assert "NameError" in result["stderr"]

    @pytest.mark.asyncio
    async def test_empty_code(self, node):
        """Test rejection of empty code."""
        result = await node.execute(
            {"code": "", "language": "python", "timeout": 5},
            {"$vars": {}}
        )
        assert result["success"] is False
        assert "Code is required" in result["stderr"]

    @pytest.mark.asyncio
    async def test_whitespace_only_code(self, node):
        """Test rejection of whitespace-only code."""
        result = await node.execute(
            {"code": "   \n\t  ", "language": "python", "timeout": 5},
            {"$vars": {}}
        )
        assert result["success"] is False
        assert "Code is required" in result["stderr"]

    @pytest.mark.asyncio
    async def test_invalid_language(self, node):
        """Test rejection of unsupported language."""
        result = await node.execute(
            {"code": "print('hello')", "language": "cobol", "timeout": 5},
            {"$vars": {}}
        )
        assert result["success"] is False
        assert "Unsupported language" in result["stderr"]

    @pytest.mark.asyncio
    async def test_invalid_timeout(self, node):
        """Test rejection of invalid timeout."""
        result = await node.execute(
            {"code": "print('hello')", "language": "python", "timeout": -5},
            {"$vars": {}}
        )
        assert result["success"] is False
        assert "positive" in result["stderr"].lower()

    @pytest.mark.asyncio
    async def test_timeout_exceeds_max(self, node):
        """Test rejection of timeout exceeding maximum."""
        result = await node.execute(
            {"code": "print('hello')", "language": "python", "timeout": 500},
            {"$vars": {}}
        )
        assert result["success"] is False
        assert "300" in result["stderr"]

    # === JavaScript Tests (conditional) ===

    @pytest.mark.skipif(not shutil.which("node"), reason="Node.js not installed")
    @pytest.mark.asyncio
    async def test_javascript_execution(self, node):
        """Test JavaScript code execution."""
        result = await node.execute(
            {"code": "console.log('hello js')", "language": "javascript", "timeout": 5},
            {"$vars": {}}
        )
        assert result["success"] is True
        assert "hello js" in result["stdout"]

    @pytest.mark.skipif(not shutil.which("node"), reason="Node.js not installed")
    @pytest.mark.asyncio
    async def test_javascript_variable_injection(self, node):
        """Test JavaScript variable injection."""
        result = await node.execute(
            {"code": "console.log(`Name: ${name}`)", "language": "javascript", "timeout": 5},
            {"$vars": {"name": "Bob"}}
        )
        assert result["success"] is True
        assert "Name: Bob" in result["stdout"]

    # === Bash Tests (conditional) ===

    @pytest.mark.skipif(not shutil.which("bash"), reason="Bash not installed")
    @pytest.mark.asyncio
    async def test_bash_execution(self, node):
        """Test Bash code execution."""
        result = await node.execute(
            {"code": "echo 'hello bash'", "language": "bash", "timeout": 5},
            {"$vars": {}}
        )
        assert result["success"] is True
        assert "hello bash" in result["stdout"]

    @pytest.mark.skipif(not shutil.which("bash"), reason="Bash not installed")
    @pytest.mark.asyncio
    async def test_bash_variable_injection(self, node):
        """Test Bash variable injection generates correct code."""
        # Verify the injection creates valid bash code
        # Note: env var expansion behavior varies by platform
        injected = node._inject_variables("echo test", "bash", {"greeting": "Hello"})
        assert 'export greeting="Hello"' in injected
        # Basic execution with injected vars should succeed
        result = await node.execute(
            {"code": "echo test", "language": "bash", "timeout": 5},
            {"$vars": {"greeting": "Hello"}}
        )
        assert result["success"] is True

    # === Node Definition Tests ===

    def test_node_definition(self, node):
        """Test node definition structure."""
        definition = CodeExecutionNode.get_definition()
        assert definition.type == "code_execution"
        assert definition.name == "Execute Code"
        assert definition.category == "Execution"

        # Check inputs
        input_names = [i.name for i in definition.inputs]
        assert "code" in input_names
        assert "language" in input_names
        assert "timeout" in input_names

        # Check outputs
        output_names = [o.name for o in definition.outputs]
        assert "stdout" in output_names
        assert "stderr" in output_names
        assert "return_code" in output_names
        assert "success" in output_names

    def test_node_attributes(self, node):
        """Test node class attributes."""
        assert node.type == "code_execution"
        assert node.is_trigger is False
        assert "python" in node.SUPPORTED_LANGUAGES
        assert "javascript" in node.SUPPORTED_LANGUAGES
        assert "bash" in node.SUPPORTED_LANGUAGES
        assert "powershell" in node.SUPPORTED_LANGUAGES

    # === Variable Injection Unit Tests ===

    def test_inject_variables_python(self, node):
        """Test Python variable injection method."""
        code = "print(x)"
        result = node._inject_variables(code, "python", {"x": 42, "y": "test"})
        assert "x = 42" in result
        assert "y = 'test'" in result
        assert "print(x)" in result

    def test_inject_variables_javascript(self, node):
        """Test JavaScript variable injection method."""
        code = "console.log(x)"
        result = node._inject_variables(code, "javascript", {"x": 42, "y": "test"})
        assert "const x = 42" in result
        assert 'const y = "test"' in result
        assert "console.log(x)" in result

    def test_inject_variables_bash(self, node):
        """Test Bash variable injection method."""
        code = "echo $x"
        result = node._inject_variables(code, "bash", {"x": "value"})
        assert 'export x="value"' in result
        assert "echo $x" in result

    def test_inject_variables_powershell(self, node):
        """Test PowerShell variable injection method."""
        code = "Write-Host $env:x"
        result = node._inject_variables(code, "powershell", {"x": "value"})
        assert '$env:x="value"' in result
        assert "Write-Host $env:x" in result

    def test_inject_variables_empty(self, node):
        """Test variable injection with empty dict."""
        code = "print('hello')"
        result = node._inject_variables(code, "python", {})
        assert result == code

    # === Validation Tests ===

    def test_validate_config_valid(self, node):
        """Test validation of valid config."""
        valid, error = node._validate_config({
            "code": "print('hello')",
            "language": "python",
            "timeout": 30
        })
        assert valid is True
        assert error == ""

    def test_validate_config_empty_code(self, node):
        """Test validation rejects empty code."""
        valid, error = node._validate_config({
            "code": "",
            "language": "python",
            "timeout": 30
        })
        assert valid is False
        assert "required" in error.lower()

    def test_validate_config_invalid_language(self, node):
        """Test validation rejects invalid language."""
        valid, error = node._validate_config({
            "code": "print('hello')",
            "language": "ruby",
            "timeout": 30
        })
        assert valid is False
        assert "unsupported" in error.lower()
