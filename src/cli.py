"""
Skynette CLI - Command Line Interface

Run workflows from the command line:
    python -m src.cli run workflow.yaml
    python -m src.cli list
    python -m src.cli exec <workflow-id>
"""

import argparse
import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.workflow.models import Workflow, WorkflowExecution
from src.core.workflow.executor import WorkflowExecutor
from src.data.storage import get_storage

# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def print_banner():
    """Print Skynette CLI banner."""
    banner = f"""{Colors.CYAN}{Colors.BOLD}
   ____  _  ____   ___  _ _____ _____ _____ _____
  / ___|| |/ /\\ \\ / / \\| | ____|_   _|_   _| ____|
  \\___ \\| ' /  \\ V /|  ` |  _|   | |   | | |  _|
   ___) | . \\   | | | |\\  | |___  | |   | | | |___
  |____/|_|\\_\\  |_| |_| \\_|_____| |_|   |_| |_____|
{Colors.RESET}
{Colors.DIM}  AI-Native Workflow Automation Platform - CLI v1.0.0{Colors.RESET}
"""
    print(banner)


def format_status(status: str) -> str:
    """Format status with color."""
    colors = {
        'completed': Colors.GREEN,
        'running': Colors.BLUE,
        'failed': Colors.RED,
        'pending': Colors.YELLOW,
    }
    color = colors.get(status, Colors.RESET)
    return f"{color}{status}{Colors.RESET}"


