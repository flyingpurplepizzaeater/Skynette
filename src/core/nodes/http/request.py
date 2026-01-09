"""
HTTP Request Node

Makes HTTP requests to external APIs.
"""

from typing import Any
import httpx

from src.core.nodes.base import HTTPNode, NodeField, NodeOutput, FieldType


class HTTPRequestNode(HTTPNode):
    """HTTP Request node - makes HTTP calls to APIs."""

    type = "http_request"
    name = "HTTP Request"
    description = "Make an HTTP request to any URL"
    icon = "http"

    @classmethod
    def get_inputs(cls) -> list[NodeField]:
        return [
            NodeField(
                name="method",
                label="Method",
                type=FieldType.SELECT,
                description="HTTP method",
                required=True,
                default="GET",
                options=[
                    {"label": "GET", "value": "GET"},
                    {"label": "POST", "value": "POST"},
                    {"label": "PUT", "value": "PUT"},
                    {"label": "PATCH", "value": "PATCH"},
                    {"label": "DELETE", "value": "DELETE"},
                    {"label": "HEAD", "value": "HEAD"},
                    {"label": "OPTIONS", "value": "OPTIONS"},
                ],
            ),
            NodeField(
                name="url",
                label="URL",
                type=FieldType.EXPRESSION,
                description="The URL to request",
                required=True,
                placeholder="https://api.example.com/endpoint",
            ),
            NodeField(
                name="headers",
                label="Headers",
                type=FieldType.JSON,
                description="HTTP headers as JSON object",
                required=False,
                default={},
            ),
            NodeField(
                name="query_params",
                label="Query Parameters",
                type=FieldType.JSON,
                description="URL query parameters as JSON object",
                required=False,
                default={},
            ),
            NodeField(
                name="body",
                label="Body",
                type=FieldType.JSON,
                description="Request body (for POST/PUT/PATCH)",
                required=False,
                default={},
            ),
            NodeField(
                name="body_type",
                label="Body Type",
                type=FieldType.SELECT,
                description="Content type for the body",
                required=False,
                default="json",
                options=[
                    {"label": "JSON", "value": "json"},
                    {"label": "Form Data", "value": "form"},
                    {"label": "Raw", "value": "raw"},
                ],
            ),
            NodeField(
                name="timeout",
                label="Timeout (seconds)",
                type=FieldType.NUMBER,
                description="Request timeout",
                required=False,
                default=30,
                min_value=1,
                max_value=300,
            ),
            NodeField(
                name="follow_redirects",
                label="Follow Redirects",
                type=FieldType.BOOLEAN,
                description="Automatically follow redirects",
                required=False,
                default=True,
            ),
        ]

    @classmethod
    def get_outputs(cls) -> list[NodeOutput]:
        return [
            NodeOutput(
                name="status",
                type="number",
                description="HTTP status code",
            ),
            NodeOutput(
                name="body",
                type="object",
                description="Response body (parsed as JSON if possible)",
            ),
            NodeOutput(
                name="headers",
                type="object",
                description="Response headers",
            ),
            NodeOutput(
                name="ok",
                type="boolean",
                description="True if status is 2xx",
            ),
        ]

    async def execute(self, config: dict, context: dict) -> Any:
        """Execute the HTTP request."""
        method = config.get("method", "GET")
        url = config.get("url")
        headers = config.get("headers", {})
        query_params = config.get("query_params", {})
        body = config.get("body", {})
        body_type = config.get("body_type", "json")
        timeout = config.get("timeout", 30)
        follow_redirects = config.get("follow_redirects", True)

        if not url:
            raise ValueError("URL is required")

        # Build request kwargs
        kwargs = {
            "method": method,
            "url": url,
            "headers": headers,
            "params": query_params,
            "timeout": timeout,
            "follow_redirects": follow_redirects,
        }

        # Add body for methods that support it
        if method in ["POST", "PUT", "PATCH"]:
            if body_type == "json":
                kwargs["json"] = body
            elif body_type == "form":
                kwargs["data"] = body
            else:
                kwargs["content"] = str(body)

        # Make the request
        async with httpx.AsyncClient() as client:
            response = await client.request(**kwargs)

        # Parse response body
        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        return {
            "status": response.status_code,
            "body": response_body,
            "headers": dict(response.headers),
            "ok": response.is_success,
        }
