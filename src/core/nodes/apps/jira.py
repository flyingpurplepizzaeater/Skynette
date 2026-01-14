"""
Jira Integration Nodes - Manage Jira projects and issues.

Uses Jira REST API with Basic Auth (email + API token).
"""

import base64
from typing import Optional

from src.core.nodes.base import BaseNode, NodeField, FieldType


def _get_credential(credential_id: Optional[str]) -> Optional[dict]:
    """Load credential from vault if ID is provided."""
    if not credential_id:
        return None
    try:
        from src.data.credentials import CredentialVault
        vault = CredentialVault()
        cred = vault.get_credential(credential_id)
        if cred:
            return cred.get("data", {})
    except Exception:
        pass
    return None


def _get_auth(config: dict) -> tuple[str, str, str]:
    """Get domain, email, and API token from config or credential."""
    credential_id = config.get("credential")
    cred_data = _get_credential(credential_id) if credential_id else None

    if cred_data:
        domain = cred_data.get("domain", "") or config.get("domain", "")
        email = cred_data.get("email", "")
        api_token = cred_data.get("api_token", "") or cred_data.get("password", "")
    else:
        domain = config.get("domain", "")
        email = config.get("email", "")
        api_token = config.get("api_token", "")

    return domain, email, api_token


def _make_auth_header(email: str, api_token: str) -> str:
    """Create Basic Auth header value."""
    credentials = f"{email}:{api_token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


