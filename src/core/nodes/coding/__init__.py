"""Coding and development workflow nodes."""

from src.core.nodes.coding.git import (
    GitCloneNode,
    GitCommitNode,
    GitPushNode,
    GitPullNode,
    GitBranchNode,
    GitStatusNode,
    GitDiffNode,
)

from src.core.nodes.coding.execution import (
    RunPythonNode,
    RunNodeJSNode,
    RunShellNode,
    RunTestsNode,
    LintCodeNode,
)

from src.core.nodes.coding.debugging import (
    TryCatchNode,
    RetryLoopNode,
    ErrorDetectorNode,
    DebugLoopNode,
    VerifyFixNode,
    ErrorAggregatorNode,
    ConditionalBranchNode,
    WaitNode,
)

from src.core.nodes.coding.docker import (
    DockerBuildNode,
    DockerRunNode,
    DockerComposeNode,
    DockerExecNode,
    DockerLogsNode,
    DockerPushNode,
)

from src.core.nodes.coding.cicd import (
    GitHubActionsNode,
    WaitForCINode,
    NPMPublishNode,
    PyPIPublishNode,
)

from src.core.nodes.coding.deployment import (
    VercelDeployNode,
    NetlifyDeployNode,
    CloudflareDeployNode,
    HerokuDeployNode,
    RailwayDeployNode,
    SupabaseDeployNode,
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