def format_duration(ms: float) -> str:
    """Format duration in human-readable form."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:
        return f"{ms/1000:.1f}s"
    else:
        return f"{ms/60000:.1f}m"


# ==================== Commands ====================

async def cmd_run(args):
    """Run a workflow from a YAML file."""
    yaml_path = Path(args.file)

    if not yaml_path.exists():
        print(f"{Colors.RED}Error: File not found: {yaml_path}{Colors.RESET}")
        return 1

    # Load workflow from file
    print(f"{Colors.CYAN}Loading workflow from {yaml_path}...{Colors.RESET}")

    with open(yaml_path, 'r', encoding='utf-8') as f:
        workflow = Workflow.from_yaml(f.read())

    print(f"{Colors.GREEN}Loaded: {workflow.name}{Colors.RESET}")
    print(f"{Colors.DIM}  Nodes: {len(workflow.nodes)}{Colors.RESET}")
    print(f"{Colors.DIM}  Description: {workflow.description or 'N/A'}{Colors.RESET}")
    print()

    # Parse trigger data
    trigger_data = {}
    if args.data:
        try:
            trigger_data = json.loads(args.data)
        except json.JSONDecodeError:
            print(f"{Colors.RED}Error: Invalid JSON data{Colors.RESET}")
            return 1

    # Execute workflow
    print(f"{Colors.CYAN}Executing workflow...{Colors.RESET}")
    print("-" * 50)

    executor = WorkflowExecutor()
    execution = await executor.execute(
        workflow,
        trigger_data=trigger_data,
        trigger_type="cli"
    )

    # Print results
    print("-" * 50)
    print()
    print(f"{Colors.BOLD}Execution Results:{Colors.RESET}")
    print(f"  Status: {format_status(execution.status)}")
    print(f"  Duration: {format_duration(execution.duration_ms)}")

    if execution.error:
        print(f"  Error: {Colors.RED}{execution.error}{Colors.RESET}")

    print()
    print(f"{Colors.BOLD}Node Results:{Colors.RESET}")

    for result in execution.node_results:
        node = workflow.get_node(result.node_id)
        node_name = node.name if node else result.node_id[:8]
        status_icon = "✓" if result.success else "✗"
        status_color = Colors.GREEN if result.success else Colors.RED

        print(f"  {status_color}{status_icon}{Colors.RESET} {node_name} ({format_duration(result.duration_ms)})")

        if args.verbose and result.data:
            data_str = json.dumps(result.data, indent=4, default=str)
            for line in data_str.split('\n'):
                print(f"      {Colors.DIM}{line}{Colors.RESET}")

        if result.error:
            print(f"      {Colors.RED}Error: {result.error}{Colors.RESET}")

    # Save execution if requested
    if args.save:
        storage = get_storage()
        storage.save_workflow(workflow)
        storage.save_execution(execution)
        print(f"\n{Colors.GREEN}Execution saved to history.{Colors.RESET}")

    # Output result data as JSON if requested
    if args.output:
        output_data = {
            "status": execution.status,
            "duration_ms": execution.duration_ms,
            "error": execution.error,
            "results": {r.node_id: r.data for r in execution.node_results if r.success}
        }

        if args.output == '-':
            print(json.dumps(output_data, indent=2, default=str))
        else:
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"{Colors.GREEN}Output written to {args.output}{Colors.RESET}")

    return 0 if execution.status == 'completed' else 1


async def cmd_exec(args):
    """Execute a workflow by ID from the database."""
    storage = get_storage()
    workflow = storage.load_workflow(args.workflow_id)

    if not workflow:
        print(f"{Colors.RED}Error: Workflow not found: {args.workflow_id}{Colors.RESET}")
        return 1

    # Parse trigger data
    trigger_data = {}
    if args.data:
        try:
            trigger_data = json.loads(args.data)
        except json.JSONDecodeError:
            print(f"{Colors.RED}Error: Invalid JSON data{Colors.RESET}")
            return 1

    print(f"{Colors.CYAN}Executing: {workflow.name}{Colors.RESET}")
    print("-" * 50)

    executor = WorkflowExecutor()

    # Resume from node if specified
    start_node = args.resume_from if hasattr(args, 'resume_from') else None

    execution = await executor.execute(
        workflow,
        trigger_data=trigger_data,
        trigger_type="cli"
    )

    # Save execution
    storage.save_execution(execution)

    # Print summary
    print("-" * 50)
    print(f"Status: {format_status(execution.status)}")
    print(f"Duration: {format_duration(execution.duration_ms)}")

    if execution.error:
        print(f"Error: {Colors.RED}{execution.error}{Colors.RESET}")

    return 0 if execution.status == 'completed' else 1


def cmd_list(args):
    """List all workflows."""
    storage = get_storage()
    workflows = storage.list_workflows()

    if not workflows:
        print(f"{Colors.YELLOW}No workflows found.{Colors.RESET}")
        print(f"{Colors.DIM}Create one with: skynette run workflow.yaml --save{Colors.RESET}")
        return 0

    print(f"{Colors.BOLD}Workflows ({len(workflows)}):{Colors.RESET}")
    print()

    for wf in workflows:
        tags = ", ".join(wf['tags']) if wf['tags'] else ""
        updated = wf['updated_at'][:10] if wf['updated_at'] else "N/A"

        print(f"  {Colors.CYAN}{wf['id'][:8]}{Colors.RESET}  {wf['name']}")
        print(f"           {Colors.DIM}{wf['description'] or 'No description'}{Colors.RESET}")
        if tags:
            print(f"           {Colors.YELLOW}[{tags}]{Colors.RESET}")
        print(f"           Updated: {updated}")
        print()

    return 0


def cmd_history(args):
    """Show execution history."""
    storage = get_storage()
    executions = storage.get_executions(
        workflow_id=args.workflow_id if hasattr(args, 'workflow_id') else None,
        limit=args.limit
    )

    if not executions:
        print(f"{Colors.YELLOW}No executions found.{Colors.RESET}")
        return 0

    print(f"{Colors.BOLD}Execution History ({len(executions)}):{Colors.RESET}")
    print()

    for ex in executions:
        started = ex['started_at'][:19] if ex['started_at'] else "N/A"
        duration = format_duration(ex['duration_ms']) if ex['duration_ms'] else "N/A"

        print(f"  {Colors.CYAN}{ex['id'][:8]}{Colors.RESET}  {ex['workflow_name'] or 'Unknown'}")
        print(f"           Status: {format_status(ex['status'])}  |  Duration: {duration}")
        print(f"           Started: {started}  |  Trigger: {ex['trigger_type']}")
        if ex['error']:
            print(f"           {Colors.RED}Error: {ex['error'][:50]}...{Colors.RESET}")
        print()

    return 0


def cmd_validate(args):
    """Validate a workflow YAML file."""
    yaml_path = Path(args.file)

    if not yaml_path.exists():
        print(f"{Colors.RED}Error: File not found: {yaml_path}{Colors.RESET}")
        return 1

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            workflow = Workflow.from_yaml(f.read())

        print(f"{Colors.GREEN}✓ Workflow is valid{Colors.RESET}")
        print()
        print(f"  Name: {workflow.name}")
        print(f"  Nodes: {len(workflow.nodes)}")
        print(f"  Connections: {len(workflow.connections)}")

        # Check for issues
        issues = []

        # Check for unconnected nodes
        connected_nodes = set()
        for conn in workflow.connections:
            connected_nodes.add(conn.source_node_id)
            connected_nodes.add(conn.target_node_id)

        for node in workflow.nodes:
            if node.id not in connected_nodes and len(workflow.nodes) > 1:
                issues.append(f"Node '{node.name}' is not connected")

        # Check for missing node types
        from src.core.nodes.registry import NodeRegistry
        registry = NodeRegistry()
        for node in workflow.nodes:
            if not registry.get_handler(node.type):
                issues.append(f"Unknown node type: {node.type}")

        if issues:
            print()
            print(f"{Colors.YELLOW}Warnings:{Colors.RESET}")
            for issue in issues:
                print(f"  - {issue}")

        return 0

    except Exception as e:
        print(f"{Colors.RED}✗ Validation failed: {e}{Colors.RESET}")
        return 1


def cmd_export(args):
    """Export a workflow to YAML."""
    storage = get_storage()
    workflow = storage.load_workflow(args.workflow_id)

    if not workflow:
        print(f"{Colors.RED}Error: Workflow not found: {args.workflow_id}{Colors.RESET}")
        return 1

    yaml_content = workflow.to_yaml()

    if args.output == '-':
        print(yaml_content)
    else:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        print(f"{Colors.GREEN}Exported to {output_path}{Colors.RESET}")

    return 0


def cmd_credentials(args):
    """Manage credentials."""
    from src.data.credentials import CredentialVault

    vault = CredentialVault()

    if args.action == 'list':
        creds = vault.list_credentials()
        if not creds:
            print(f"{Colors.YELLOW}No credentials stored.{Colors.RESET}")
            return 0

        print(f"{Colors.BOLD}Stored Credentials:{Colors.RESET}")
        for cred in creds:
            print(f"  {Colors.CYAN}{cred['id'][:8]}{Colors.RESET}  {cred['name']} ({cred['service']})")
        return 0

    elif args.action == 'add':
        name = input("Credential name: ")
        service = input("Service (e.g., openai, slack, github): ")

        # Collect credential data
        data = {}
        print("Enter credential fields (empty line to finish):")
        while True:
            field = input("  Field name: ").strip()
            if not field:
                break
            value = input(f"  {field}: ").strip()
            data[field] = value

        vault.save_credential(name, service, data)
        print(f"{Colors.GREEN}Credential saved.{Colors.RESET}")
        return 0

    elif args.action == 'delete':
        if vault.delete_credential(args.credential_id):
            print(f"{Colors.GREEN}Credential deleted.{Colors.RESET}")
        else:
            print(f"{Colors.RED}Credential not found.{Colors.RESET}")
        return 0

    return 0


# ==================== Main Entry Point ====================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='skynette',
        description='Skynette CLI - AI-Native Workflow Automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  skynette run workflow.yaml              Run a workflow from file
  skynette run workflow.yaml -d '{"key":"value"}'  Run with trigger data
  skynette list                           List saved workflows
  skynette exec abc123                    Execute workflow by ID
  skynette history                        Show execution history
  skynette validate workflow.yaml         Validate a workflow file
  skynette export abc123 -o workflow.yaml Export workflow to file
        """
    )

    parser.add_argument('--version', action='version', version='Skynette CLI 1.0.0')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--no-banner', action='store_true', help='Suppress banner')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run a workflow from YAML file')
    run_parser.add_argument('file', help='Path to workflow YAML file')
    run_parser.add_argument('-d', '--data', help='Trigger data as JSON string')
    run_parser.add_argument('-o', '--output', help='Output file for results (- for stdout)')
    run_parser.add_argument('--save', action='store_true', help='Save workflow and execution to database')
    run_parser.set_defaults(func=lambda args: asyncio.run(cmd_run(args)))

    # Exec command
    exec_parser = subparsers.add_parser('exec', help='Execute a saved workflow by ID')
    exec_parser.add_argument('workflow_id', help='Workflow ID')
    exec_parser.add_argument('-d', '--data', help='Trigger data as JSON string')
    exec_parser.add_argument('--resume-from', help='Resume from specific node ID')
    exec_parser.set_defaults(func=lambda args: asyncio.run(cmd_exec(args)))

    # List command
    list_parser = subparsers.add_parser('list', aliases=['ls'], help='List saved workflows')
    list_parser.set_defaults(func=cmd_list)

    # History command
    history_parser = subparsers.add_parser('history', help='Show execution history')
    history_parser.add_argument('workflow_id', nargs='?', help='Filter by workflow ID')
    history_parser.add_argument('-n', '--limit', type=int, default=20, help='Number of results')
    history_parser.set_defaults(func=cmd_history)

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a workflow file')
    validate_parser.add_argument('file', help='Path to workflow YAML file')
    validate_parser.set_defaults(func=cmd_validate)

    # Export command
    export_parser = subparsers.add_parser('export', help='Export a workflow to YAML')
    export_parser.add_argument('workflow_id', help='Workflow ID')
    export_parser.add_argument('-o', '--output', default='-', help='Output file (- for stdout)')
    export_parser.set_defaults(func=cmd_export)

    # Credentials command
    creds_parser = subparsers.add_parser('credentials', aliases=['creds'], help='Manage credentials')
    creds_parser.add_argument('action', choices=['list', 'add', 'delete'], help='Action to perform')
    creds_parser.add_argument('credential_id', nargs='?', help='Credential ID (for delete)')
    creds_parser.set_defaults(func=cmd_credentials)

    # Parse arguments
    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)

    if not args.no_banner and args.command:
        print_banner()

    # Execute command
    if args.command:
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