class JiraListProjectsNode(BaseNode):
    """
    List all Jira projects accessible to the user.
    """

    type = "jira-list-projects"
    name = "Jira: List Projects"
    category = "Apps"
    description = "List all Jira projects"
    icon = "folder"
    color = "#0052CC"  # Jira blue

    inputs = [
        NodeField(
            name="credential",
            label="Jira Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Jira credential.",
            credential_service="jira",
        ),
        NodeField(
            name="domain",
            label="Jira Domain",
            type=FieldType.STRING,
            required=False,
            description="Your Jira domain (e.g., yourcompany.atlassian.net).",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=False,
            description="Your Atlassian account email.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.SECRET,
            required=False,
            description="Jira API token (create at id.atlassian.com).",
        ),
    ]

    outputs = [
        NodeField(
            name="projects",
            label="Projects",
            type=FieldType.JSON,
            description="List of projects.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of projects.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List Jira projects."""
        import httpx

        domain, email, api_token = _get_auth(config)

        if not domain:
            raise ValueError("Jira domain is required")
        if not email or not api_token:
            raise ValueError("Email and API token are required")

        # Normalize domain
        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

        headers = {
            "Authorization": _make_auth_header(email, api_token),
            "Accept": "application/json",
        }

        url = f"https://{domain}/rest/api/3/project"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                projects = response.json()
                return {
                    "projects": projects,
                    "count": len(projects),
                }
            else:
                return {
                    "projects": [],
                    "count": 0,
                }


class JiraSearchIssuesNode(BaseNode):
    """
    Search for issues using JQL (Jira Query Language).
    """

    type = "jira-search-issues"
    name = "Jira: Search Issues"
    category = "Apps"
    description = "Search issues using JQL"
    icon = "search"
    color = "#0052CC"

    inputs = [
        NodeField(
            name="credential",
            label="Jira Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Jira credential.",
            credential_service="jira",
        ),
        NodeField(
            name="domain",
            label="Jira Domain",
            type=FieldType.STRING,
            required=False,
            description="Your Jira domain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=False,
            description="Your Atlassian account email.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.SECRET,
            required=False,
            description="Jira API token.",
        ),
        NodeField(
            name="jql",
            label="JQL Query",
            type=FieldType.STRING,
            required=True,
            description="JQL query (e.g., 'project = PROJ AND status = Open').",
        ),
        NodeField(
            name="max_results",
            label="Max Results",
            type=FieldType.NUMBER,
            required=False,
            default=50,
            description="Maximum number of issues to return.",
        ),
        NodeField(
            name="fields",
            label="Fields",
            type=FieldType.STRING,
            required=False,
            default="summary,status,assignee,priority,created,updated",
            description="Comma-separated list of fields to return.",
        ),
    ]

    outputs = [
        NodeField(
            name="issues",
            label="Issues",
            type=FieldType.JSON,
            description="List of issues.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of issues returned.",
        ),
        NodeField(
            name="total",
            label="Total",
            type=FieldType.NUMBER,
            description="Total matching issues.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Search Jira issues."""
        import httpx

        domain, email, api_token = _get_auth(config)

        if not domain:
            raise ValueError("Jira domain is required")
        if not email or not api_token:
            raise ValueError("Email and API token are required")

        jql = config.get("jql", "")
        if not jql:
            raise ValueError("JQL query is required")

        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

        headers = {
            "Authorization": _make_auth_header(email, api_token),
            "Accept": "application/json",
        }

        params = {
            "jql": jql,
            "maxResults": config.get("max_results", 50),
        }

        fields = config.get("fields", "")
        if fields:
            params["fields"] = fields

        url = f"https://{domain}/rest/api/3/search"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])
                return {
                    "issues": issues,
                    "count": len(issues),
                    "total": data.get("total", len(issues)),
                }
            else:
                return {
                    "issues": [],
                    "count": 0,
                    "total": 0,
                }


class JiraGetIssueNode(BaseNode):
    """
    Get details of a single Jira issue.
    """

    type = "jira-get-issue"
    name = "Jira: Get Issue"
    category = "Apps"
    description = "Get issue details by key"
    icon = "description"
    color = "#0052CC"

    inputs = [
        NodeField(
            name="credential",
            label="Jira Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Jira credential.",
            credential_service="jira",
        ),
        NodeField(
            name="domain",
            label="Jira Domain",
            type=FieldType.STRING,
            required=False,
            description="Your Jira domain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=False,
            description="Your Atlassian account email.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.SECRET,
            required=False,
            description="Jira API token.",
        ),
        NodeField(
            name="issue_key",
            label="Issue Key",
            type=FieldType.STRING,
            required=True,
            description="Issue key (e.g., PROJ-123).",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the issue was found.",
        ),
        NodeField(
            name="issue",
            label="Issue",
            type=FieldType.JSON,
            description="The issue data.",
        ),
        NodeField(
            name="summary",
            label="Summary",
            type=FieldType.STRING,
            description="Issue summary.",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.STRING,
            description="Issue status.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Get Jira issue details."""
        import httpx

        domain, email, api_token = _get_auth(config)

        if not domain:
            raise ValueError("Jira domain is required")
        if not email or not api_token:
            raise ValueError("Email and API token are required")

        issue_key = config.get("issue_key", "")
        if not issue_key:
            raise ValueError("Issue key is required")

        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

        headers = {
            "Authorization": _make_auth_header(email, api_token),
            "Accept": "application/json",
        }

        url = f"https://{domain}/rest/api/3/issue/{issue_key}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                issue = response.json()
                fields = issue.get("fields", {})
                status_obj = fields.get("status", {})
                return {
                    "success": True,
                    "issue": issue,
                    "summary": fields.get("summary", ""),
                    "status": status_obj.get("name", "") if status_obj else "",
                }
            else:
                return {
                    "success": False,
                    "issue": {},
                    "summary": "",
                    "status": "",
                }


class JiraCreateIssueNode(BaseNode):
    """
    Create a new Jira issue.
    """

    type = "jira-create-issue"
    name = "Jira: Create Issue"
    category = "Apps"
    description = "Create a new issue"
    icon = "add_box"
    color = "#0052CC"

    inputs = [
        NodeField(
            name="credential",
            label="Jira Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Jira credential.",
            credential_service="jira",
        ),
        NodeField(
            name="domain",
            label="Jira Domain",
            type=FieldType.STRING,
            required=False,
            description="Your Jira domain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=False,
            description="Your Atlassian account email.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.SECRET,
            required=False,
            description="Jira API token.",
        ),
        NodeField(
            name="project_key",
            label="Project Key",
            type=FieldType.STRING,
            required=True,
            description="Project key (e.g., PROJ).",
        ),
        NodeField(
            name="issue_type",
            label="Issue Type",
            type=FieldType.SELECT,
            required=True,
            default="Task",
            options=[
                {"value": "Task", "label": "Task"},
                {"value": "Bug", "label": "Bug"},
                {"value": "Story", "label": "Story"},
                {"value": "Epic", "label": "Epic"},
                {"value": "Subtask", "label": "Subtask"},
            ],
            description="Type of issue to create.",
        ),
        NodeField(
            name="summary",
            label="Summary",
            type=FieldType.STRING,
            required=True,
            description="Issue summary/title.",
        ),
        NodeField(
            name="description",
            label="Description",
            type=FieldType.TEXT,
            required=False,
            description="Issue description.",
        ),
        NodeField(
            name="priority",
            label="Priority",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "Highest", "label": "Highest"},
                {"value": "High", "label": "High"},
                {"value": "Medium", "label": "Medium"},
                {"value": "Low", "label": "Low"},
                {"value": "Lowest", "label": "Lowest"},
            ],
            description="Issue priority.",
        ),
        NodeField(
            name="assignee",
            label="Assignee",
            type=FieldType.STRING,
            required=False,
            description="Assignee account ID.",
        ),
        NodeField(
            name="labels",
            label="Labels",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated labels.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the issue was created.",
        ),
        NodeField(
            name="issue_key",
            label="Issue Key",
            type=FieldType.STRING,
            description="Created issue key.",
        ),
        NodeField(
            name="issue_id",
            label="Issue ID",
            type=FieldType.STRING,
            description="Created issue ID.",
        ),
        NodeField(
            name="issue_url",
            label="Issue URL",
            type=FieldType.STRING,
            description="URL to the created issue.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Create Jira issue."""
        import httpx

        domain, email, api_token = _get_auth(config)

        if not domain:
            raise ValueError("Jira domain is required")
        if not email or not api_token:
            raise ValueError("Email and API token are required")

        project_key = config.get("project_key", "")
        if not project_key:
            raise ValueError("Project key is required")

        summary = config.get("summary", "")
        if not summary:
            raise ValueError("Summary is required")

        issue_type = config.get("issue_type", "Task")

        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

        headers = {
            "Authorization": _make_auth_header(email, api_token),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Build issue fields
        fields = {
            "project": {"key": project_key},
            "issuetype": {"name": issue_type},
            "summary": summary,
        }

        # Add description in Atlassian Document Format
        description = config.get("description", "")
        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            }

        priority = config.get("priority")
        if priority:
            fields["priority"] = {"name": priority}

        assignee = config.get("assignee")
        if assignee:
            fields["assignee"] = {"accountId": assignee}

        labels = config.get("labels", "")
        if labels:
            fields["labels"] = [l.strip() for l in labels.split(",") if l.strip()]

        body = {"fields": fields}
        url = f"https://{domain}/rest/api/3/issue"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)

            if response.status_code in (200, 201):
                data = response.json()
                issue_key = data.get("key", "")
                return {
                    "success": True,
                    "issue_key": issue_key,
                    "issue_id": data.get("id", ""),
                    "issue_url": f"https://{domain}/browse/{issue_key}",
                }
            else:
                return {
                    "success": False,
                    "issue_key": "",
                    "issue_id": "",
                    "issue_url": "",
                }


class JiraUpdateIssueNode(BaseNode):
    """
    Update an existing Jira issue.
    """

    type = "jira-update-issue"
    name = "Jira: Update Issue"
    category = "Apps"
    description = "Update an existing issue"
    icon = "edit"
    color = "#0052CC"

    inputs = [
        NodeField(
            name="credential",
            label="Jira Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Jira credential.",
            credential_service="jira",
        ),
        NodeField(
            name="domain",
            label="Jira Domain",
            type=FieldType.STRING,
            required=False,
            description="Your Jira domain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=False,
            description="Your Atlassian account email.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.SECRET,
            required=False,
            description="Jira API token.",
        ),
        NodeField(
            name="issue_key",
            label="Issue Key",
            type=FieldType.STRING,
            required=True,
            description="Issue key (e.g., PROJ-123).",
        ),
        NodeField(
            name="summary",
            label="Summary",
            type=FieldType.STRING,
            required=False,
            description="New summary (leave empty to keep current).",
        ),
        NodeField(
            name="description",
            label="Description",
            type=FieldType.TEXT,
            required=False,
            description="New description.",
        ),
        NodeField(
            name="priority",
            label="Priority",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "", "label": "Don't change"},
                {"value": "Highest", "label": "Highest"},
                {"value": "High", "label": "High"},
                {"value": "Medium", "label": "Medium"},
                {"value": "Low", "label": "Low"},
                {"value": "Lowest", "label": "Lowest"},
            ],
            description="New priority.",
        ),
        NodeField(
            name="assignee",
            label="Assignee",
            type=FieldType.STRING,
            required=False,
            description="New assignee account ID.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the issue was updated.",
        ),
        NodeField(
            name="issue_key",
            label="Issue Key",
            type=FieldType.STRING,
            description="Updated issue key.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Update Jira issue."""
        import httpx

        domain, email, api_token = _get_auth(config)

        if not domain:
            raise ValueError("Jira domain is required")
        if not email or not api_token:
            raise ValueError("Email and API token are required")

        issue_key = config.get("issue_key", "")
        if not issue_key:
            raise ValueError("Issue key is required")

        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

        headers = {
            "Authorization": _make_auth_header(email, api_token),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Build update fields
        fields = {}

        summary = config.get("summary")
        if summary:
            fields["summary"] = summary

        description = config.get("description")
        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            }

        priority = config.get("priority")
        if priority:
            fields["priority"] = {"name": priority}

        assignee = config.get("assignee")
        if assignee:
            fields["assignee"] = {"accountId": assignee}

        if not fields:
            return {
                "success": True,
                "issue_key": issue_key,
            }

        body = {"fields": fields}
        url = f"https://{domain}/rest/api/3/issue/{issue_key}"

        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers, json=body)

            if response.status_code in (200, 204):
                return {
                    "success": True,
                    "issue_key": issue_key,
                }
            else:
                return {
                    "success": False,
                    "issue_key": issue_key,
                }


class JiraAddCommentNode(BaseNode):
    """
    Add a comment to a Jira issue.
    """

    type = "jira-add-comment"
    name = "Jira: Add Comment"
    category = "Apps"
    description = "Add a comment to an issue"
    icon = "comment"
    color = "#0052CC"

    inputs = [
        NodeField(
            name="credential",
            label="Jira Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Jira credential.",
            credential_service="jira",
        ),
        NodeField(
            name="domain",
            label="Jira Domain",
            type=FieldType.STRING,
            required=False,
            description="Your Jira domain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=False,
            description="Your Atlassian account email.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.SECRET,
            required=False,
            description="Jira API token.",
        ),
        NodeField(
            name="issue_key",
            label="Issue Key",
            type=FieldType.STRING,
            required=True,
            description="Issue key (e.g., PROJ-123).",
        ),
        NodeField(
            name="comment",
            label="Comment",
            type=FieldType.TEXT,
            required=True,
            description="Comment text.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the comment was added.",
        ),
        NodeField(
            name="comment_id",
            label="Comment ID",
            type=FieldType.STRING,
            description="ID of the created comment.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Add comment to Jira issue."""
        import httpx

        domain, email, api_token = _get_auth(config)

        if not domain:
            raise ValueError("Jira domain is required")
        if not email or not api_token:
            raise ValueError("Email and API token are required")

        issue_key = config.get("issue_key", "")
        if not issue_key:
            raise ValueError("Issue key is required")

        comment = config.get("comment", "")
        if not comment:
            raise ValueError("Comment text is required")

        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

        headers = {
            "Authorization": _make_auth_header(email, api_token),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Atlassian Document Format
        body = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": comment}
                        ]
                    }
                ]
            }
        }

        url = f"https://{domain}/rest/api/3/issue/{issue_key}/comment"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)

            if response.status_code in (200, 201):
                data = response.json()
                return {
                    "success": True,
                    "comment_id": data.get("id", ""),
                }
            else:
                return {
                    "success": False,
                    "comment_id": "",
                }


