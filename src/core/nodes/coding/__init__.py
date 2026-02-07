"""Coding and development workflow nodes."""

from src.core.nodes.coding.cicd import (
    GitHubActionsNode,
    NPMPublishNode,
    PyPIPublishNode,
    WaitForCINode,
)
from src.core.nodes.coding.debugging import (
    ConditionalBranchNode,
    DebugLoopNode,
    ErrorAggregatorNode,
    ErrorDetectorNode,
    RetryLoopNode,
    TryCatchNode,
    VerifyFixNode,
    WaitNode,
)
from src.core.nodes.coding.deployment import (
    CloudflareDeployNode,
    HerokuDeployNode,
    NetlifyDeployNode,
    RailwayDeployNode,
    SupabaseDeployNode,
    VercelDeployNode,
)
from src.core.nodes.coding.docker import (
    DockerBuildNode,
    DockerComposeNode,
    DockerExecNode,
    DockerLogsNode,
    DockerPushNode,
    DockerRunNode,
)
from src.core.nodes.coding.execution import (
    LintCodeNode,
    RunNodeJSNode,
    RunPythonNode,
    RunShellNode,
    RunTestsNode,
)
from src.core.nodes.coding.git import (
    GitBranchNode,
    GitCloneNode,
    GitCommitNode,
    GitDiffNode,
    GitPullNode,
    GitPushNode,
    GitStatusNode,
)

__all__ = [
    # Git
    "GitCloneNode",
    "GitCommitNode",
    "GitPushNode",
    "GitPullNode",
    "GitBranchNode",
    "GitStatusNode",
    "GitDiffNode",
    # Code Execution
    "RunPythonNode",
    "RunNodeJSNode",
    "RunShellNode",
    "RunTestsNode",
    "LintCodeNode",
    # Debugging & Error Handling
    "TryCatchNode",
    "RetryLoopNode",
    "ErrorDetectorNode",
    "DebugLoopNode",
    "VerifyFixNode",
    "ErrorAggregatorNode",
    "ConditionalBranchNode",
    "WaitNode",
    # Docker
    "DockerBuildNode",
    "DockerRunNode",
    "DockerComposeNode",
    "DockerExecNode",
    "DockerLogsNode",
    "DockerPushNode",
    # CI/CD
    "GitHubActionsNode",
    "WaitForCINode",
    "NPMPublishNode",
    "PyPIPublishNode",
    # Deployment
    "VercelDeployNode",
    "NetlifyDeployNode",
    "CloudflareDeployNode",
    "HerokuDeployNode",
    "RailwayDeployNode",
    "SupabaseDeployNode",
]

# All coding nodes for registry
CODING_NODES = [
    # Git Operations
    GitCloneNode,
    GitCommitNode,
    GitPushNode,
    GitPullNode,
    GitBranchNode,
    GitStatusNode,
    GitDiffNode,
    # Code Execution
    RunPythonNode,
    RunNodeJSNode,
    RunShellNode,
    RunTestsNode,
    LintCodeNode,
    # Debugging & Error Handling
    TryCatchNode,
    RetryLoopNode,
    ErrorDetectorNode,
    DebugLoopNode,
    VerifyFixNode,
    ErrorAggregatorNode,
    ConditionalBranchNode,
    WaitNode,
    # Docker
    DockerBuildNode,
    DockerRunNode,
    DockerComposeNode,
    DockerExecNode,
    DockerLogsNode,
    DockerPushNode,
    # CI/CD
    GitHubActionsNode,
    WaitForCINode,
    NPMPublishNode,
    PyPIPublishNode,
    # Deployment
    VercelDeployNode,
    NetlifyDeployNode,
    CloudflareDeployNode,
    HerokuDeployNode,
    RailwayDeployNode,
    SupabaseDeployNode,
]
