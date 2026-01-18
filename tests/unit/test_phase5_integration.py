"""
Phase 5 Integration Tests

Tests to verify all Phase 5 modules are importable and functional.
Covers: WorkflowBridge, RAG system, Code Execution, AI Panel integration.
"""

import pytest


class TestPhase5ModuleImports:
    """Tests that all Phase 5 modules can be imported."""

    def test_workflow_bridge_import(self):
        """WorkflowBridge and WorkflowFormat can be imported."""
        from src.ui.views.code_editor.workflow_bridge import WorkflowBridge, WorkflowFormat

        assert WorkflowBridge is not None
        assert WorkflowFormat is not None

    def test_project_indexer_import(self):
        """ProjectIndexer can be imported."""
        from src.rag.project_indexer import ProjectIndexer

        assert ProjectIndexer is not None

    def test_dimension_validator_import(self):
        """DimensionValidator and utilities can be imported."""
        from src.rag.dimension_validator import (
            DimensionValidator,
            DimensionMismatchError,
            validate_embeddings,
            EXPECTED_DIMENSIONS,
        )

        assert DimensionValidator is not None
        assert DimensionMismatchError is not None
        assert validate_embeddings is not None
        assert isinstance(EXPECTED_DIMENSIONS, dict)

    def test_code_execution_node_import(self):
        """CodeExecutionNode can be imported."""
        from src.core.nodes.execution.code_runner import CodeExecutionNode

        assert CodeExecutionNode is not None

    def test_rag_context_provider_import(self):
        """RAGContextProvider can be imported."""
        from src.ui.views.code_editor.ai_panel.rag_context import RAGContextProvider

        assert RAGContextProvider is not None


class TestPhase5WorkflowFormats:
    """Tests for WorkflowFormat enum."""

    def test_workflow_formats_defined(self):
        """All expected workflow formats are defined."""
        from src.ui.views.code_editor.workflow_bridge import WorkflowFormat

        assert hasattr(WorkflowFormat, "YAML")
        assert hasattr(WorkflowFormat, "JSON")
        assert hasattr(WorkflowFormat, "PYTHON_DSL")

    def test_workflow_format_values(self):
        """WorkflowFormat values are correct."""
        from src.ui.views.code_editor.workflow_bridge import WorkflowFormat

        assert WorkflowFormat.YAML.value == "yaml"
        assert WorkflowFormat.JSON.value == "json"
        assert WorkflowFormat.PYTHON_DSL.value == "python"


class TestPhase5CodeExecutionNode:
    """Tests for CodeExecutionNode configuration."""

    def test_node_type_defined(self):
        """CodeExecutionNode has correct type."""
        from src.core.nodes.execution.code_runner import CodeExecutionNode

        assert CodeExecutionNode.type == "code_execution"

    def test_supported_languages(self):
        """CodeExecutionNode supports expected languages."""
        from src.core.nodes.execution.code_runner import CodeExecutionNode

        assert "python" in CodeExecutionNode.SUPPORTED_LANGUAGES
        assert "javascript" in CodeExecutionNode.SUPPORTED_LANGUAGES
        assert "bash" in CodeExecutionNode.SUPPORTED_LANGUAGES
        assert "powershell" in CodeExecutionNode.SUPPORTED_LANGUAGES

    def test_max_timeout_defined(self):
        """CodeExecutionNode has maximum timeout."""
        from src.core.nodes.execution.code_runner import CodeExecutionNode

        assert CodeExecutionNode.MAX_TIMEOUT == 300  # 5 minutes

    def test_node_has_inputs_outputs(self):
        """CodeExecutionNode defines inputs and outputs."""
        from src.core.nodes.execution.code_runner import CodeExecutionNode

        inputs = CodeExecutionNode.get_inputs()
        outputs = CodeExecutionNode.get_outputs()

        assert len(inputs) > 0
        assert len(outputs) > 0

        # Check for expected fields
        input_names = [i.name for i in inputs]
        assert "code" in input_names
        assert "language" in input_names
        assert "timeout" in input_names

        output_names = [o.name for o in outputs]
        assert "stdout" in output_names
        assert "stderr" in output_names
        assert "return_code" in output_names
        assert "success" in output_names