class JiraTransitionIssueNode(BaseNode):
    """
    Transition a Jira issue to a different status.
    """

    type = "jira-transition-issue"
    name = "Jira: Transition Issue"
    category = "Apps"
    description = "Change issue status"
    icon = "swap_horiz"
    color = "#0052CC"

    inputs = [
        NodeField(
            name="credential",
            label="Jira Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Jira credential.",
            credential_service="jira",
        ),
        NodeField(
            name="domain",
            label="Jira Domain",
            type=FieldType.STRING,
            required=False,
            description="Your Jira domain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=False,
            description="Your Atlassian account email.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.SECRET,
            required=False,
            description="Jira API token.",
        ),
        NodeField(
            name="issue_key",
            label="Issue Key",
            type=FieldType.STRING,
            required=True,
            description="Issue key (e.g., PROJ-123).",
        ),
        NodeField(
            name="transition_id",
            label="Transition ID",
            type=FieldType.STRING,
            required=True,
            description="ID of the transition to perform.",
        ),
        NodeField(
            name="comment",
            label="Comment",
            type=FieldType.TEXT,
            required=False,
            description="Optional comment to add with transition.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the transition was successful.",
        ),
        NodeField(
            name="issue_key",
            label="Issue Key",
            type=FieldType.STRING,
            description="Transitioned issue key.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Transition Jira issue."""
        import httpx

        domain, email, api_token = _get_auth(config)

        if not domain:
            raise ValueError("Jira domain is required")
        if not email or not api_token:
            raise ValueError("Email and API token are required")

        issue_key = config.get("issue_key", "")
        if not issue_key:
            raise ValueError("Issue key is required")

        transition_id = config.get("transition_id", "")
        if not transition_id:
            raise ValueError("Transition ID is required")

        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

        headers = {
            "Authorization": _make_auth_header(email, api_token),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        body = {
            "transition": {"id": transition_id}
        }

        # Add comment if provided
        comment = config.get("comment")
        if comment:
            body["update"] = {
                "comment": [
                    {
                        "add": {
                            "body": {
                                "type": "doc",
                                "version": 1,
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {"type": "text", "text": comment}
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                ]
            }

        url = f"https://{domain}/rest/api/3/issue/{issue_key}/transitions"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)

            if response.status_code in (200, 204):
                return {
                    "success": True,
                    "issue_key": issue_key,
                }
            else:
                return {
                    "success": False,
                    "issue_key": issue_key,
                }


class JiraGetTransitionsNode(BaseNode):
    """
    Get available transitions for a Jira issue.
    """

    type = "jira-get-transitions"
    name = "Jira: Get Transitions"
    category = "Apps"
    description = "Get available status transitions for an issue"
    icon = "list"
    color = "#0052CC"

    inputs = [
        NodeField(
            name="credential",
            label="Jira Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Jira credential.",
            credential_service="jira",
        ),
        NodeField(
            name="domain",
            label="Jira Domain",
            type=FieldType.STRING,
            required=False,
            description="Your Jira domain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=False,
            description="Your Atlassian account email.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.SECRET,
            required=False,
            description="Jira API token.",
        ),
        NodeField(
            name="issue_key",
            label="Issue Key",
            type=FieldType.STRING,
            required=True,
            description="Issue key (e.g., PROJ-123).",
        ),
    ]

    outputs = [
        NodeField(
            name="transitions",
            label="Transitions",
            type=FieldType.JSON,
            description="Available transitions.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of available transitions.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Get available Jira transitions."""
        import httpx

        domain, email, api_token = _get_auth(config)

        if not domain:
            raise ValueError("Jira domain is required")
        if not email or not api_token:
            raise ValueError("Email and API token are required")

        issue_key = config.get("issue_key", "")
        if not issue_key:
            raise ValueError("Issue key is required")

        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

        headers = {
            "Authorization": _make_auth_header(email, api_token),
            "Accept": "application/json",
        }

        url = f"https://{domain}/rest/api/3/issue/{issue_key}/transitions"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                transitions = data.get("transitions", [])
                return {
                    "transitions": transitions,
                    "count": len(transitions),
                }
            else:
                return {
                    "transitions": [],
                    "count": 0,
                }
