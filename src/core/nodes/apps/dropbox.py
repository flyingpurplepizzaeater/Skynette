"""
Dropbox Integration Nodes - Upload, download, and manage files.

Uses Dropbox API v2 for file operations.
"""

import base64

from src.core.nodes.base import BaseNode, FieldType, NodeField


def _get_credential(credential_id: str | None) -> dict | None:
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


def _get_access_token(config: dict) -> str:
    """Get access token from config or credential."""
    credential_id = config.get("credential")
    cred_data = _get_credential(credential_id) if credential_id else None

    if cred_data:
        return cred_data.get("access_token", "")

    return config.get("access_token", "")


class DropboxListNode(BaseNode):
    """
    List files and folders in Dropbox.

    Supports:
    - Listing folder contents
    - Recursive listing
    - Filtering by type
    """

    type = "dropbox-list"
    name = "Dropbox: List Files"
    category = "Apps"
    description = "List files and folders in Dropbox"
    icon = "folder"
    color = "#0061FF"  # Dropbox blue

    inputs = [
        NodeField(
            name="credential",
            label="Dropbox Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Dropbox credential.",
            credential_service="dropbox_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Dropbox access token (or use saved credential).",
        ),
        NodeField(
            name="path",
            label="Folder Path",
            type=FieldType.STRING,
            required=False,
            default="",
            description="Folder path to list (empty for root).",
        ),
        NodeField(
            name="recursive",
            label="Recursive",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="List files recursively in subfolders.",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=100,
            description="Maximum number of entries to return.",
        ),
    ]

    outputs = [
        NodeField(
            name="entries",
            label="Entries",
            type=FieldType.JSON,
            description="List of files and folders.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of entries returned.",
        ),
        NodeField(
            name="has_more",
            label="Has More",
            type=FieldType.BOOLEAN,
            description="Whether there are more entries to fetch.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List files in Dropbox."""
        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required")

        path = config.get("path", "")
        recursive = config.get("recursive", False)
        limit = min(config.get("limit", 100), 2000)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        body = {
            "path": path if path else "",
            "recursive": recursive,
            "limit": limit,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.dropboxapi.com/2/files/list_folder",
                json=body,
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                entries = data.get("entries", [])

                # Simplify entry data
                simplified = []
                for entry in entries:
                    simplified.append(
                        {
                            "name": entry.get("name"),
                            "path": entry.get("path_display"),
                            "type": entry.get(".tag"),
                            "size": entry.get("size", 0),
                            "modified": entry.get("client_modified", ""),
                            "id": entry.get("id"),
                        }
                    )

                return {
                    "entries": simplified,
                    "count": len(simplified),
                    "has_more": data.get("has_more", False),
                }
            else:
                return {
                    "entries": [],
                    "count": 0,
                    "has_more": False,
                }


class DropboxDownloadNode(BaseNode):
    """
    Download files from Dropbox.
    """

    type = "dropbox-download"
    name = "Dropbox: Download"
    category = "Apps"
    description = "Download a file from Dropbox"
    icon = "cloud_download"
    color = "#0061FF"

    inputs = [
        NodeField(
            name="credential",
            label="Dropbox Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Dropbox credential.",
            credential_service="dropbox_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Dropbox access token (or use saved credential).",
        ),
        NodeField(
            name="path",
            label="File Path",
            type=FieldType.STRING,
            required=True,
            description="Path to the file to download.",
        ),
    ]

    outputs = [
        NodeField(
            name="content",
            label="Content",
            type=FieldType.STRING,
            description="File content (base64 encoded for binary).",
        ),
        NodeField(
            name="filename",
            label="Filename",
            type=FieldType.STRING,
            description="Original filename.",
        ),
        NodeField(
            name="size",
            label="Size",
            type=FieldType.NUMBER,
            description="File size in bytes.",
        ),
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether download was successful.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Download file from Dropbox."""
        import json

        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required")

        path = config.get("path", "")
        if not path:
            raise ValueError("File path is required")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Dropbox-API-Arg": json.dumps({"path": path}),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://content.dropboxapi.com/2/files/download",
                headers=headers,
            )

            if response.status_code == 200:
                content = response.content
                # Get metadata from response header
                metadata = json.loads(response.headers.get("Dropbox-API-Result", "{}"))

                return {
                    "content": base64.b64encode(content).decode("utf-8"),
                    "filename": metadata.get("name", path.split("/")[-1]),
                    "size": len(content),
                    "success": True,
                }
            else:
                return {
                    "content": "",
                    "filename": "",
                    "size": 0,
                    "success": False,
                }


class DropboxUploadNode(BaseNode):
    """
    Upload files to Dropbox.
    """

    type = "dropbox-upload"
    name = "Dropbox: Upload"
    category = "Apps"
    description = "Upload a file to Dropbox"
    icon = "cloud_upload"
    color = "#0061FF"

    inputs = [
        NodeField(
            name="credential",
            label="Dropbox Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Dropbox credential.",
            credential_service="dropbox_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Dropbox access token (or use saved credential).",
        ),
        NodeField(
            name="path",
            label="Destination Path",
            type=FieldType.STRING,
            required=True,
            description="Full path including filename (e.g., /folder/file.txt).",
        ),
        NodeField(
            name="content",
            label="Content",
            type=FieldType.TEXT,
            required=True,
            description="File content (text or base64 for binary).",
        ),
        NodeField(
            name="is_base64",
            label="Content is Base64",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Set to true if content is base64 encoded.",
        ),
        NodeField(
            name="mode",
            label="Write Mode",
            type=FieldType.SELECT,
            required=False,
            default="add",
            options=[
                {"value": "add", "label": "Add (fail if exists)"},
                {"value": "overwrite", "label": "Overwrite"},
            ],
            description="What to do if file already exists.",
        ),
    ]

    outputs = [
        NodeField(
            name="path",
            label="Path",
            type=FieldType.STRING,
            description="Path of the uploaded file.",
        ),
        NodeField(
            name="id",
            label="File ID",
            type=FieldType.STRING,
            description="Dropbox file ID.",
        ),
        NodeField(
            name="size",
            label="Size",
            type=FieldType.NUMBER,
            description="File size in bytes.",
        ),
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether upload was successful.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Upload file to Dropbox."""
        import json

        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required")

        path = config.get("path", "")
        content = config.get("content", "")
        is_base64 = config.get("is_base64", False)
        mode = config.get("mode", "add")

        if not path:
            raise ValueError("Destination path is required")

        # Prepare content
        if is_base64:
            file_content = base64.b64decode(content)
        else:
            file_content = content.encode("utf-8")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": json.dumps(
                {
                    "path": path,
                    "mode": mode,
                    "autorename": False,
                    "mute": False,
                }
            ),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://content.dropboxapi.com/2/files/upload",
                content=file_content,
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "path": data.get("path_display", ""),
                    "id": data.get("id", ""),
                    "size": data.get("size", len(file_content)),
                    "success": True,
                }
            else:
                return {
                    "path": "",
                    "id": "",
                    "size": 0,
                    "success": False,
                }


class DropboxCreateFolderNode(BaseNode):
    """
    Create folders in Dropbox.
    """

    type = "dropbox-create-folder"
    name = "Dropbox: Create Folder"
    category = "Apps"
    description = "Create a new folder in Dropbox"
    icon = "create_new_folder"
    color = "#0061FF"

    inputs = [
        NodeField(
            name="credential",
            label="Dropbox Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Dropbox credential.",
            credential_service="dropbox_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Dropbox access token (or use saved credential).",
        ),
        NodeField(
            name="path",
            label="Folder Path",
            type=FieldType.STRING,
            required=True,
            description="Full path for the new folder (e.g., /new-folder).",
        ),
    ]

    outputs = [
        NodeField(
            name="path",
            label="Path",
            type=FieldType.STRING,
            description="Path of the created folder.",
        ),
        NodeField(
            name="id",
            label="Folder ID",
            type=FieldType.STRING,
            description="Dropbox folder ID.",
        ),
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether creation was successful.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Create folder in Dropbox."""
        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required")

        path = config.get("path", "")
        if not path:
            raise ValueError("Folder path is required")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        body = {"path": path, "autorename": False}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.dropboxapi.com/2/files/create_folder_v2",
                json=body,
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                metadata = data.get("metadata", {})
                return {
                    "path": metadata.get("path_display", ""),
                    "id": metadata.get("id", ""),
                    "success": True,
                }
            else:
                return {
                    "path": "",
                    "id": "",
                    "success": False,
                }


class DropboxDeleteNode(BaseNode):
    """
    Delete files or folders from Dropbox.
    """

    type = "dropbox-delete"
    name = "Dropbox: Delete"
    category = "Apps"
    description = "Delete a file or folder from Dropbox"
    icon = "delete"
    color = "#0061FF"

    inputs = [
        NodeField(
            name="credential",
            label="Dropbox Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Dropbox credential.",
            credential_service="dropbox_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Dropbox access token (or use saved credential).",
        ),
        NodeField(
            name="path",
            label="Path",
            type=FieldType.STRING,
            required=True,
            description="Path of the file or folder to delete.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether deletion was successful.",
        ),
        NodeField(
            name="deleted_path",
            label="Deleted Path",
            type=FieldType.STRING,
            description="Path that was deleted.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Delete file or folder from Dropbox."""
        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required")

        path = config.get("path", "")
        if not path:
            raise ValueError("Path is required")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        body = {"path": path}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.dropboxapi.com/2/files/delete_v2",
                json=body,
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                metadata = data.get("metadata", {})
                return {
                    "success": True,
                    "deleted_path": metadata.get("path_display", path),
                }
            else:
                return {
                    "success": False,
                    "deleted_path": "",
                }


class DropboxGetLinkNode(BaseNode):
    """
    Get a shareable link for a Dropbox file.
    """

    type = "dropbox-get-link"
    name = "Dropbox: Get Share Link"
    category = "Apps"
    description = "Get a shareable link for a file or folder"
    icon = "link"
    color = "#0061FF"

    inputs = [
        NodeField(
            name="credential",
            label="Dropbox Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Dropbox credential.",
            credential_service="dropbox_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Dropbox access token (or use saved credential).",
        ),
        NodeField(
            name="path",
            label="Path",
            type=FieldType.STRING,
            required=True,
            description="Path of the file or folder to share.",
        ),
    ]

    outputs = [
        NodeField(
            name="url",
            label="Share URL",
            type=FieldType.STRING,
            description="Shareable URL.",
        ),
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether link creation was successful.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Get shareable link for Dropbox file."""
        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required")

        path = config.get("path", "")
        if not path:
            raise ValueError("Path is required")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Try to create a new shared link
        body = {"path": path, "settings": {"requested_visibility": "public"}}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings",
                json=body,
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "url": data.get("url", ""),
                    "success": True,
                }
            elif response.status_code == 409:
                # Link already exists, get existing links
                list_body = {"path": path}
                list_response = await client.post(
                    "https://api.dropboxapi.com/2/sharing/list_shared_links",
                    json=list_body,
                    headers=headers,
                )

                if list_response.status_code == 200:
                    list_data = list_response.json()
                    links = list_data.get("links", [])
                    if links:
                        return {
                            "url": links[0].get("url", ""),
                            "success": True,
                        }

            return {
                "url": "",
                "success": False,
            }