class TestPhase5DimensionValidation:
    """Tests for dimension validation utilities."""

    def test_known_model_dimensions(self):
        """Known model dimensions are correctly defined."""
        from src.rag.dimension_validator import EXPECTED_DIMENSIONS

        assert EXPECTED_DIMENSIONS["all-MiniLM-L6-v2"] == 384
        assert EXPECTED_DIMENSIONS["text-embedding-ada-002"] == 1536
        assert EXPECTED_DIMENSIONS["text-embedding-3-small"] == 1536
        assert EXPECTED_DIMENSIONS["text-embedding-3-large"] == 3072

    def test_validate_embeddings_utility(self):
        """validate_embeddings utility works correctly."""
        from src.rag.dimension_validator import validate_embeddings

        embeddings = [[0.1] * 384, [0.2] * 384]
        dim = validate_embeddings(embeddings)

        assert dim == 384


class TestPhase5ProjectIndexer:
    """Tests for ProjectIndexer configuration."""

    def test_supported_extensions(self):
        """ProjectIndexer has supported extensions."""
        from src.rag.project_indexer import SUPPORTED_EXTENSIONS

        # Programming languages
        assert ".py" in SUPPORTED_EXTENSIONS
        assert ".js" in SUPPORTED_EXTENSIONS
        assert ".ts" in SUPPORTED_EXTENSIONS
        assert ".go" in SUPPORTED_EXTENSIONS
        assert ".rs" in SUPPORTED_EXTENSIONS

        # Web files
        assert ".html" in SUPPORTED_EXTENSIONS
        assert ".css" in SUPPORTED_EXTENSIONS

        # Config files
        assert ".json" in SUPPORTED_EXTENSIONS
        assert ".yaml" in SUPPORTED_EXTENSIONS

    def test_file_size_limits_defined(self):
        """File size limits are defined."""
        from src.rag.project_indexer import MAX_FILE_SIZE_WARN, MAX_FILE_SIZE_REFUSE

        assert MAX_FILE_SIZE_WARN == 50 * 1024  # 50KB
        assert MAX_FILE_SIZE_REFUSE == 500 * 1024  # 500KB


class TestPhase5Integration:
    """Integration tests for Phase 5 components working together."""

    def test_workflow_model_has_yaml_methods(self):
        """Workflow model has YAML serialization methods."""
        from src.core.workflow.models import Workflow

        workflow = Workflow(name="Test")

        # Should have to_yaml method
        assert hasattr(workflow, "to_yaml")
        yaml_output = workflow.to_yaml()
        assert "name: Test" in yaml_output

    def test_workflow_model_has_python_dsl_methods(self):
        """Workflow model has Python DSL methods."""
        from src.core.workflow.models import Workflow

        workflow = Workflow(name="DSL Test", description="Testing DSL")

        # Should have to_python_dsl method
        assert hasattr(workflow, "to_python_dsl")
        dsl_output = workflow.to_python_dsl()
        assert 'Workflow(name="DSL Test")' in dsl_output

        # Should have from_python_dsl class method
        assert hasattr(Workflow, "from_python_dsl")

    def test_workflow_model_python_dsl_roundtrip(self):
        """Workflow survives Python DSL roundtrip."""
        from src.core.workflow.models import Workflow, WorkflowNode

        original = Workflow(
            name="Roundtrip Test",
            description="Testing",
            nodes=[
                WorkflowNode(id="n1", type="manual_trigger", name="Start"),
            ],
        )

        # Convert to DSL
        dsl = original.to_python_dsl()

        # Parse back
        restored = Workflow.from_python_dsl(dsl)

        assert restored.name == "Roundtrip Test"
        assert restored.description == "Testing"

    def test_base_node_inheritance(self):
        """CodeExecutionNode inherits from BaseNode."""
        from src.core.nodes.base import BaseNode
        from src.core.nodes.execution.code_runner import CodeExecutionNode

        assert issubclass(CodeExecutionNode, BaseNode)


class TestPhase5Security:
    """Security-related tests for Phase 5 features."""

    def test_python_dsl_uses_restricted_exec(self):
        """Python DSL parsing is restricted."""
        from src.core.workflow.models import Workflow

        # Try to execute malicious code
        malicious_dsl = '''
import os
workflow = Workflow(name="Malicious")
'''
        with pytest.raises(ValueError):
            Workflow.from_python_dsl(malicious_dsl)

    def test_yaml_uses_safe_load(self):
        """YAML parsing uses safe_load."""
        from src.core.workflow.models import Workflow

        # YAML with Python object tag should fail
        dangerous_yaml = """
name: !!python/object:os.system ["echo pwned"]
version: "1.0.0"
nodes: []
connections: []
variables: {}
settings: {}
tags: []
"""
        with pytest.raises((ValueError, Exception)):
            Workflow.from_yaml(dangerous_yaml)
