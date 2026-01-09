"""
Webhook Nodes - Trigger workflows via HTTP and make webhook calls.
"""

from typing import Any, Optional

from src.core.nodes.base import BaseNode, NodeField, FieldType


class WebhookTriggerNode(BaseNode):
    """
    Webhook Trigger - Start workflow via HTTP request.

    Creates an HTTP endpoint that triggers the workflow when called.
    Supports GET, POST, PUT, DELETE methods.
    """

    type = "webhook-trigger"
    name = "Webhook Trigger"
    category = "Triggers"
    description = "Start workflow when webhook is called"
    icon = "webhook"
    color = "#F59E0B"  # Amber

    inputs = [
        NodeField(
            name="path",
            label="Webhook Path",
            type=FieldType.STRING,
            required=False,
            default="/webhook",
            description="URL path for the webhook (e.g., /my-webhook).",
        ),
        NodeField(
            name="method",
            label="HTTP Method",
            type=FieldType.SELECT,
            required=False,
            default="POST",
            options=[
                {"value": "GET", "label": "GET"},
                {"value": "POST", "label": "POST"},
                {"value": "PUT", "label": "PUT"},
                {"value": "DELETE", "label": "DELETE"},
                {"value": "ANY", "label": "Any Method"},
            ],
            description="Allowed HTTP method(s).",
        ),
        NodeField(
            name="auth_type",
            label="Authentication",
            type=FieldType.SELECT,
            required=False,
            default="none",
            options=[
                {"value": "none", "label": "None"},
                {"value": "header", "label": "Header Token"},
                {"value": "query", "label": "Query Parameter"},
                {"value": "basic", "label": "Basic Auth"},
            ],
            description="Authentication method.",
        ),
        NodeField(
            name="auth_token",
            label="Auth Token/Password",
            type=FieldType.SECRET,
            required=False,
            description="Token or password for authentication.",
        ),
        NodeField(
            name="response_mode",
            label="Response Mode",
            type=FieldType.SELECT,
            required=False,
            default="immediate",
            options=[
                {"value": "immediate", "label": "Respond Immediately"},
                {"value": "wait", "label": "Wait for Workflow"},
            ],
            description="When to send HTTP response.",
        ),
    ]

    outputs = [
        NodeField(
            name="body",
            label="Request Body",
            type=FieldType.JSON,
            description="Parsed request body.",
        ),
        NodeField(
            name="headers",
            label="Request Headers",
            type=FieldType.JSON,
            description="Request headers.",
        ),
        NodeField(
            name="query",
            label="Query Parameters",
            type=FieldType.JSON,
            description="URL query parameters.",
        ),
        NodeField(
            name="method",
            label="HTTP Method",
            type=FieldType.STRING,
            description="HTTP method used.",
        ),
        NodeField(
            name="path",
            label="Request Path",
            type=FieldType.STRING,
            description="Full request path.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """
        Process webhook trigger.

        Note: The actual HTTP server is managed by the workflow engine.
        This node receives data from the trigger context.
        """
        # Get trigger data from context
        trigger_data = context.get("trigger", {})

        return {
            "body": trigger_data.get("body", {}),
            "headers": trigger_data.get("headers", {}),
            "query": trigger_data.get("query", {}),
            "method": trigger_data.get("method", "POST"),
            "path": trigger_data.get("path", config.get("path", "/webhook")),
        }

    def get_webhook_config(self, config: dict) -> dict:
        """Get webhook configuration for the workflow engine."""
        return {
            "path": config.get("path", "/webhook"),
            "method": config.get("method", "POST"),
            "auth_type": config.get("auth_type", "none"),
            "auth_token": config.get("auth_token", ""),
            "response_mode": config.get("response_mode", "immediate"),
        }


class WebhookResponseNode(BaseNode):
    """
    Send HTTP response for webhook trigger.

    Use at the end of a webhook-triggered workflow to send
    a custom response back to the caller.
    """

    type = "webhook-response"
    name = "Webhook Response"
    category = "Triggers"
    description = "Send HTTP response for webhook"
    icon = "reply"
    color = "#F59E0B"

    inputs = [
        NodeField(
            name="status_code",
            label="Status Code",
            type=FieldType.NUMBER,
            required=False,
            default=200,
            description="HTTP status code.",
        ),
        NodeField(
            name="body",
            label="Response Body",
            type=FieldType.JSON,
            required=False,
            description="Response body (JSON or string).",
        ),
        NodeField(
            name="headers",
            label="Response Headers",
            type=FieldType.JSON,
            required=False,
            description="Additional response headers.",
        ),
        NodeField(
            name="content_type",
            label="Content Type",
            type=FieldType.SELECT,
            required=False,
            default="application/json",
            options=[
                {"value": "application/json", "label": "JSON"},
                {"value": "text/plain", "label": "Plain Text"},
                {"value": "text/html", "label": "HTML"},
                {"value": "application/xml", "label": "XML"},
            ],
            description="Response content type.",
        ),
    ]

    outputs = [
        NodeField(
            name="sent",
            label="Response Sent",
            type=FieldType.BOOLEAN,
            description="Whether response was sent.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """
        Set webhook response.

        Note: The actual response sending is handled by the workflow engine.
        This node sets the response in the execution context.
        """
        import json

        status_code = int(config.get("status_code", 200))
        body = config.get("body", {})
        headers = config.get("headers", {})
        content_type = config.get("content_type", "application/json")

        # Ensure body is serializable
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except:
                pass  # Keep as string

        # Set response in context for workflow engine
        context["_webhook_response"] = {
            "status_code": status_code,
            "body": body,
            "headers": {
                "Content-Type": content_type,
                **(headers if isinstance(headers, dict) else {}),
            },
        }

        return {
            "sent": True,
        }


class WebhookCallNode(BaseNode):
    """
    Call an external webhook/HTTP endpoint.

    Makes outgoing HTTP requests with full control over
    method, headers, body, and authentication.
    """

    type = "webhook-call"
    name = "Call Webhook"
    category = "HTTP"
    description = "Make HTTP request to external webhook"
    icon = "send"
    color = "#3B82F6"  # Blue

    inputs = [
        NodeField(
            name="url",
            label="URL",
            type=FieldType.STRING,
            required=True,
            description="Webhook URL to call.",
        ),
        NodeField(
            name="method",
            label="HTTP Method",
            type=FieldType.SELECT,
            required=False,
            default="POST",
            options=[
                {"value": "GET", "label": "GET"},
                {"value": "POST", "label": "POST"},
                {"value": "PUT", "label": "PUT"},
                {"value": "PATCH", "label": "PATCH"},
                {"value": "DELETE", "label": "DELETE"},
            ],
        ),
        NodeField(
            name="body",
            label="Request Body",
            type=FieldType.JSON,
            required=False,
            description="Request body (for POST, PUT, PATCH).",
        ),
        NodeField(
            name="headers",
            label="Headers",
            type=FieldType.JSON,
            required=False,
            description="Request headers as JSON object.",
        ),
        NodeField(
            name="auth_header",
            label="Authorization Header",
            type=FieldType.SECRET,
            required=False,
            description="Authorization header value (e.g., 'Bearer token').",
        ),
        NodeField(
            name="timeout",
            label="Timeout (seconds)",
            type=FieldType.NUMBER,
            required=False,
            default=30,
            description="Request timeout in seconds.",
        ),
    ]

    outputs = [
        NodeField(
            name="response",
            label="Response Body",
            type=FieldType.JSON,
            description="Response body.",
        ),
        NodeField(
            name="status_code",
            label="Status Code",
            type=FieldType.NUMBER,
            description="HTTP response status code.",
        ),
        NodeField(
            name="headers",
            label="Response Headers",
            type=FieldType.JSON,
            description="Response headers.",
        ),
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether request was successful (2xx status).",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Make HTTP request to webhook."""
        import httpx
        import json

        url = config.get("url", "")
        method = config.get("method", "POST")
        body = config.get("body")
        headers = config.get("headers", {})
        auth_header = config.get("auth_header")
        timeout = float(config.get("timeout", 30))

        # Parse headers if string
        if isinstance(headers, str):
            try:
                headers = json.loads(headers)
            except:
                headers = {}

        # Add auth header if provided
        if auth_header:
            headers["Authorization"] = auth_header

        # Parse body if string
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except:
                pass  # Keep as string

        # Make request
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                json=body if isinstance(body, (dict, list)) else None,
                content=body if isinstance(body, str) else None,
                headers=headers,
            )

        # Parse response
        try:
            response_body = response.json()
        except:
            response_body = response.text

        return {
            "response": response_body,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "success": 200 <= response.status_code < 300,
        }
